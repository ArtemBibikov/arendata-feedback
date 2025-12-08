"""
Admin UI router for Arenadata Feedback System
Веб-интерфейс администрирования вместо Adminer
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.crud import (
    get_feedbacks, get_feedbacks_count, get_stats, get_recent_feedbacks,
    get_clients, get_form_configs
)
from app.models import Feedback, Client, FormConfig

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Главная страница админ-панели"""
    stats = get_stats(db=db)
    recent_feedbacks = get_recent_feedbacks(db=db, limit=5)
    critical_count = len([f for f in recent_feedbacks if f.urgency == 'critical'])
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_feedbacks": recent_feedbacks,
        "critical_count": critical_count
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
    """Страница управления отзывами"""
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
async def feedback_detail(request: Request, feedback_id: int, db: Session = Depends(get_db)):
    """Детальная страница отзыва"""
    from app.crud import get_feedback
    
    feedback = get_feedback(db=db, feedback_id=feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    return templates.TemplateResponse("admin/feedback_detail.html", {
        "request": request,
        "feedback": feedback
    })


@router.get("/admin/clients", response_class=HTMLResponse)
async def admin_clients(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    client_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Страница управления клиентами"""
    from app.models import Client
    
    query = db.query(Client)
    
    if client_type:
        query = query.filter(Client.client_type == client_type)
    
    clients = query.order_by(Client.created_at.desc()).offset(skip).limit(limit).all()
    total = query.count()
    
    return templates.TemplateResponse("admin/clients.html", {
        "request": request,
        "clients": clients,
        "total": total,
        "filters": {"client_type": client_type}
    })


@router.get("/admin/forms", response_class=HTMLResponse)
async def admin_forms(request: Request, db: Session = Depends(get_db)):
    """Страница управления формами"""
    forms_info = {}
    for form_type in ["tech", "business", "exec"]:
        configs = get_form_configs(db=db, form_type=form_type)
        forms_info[form_type] = configs
    
    return templates.TemplateResponse("admin/forms.html", {
        "request": request,
        "forms_info": forms_info
    })


@router.get("/admin/analytics", response_class=HTMLResponse)
async def admin_analytics(request: Request, db: Session = Depends(get_db)):
    """Страница аналитики"""
    stats = get_stats(db=db)
    
    # Дополнительная аналитика
    from sqlalchemy import func
    from app.models import Analytics
    
    daily_stats = db.query(Analytics).filter(
        Analytics.metric_type == 'daily_stats'
    ).order_by(Analytics.metric_date.desc()).limit(30).all()
    
    return templates.TemplateResponse("admin/analytics.html", {
        "request": request,
        "stats": stats,
        "daily_stats": daily_stats
    })
