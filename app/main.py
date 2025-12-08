"""
Arenadata Feedback System - FastAPI Main Application
MVP система сбора обратной связи за 2 недели
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import pytz

from app.database import engine, Base
from app.routers import feedback, forms, admin, admin_panel
from app.admin import create_admin_app

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
app.include_router(feedback.router, prefix="/api", tags=["feedback"])
app.include_router(forms.router, prefix="/api", tags=["forms"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(admin_panel.router)

# SQL Admin панель
from sqladmin import Admin
from app.admin import FeedbackAdmin, FormConfigAdmin

admin = Admin(app, engine, title="Arenadata Feedback Admin")
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

@app.get("/")
async def root():
    return {"message": "Arenadata Feedback System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "arenadata-feedback"}


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
