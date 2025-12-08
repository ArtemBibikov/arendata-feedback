-- Создание пользователя и предоставление прав
-- Выполняется под пользователем postgres

-- Создание пользователя для приложения
CREATE USER arenadata_app WITH 
    PASSWORD 'app_password_123'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    INHERIT
    LOGIN;

-- Создание пользователя для админки (Adminer)
CREATE USER arenadata_admin WITH 
    PASSWORD 'admin_password_123'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    INHERIT
    LOGIN;

-- Предоставление прав на базу данных
GRANT CONNECT ON DATABASE arenadata_feedback TO arenadata_admin;
GRANT CONNECT ON DATABASE arenadata_feedback TO arenadata_app;

-- Подключение к базе данных для предоставления прав на таблицы
\c arenadata_feedback;

-- Предоставление прав на схему public
GRANT USAGE ON SCHEMA public TO arenadata_admin;
GRANT CREATE ON SCHEMA public TO arenadata_admin;

GRANT USAGE ON SCHEMA public TO arenadata_app;

-- Предоставление прав на будущие таблицы
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO arenadata_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO arenadata_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO arenadata_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO arenadata_app;

COMMENT ON ROLE arenadata_app IS 'Пользователь приложения для FastAPI';
COMMENT ON ROLE arenadata_admin IS 'Администратор для доступа через Adminer';
