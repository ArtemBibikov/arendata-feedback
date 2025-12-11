FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

# Создание файла .env
RUN echo "DATABASE_URL=postgresql://arenadata_app:app_password_123@postgres:5432/arenadata_feedback" > .env

# Копирование SSL сертификатов
COPY ssl/ /app/ssl/

# Открытие портов
EXPOSE 8000 8443

# Запуск приложения
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 & uvicorn app.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile /app/ssl/key.pem --ssl-certfile /app/ssl/cert.pem"]
