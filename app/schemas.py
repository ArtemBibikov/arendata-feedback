"""
Pydantic schemas for Arenadata Feedback System
Схемы валидации данных для API endpoints
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
import json
from pydantic import BaseModel, EmailStr, Field, validator


# Базовые схемы
class BaseSchema(BaseModel):
    """Базовая схема с общими полями"""
    class Config:
        from_attributes = True


# Form Config schemas
class FormConfigBase(BaseSchema):
    """Базовая схема конфигурации формы"""
    form_type: str = Field(..., pattern="^(tech|business|exec)$")
    section_name: Optional[str] = None
    field_order: int = Field(default=0, ge=0)
    field_type: str = Field(..., pattern="^(text|textarea|select|radio|checkbox|email|file)$")
    field_label: str
    field_name: str
    options: Optional[Dict[str, Any]] = None
    required: bool = False
    validation_rules: Optional[Dict[str, Any]] = None
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    is_active: bool = True


class FormConfigCreate(FormConfigBase):
    """Схема для создания конфигурации формы"""


class FormConfigUpdate(BaseSchema):
    """Схема для обновления конфигурации формы"""
    section_name: Optional[str] = None
    field_order: Optional[int] = Field(default=None, ge=0)
    field_type: Optional[str] = Field(default=None, pattern="^(text|textarea|select|radio|checkbox|email|file)$")
    field_label: Optional[str] = None
    field_name: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    required: Optional[bool] = None
    validation_rules: Optional[Dict[str, Any]] = None
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    is_active: Optional[bool] = None


class FormConfig(FormConfigBase):
    """Полная схема конфигурации формы"""
    id: int
    created_at: datetime
    updated_at: datetime


# Feedback schemas
class FeedbackBase(BaseSchema):
    """Базовая схема отзыва"""
    form_type: str = Field(..., pattern="^(tech|business|exec)$")
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_role: Optional[str] = None
    problem_text: Optional[str] = None
    urgency: str = Field(default="normal", pattern="^(high|medium|low|normal)$")
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    form_data: Optional[Dict[str, Any]] = None


class FeedbackCreate(FeedbackBase):
    """Схема для создания отзыва"""


class FeedbackUpdate(BaseSchema):
    """Схема для обновления отзыва"""
    status: Optional[str] = Field(default=None, pattern="^(new|in_progress|resolved|rejected)$")
    assigned_to: Optional[str] = None
    priority_score: Optional[int] = Field(default=None, ge=0)
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    satisfaction_score: Optional[int] = Field(default=None, ge=1, le=5)
    resolved_at: Optional[datetime] = None
    response_time_seconds: Optional[int] = None


class Feedback(FeedbackBase):
    """Полная схема отзыва"""
    id: int
    uuid: UUID
    status: str
    assigned_to: Optional[str] = None
    priority_score: int
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    response_time_seconds: Optional[int] = None
    satisfaction_score: Optional[int] = None


# Client schemas
class ClientBase(BaseSchema):
    """Базовая схема клиента"""
    client_id: Optional[str] = None
    company_name: Optional[str] = None
    client_name: Optional[str] = None
    client_email: Optional[EmailStr] = None
    client_role: Optional[str] = None
    client_type: Optional[str] = Field(default=None, pattern="^(technical|business|executive)$")
    phone: Optional[str] = None
    department: Optional[str] = None
    is_active: bool = True


class ClientCreate(ClientBase):
    """Схема для создания клиента"""
    client_id: str
    client_email: EmailStr


class ClientUpdate(BaseSchema):
    """Схема для обновления клиента"""
    company_name: Optional[str] = None
    client_name: Optional[str] = None
    client_role: Optional[str] = None
    client_type: Optional[str] = Field(default=None, pattern="^(technical|business|executive)$")
    phone: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


class Client(ClientBase):
    """Полная схема клиента"""
    id: int
    total_feedbacks: int
    last_feedback_at: Optional[datetime] = None
    satisfaction_avg: Optional[float] = None
    created_at: datetime
    updated_at: datetime


# Analytics schemas
class AnalyticsBase(BaseSchema):
    """Базовая схема аналитики"""
    metric_type: str
    metric_date: datetime
    form_type: Optional[str] = Field(default=None, pattern="^(tech|business|exec)$")
    total_feedbacks: int = 0
    critical_feedbacks: int = 0
    resolved_feedbacks: int = 0
    avg_response_time_minutes: Optional[float] = None
    satisfaction_avg: Optional[float] = None
    additional_metrics: Optional[Dict[str, Any]] = None


class AnalyticsCreate(AnalyticsBase):
    """Схема для создания аналитики"""


class Analytics(AnalyticsBase):
    """Полная схема аналитики"""
    id: int
    created_at: datetime


# Response schemas
class FeedbackListResponse(BaseSchema):
    """Схема ответа для списка отзывов"""
    items: List[Feedback]
    total: int
    page: int
    size: int
    pages: int


class StatsResponse(BaseSchema):
    """Схема ответа для статистики"""
    total_feedbacks: int
    critical_feedbacks: int
    resolved_feedbacks: int
    avg_response_time_minutes: float
    satisfaction_avg: float
    feedbacks_by_type: Dict[str, int]
    feedbacks_by_status: Dict[str, int]
    recent_feedbacks: List[Feedback]
    recent_feedbacks_by_day: List[int]


class FormResponse(BaseSchema):
    """Схема ответа для конфигурации формы"""
    form_type: str
    title: str
    fields: List[FormConfig]


# Валидаторы
@validator('tags', pre=True)
def validate_tags(_, v):
    """Валидация тегов"""
    if v is None:
        return []
    if isinstance(v, str):
        return [tag.strip() for tag in v.split(',') if tag.strip()]
    return v


@validator('form_data', pre=True)
def validate_form_data(_, v):
    """Валидация данных формы"""
    if v is None:
        return {}
    # Если пришла строка, пробуем распарсить как JSON
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return {}
    return v


# Attachment schemas
class AttachmentBase(BaseSchema):
    """Базовая схема вложения"""
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    content_type: str


class AttachmentCreate(AttachmentBase):
    """Схема для создания вложения"""
    feedback_id: int


class Attachment(AttachmentBase):
    """Схема ответа для вложения"""
    id: int
    feedback_id: int
    uploaded_at: datetime


class AttachmentUpload(BaseModel):
    """Схема для загрузки файла"""
    file: bytes
    filename: str
    content_type: str
