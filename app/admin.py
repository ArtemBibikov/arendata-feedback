"""
SQL Admin configuration for Arenadata Feedback System
Админ-панель на базе SQLAdmin вместо Adminer
"""

from sqladmin import Admin, ModelView
from app.models import Feedback, FormConfig
from app.database import engine


class FeedbackAdmin(ModelView, model=Feedback):
    """Админ-панель для отзывов"""
    column_list = [
        Feedback.id,
        Feedback.uuid,
        Feedback.form_type,
        Feedback.client_name,
        Feedback.client_email,
        Feedback.urgency,
        Feedback.status,
        Feedback.category,
        Feedback.created_at
    ]
    column_searchable_list = [
        Feedback.client_name,
        Feedback.client_email,
        Feedback.problem_text,
        Feedback.category
    ]
    column_filters = [
        Feedback.form_type,
        Feedback.urgency,
        Feedback.status,
        Feedback.category,
        Feedback.created_at
    ]
    column_sortable_list = [
        Feedback.created_at,
        Feedback.urgency,
        Feedback.status
    ]
    column_default_sort = [(Feedback.created_at, True)]
    
    form_columns = [
        "form_type",
        "client_name", 
        "client_email",
        "client_role",
        "problem_text",
        "urgency",
        "category",
        "status",
        "assigned_to",
        "priority_score",
        "satisfaction_score",
        "tags"
    ]
    
    form_widget_args = {
        "problem_text": {"textarea": {"rows": 6}},
        "tags": {"textarea": {"rows": 3}},
        "urgency": {"select": {
            "choices": [
                ("critical", "Критический"),
                ("high", "Высокий"),
                ("medium", "Средний"),
                ("low", "Низкий"),
                ("normal", "Обычный")
            ]
        }},
        "status": {"select": {
            "choices": [
                ("new", "Новый"),
                ("in_progress", "В работе"),
                ("resolved", "Решен"),
                ("rejected", "Отклонен")
            ]
        }},
        "form_type": {"select": {
            "choices": [
                ("tech", "Технический"),
                ("business", "Бизнес"),
                ("exec", "Руководитель")
            ]
        }}
    }




class FormConfigAdmin(ModelView, model=FormConfig):
    """Админ-панель для конфигурации форм"""
    column_list = [
        FormConfig.id,
        FormConfig.form_type,
        FormConfig.section_name,
        FormConfig.field_order,
        FormConfig.field_type,
        FormConfig.field_label,
        FormConfig.field_name,
        FormConfig.required,
        FormConfig.is_active
    ]
    column_filters = [
        FormConfig.form_type,
        FormConfig.field_type,
        FormConfig.section_name,
        FormConfig.is_active
    ]
    column_sortable_list = [
        FormConfig.form_type,
        FormConfig.field_order
    ]
    
    form_columns = [
        "form_type",
        "section_name",
        "field_order",
        "field_type",
        "field_label",
        "field_name",
        "options",
        "required",
        "validation_rules",
        "placeholder",
        "help_text",
        "is_active"
    ]




def create_admin_app():
    """Создание админ-приложения"""
    from sqladmin import Admin
    
    admin = Admin(engine, title="Arenadata Feedback Admin")
    
    # Добавляем модели
    admin.add_view(FeedbackAdmin)
    admin.add_view(ClientAdmin)
    admin.add_view(FormConfigAdmin)
    
    return admin
