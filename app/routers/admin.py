"""
Admin API router for Arenadata Feedback System
Endpoints для административных функций
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud import (
    get_feedbacks, get_feedbacks_count, get_stats, get_recent_feedbacks
)
from app.schemas import (
    Feedback, FeedbackListResponse, StatsResponse
)
from app.services.telegram import test_telegram_connection

router = APIRouter()


@router.get("/admin/dashboard", response_model=StatsResponse, summary="Дашборд администратора")
async def get_admin_dashboard(
    form_type: Optional[str] = Query(None, regex="^(tech|business|exec)$"),
    db: Session = Depends(get_db)
):
    """
    Получить данные для дашборда администратора
    
    - **form_type**: Фильтр по типу формы (опционально)
    
    Возвращает полную статистику и последние отзывы
    """
    stats = get_stats(db=db, form_type=form_type)
    recent = get_recent_feedbacks(db=db, limit=10, form_type=form_type)
    
    return StatsResponse(
        recent_feedbacks=recent,
        **stats
    )


@router.get("/admin/feedbacks", response_model=FeedbackListResponse, summary="Управление отзывами")
async def admin_list_feedbacks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    form_type: Optional[str] = Query(None, regex="^(tech|business|exec)$"),
    status: Optional[str] = Query(None, regex="^(new|in_progress|resolved|rejected)$"),
    urgency: Optional[str] = Query(None, regex="^(high|medium|low|normal)$"),
    client_email: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Получить список отзывов для администрирования
    
    Поддерживает все фильтры для управления отзывами
    """
    feedbacks = get_feedbacks(
        db=db, skip=skip, limit=limit,
        form_type=form_type, status=status, urgency=urgency,
        client_email=client_email
    )
    total = get_feedbacks_count(
        db=db, form_type=form_type, status=status, urgency=urgency
    )
    
    pages = (total + limit - 1) // limit
    
    return FeedbackListResponse(
        items=feedbacks,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=pages
    )


@router.get("/admin/feedbacks/critical", response_model=List[Feedback], summary="Критические отзывы")
async def get_critical_feedbacks(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Получить список критических отзывов для срочной обработки
    
    - **limit**: Максимальное количество записей
    """
    feedbacks = get_feedbacks(
        db=db, skip=0, limit=limit,
        urgency='critical'
    )
    return feedbacks


@router.get("/admin/feedbacks/unassigned", response_model=List[Feedback], summary="Неназначенные отзывы")
async def get_unassigned_feedbacks(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Получить список отзывов без ответственного
    
    - **limit**: Максимальное количество записей
    """
    from app.models import Feedback
    from sqlalchemy import is_, desc
    
    feedbacks = db.query(Feedback).filter(
        is_(Feedback.assigned_to, None)
    ).order_by(desc(Feedback.created_at)).limit(limit).all()
    
    return feedbacks


@router.post("/admin/feedbacks/{feedback_id}/assign", summary="Назначить ответственного")
async def assign_feedback(
    feedback_id: int,
    assigned_to: str,
    db: Session = Depends(get_db)
):
    """
    Назначить ответственного за отзыв
    
    - **feedback_id**: ID отзыва
    - **assigned_to**: Email или имя ответственного
    """
    from app.crud import update_feedback
    from app.schemas import FeedbackUpdate
    
    feedback_update = FeedbackUpdate(
        assigned_to=assigned_to,
        status="in_progress"
    )
    
    updated = update_feedback(db=db, feedback_id=feedback_id, feedback=feedback_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    return {"message": f"Отзыв {feedback_id} назначен на {assigned_to}"}


@router.post("/admin/feedbacks/{feedback_id}/resolve", summary="Отметить как решенный")
async def resolve_feedback(
    feedback_id: int,
    satisfaction_score: Optional[int] = Query(None, ge=1, le=5),
    db: Session = Depends(get_db)
):
    """
    Отметить отзыв как решенный
    
    - **feedback_id**: ID отзыва
    - **satisfaction_score**: Оценка удовлетворенности клиента (1-5)
    """
    from app.crud import update_feedback
    from app.schemas import FeedbackUpdate
    from datetime import datetime
    
    feedback_update = FeedbackUpdate(
        status="resolved",
        resolved_at=datetime.utcnow(),
        satisfaction_score=satisfaction_score
    )
    
    updated = update_feedback(db=db, feedback_id=feedback_id, feedback=feedback_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    return {"message": f"Отзыв {feedback_id} отмечен как решенный"}




@router.get("/admin/export/feedbacks", summary="Экспорт отзывов")
async def export_feedbacks(
    format: str = Query("csv", regex="^(csv|json)$"),
    form_type: Optional[str] = Query(None, regex="^(tech|business|exec)$"),
    status: Optional[str] = Query(None, regex="^(new|in_progress|resolved|rejected)$"),
    db: Session = Depends(get_db)
):
    """
    Экспортировать отзывы в CSV или JSON
    
    - **format**: Формат экспорта (csv, json)
    - **form_type**: Фильтр по типу формы
    - **status**: Фильтр по статусу
    """
    feedbacks = get_feedbacks(
        db=db, skip=0, limit=10000,  # Большой лимит для экспорта
        form_type=form_type, status=status
    )
    
    if format == "json":
        return {"feedbacks": [feedback.__dict__ for feedback in feedbacks]}
    
    # Для CSV возвращаем простой текст
    csv_lines = [
        "ID,UUID,Form Type,Client Name,Client Email,Problem Text,Urgency,Status,Created At"
    ]
    
    for feedback in feedbacks:
        line = f"{feedback.id},{feedback.uuid},{feedback.form_type},"
        line += f'"{feedback.client_name or ""}","{feedback.client_email or ""}",'
        line += f'"{feedback.problem_text or ""}",{feedback.urgency},{feedback.status},{feedback.created_at}'
        csv_lines.append(line)
    
    return {"csv": "\n".join(csv_lines)}


@router.get("/admin/health", summary="Проверка здоровья системы")
async def system_health(db: Session = Depends(get_db)):
    """
    Проверить здоровье системы и компонентов
    """
    from app.database import check_connection
    
    db_health = check_connection()
    
    # Статистика по системе
    total_feedbacks = get_feedbacks_count(db=db)
    total_clients = len(get_clients(db=db, skip=0, limit=10000))
    
    return {
        "status": "healthy" if db_health else "unhealthy",
        "database": "connected" if db_health else "disconnected",
        "stats": {
            "total_feedbacks": total_feedbacks,
            "total_clients": total_clients
        },
        "timestamp": "2024-01-01T00:00:00Z"  # TODO: Использовать реальное время
    }


@router.get("/admin/telegram/test", summary="Проверка связи с Telegram")
async def telegram_test():
    """Проверить соединение с Telegram и корректность токена/чата"""
    ok = await test_telegram_connection()
    return {
        "ok": ok,
        "message": "Telegram connection successful" if ok else "Telegram connection failed"
    }
