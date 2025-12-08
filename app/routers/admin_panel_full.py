"""
Admin Panel router for Arenadata Feedback System
Полноценная админ-панель с управлением отзывами, формами, аналитикой
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

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    if not check_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    stats = get_stats(db=db)
    recent_feedbacks = get_recent_feedbacks(db=db, limit=10)
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_feedbacks": recent_feedbacks
    })

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

@router.get("/admin/feedbacks/{feedback_id}", response_class=HTMLResponse)
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
    from app.models import Feedback
    from datetime import datetime
    
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    response_time = None
    if status == "resolved" and feedback.status != "resolved":
        response_time = int((datetime.utcnow() - feedback.created_at).total_seconds())
    
    feedback_update = {
        "status": status,
        "response_time_seconds": response_time
    }
    
    updated = update_feedback(db=db, feedback_id=feedback_id, feedback=feedback_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    return {"message": f"Отзыв {feedback_id} отмечен как решенный"}

@router.get("/admin/forms", response_class=HTMLResponse)
async def admin_forms(request: Request, db: Session = Depends(get_db)):
    if not check_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    tech_configs = get_all_form_configs(db=db, form_type="tech")
    business_configs = get_all_form_configs(db=db, form_type="business")
    exec_configs = get_all_form_configs(db=db, form_type="exec")
    
    return templates.TemplateResponse("admin/forms.html", {
        "request": request,
        "tech_configs": tech_configs,
        "business_configs": business_configs,
        "exec_configs": exec_configs
    })

@router.post("/admin/forms/{config_id}/toggle")
async def toggle_form_field(
    config_id: int,
    is_active: bool = Form(...),
    db: Session = Depends(get_db)
):
    config = db.query(FormConfig).filter(FormConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Поле не найдено")
    
    config.is_active = is_active
    db.commit()
    
    return {"message": f"Поле {config.field_name} {'активировано' if is_active else 'деактивировано'}"}

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

@router.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings(request: Request, db: Session = Depends(get_db)):
    if not check_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    # Получаем настройки из переменных окружения
    settings = {
        "admin_username": ADMIN_USERNAME,
        "telegram_enabled": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "smtp_enabled": bool(os.getenv("SMTP_HOST")),
        "db_host": os.getenv("DATABASE_URL", "").split("@")[-1].split(":")[0] if os.getenv("DATABASE_URL") else ""
    }
    
    return templates.TemplateResponse("admin/settings.html", {
        "request": request,
        "settings": settings
    })
