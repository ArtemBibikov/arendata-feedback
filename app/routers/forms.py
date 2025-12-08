"""
Forms API router for Arenadata Feedback System
Endpoints для работы с динамическими формами
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud import get_form_configs, create_form_config, update_form_config
from app.schemas import FormConfig, FormConfigCreate, FormConfigUpdate, FormResponse

router = APIRouter()


@router.get("/forms/{form_type}", response_model=FormResponse, summary="Получить конфигурацию формы")
async def get_form_configuration(form_type: str, db: Session = Depends(get_db)):
    """
    Получить конфигурацию динамической формы
    
    - **form_type**: Тип формы (tech, business, exec)
    
    Возвращает полную конфигурацию формы с полями для рендеринга
    """
    if form_type not in ["tech", "business", "exec"]:
        raise HTTPException(
            status_code=400, 
            detail="Неверный тип формы. Доступные: tech, business, exec"
        )
    
    configs = get_form_configs(db=db, form_type=form_type)
    
    if not configs:
        raise HTTPException(
            status_code=404, 
            detail=f"Конфигурация для формы '{form_type}' не найдена"
        )
    
    titles = {
        "tech": "Форма для технических специалистов",
        "business": "Форма для бизнес-пользователей", 
        "exec": "Форма для руководителей"
    }
    
    return FormResponse(
        form_type=form_type,
        title=titles.get(form_type, "Форма обратной связи"),
        fields=configs
    )


@router.post("/forms/{form_type}/fields", response_model=FormConfig, summary="Добавить поле в форму")
async def add_field_to_form(
    form_type: str, 
    field: FormConfigCreate, 
    db: Session = Depends(get_db)
):
    """
    Добавить новое поле в конфигурацию формы
    
    - **form_type**: Тип формы (tech, business, exec)
    - **field**: Конфигурация поля
    """
    if form_type != field.form_type:
        raise HTTPException(
            status_code=400,
            detail="Тип поля не соответствует типу формы"
        )
    
    try:
        db_field = create_form_config(db=db, config=field.dict())
        return db_field
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("/forms/fields/{field_id}", response_model=FormConfig, summary="Обновить поле формы")
async def update_form_field(
    field_id: int, 
    field: FormConfigUpdate, 
    db: Session = Depends(get_db)
):
    """
    Обновить существующее поле формы
    
    - **field_id**: ID поля для обновления
    - **field**: Новая конфигурация поля
    """
    update_data = field.dict(exclude_unset=True)
    
    try:
        db_field = update_form_config(db=db, config_id=field_id, config=update_data)
        if db_field is None:
            raise HTTPException(status_code=404, detail="Поле не найдено")
        return db_field
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/forms/{form_type}/preview", summary="Предпросмотр формы")
async def preview_form(form_type: str, db: Session = Depends(get_db)):
    """
    Получить предпросмотр формы в формате для рендеринга
    
    - **form_type**: Тип формы (tech, business, exec)
    
    Возвращает JSON структуру для фронтенда
    """
    if form_type not in ["tech", "business", "exec"]:
        raise HTTPException(
            status_code=400, 
            detail="Неверный тип формы. Доступные: tech, business, exec"
        )
    
    configs = get_form_configs(db=db, form_type=form_type)
    
    if not configs:
        raise HTTPException(
            status_code=404, 
            detail=f"Конфигурация для формы '{form_type}' не найдена"
        )
    
    # Группировка полей по секциям
    sections: Dict[str, List[Dict[str, Any]]] = {}
    
    for config in configs:
        # Пропускаем неактивные поля
        if not config.is_active:
            continue
            
        section_name = config.section_name or "Основная информация"
        
        if section_name not in sections:
            sections[section_name] = []
        
        field_data = {
            "id": config.id,
            "order": config.field_order,
            "type": config.field_type,
            "label": config.field_label,
            "name": config.field_name,
            "required": config.required,
            "placeholder": config.placeholder,
            "help_text": config.help_text
        }
        
        # Добавляем опции для select, radio, checkbox
        if config.options:
            field_data["options"] = config.options
        
        # Добавляем правила валидации
        if config.validation_rules:
            field_data["validation"] = config.validation_rules
        
        sections[section_name].append(field_data)
    
    # Сортировка полей внутри секций
    for section in sections:
        sections[section].sort(key=lambda x: x["order"])
    
    titles = {
        "tech": "Форма для технических специалистов",
        "business": "Форма для бизнес-пользователей",
        "exec": "Форма для руководителей"
    }
    
    return {
        "form_type": form_type,
        "title": titles.get(form_type, "Форма обратной связи"),
        "sections": sections,
        "submit_url": f"/api/feedback",
        "method": "POST"
    }


@router.get("/forms", summary="Получить список всех форм")
async def list_forms(db: Session = Depends(get_db)):
    """
    Получить список всех доступных форм с базовой информацией
    """
    from app.crud import get_form_configs
    
    forms_info = {}
    for form_type in ["tech", "business", "exec"]:
        configs = get_form_configs(db=db, form_type=form_type)
        forms_info[form_type] = {
            "type": form_type,
            "field_count": len(configs),
            "has_config": len(configs) > 0
        }
    
    return {
        "forms": forms_info,
        "total_types": len(forms_info)
    }
