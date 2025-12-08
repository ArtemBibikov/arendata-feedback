-- Миграция для добавления таблицы вложений к отзывам
-- Выполняется под пользователем arenadata_admin

-- Таблица для хранения файлов к отзывам
CREATE TABLE feedback_attachments (
    id SERIAL PRIMARY KEY,
    feedback_id INTEGER NOT NULL REFERENCES feedbacks(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Индексы для feedback_attachments
CREATE INDEX idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id);
CREATE INDEX idx_feedback_attachments_filename ON feedback_attachments(filename);
CREATE INDEX idx_feedback_attachments_uploaded_at ON feedback_attachments(uploaded_at);

-- Комментарии к таблице
COMMENT ON TABLE feedback_attachments IS 'Файлы, прикрепленные к отзывам';
COMMENT ON COLUMN feedback_attachments.feedback_id IS 'ID отзыва';
COMMENT ON COLUMN feedback_attachments.filename IS 'Имя файла в системе';
COMMENT ON COLUMN feedback_attachments.original_filename IS 'Оригинальное имя файла';
COMMENT ON COLUMN feedback_attachments.file_path IS 'Путь к файлу';
COMMENT ON COLUMN feedback_attachments.file_size IS 'Размер файла в байтах';
COMMENT ON COLUMN feedback_attachments.content_type IS 'MIME тип файла';
