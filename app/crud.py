"""
CRUD operations for Arenadata Feedback System
Базовые операции с базой данных
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from app.models import Feedback, FormConfig
from app.schemas import FeedbackCreate, FeedbackUpdate


# Feedback CRUD operations
def get_feedback(db: Session, feedback_id: int) -> Optional[Feedback]:
    """Получить отзыв по ID"""
    return db.query(Feedback).filter(Feedback.id == feedback_id).first()


def get_feedback_by_uuid(db: Session, feedback_uuid: str) -> Optional[Feedback]:
    """Получить отзыв по UUID"""
    return db.query(Feedback).filter(Feedback.uuid == feedback_uuid).first()


def get_feedbacks(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    form_type: Optional[str] = None,
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    client_email: Optional[str] = None
) -> List[Feedback]:
    """Получить список отзывов с фильтрами"""
    query = db.query(Feedback)
    
    if form_type:
        query = query.filter(Feedback.form_type == form_type)
    if status:
        query = query.filter(Feedback.status == status)
    if urgency:
        query = query.filter(Feedback.urgency == urgency)
    if client_email:
        query = query.filter(Feedback.client_email == client_email)
    
    return query.order_by(desc(Feedback.created_at)).offset(skip).limit(limit).all()


def get_feedbacks_count(
    db: Session,
    form_type: Optional[str] = None,
    status: Optional[str] = None,
    urgency: Optional[str] = None
) -> int:
    """Получить количество отзывов с фильтрами"""
    query = db.query(Feedback)
    
    if form_type:
        query = query.filter(Feedback.form_type == form_type)
    if status:
        query = query.filter(Feedback.status == status)
    if urgency:
        query = query.filter(Feedback.urgency == urgency)
    
    return query.count()


def create_feedback(db: Session, feedback: FeedbackCreate) -> Feedback:
    """Создать новый отзыв"""
    db_feedback = Feedback(**feedback.dict())
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


def update_feedback(db: Session, feedback_id: int, feedback: FeedbackUpdate, update_data: Optional[Dict] = None) -> Optional[Feedback]:
    """Обновить отзыв"""
    db_feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not db_feedback:
        return None
    
    if update_data is None:
        update_data = feedback.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_feedback, field, value)
    
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


def delete_feedback(db: Session, feedback_id: int) -> bool:
    """Удалить отзыв"""
    db_feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not db_feedback:
        return False
    
    db.delete(db_feedback)
    db.commit()
    return True




# Form Config CRUD operations
def get_form_configs(db: Session, form_type: str) -> List[FormConfig]:
    """Получить конфигурацию формы по типу (только активные поля)"""
    return db.query(FormConfig).filter(
        and_(FormConfig.form_type == form_type, FormConfig.is_active == True)
    ).order_by(FormConfig.field_order).all()

def get_all_form_configs(db: Session, form_type: str) -> List[FormConfig]:
    """Получить все конфигурации формы по типу (включая неактивные)"""
    return db.query(FormConfig).filter(
        FormConfig.form_type == form_type
    ).order_by(FormConfig.field_order).all()


def create_form_config(db: Session, config: Dict[str, Any]) -> FormConfig:
    """Создать конфигурацию поля формы"""
    db_config = FormConfig(**config)
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


def update_form_config(db: Session, config_id: int, config: Dict[str, Any]) -> Optional[FormConfig]:
    """Обновить конфигурацию поля формы"""
    db_config = db.query(FormConfig).filter(FormConfig.id == config_id).first()
    if not db_config:
        return None
    
    for field, value in config.items():
        setattr(db_config, field, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config


# Analytics CRUD operations
def get_stats(db: Session, form_type: Optional[str] = None) -> Dict[str, Any]:
    """Получить статистику по отзывам"""
    query = db.query(Feedback)
    
    if form_type:
        query = query.filter(Feedback.form_type == form_type)
    
    total = query.count()
    critical = query.filter(Feedback.urgency == 'high').count()
    resolved = query.filter(Feedback.status == 'resolved').count()
    
    # Среднее время ответа
    avg_response = db.query(func.avg(Feedback.response_time_seconds)).filter(
        and_(Feedback.response_time_seconds.isnot(None), Feedback.status == 'resolved')
    ).scalar() or 0
    
    # Средняя удовлетворенность
    avg_satisfaction = db.query(func.avg(Feedback.satisfaction_score)).filter(
        and_(Feedback.satisfaction_score.isnot(None), Feedback.satisfaction_score > 0)
    ).scalar() or 0
    
    # Распределение по типам
    feedbacks_by_type = {}
    if not form_type:
        for ft in ['tech', 'business', 'exec']:
            feedbacks_by_type[ft] = db.query(Feedback).filter(Feedback.form_type == ft).count()
    
    # Распределение по статусам
    feedbacks_by_status = {}
    for status in ['new', 'in_progress', 'resolved', 'rejected']:
        feedbacks_by_status[status] = query.filter(Feedback.status == status).count()
    
    # Статистика по последним 7 дням
    from datetime import datetime, timedelta
    recent_feedbacks_by_day = []
    for i in range(6, -1, -1):  # от 6 дней назад до сегодня
        date = datetime.utcnow() - timedelta(days=i)
        day_count = db.query(Feedback).filter(
            func.date(Feedback.created_at) == date.date()
        ).count()
        recent_feedbacks_by_day.append(day_count)
    
    return {
        'total_feedbacks': total,
        'critical_feedbacks': critical,
        'resolved_feedbacks': resolved,
        'avg_response_time_minutes': round(avg_response / 60, 2) if avg_response else 0,
        'satisfaction_avg': round(float(avg_satisfaction), 2) if avg_satisfaction else 0,
        'feedbacks_by_type': feedbacks_by_type,
        'feedbacks_by_status': feedbacks_by_status,
        'recent_feedbacks_by_day': recent_feedbacks_by_day
    }


def get_recent_feedbacks(db: Session, limit: int = 5, form_type: Optional[str] = None) -> List[Feedback]:
    """Получить последние отзывы"""
    query = db.query(Feedback)
    
    if form_type:
        query = query.filter(Feedback.form_type == form_type)
    
    return query.order_by(desc(Feedback.created_at)).limit(limit).all()
