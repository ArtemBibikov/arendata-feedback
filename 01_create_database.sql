-- Создание базы данных Arenadata Feedback System
-- Выполняется под пользователем postgres

-- Создание базы данных
CREATE DATABASE arenadata_feedback 
    WITH 
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Подключение к новой базе данных
\c arenadata_feedback;

-- Включение расширения для JSONB и UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

COMMENT ON DATABASE arenadata_feedback IS 'Система сбора обратной связи для Arenadata';
