"""
Database configuration for Arenadata Feedback System
Настройка SQLAlchemy и подключение к PostgreSQL
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Настройки подключения к PostgreSQL
# В продакшене использовать переменные окружения
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://arenadata_app:app_password_123@postgres:5432/arenadata_feedback"
)

# Создание движка SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Проверка соединения
    pool_recycle=3600,   # Пересоздание соединения каждый час
    echo=False           # Включить SQL логи для отладки
)

# Создание сессии
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()


def get_db():
    """
    Dependency для получения сессии БД
    Используется в FastAPI endpoints
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Создание всех таблиц в БД"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Удаление всех таблиц (только для разработки)"""
    Base.metadata.drop_all(bind=engine)


def check_connection():
    """Проверка подключения к БД"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False
