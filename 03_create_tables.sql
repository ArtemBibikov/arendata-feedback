-- Создание таблиц для Arenadata Feedback System
-- Выполняется под пользователем arenadata_admin

-- Таблица 1: Конфигурация динамических форм
CREATE TABLE form_configs (
    id SERIAL PRIMARY KEY,
    form_type VARCHAR(20) NOT NULL, -- 'tech', 'business', 'exec'
    section_name VARCHAR(100),
    field_order INTEGER NOT NULL DEFAULT 0,
    field_type VARCHAR(50) NOT NULL, -- 'text', 'textarea', 'select', 'radio', 'checkbox', 'email'
    field_label TEXT NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    options JSONB, -- для select, radio, checkbox
    required BOOLEAN DEFAULT false,
    validation_rules JSONB,
    placeholder TEXT,
    help_text TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Индексы для form_configs
CREATE INDEX idx_form_configs_type ON form_configs(form_type);
CREATE INDEX idx_form_configs_active ON form_configs(is_active);
CREATE INDEX idx_form_configs_order ON form_configs(form_type, field_order);

-- Таблица 2: Все отзывы клиентов
CREATE TABLE feedbacks (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    form_type VARCHAR(20) NOT NULL, -- 'tech', 'business', 'exec'
    client_id VARCHAR(100),
    client_name VARCHAR(255),
    client_email VARCHAR(255),
    client_role VARCHAR(50), -- 'technical', 'business', 'executive'
    
    -- Основные поля отзыва
    problem_text TEXT,
    urgency VARCHAR(20) DEFAULT 'normal', -- 'critical', 'high', 'medium', 'low', 'normal'
    category VARCHAR(50),
    tags TEXT[],
    
    -- Статусы и метаданные
    status VARCHAR(20) DEFAULT 'new', -- 'new', 'in_progress', 'resolved', 'rejected'
    assigned_to VARCHAR(100),
    priority_score INTEGER DEFAULT 0,
    
    -- Данные формы (JSON для гибкости)
    form_data JSONB,
    
    -- Временные метки
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    
    -- Метрики
    response_time_seconds INTEGER,
    satisfaction_score INTEGER CHECK (satisfaction_score >= 1 AND satisfaction_score <= 5)
);

-- Индексы для feedbacks
CREATE INDEX idx_feedbacks_form_type ON feedbacks(form_type);
CREATE INDEX idx_feedbacks_status ON feedbacks(status);
CREATE INDEX idx_feedbacks_urgency ON feedbacks(urgency);
CREATE INDEX idx_feedbacks_created_at ON feedbacks(created_at);
CREATE INDEX idx_feedbacks_client_email ON feedbacks(client_email);
CREATE INDEX idx_feedbacks_category ON feedbacks(category);
CREATE INDEX idx_feedbacks_tags ON feedbacks USING GIN(tags);
CREATE INDEX idx_feedbacks_form_data ON feedbacks USING GIN(form_data);

-- Таблица 3: Информация о клиентах (опционально)
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(100) UNIQUE,
    company_name VARCHAR(255),
    client_name VARCHAR(255),
    client_email VARCHAR(255) UNIQUE,
    client_role VARCHAR(50),
    client_type VARCHAR(20), -- 'technical', 'business', 'executive'
    
    -- Контактная информация
    phone VARCHAR(50),
    department VARCHAR(100),
    
    -- Метрики клиента
    total_feedbacks INTEGER DEFAULT 0,
    last_feedback_at TIMESTAMP,
    satisfaction_avg DECIMAL(3,2),
    
    -- Статус
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Индексы для clients
CREATE INDEX idx_clients_client_id ON clients(client_id);
CREATE INDEX idx_clients_email ON clients(client_email);
CREATE INDEX idx_clients_type ON clients(client_type);
CREATE INDEX idx_clients_active ON clients(is_active);

-- Таблица 4: Метрики и статистика
CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL, -- 'daily_stats', 'weekly_stats', 'category_stats'
    metric_date DATE NOT NULL,
    form_type VARCHAR(20),
    
    -- Счетчики
    total_feedbacks INTEGER DEFAULT 0,
    critical_feedbacks INTEGER DEFAULT 0,
    resolved_feedbacks INTEGER DEFAULT 0,
    avg_response_time_minutes DECIMAL(10,2),
    satisfaction_avg DECIMAL(3,2),
    
    -- Дополнительные метрики (JSON для гибкости)
    additional_metrics JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(metric_type, metric_date, form_type)
);

-- Индексы для analytics
CREATE INDEX idx_analytics_type_date ON analytics(metric_type, metric_date);
CREATE INDEX idx_analytics_form_type ON analytics(form_type);
CREATE INDEX idx_analytics_date ON analytics(metric_date);

-- Триггеры для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_form_configs_updated_at BEFORE UPDATE ON form_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feedbacks_updated_at BEFORE UPDATE ON feedbacks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Триггер для обновления статистики клиента при новом отзыве
CREATE OR REPLACE FUNCTION update_client_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE clients 
        SET 
            total_feedbacks = total_feedbacks + 1,
            last_feedback_at = NEW.created_at
        WHERE client_id = NEW.client_id;
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.status != 'resolved' AND NEW.status = 'resolved' THEN
            UPDATE clients 
            SET satisfaction_avg = (
                SELECT COALESCE(AVG(satisfaction_score), 0) 
                FROM feedbacks 
                WHERE client_id = NEW.client_id 
                AND satisfaction_score IS NOT NULL
            )
            WHERE client_id = NEW.client_id;
        END IF;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_update_client_stats 
    AFTER INSERT OR UPDATE ON feedbacks
    FOR EACH ROW EXECUTE FUNCTION update_client_stats();

-- Комментарии к таблицам
COMMENT ON TABLE form_configs IS 'Конфигурация динамических форм для разных типов клиентов';
COMMENT ON TABLE feedbacks IS 'Все отзывы клиентов с полной информацией';
COMMENT ON TABLE clients IS 'Информация о клиентах и их истории';
COMMENT ON TABLE analytics IS 'Агрегированная статистика и метрики';
