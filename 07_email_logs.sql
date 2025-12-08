-- Миграция для логирования email уведомлений
-- Выполняется под пользователем arenadata_admin

-- Таблица для логирования email отправки
CREATE TABLE email_logs (
    id SERIAL PRIMARY KEY,
    feedback_id INTEGER REFERENCES feedbacks(id) ON DELETE CASCADE,
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    status VARCHAR(50) NOT NULL, -- 'sent', 'failed', 'pending'
    sent_at TIMESTAMP DEFAULT NOW(),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Индексы
CREATE INDEX idx_email_logs_feedback_id ON email_logs(feedback_id);
CREATE INDEX idx_email_logs_status ON email_logs(status);
CREATE INDEX idx_email_logs_sent_at ON email_logs(sent_at);
CREATE INDEX idx_email_logs_recipient ON email_logs(recipient);

-- Комментарии
COMMENT ON TABLE email_logs IS 'Логирование отправки email уведомлений';
COMMENT ON COLUMN email_logs.feedback_id IS 'ID связанного отзыва';
COMMENT ON COLUMN email_logs.recipient IS 'Email получателя';
COMMENT ON COLUMN email_logs.status IS 'Статус отправки';
COMMENT ON COLUMN email_logs.error_message IS 'Текст ошибки при неудаче';
COMMENT ON COLUMN email_logs.retry_count IS 'Количество попыток отправки';
