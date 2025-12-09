"""
SQLAlchemy models for Arenadata Feedback System
Модели данных соответствуют таблицам в PostgreSQL
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ARRAY, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.database import Base


class FormConfig(Base):
    """Конфигурация динамических форм"""
    __tablename__ = "form_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    form_type = Column(String(20), nullable=False, index=True)  # 'tech', 'business', 'exec'
    section_name = Column(String(100))
    field_order = Column(Integer, nullable=False, default=0)
    field_type = Column(String(50), nullable=False)  # 'text', 'textarea', 'select', 'radio', 'checkbox', 'email'
    field_label = Column(Text, nullable=False)
    field_name = Column(String(100), nullable=False)
    options = Column(JSONB)  # для select, radio, checkbox
    required = Column(Boolean, default=False)
    validation_rules = Column(JSONB)
    placeholder = Column(Text)
    help_text = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Feedback(Base):
    """Все отзывы клиентов"""
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    form_type = Column(String(20), nullable=False, index=True)  # 'tech', 'business', 'exec'
    client_id = Column(String(100), index=True)
    client_name = Column(String(255))
    client_email = Column(String(255), index=True)
    client_role = Column(String(50))  # 'technical', 'business', 'executive'
    
    # Основные поля отзыва
    problem_text = Column(Text)
    urgency = Column(String(20), default='normal', index=True)  # 'critical', 'high', 'medium', 'low', 'normal'
    category = Column(String(50), index=True)
    tags = Column(ARRAY(String))
    
    # Статусы и метаданные
    status = Column(String(20), default='new', index=True)  # 'new', 'in_progress', 'resolved', 'rejected'
    assigned_to = Column(String(100))
    priority_score = Column(Integer, default=0)
    
    # Данные формы (JSON для гибкости)
    form_data = Column(JSONB, index=True)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    # Метрики
    response_time_seconds = Column(Integer)
    satisfaction_score = Column(Integer)  # 1-5


class FeedbackAttachment(Base):
    """Вложения к отзывам"""
    __tablename__ = "feedback_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(Integer, nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    

    
        


    








