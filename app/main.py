"""
Arenadata Feedback System - FastAPI Main Application
MVP система сбора обратной связи за 2 недели
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime
from typing import Optional, List
import pytz
import httpx

from app.database import engine, Base, SessionLocal
from app.routers import feedback as feedback_router, forms, admin, admin_panel
from app.admin import create_admin_app
from app import models
from pydantic import BaseModel

# Создание таблиц в БД
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Arenadata Feedback System",
    description="MVP система сбора обратной связи для клиентов Arenadata",
    version="1.0.0"
)

# CORS для работы с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware для авторизации
app.add_middleware(SessionMiddleware, secret_key="arenadata-secret-key")

# Статические файлы
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Роутеры API
app.include_router(forms.router, prefix="/api", tags=["forms"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(admin_panel.router)

# SQL Admin панель
from sqladmin import Admin
from app.admin import FeedbackAdmin, FormConfigAdmin

admin = Admin(app, engine, title="Arenadata Feedback Admin", base_url="/sql-admin")
admin.add_view(FeedbackAdmin)
admin.add_view(FormConfigAdmin)

# Templates
templates = Jinja2Templates(directory="app/templates")

# Добавляем timezone фильтр для шаблонов
def format_datetime_msk(dt, format_str='%d.%m.%Y %H:%M'):
    """Форматирует datetime в MSK timezone"""
    if dt is None:
        return ''
    
    # Если datetime уже имеет timezone, конвертируем в MSK
    if dt.tzinfo is not None:
        msk_tz = pytz.timezone('Europe/Moscow')
        dt_msk = dt.astimezone(msk_tz)
    else:
        # Если timezone нет, считаем что это UTC и добавляем MSK
        msk_tz = pytz.timezone('Europe/Moscow')
        dt_msk = pytz.utc.localize(dt).astimezone(msk_tz)
    
    return dt_msk.strftime(format_str)

templates.env.filters['datetime_msk'] = format_datetime_msk

# Pydantic модели
class FeedbackCreate(BaseModel):
    form_type: str
    message: str

# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Arenadata Feedback System API"}

@app.get("/favicon.ico")
async def favicon():
    # Возвращаем пустой ответ чтобы избежать 404 ошибки
    return {"message": "No favicon"}

@app.post("/api/analyze-urgency")
async def test_urgency_analysis(request: dict):
    """
    Тестовый эндпоинт для анализа срочности текста
    """
    text = request.get('text', '')
    if not text:
        raise HTTPException(status_code=400, detail="Текст не может быть пустым")
    
    result = analyze_urgency(text)
    return result

@app.post("/api/feedback")
async def create_feedback(feedback: FeedbackCreate):
    """
    Создание нового отзыва с автоматическим определением срочности
    """
    # Автоматически определяем срочность на основе текста
    urgency_analysis = analyze_urgency(feedback.message)
    
    # Создаем запись в базе данных
    db = SessionLocal()
    try:
        db_feedback = models.Feedback(
            form_type=feedback.form_type,
            message=feedback.message,
            urgency=urgency_analysis['urgency'],
            urgency_confidence=urgency_analysis['confidence'],
            urgency_reason=urgency_analysis['reason'],
            created_at=datetime.utcnow()
        )
        
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        
        return {
            "id": db_feedback.id,
            "urgency": urgency_analysis['urgency'],
            "confidence": urgency_analysis['confidence'],
            "reason": urgency_analysis['reason'],
            "message": "Отзыв успешно сохранен"
        }
    finally:
        db.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "arenadata-feedback"}

def analyze_urgency(text: str) -> dict:
    """
    Анализирует текст и определяет уровень срочности
    
    Args:
        text: Текст сообщения от клиента
        
    Returns:
        dict: Уровень срочности и уверенность
    """
    # Словарь ключевых слов для определения срочности
    urgency_keywords = {
        'high': [
            'не работает', 'ошибка', 'сбой', 'упал', 'завис', 'критично',
            'не открывается', 'не запускается', 'не загружается', 'пропал',
            'потерял', 'сломался', 'вылетает', 'крашится', 'блокирует',
            'нет доступа', 'запрещен', 'отказывает', 'не отвечает',
            '500', '404', '403', 'connection', 'failed', 'crash',
            # Дополнительные критические слова
            'авария', 'катастрофа', 'проблема', 'баг', 'неисправность',
            'отказ', 'поломка', 'поврежден', 'испорчен', 'неработающий',
            'недоступен', 'сломан', 'не функционален', 'деактивирован',
            'перестал', 'прекратил', 'остановился', 'замерз', 'застыл',
            'corrupted', 'broken', 'down', 'unavailable', 'timeout',
            'exception', 'fatal', 'critical', 'emergency', 'urgent',
            'не загружается', 'не отображается', 'не появляется',
            'пустой экран', 'белый экран', 'черный экран', 'зависает'
        ],
        'medium': [
            'медленно', 'тормозит', 'глючит', 'неудобно', 'проблема',
            'долго', 'медленно', 'задержка', 'подвисает', 'тупит',
            'не получается', 'не могу', 'сложно', 'проблемный',
            'странно', 'неожиданно', 'иногда', 'периодически',
            'часть функций', 'некоторые', 'отдельные',
            # Дополнительные слова средней срочности
            'плохо', 'неудобно', 'сложно', 'затруднительно', 'проблематично',
            'нестабильно', 'непостоянно', 'рванно', 'рывками', 'прыгает',
            'медленная загрузка', 'долгое ожидание', 'задерживается',
            'подвисает', 'замирает', 'останавливается', 'прерывается',
            'некорректно', 'неправильно', 'не так', 'не работает как надо',
            'требует перезагрузки', 'нужно перезапустить', 'слетел',
            'пропали настройки', 'сбросились настройки', 'исчезли данные',
            'slow', 'lag', 'delay', 'unstable', 'inconsistent', 'buggy'
        ],
        'low': [
            'хотелось бы', 'можно добавить', 'было бы хорошо', 'предлагаю',
            'желаю', 'нужно', 'требуется', 'предложение', 'пожелание',
            'удобно было бы', 'отлично было бы', 'супер было бы',
            'новая функция', 'улучшить', 'оптимизировать', 'развитие',
            'статистика', 'отчет', 'фильтр', 'сортировка', 'поиск',
            # Дополнительные слова низкой срочности
            'пожелание', 'идея', 'мысль', 'предложение', 'рекомендация',
            'улучшение', 'оптимизация', 'модернизация', 'доработка',
            'дополнение', 'расширение', 'усиление', 'усилить',
            'интересно', 'любопытно', 'замечательно', 'прекрасно',
            'отличная идея', 'хорошая мысль', 'полезно', 'удобно',
            'красиво', 'эстетично', 'профессионально', 'качественно',
            'feature', 'enhancement', 'improvement', 'suggestion', 'idea',
            'request', 'wishlist', 'nice to have', 'would be great'
        ]
    }
    
    # Приводим текст к нижнему регистру для анализа
    text_lower = text.lower()
    
    # Считаем совпадения для каждого уровня срочности
    urgency_scores = {
        'high': 0,
        'medium': 0,
        'low': 0
    }
    
    # Анализируем ключевые слова
    for urgency_level, keywords in urgency_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                urgency_scores[urgency_level] += 1
    
    # Определяем уровень срочности
    total_score = sum(urgency_scores.values())
    
    if total_score == 0:
        # Если ключевых слов нет, определяем по длине и общим признакам
        if len(text) > 200:  # Длинные сообщения обычно более срочные
            return {'urgency': 'medium', 'confidence': 0.3, 'reason': 'Длинное сообщение'}
        else:
            return {'urgency': 'low', 'confidence': 0.2, 'reason': 'Нет явных признаков срочности'}
    
    # Находим уровень с максимальным счетом
    max_urgency = max(urgency_scores, key=urgency_scores.get)
    max_score = urgency_scores[max_urgency]
    confidence = max_score / total_score
    
    # Дополнительные правила для уточнения
    if max_urgency == 'high' and confidence > 0.4:
        return {
            'urgency': 'high', 
            'confidence': confidence,
            'reason': f'Найдены {max_score} критичных признаков'
        }
    elif max_urgency == 'medium' and confidence > 0.3:
        return {
            'urgency': 'medium', 
            'confidence': confidence,
            'reason': f'Найдены {max_score} признаков проблем'
        }
    else:
        return {
            'urgency': 'low', 
            'confidence': confidence,
            'reason': f'Найдены {max_score} признаков улучшений'
        }


@app.get("/metrics")
async def metrics():
    """Простые метрики системы"""
    import psutil
    import time
    
    return {
        "uptime_seconds": int(time.time()),
        "memory_percent": psutil.virtual_memory().percent,
        "cpu_percent": psutil.cpu_percent(interval=1),
        "disk_usage_percent": psutil.disk_usage('/').percent,
        "service": "arenadata-feedback"
    }


@app.get("/form/{form_type}", response_class=HTMLResponse)
async def render_form(request: Request, form_type: str):
    """
    Рендер динамической формы
    /form/tech - для технических специалистов
    /form/business - для бизнес-пользователей
    /form/exec - для руководителей
    """
    if form_type not in ["tech", "business", "exec"]:
        return HTMLResponse("Форма не найдена", status_code=404)
    
    return templates.TemplateResponse(
        "form.html", 
        {
            "request": request,
            "form_type": form_type,
            "title": f"Форма обратной связи - {form_type.title()}"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
