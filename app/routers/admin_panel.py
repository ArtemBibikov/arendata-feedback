from sqlalchemy import func
from fastapi.responses import RedirectResponse
"""
Admin Panel router for Arenadata Feedback System
Полноценная админ-панель с управлением отзывами, клиентами, аналитикой
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import os
from datetime import datetime

from app.database import get_db
from app.crud import (
    get_feedbacks, get_feedbacks_count, get_stats, get_recent_feedbacks,
    get_form_configs, get_all_form_configs, update_feedback
)
from app.models import Feedback, FormConfig

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

def check_auth(request: Request):
    session = request.session
    return session.get("authenticated") == True

@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login(request: Request):
    if check_auth(request):
        return RedirectResponse(url="/admin", status_code=302)
    
    return templates.TemplateResponse("admin/login.html", {"request": request})

@router.post("/admin/login")
async def admin_login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["authenticated"] = True
        request.session["username"] = username
        return RedirectResponse(url="/admin", status_code=302)
    
    return templates.TemplateResponse("admin/login.html", {
        "request": request,
        "error": "Неверные учетные данные"
    })

@router.get("/admin/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=302)

def get_stats(db: Session):
    total_feedbacks = db.query(Feedback).count()
    high_feedbacks = db.query(Feedback).filter(Feedback.urgency == 'high').count()
    new_feedbacks = db.query(Feedback).filter(Feedback.status == 'new').count()
    resolved_feedbacks = db.query(Feedback).filter(Feedback.status == 'resolved').count()
    
    return {
        "total_feedbacks": total_feedbacks,
        "high_feedbacks": high_feedbacks,
        "new_feedbacks": new_feedbacks,
        "resolved_feedbacks": resolved_feedbacks
    }

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    if not check_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    stats = get_stats(db=db)
    recent_feedbacks = get_recent_feedbacks(db=db, limit=10)
    
    # Получаем данные для графиков
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # Данные за последние 7 дней
    start_date = datetime.utcnow() - timedelta(days=7)
    daily_feedbacks = db.query(
        func.date(Feedback.created_at).label('date'),
        func.count(Feedback.id).label('count')
    ).filter(Feedback.created_at >= start_date).group_by(
        func.date(Feedback.created_at)
    ).all()
    
    # Данные по срочности
    urgency_data = db.query(
        Feedback.urgency,
        func.count(Feedback.id).label('count')
    ).group_by(Feedback.urgency).all()
    
    # Данные по типам форм
    form_types = db.query(
        Feedback.form_type,
        func.count(Feedback.id).label('count')
    ).group_by(Feedback.form_type).all()
    
    # Данные по статусам
    status_data = db.query(
        Feedback.status,
        func.count(Feedback.id).label('count')
    ).group_by(Feedback.status).all()
    
    # Сортируем данные по дням
    daily_sorted = sorted([{"date": str(d.date), "count": d.count} for d in daily_feedbacks], key=lambda x: x["date"])
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_feedbacks": recent_feedbacks,
        "daily_feedbacks": daily_sorted,
        "urgency_data": [{"urgency": u.urgency or "unknown", "count": u.count} for u in urgency_data],
        "form_types": [{"type": f.form_type, "count": f.count} for f in form_types],
        "status_data": [{"status": s.status or "unknown", "count": s.count} for s in status_data]
    })

@router.get("/admin/clients", response_class=HTMLResponse)
async def admin_clients(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    client_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if not check_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    # Возвращаем список клиентов из отзывов с фильтрацией
    feedbacks = get_feedbacks(db=db, skip=skip, limit=limit, form_type=client_type)
    
    # Группируем по клиентам
    clients_data = {}
    for feedback in feedbacks:
        client_email = feedback.client_email or "unknown"
        if client_email not in clients_data:
            clients_data[client_email] = {
                "id": len(clients_data) + 1,
                "company_name": feedback.client_name or "Не указано",
                "client_name": feedback.client_name or "Не указано",
                "client_email": feedback.client_email,
                "client_type": feedback.form_type,  # Тип из отфильтрованных отзывов
                "total_feedbacks": 0,
                "last_feedback_at": feedback.created_at,
                "urgency": feedback.urgency,
                "is_active": True  # Все клиенты активны
            }
        clients_data[client_email]["total_feedbacks"] += 1
        if feedback.created_at > clients_data[client_email]["last_feedback_at"]:
            clients_data[client_email]["last_feedback_at"] = feedback.created_at
    
    clients = list(clients_data.values())
    
    return templates.TemplateResponse("admin/clients.html", {
        "request": request,
        "clients": clients,
        "total": len(clients),
        "filters": {
            "client_type": client_type
        }
    })

@router.get("/admin/analytics", response_class=HTMLResponse)
async def admin_analytics(request: Request, db: Session = Depends(get_db)):
    if not check_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    return templates.TemplateResponse("admin/analytics.html", {
        "request": request
    })

@router.get("/api/admin/analytics/data")
async def get_analytics_data(
    period: str = "week",
    db: Session = Depends(get_db)
):
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    # Определяем период
    if period == "week":
        start_date = datetime.utcnow() - timedelta(days=7)
    elif period == "month":
        start_date = datetime.utcnow() - timedelta(days=30)
    else:  # year
        start_date = datetime.utcnow() - timedelta(days=365)
    
    print(f"Period: {period}, Start date: {start_date}")  # Отладка
    
    # Динамика отзывов по дням
    daily_data = db.query(
        func.date(Feedback.created_at).label('date'),
        func.count(Feedback.id).label('count')
    ).filter(
        Feedback.created_at >= start_date
    ).group_by(
        func.date(Feedback.created_at)
    ).order_by('date').all()
    
    # Формируем данные для графика
    labels = []
    total_counts = []
    high_counts = []
    
    for date, count in daily_data:
        labels.append(date.strftime('%d.%m'))
        total_counts.append(count)
        
        # Считаем высокие за этот день
        high_count = db.query(Feedback).filter(
            func.date(Feedback.created_at) == date,
            Feedback.urgency == 'high'
        ).count()
        high_counts.append(high_count)
    
    # Распределение по типам форм
    form_types = db.query(
        Feedback.form_type,
        func.count(Feedback.id).label('count')
    ).filter(
        Feedback.created_at >= start_date
    ).group_by(Feedback.form_type).all()
    
    form_type_data = {'tech': 0, 'business': 0, 'exec': 0}
    for form_type, count in form_types:
        if form_type in form_type_data:
            form_type_data[form_type] = count
    
    return {
        "labels": labels,
        "total": total_counts,
        "critical": high_counts,
        "form_types": form_type_data
    }

@router.get("/admin/feedbacks", response_class=HTMLResponse)
async def admin_feedbacks(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    form_type: Optional[str] = None,
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if not check_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    feedbacks = get_feedbacks(
        db=db, skip=skip, limit=limit,
        form_type=form_type, status=status, urgency=urgency
    )
    total = get_feedbacks_count(
        db=db, form_type=form_type, status=status, urgency=urgency
    )
    
    return templates.TemplateResponse("admin/feedbacks.html", {
        "request": request,
        "feedbacks": feedbacks,
        "total": total,
        "filters": {
            "form_type": form_type,
            "status": status,
            "urgency": urgency
        }
    })

@router.get("/feedbacks/{feedback_id}", response_class=HTMLResponse)
async def admin_feedback_detail(
    feedback_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    if not check_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    from app.crud import get_feedback
    feedback = get_feedback(db=db, feedback_id=feedback_id)
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    return templates.TemplateResponse("admin/feedback_detail.html", {
        "request": request,
        "feedback": feedback
    })

@router.put("/api/admin/feedbacks/{feedback_id}/status")
async def update_feedback_status(
    feedback_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    response_time = None
    if status == "resolved" and feedback.status != "resolved":
        from datetime import timezone
        now = datetime.now(timezone.utc)
        response_time = int((now - feedback.created_at).total_seconds())
    
    feedback.status = status
    if response_time:
        feedback.response_time_seconds = response_time
    
    db.commit()
    
    return {"success": True, "message": "Статус обновлен"}

@router.get("/admin/form-editor", response_class=HTMLResponse)
async def admin_forms(request: Request, db: Session = Depends(get_db)):
    if not check_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    tech_configs = get_all_form_configs(db=db, form_type="tech")
    business_configs = get_all_form_configs(db=db, form_type="business")
    exec_configs = get_all_form_configs(db=db, form_type="exec")
    
    forms_info = {
        "tech": tech_configs,
        "business": business_configs,
        "exec": exec_configs
    }
    
    return templates.TemplateResponse("admin/forms.html", {
        "request": request,
        "forms_info": forms_info
    })

async def add_form_field(request: Request, 
    form_type: str = Form(...),
    section_name: str = Form(""),
    field_name: str = Form(...),
    field_label: str = Form(...),
    required: bool = Form(False),
    db: Session = Depends(get_db)
):
    try:
        print(f"Adding field: {form_type}, {section_name}, {field_name}, {field_label}, {required}")
        
        # Проверяем обязательные поля
        if not all([form_type, field_name, field_label]):
            missing_fields = []
            if not form_type: missing_fields.append("form_type")
            if not field_name: missing_fields.append("field_name")
            if not field_label: missing_fields.append("field_label")
            
            return {"success": False, "error": f"Missing required fields: {', '.join(missing_fields)}"}
        
        # Создаем новую конфигурацию поля
        new_config = FormConfig(
            form_type=form_type,
            section_name=section_name,
            field_name=field_name,
            field_label=field_label,
            field_type="text",  # Фиксированный тип
            required=required,
            is_active=True,
            field_order=0
        )
        
        db.add(new_config)
        db.commit()
        db.refresh(new_config)
        
        print(f"Field added with ID: {new_config.id}")
        
        return {"success": True, "message": "field added", "field_id": new_config.id}
    
    except Exception as e:
        print(f"Error adding field: {str(e)}")
        return {"success": False, "error": str(e)}


async def toggle_form_field(
    config_id: int,
    is_active: bool = Form(...),
    db: Session = Depends(get_db)
):
    config = db.query(FormConfig).filter(FormConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="field not found")
    
    config.is_active = is_active
    db.commit()
    
    return {"message": f"field {config.field_name} {'activated' if is_active else 'deactivated'}"}

async def reorder_form_fields(
    field_orders: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        print(f"Reordering fields: {field_orders}")
        
        # Парсим строку с порядком полей
        # Формат: "field_id1:new_order1,field_id2:new_order2"
        for item in field_orders.split(','):
            if ':' not in item:
                continue
                
            field_id, new_order = item.split(':')
            field_id = int(field_id.strip())
            new_order = int(new_order.strip())
            
            # Обновляем порядок поля
            config = db.query(FormConfig).filter(FormConfig.id == field_id).first()
            if config:
                config.field_order = new_order
                print(f"Updated field {field_id} order to {new_order}")
        
        db.commit()
        return {"success": True, "message": "Poryadok poley obnovlen"}
        
    except Exception as e:
        print(f"Error reordering fields: {str(e)}")
        return {"success": False, "error": str(e)}

async def delete_form_field(
    config_id: int,
    db: Session = Depends(get_db)
):
    config = db.query(FormConfig).filter(FormConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="field not found")
    
    db.delete(config)
    db.commit()
    
    return {"success": True, "message": "field deleted"}

async def update_form_field(
    config_id: int,
    field_label: str = Form(...),
    field_type: str = Form("text"),
    required: bool = Form(False),
    is_active: bool = Form(True),
    db: Session = Depends(get_db)
):
    print(f"Updating field {config_id}: {field_label}, {field_type}, {required}, {is_active}")
    
    config = db.query(FormConfig).filter(FormConfig.id == config_id).first()
    if not config:
        print(f"Field {config_id} not found")
        raise HTTPException(status_code=404, detail="field not found")
    
    print(f"Before update: {config.field_label}, {config.field_type}")
    
    config.field_label = field_label
    config.field_type = field_type
    config.required = required
    config.is_active = is_active
    
    db.commit()
    
    print(f"After update: {config.field_label}, {config.field_type}")
    
    return {"success": True, "message": "saved"}

@router.get("/admin/forms/status")
async def forms_status():
    return {"status": "ok", "reload": False}

@router.get("/admin/export/feedbacks/csv")
async def export_feedbacks_csv(
    form_type: Optional[str] = None,
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    db: Session = Depends(get_db)
):
    import csv
    from io import StringIO
    
    feedbacks = get_feedbacks(
        db=db, skip=0, limit=10000,
        form_type=form_type, status=status, urgency=urgency
    )
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow([
        'ID', 'UUID', 'Тип формы', 'Клиент', 'Email', 'Проблема', 
        'Срочность', 'Категория', 'Статус', 'Приоритет', 'Создан'
    ])
    
    # Данные
    for feedback in feedbacks:
        writer.writerow([
            feedback.id,
            feedback.uuid,
            feedback.form_type,
            feedback.client_name or '',
            feedback.client_email or '',
            feedback.problem_text or '',
            feedback.urgency or '',
            feedback.category or '',
            feedback.status or '',
            feedback.priority_score or 0,
            feedback.created_at.strftime('%d.%m.%Y %H:%M')
        ])
    
    output.seek(0)
    
    from fastapi.responses import Response
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=feedbacks.csv"}
    )

@router.get("/admin/export/feedbacks/excel")
async def export_feedbacks_excel(
    form_type: Optional[str] = None,
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    db: Session = Depends(get_db)
):
    import pandas as pd
    
    feedbacks = get_feedbacks(
        db=db, skip=0, limit=10000,
        form_type=form_type, status=status, urgency=urgency
    )
    
    # Конвертируем в DataFrame
    data = []
    for feedback in feedbacks:
        data.append({
            'ID': feedback.id,
            'UUID': feedback.uuid,
            'Тип формы': feedback.form_type,
            'Клиент': feedback.client_name or '',
            'Email': feedback.client_email or '',
            'Проблема': feedback.problem_text or '',
            'Срочность': feedback.urgency or '',
            'Категория': feedback.category or '',
            'Статус': feedback.status or '',
            'Приоритет': feedback.priority_score or 0,
            'Создан': feedback.created_at.strftime('%d.%m.%Y %H:%M')
        })
    
    df = pd.DataFrame(data)
    
    # Создаем Excel файл в памяти
    from io import BytesIO
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Отзывы')
        
        # Добавляем форматирование
        worksheet = writer.sheets['Отзывы']
        worksheet.column_dimensions['A'].width = 10
        worksheet.column_dimensions['B'].width = 40
        worksheet.column_dimensions['C'].width = 15
        worksheet.column_dimensions['D'].width = 20
        worksheet.column_dimensions['E'].width = 30
        worksheet.column_dimensions['F'].width = 15
        worksheet.column_dimensions['G'].width = 20
        worksheet.column_dimensions['H'].width = 15
        worksheet.column_dimensions['I'].width = 15
        worksheet.column_dimensions['J'].width = 20
    
    output.seek(0)
    
    from fastapi.responses import Response
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=feedbacks.xlsx"}
    )

@router.get("/admin/export/clients/csv")
async def export_clients_csv(db: Session = Depends(get_db)):
    import csv
    from io import StringIO
    
    feedbacks = get_feedbacks(db=db, skip=0, limit=10000)
    
    # Группируем по клиентам
    clients_data = {}
    for feedback in feedbacks:
        client_email = feedback.client_email or "unknown"
        if client_email not in clients_data:
            clients_data[client_email] = {
                "client_name": feedback.client_name,
                "client_email": feedback.client_email,
                "form_type": feedback.form_type,
                "total_feedbacks": 0,
                "last_feedback": feedback.created_at,
                "urgency": feedback.urgency
            }
        clients_data[client_email]["total_feedbacks"] += 1
        if feedback.created_at > clients_data[client_email]["last_feedback"]:
            clients_data[client_email]["last_feedback"] = feedback.created_at
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow([
        'Имя клиента', 'Email', 'Тип формы', 'Всего отзывов', 'Последний отзыв', 'Срочность'
    ])
    
    # Данные
    for client_data in clients_data.values():
        writer.writerow([
            client_data["client_name"] or '',
            client_data["client_email"] or '',
            client_data["form_type"] or '',
            client_data["total_feedbacks"],
            client_data["last_feedback"].strftime('%d.%m.%Y %H:%M') if client_data["last_feedback"] else '',
            client_data["urgency"] or ''
        ])
    
    output.seek(0)
    
    from fastapi.responses import Response
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=clients.csv"}
    )

@router.get("/admin/export/clients/excel")
async def export_clients_excel(db: Session = Depends(get_db)):
    import pandas as pd
    
    feedbacks = get_feedbacks(db=db, skip=0, limit=10000)
    
    # Группируем по клиентам
    clients_data = {}
    for feedback in feedbacks:
        client_email = feedback.client_email or "unknown"
        if client_email not in clients_data:
            clients_data[client_email] = {
                "client_name": feedback.client_name,
                "client_email": feedback.client_email,
                "form_type": feedback.form_type,
                "total_feedbacks": 0,
                "last_feedback": feedback.created_at,
                "urgency": feedback.urgency
            }
        clients_data[client_email]["total_feedbacks"] += 1
        if feedback.created_at > clients_data[client_email]["last_feedback"]:
            clients_data[client_email]["last_feedback"] = feedback.created_at
    
    # Конвертируем в DataFrame
    data = []
    for client_data in clients_data.values():
        data.append({
            'Имя клиента': client_data["client_name"] or '',
            'Email': client_data["client_email"] or '',
            'Тип формы': client_data["form_type"] or '',
            'Всего отзывов': client_data["total_feedbacks"],
            'Последний отзыв': client_data["last_feedback"].strftime('%d.%m.%Y %H:%M') if client_data["last_feedback"] else '',
            'Срочность': client_data["urgency"] or ''
        })
    
    df = pd.DataFrame(data)
    
    # Создаем Excel файл в памяти
    from io import BytesIO
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Клиенты')
        
        # Добавляем форматирование
        worksheet = writer.sheets['Клиенты']
        worksheet.column_dimensions['A'].width = 25
        worksheet.column_dimensions['B'].width = 30
        worksheet.column_dimensions['C'].width = 15
        worksheet.column_dimensions['D'].width = 15
        worksheet.column_dimensions['E'].width = 20
        worksheet.column_dimensions['F'].width = 15
    
    output.seek(0)
    
    from fastapi.responses import Response
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=clients.xlsx"}
    )

@router.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings(request: Request, db: Session = Depends(get_db)):
    if not check_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    # Получаем настройки из переменных окружения
    settings = {
        "admin_username": ADMIN_USERNAME,
        "admin_password": ADMIN_PASSWORD,
        "telegram_enabled": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        "smtp_enabled": bool(os.getenv("SMTP_HOST")),
        "smtp_host": os.getenv("SMTP_HOST", ""),
        "smtp_port": os.getenv("SMTP_PORT", "587"),
        "smtp_username": os.getenv("SMTP_USERNAME", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "db_host": os.getenv("DATABASE_URL", "").split("@")[-1].split(":")[0] if os.getenv("DATABASE_URL") else ""
    }
    
    return templates.TemplateResponse("admin/settings.html", {
        "request": request,
        "settings": settings
    })

@router.post("/admin/settings")
async def admin_settings_post(
    request: Request,
    admin_password: str = Form(""),
    telegram_enabled: bool = Form(False),
    telegram_bot_token: str = Form(""),
    telegram_chat_id: str = Form(""),
    smtp_enabled: bool = Form(False),
    smtp_host: str = Form(""),
    smtp_port: str = Form("587"),
    smtp_username: str = Form(""),
    smtp_password: str = Form(""),
    db: Session = Depends(get_db)
):
    if not check_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    # Здесь можно сохранить настройки в файл или базу данных
    # Для простоты пока просто возвращаем сообщение
    
    success_message = "Настройки сохранены"
    
    return templates.TemplateResponse("admin/settings.html", {
        "request": request,
        "settings": {
            "admin_username": ADMIN_USERNAME,
            "admin_password": admin_password,
            "telegram_enabled": telegram_enabled,
            "telegram_bot_token": telegram_bot_token,
            "telegram_chat_id": telegram_chat_id,
            "smtp_enabled": smtp_enabled,
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "smtp_username": smtp_username,
            "smtp_password": smtp_password,
            "db_host": os.getenv("DATABASE_URL", "").split("@")[-1].split(":")[0] if os.getenv("DATABASE_URL") else ""
        },
        "success_message": success_message
    })


@router.get("/admin", response_class=HTMLResponse, summary="Главная админка")
async def admin_home(request: Request, db: Session = Depends(get_db)):
    """Главная страница админки с редиректом на дашборд"""
    return RedirectResponse(url="/admin/dashboard", status_code=302)

@router.get("/test", response_class=HTMLResponse)
async def test_route():
    return "<h1>Test route works</h1>"


@router.get("/admin/form-editor", response_class=HTMLResponse)
async def form_editor(request: Request, db: Session = Depends(get_db)):
    """Простой редактор форм"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Редактор форм</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>Редактор форм работает!</h1>
        <p>Здесь будет редактор форм</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

async def admin_forms(request: Request, db: Session = Depends(get_db)):
    """Редактор форм"""
    if not check_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    tech_configs = get_all_form_configs(db=db, form_type="tech")
    business_configs = get_all_form_configs(db=db, form_type="business")
    exec_configs = get_all_form_configs(db=db, form_type="exec")
    
    forms_info = {
        "tech": tech_configs,
        "business": business_configs,
        "exec": exec_configs
    }
    
    return templates.TemplateResponse("admin/forms.html", {"request": request, "forms_info": forms_info})

async def admin_forms_simple(request: Request, db: Session = Depends(get_db)):
    """Простой редактор форм"""
    return "<h1>Forms page works!</h1>"


async def form_manager(request: Request):
    """Менеджер форм"""
    return "<h1>Form Manager Works!</h1>"


async def admin_forms_final(request: Request):
    """Финальный редактор форм"""
    return "<h1>Forms Page Finally Works!</h1>"


@router.get("/admin/forms", response_class=HTMLResponse)
async def admin_forms(request: Request, db: Session = Depends(get_db)):
    """Полный редактор форм"""
    if not check_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    try:
        tech_configs = get_all_form_configs(db=db, form_type="tech")
        business_configs = get_all_form_configs(db=db, form_type="business")
        exec_configs = get_all_form_configs(db=db, form_type="exec")
        
        forms_info = {
            "tech": tech_configs,
            "business": business_configs,
            "exec": exec_configs
        }
        
        return templates.TemplateResponse("admin/forms.html", {"request": request, "forms_info": forms_info})
    except Exception as e:
        return f"<h1>Error loading forms: {str(e)}</h1>"

@router.post("/admin/forms/add")
async def add_form_field(request: Request, 
    form_type: str = Form(...),
    section_name: str = Form(""),
    field_name: str = Form(...),
    field_label: str = Form(...),
    field_type: str = Form("text"),
    required: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Добавить новое поле в форму"""
    if not check_auth(request):
        return {"success": False, "error": "Unauthorized"}
    
    try:
        # Получаем максимальный порядок для текущей формы
        max_order = db.query(func.max(FormConfig.field_order)).filter(
            FormConfig.form_type == form_type
        ).scalar() or 0
        
        new_field = FormConfig(
            form_type=form_type,
            section_name=section_name or "main",
            field_name=field_name,
            field_label=field_label,
            field_type=field_type,
            required=required,
            is_active=True,
            field_order=max_order + 1
        )
        
        db.add(new_field)
        db.commit()
        db.refresh(new_field)
        
        return {"success": True, "message": "Field added successfully", "field_id": new_field.id}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

@router.post("/admin/forms/{config_id}/update")
async def update_form_field(
    config_id: int,
    request: Request,
    field_label: str = Form(...),
    required: bool = Form(False),
    is_active: bool = Form(True),
    db: Session = Depends(get_db)
):
    """Обновить поле формы"""
    if not check_auth(request):
        return {"success": False, "error": "Unauthorized"}
    
    try:
        field = db.query(FormConfig).filter(FormConfig.id == config_id).first()
        if not field:
            return {"success": False, "error": "Field not found"}
        
        field.field_label = field_label
        field.required = required
        field.is_active = is_active
        
        db.commit()
        
        return {"success": True, "message": "Field updated successfully"}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

@router.post("/admin/forms/{config_id}/delete")
async def delete_form_field(
    config_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Удалить поле формы"""
    if not check_auth(request):
        return {"success": False, "error": "Unauthorized"}
    
    try:
        field = db.query(FormConfig).filter(FormConfig.id == config_id).first()
        if not field:
            return {"success": False, "error": "Field not found"}
        
        db.delete(field)
        db.commit()
        
        return {"success": True, "message": "Field deleted successfully"}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

@router.post("/admin/forms/reorder")
async def reorder_form_fields(
    request: Request,
    field_orders: str = Form(...),
    db: Session = Depends(get_db)
):
    """Изменить порядок полей формы"""
    if not check_auth(request):
        return {"success": False, "error": "Unauthorized"}
    
    try:
        # Парсим строку формата "id1:order1,id2:order2"
        for pair in field_orders.split(","):
            field_id, order = pair.split(":")
            field_id = int(field_id)
            order = int(order)
            
            field = db.query(FormConfig).filter(FormConfig.id == field_id).first()
            if field:
                field.field_order = order
        
        db.commit()
        
        return {"success": True, "message": "Field order updated successfully"}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
