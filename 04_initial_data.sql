-- Начальная конфигурация форм для Arenadata Feedback System
-- Выполняется под пользователем arenadata_admin

-- Удаляем старую конфигурацию технической формы
DELETE FROM form_configs WHERE form_type = 'tech';

-- Конфигурация формы для технических специалистов (обновленная)
INSERT INTO form_configs (form_type, section_name, field_order, field_type, field_label, field_name, required, placeholder, help_text) VALUES
('tech', 'Основная информация', 1, 'text', 'Ваше имя', 'client_name', true, 'Иван Иванов', 'Как к вам обращаться?'),
('tech', 'Основная информация', 2, 'email', 'Email для связи', 'client_email', true, 'ivan@company.com', 'Для отправки ответа'),
('tech', 'Основная информация', 3, 'text', 'Компания', 'company', false, 'ООО "ТехСол"', 'Ваша организация'),
('tech', 'Тип обращения', 4, 'select', 'Тип обращения', 'request_type', true, NULL, 'Выберите тип обращения'),
('tech', 'Тип обращения', 5, 'select', 'Критичность', 'severity', true, NULL, 'Насколько критична проблема?'),
('tech', 'Описание проблемы', 6, 'textarea', 'Описание проблемы', 'problem_text', true, 'Подробно опишите проблему...', 'Максимально подробно опишите проблему, можно вставлять код'),
('tech', 'Описание проблемы', 7, 'textarea', 'Шаги воспроизведения', 'steps_to_reproduce', false, '1. Открыть... 2. Нажать...', 'Пошаговая инструкция для воспроизведения'),
('tech', 'Технические детали', 8, 'textarea', 'Окружение', 'environment', false, 'ОС: Ubuntu 22.04\nБраузер: Chrome 120\nВерсия: v2.1.0', 'Техническая информация об окружении'),
('tech', 'Технические детали', 9, 'textarea', 'Логи и ошибки', 'error_logs', false, 'Вставьте логи или сообщения об ошибках...', 'Можно вставлять текст логов и stack trace'),
('tech', 'Файлы', 10, 'file', 'Прикрепить файлы', 'attachments', false, NULL, 'Скриншоты, логи, дампы (макс. 10MB)'),
('tech', 'Дополнительно', 11, 'textarea', 'Ожидаемый результат', 'expected_result', false, 'Что должно было произойти...', 'Опишите правильное поведение'),
('tech', 'Дополнительно', 12, 'textarea', 'Предложения по решению', 'suggestions', false, 'Возможные решения...', 'Если есть идеи по исправлению');

-- Добавляем опции для select полей технической формы (обновленные)
UPDATE form_configs SET options = '["Bug", "Feature Request", "Documentation", "API Issue", "Performance", "Other"]' WHERE form_type = 'tech' AND field_name = 'request_type';
UPDATE form_configs SET options = '["High", "Medium", "Low"]' WHERE form_type = 'tech' AND field_name = 'severity';

-- Удаляем старую конфигурацию бизнес-формы
DELETE FROM form_configs WHERE form_type = 'business';

-- Конфигурация формы для бизнес-пользователей (обновленная)
INSERT INTO form_configs (form_type, section_name, field_order, field_type, field_label, field_name, required, placeholder, help_text) VALUES
('business', 'Основная информация', 1, 'text', 'Ваше имя', 'client_name', true, 'Мария Петрова', 'Как к вам обращаться?'),
('business', 'Основная информация', 2, 'email', 'Email для связи', 'client_email', true, 'maria@company.com', 'Для отправки ответа'),
('business', 'Основная информация', 3, 'text', 'Компания', 'company', false, 'ООО "БизнесПро"', 'Ваша организация'),
('business', 'Ваш опыт', 4, 'textarea', 'Что понравилось', 'liked_features', false, 'Удобный интерфейс, быстрая работа...', 'Расскажите что вам нравится в нашем продукте'),
('business', 'Ваш опыт', 5, 'textarea', 'Что не понравилось', 'disliked_features', false, 'Медленная загрузка, сложная навигация...', 'Что можно улучшить?'),
('business', 'Оценка', 6, 'select', 'Общая оценка', 'rating', true, NULL, 'Оцените от 1 до 10'),
('business', 'Сценарий использования', 7, 'textarea', 'Как вы используете продукт', 'usage_scenario', true, 'Ежедневно для отчетов, аналитики...', 'Опишите как и когда вы используете продукт'),
('business', 'Пожелания', 8, 'textarea', 'Желаемое улучшение', 'improvement_request', false, 'Хотелось бы экспорт в Excel, темная тема...', 'Что бы вы хотели добавить или изменить?'),
('business', 'Дополнительно', 9, 'select', 'Частота использования', 'usage_frequency', false, NULL, 'Как часто вы пользуетесь продуктом?'),
('business', 'Дополнительно', 10, 'textarea', 'Дополнительные комментарии', 'additional_comments', false, 'Любые другие мысли или предложения...', 'Есть что-то еще что вы хотите сказать?');

-- Добавляем опции для бизнес-формы (обновленные)
UPDATE form_configs SET options = '["10", "9", "8", "7", "6", "5", "4", "3", "2", "1"]' WHERE form_type = 'business' AND field_name = 'rating';
UPDATE form_configs SET options = '["Ежедневно", "Несколько раз в неделю", "Раз в неделю", "Раз в месяц", "Редко"]' WHERE form_type = 'business' AND field_name = 'usage_frequency';

-- Удаляем старую конфигурацию формы руководителей
DELETE FROM form_configs WHERE form_type = 'exec';

-- Конфигурация формы для руководителей IT-департаментов (обновленная)
INSERT INTO form_configs (form_type, section_name, field_order, field_type, field_label, field_name, required, placeholder, help_text) VALUES
('exec', 'Основная информация', 1, 'text', 'Ваше имя', 'client_name', true, 'Алексей Сидоров', 'ФИО'),
('exec', 'Основная информация', 2, 'email', 'Email', 'client_email', true, 'alexey@company.com', 'Рабочий email'),
('exec', 'Основная информация', 3, 'text', 'Должность', 'position', true, 'CTO', 'Ваша должность'),
('exec', 'Основная информация', 4, 'text', 'Компания', 'company', true, 'ООО "ТехХолдинг"', 'Название организации'),
('exec', 'Основная информация', 5, 'select', 'Размер компании', 'company_size', false, NULL, 'Количество сотрудников'),
('exec', 'Оценка удовлетворенности', 6, 'select', 'Общая удовлетворенность продуктом', 'satisfaction_score', true, NULL, 'Насколько вы довольны продуктом?'),
('exec', 'Бизнес-ценность', 7, 'textarea', 'Основная ценность для бизнеса', 'business_value', true, 'Снижение затрат на 30%, ускорение процессов...', 'Какую пользу продукт приносит вашему бизнесу?'),
('exec', 'Бизнес-ценность', 8, 'select', 'Оценка ROI', 'roi_score', false, NULL, 'Оцените возврат инвестиций'),
('exec', 'Бизнес-ценность', 9, 'textarea', 'Влияние на метрики', 'metrics_impact', false, 'Время ответа: -50%, Бюджет: -30%...', 'Как продукт влияет на ключевые метрики?'),
('exec', 'Стратегия', 10, 'textarea', 'Предложения по развитию', 'development_proposals', false, 'Интеграция с SAP, мобильное приложение...', 'Что бы вы хотели видеть в продукте?'),
('exec', 'Стратегия', 11, 'select', 'Приоритет развития', 'development_priority', false, NULL, 'Что наиболее важно для вас?'),
('exec', 'Интеграция и безопасность', 12, 'select', 'Требования к интеграции', 'integration_needs', false, NULL, 'С какими системами нужно интегрироваться?'),
('exec', 'Интеграция и безопасность', 13, 'select', 'Уровень безопасности', 'security_requirements', false, NULL, 'Требования к безопасности'),
('exec', 'Действия', 14, 'select', 'Запросить встречу', 'request_meeting', false, NULL, 'Хотите организовать встречу?'),
('exec', 'Действия', 15, 'select', 'Запросить демо', 'request_demo', false, NULL, 'Нужно ли дополнительное демо?'),
('exec', 'Дополнительно', 16, 'textarea', 'Дополнительные комментарии', 'additional_comments', false, 'Любые другие вопросы или предложения...', 'Есть что-то еще что вы хотите обсудить?');

-- Добавляем опции для формы руководителей IT-департаментов (обновленные)
UPDATE form_configs SET options = '["1-50", "51-200", "201-1000", "1000+"]' WHERE form_type = 'exec' AND field_name = 'company_size';
UPDATE form_configs SET options = '["10", "9", "8", "7", "6", "5", "4", "3", "2", "1"]' WHERE form_type = 'exec' AND field_name = 'satisfaction_score';
UPDATE form_configs SET options = '["Отличный (>200%)", "Хороший (100-200%)", "Средний (50-100%)", "Низкий (<50%)"]' WHERE form_type = 'exec' AND field_name = 'roi_score';
UPDATE form_configs SET options = '["Интеграция с ERP", "Мобильные приложения", "AI/ML функции", "Улучшенная аналитика", "Безопасность", "Другое"]' WHERE form_type = 'exec' AND field_name = 'development_priority';
UPDATE form_configs SET options = '["SAP", "1C", "Salesforce", "Microsoft Dynamics", "Кастомные системы", "Не требуется"]' WHERE form_type = 'exec' AND field_name = 'integration_needs';
UPDATE form_configs SET options = '["Высочайший (банковский уровень)", "Высокий (корпоративный)", "Стандартный", "Базовый"]' WHERE form_type = 'exec' AND field_name = 'security_requirements';
UPDATE form_configs SET options = '["Да, срочно", "Да, в течение недели", "Да, в течение месяца", "Нет, спасибо"]' WHERE form_type = 'exec' AND field_name = 'request_meeting';
UPDATE form_configs SET options = '["Да, нужно", "Возможно, позже", "Нет, спасибо"]' WHERE form_type = 'exec' AND field_name = 'request_demo';

-- Добавляем несколько тестовых клиентов
INSERT INTO clients (client_id, client_name, client_email, client_role, client_type, company_name, department) VALUES
('tech_001', 'Иван Иванов', 'ivan@techcompany.com', 'Разработчик', 'technical', 'ООО "ТехСол"', 'IT'),
('business_001', 'Мария Петрова', 'maria@businesscorp.ru', 'Менеджер', 'business', 'АО "БизнесПро"', 'Продажи'),
('exec_001', 'Алексей Сидоров', 'alexey@holding.com', 'CTO', 'executive', 'Холдинг "Инвест"', 'IT-дирекция');

-- Добавляем начальную аналитику
INSERT INTO analytics (metric_type, metric_date, form_type, total_feedbacks, critical_feedbacks, resolved_feedbacks) VALUES
('daily_stats', CURRENT_DATE, 'tech', 0, 0, 0),
('daily_stats', CURRENT_DATE, 'business', 0, 0, 0),
('daily_stats', CURRENT_DATE, 'exec', 0, 0, 0),
('weekly_stats', CURRENT_DATE - INTERVAL '7 days', 'tech', 0, 0, 0),
('weekly_stats', CURRENT_DATE - INTERVAL '7 days', 'business', 0, 0, 0),
('weekly_stats', CURRENT_DATE - INTERVAL '7 days', 'exec', 0, 0, 0);

-- Создаем представление для активных конфигураций форм
CREATE OR REPLACE VIEW active_form_configs AS
SELECT 
    form_type,
    section_name,
    field_order,
    field_type,
    field_label,
    field_name,
    options,
    required,
    placeholder,
    help_text
FROM form_configs 
WHERE is_active = true 
ORDER BY form_type, field_order;

COMMENT ON VIEW active_form_configs IS 'Активные конфигурации форм для генерации';

-- Создаем функцию для получения конфигурации формы
CREATE OR REPLACE FUNCTION get_form_config(p_form_type VARCHAR(20))
RETURNS TABLE (
    section_name VARCHAR(100),
    field_order INTEGER,
    field_type VARCHAR(50),
    field_label TEXT,
    field_name VARCHAR(100),
    options JSONB,
    required BOOLEAN,
    placeholder TEXT,
    help_text TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        fc.section_name,
        fc.field_order,
        fc.field_type,
        fc.field_label,
        fc.field_name,
        fc.options,
        fc.required,
        fc.placeholder,
        fc.help_text
    FROM form_configs fc
    WHERE fc.form_type = p_form_type 
    AND fc.is_active = true
    ORDER BY fc.field_order;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_form_config(VARCHAR) IS 'Получение конфигурации формы по типу';
