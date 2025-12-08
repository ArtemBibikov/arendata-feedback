-- Представления и материализованные представления для SQL Admin
-- Оптимизированные для быстрой работы в Adminer

-- 1. Представления для типовых отчетов (VIEWS)
-- ============================================

-- Активные конфигурации форм
CREATE OR REPLACE VIEW active_form_configs AS
SELECT 
    fc.form_type,
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
WHERE fc.is_active = true
ORDER BY fc.form_type, fc.field_order;

COMMENT ON VIEW active_form_configs IS 'Активные конфигурации форм для генерации динамических форм';

-- Статистика по отзывам за сегодня
CREATE OR REPLACE VIEW today_feedbacks AS
SELECT 
    COUNT(*) as total_count,
    COUNT(CASE WHEN urgency = 'critical' THEN 1 END) as critical_count,
    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_count,
    AVG(CASE WHEN satisfaction_score IS NOT NULL THEN satisfaction_score END) as avg_satisfaction
FROM feedbacks 
WHERE DATE(created_at) = CURRENT_DATE;

COMMENT ON VIEW today_feedbacks IS 'Статистика отзывов за текущий день';

-- Критические отзывы за последние 24 часа
CREATE OR REPLACE VIEW critical_feedbacks_24h AS
SELECT 
    f.id,
    f.uuid,
    f.client_name,
    f.client_email,
    f.problem_text,
    f.urgency,
    f.category,
    f.status,
    f.created_at,
    f.assigned_to
FROM feedbacks f
WHERE f.urgency IN ('critical', 'high')
AND f.created_at >= NOW() - INTERVAL '24 hours'
ORDER BY f.created_at DESC;

COMMENT ON VIEW critical_feedbacks_24h IS 'Критические отзывы за последние 24 часа для срочной обработки';

-- Топ-10 проблем по категориям
CREATE OR REPLACE VIEW top_problems_by_category AS
SELECT 
    COALESCE(category, 'other') as category,
    COUNT(*) as count,
    COUNT(CASE WHEN urgency = 'critical' THEN 1 END) as critical_count
FROM feedbacks 
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY category
ORDER BY count DESC
LIMIT 10;

COMMENT ON VIEW top_problems_by_category IS 'Топ-10 проблем за последние 7 дней';

-- Статистика по клиентам
CREATE OR REPLACE VIEW client_stats AS
SELECT 
    c.client_name,
    c.company_name,
    c.client_email,
    c.total_feedbacks,
    c.last_feedback_at,
    c.satisfaction_avg,
    COUNT(f.id) as recent_feedbacks
FROM clients c
LEFT JOIN feedbacks f ON c.client_id = f.client_id 
    AND f.created_at >= NOW() - INTERVAL '30 days'
WHERE c.is_active = true
GROUP BY c.id, c.client_name, c.company_name, c.client_email, c.total_feedbacks, c.last_feedback_at, c.satisfaction_avg
ORDER BY c.total_feedbacks DESC;

COMMENT ON VIEW client_stats IS 'Статистика по активным клиентам';

-- 2. Материализованные представления для сложной аналитики
-- =====================================================

-- Ежедневная статистика (материализованное)
CREATE MATERIALIZED VIEW daily_stats_materialized AS
SELECT 
    DATE(created_at) as date,
    form_type,
    COUNT(*) as total_feedbacks,
    COUNT(CASE WHEN urgency = 'critical' THEN 1 END) as critical_feedbacks,
    COUNT(CASE WHEN urgency = 'high' THEN 1 END) as high_feedbacks,
    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_feedbacks,
    AVG(response_time_seconds) as avg_response_time_seconds,
    AVG(CASE WHEN satisfaction_score IS NOT NULL THEN satisfaction_score END) as avg_satisfaction,
    COUNT(DISTINCT client_email) as unique_clients
FROM feedbacks
GROUP BY DATE(created_at), form_type
ORDER BY date DESC, form_type;

COMMENT ON MATERIALIZED VIEW daily_stats_materialized IS 'Ежедневная статистика по отзывам (материализованное представление)';

-- Уникальный индекс для материализованного представления
CREATE UNIQUE INDEX idx_daily_stats_date_form ON daily_stats_materialized(date, form_type);
CREATE INDEX idx_daily_stats_date ON daily_stats_materialized(date);

-- Еженедельная статистика (материализованное)
CREATE MATERIALIZED VIEW weekly_stats_materialized AS
SELECT 
    date_trunc('week', created_at) as week_start,
    form_type,
    COUNT(*) as total_feedbacks,
    COUNT(CASE WHEN urgency = 'critical' THEN 1 END) as critical_feedbacks,
    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_feedbacks,
    AVG(response_time_seconds) as avg_response_time_seconds,
    AVG(CASE WHEN satisfaction_score IS NOT NULL THEN satisfaction_score END) as avg_satisfaction,
    COUNT(DISTINCT client_email) as unique_clients
FROM feedbacks
GROUP BY date_trunc('week', created_at), form_type
ORDER BY week_start DESC, form_type;

COMMENT ON MATERIALIZED VIEW weekly_stats_materialized IS 'Еженедельная статистика по отзывам (материализованное представление)';

-- Уникальный индекс для еженедельной статистики
CREATE UNIQUE INDEX idx_weekly_stats_week_form ON weekly_stats_materialized(week_start, form_type);
CREATE INDEX idx_weekly_stats_week ON weekly_stats_materialized(week_start);

-- Статистика по категориям (материализованное)
CREATE MATERIALIZED VIEW category_stats_materialized AS
SELECT 
    COALESCE(category, 'other') as category,
    form_type,
    COUNT(*) as total_count,
    COUNT(CASE WHEN urgency = 'critical' THEN 1 END) as critical_count,
    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_count,
    AVG(CASE WHEN satisfaction_score IS NOT NULL THEN satisfaction_score END) as avg_satisfaction,
    MIN(created_at) as first_occurrence,
    MAX(created_at) as last_occurrence
FROM feedbacks
GROUP BY COALESCE(category, 'other'), form_type
ORDER BY total_count DESC;

COMMENT ON MATERIALIZED VIEW category_stats_materialized IS 'Статистика по категориям проблем (материализованное представление)';

-- Индексы для категорий
CREATE INDEX idx_category_stats_category ON category_stats_materialized(category);
CREATE INDEX idx_category_stats_form_type ON category_stats_materialized(form_type);

-- 3. Функции для обновления материализованных представлений
-- ==========================================================

-- Функция обновления всех материализованных представлений
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_stats_materialized;
    REFRESH MATERIALIZED VIEW CONCURRENTLY weekly_stats_materialized;
    REFRESH MATERIALIZED VIEW CONCURRENTLY category_stats_materialized;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_all_materialized_views() IS 'Обновление всех материализованных представлений для аналитики';

-- 4. Индексы оптимизированные для Adminer
-- ========================================

-- Дополнительные индексы для быстрых SELECT запросов из Adminer
CREATE INDEX IF NOT EXISTS idx_feedbacks_admin_search ON feedbacks USING GIN(
    to_tsvector('russian', COALESCE(problem_text, '') || ' ' || COALESCE(client_name, '') || ' ' || COALESCE(category, ''))
);

-- Композитный индекс для фильтрации по дате и статусу
CREATE INDEX IF NOT EXISTS idx_feedbacks_date_status ON feedbacks(created_at DESC, status);

-- Индекс для поиска по email клиента
CREATE INDEX IF NOT EXISTS idx_feedbacks_client_email_lower ON feedbacks(LOWER(client_email));

-- Частичный индекс только для критических отзывов
CREATE INDEX IF NOT EXISTS idx_feedbacks_critical_only ON feedbacks(created_at DESC) 
WHERE urgency IN ('critical', 'high');

-- 5. Полезные SQL запросы для Adminer
-- ==================================

-- Быстрые запросы для менеджеров (можно сохранить в Adminer)
-- 1. Все критические отзывы за сегодня
-- SELECT * FROM critical_feedbacks_24h WHERE DATE(created_at) = CURRENT_DATE;

-- 2. Статистика за сегодня
-- SELECT * FROM today_feedbacks;

-- 3. Топ проблем за неделю
-- SELECT * FROM top_problems_by_category;

-- 4. Клиенты с наибольшим количеством отзывов
-- SELECT * FROM client_stats WHERE total_feedbacks > 0 ORDER BY total_feedbacks DESC LIMIT 20;

-- 5. Среднее время решения по типам форм
-- SELECT form_type, AVG(response_time_seconds)/60 as avg_minutes 
-- FROM daily_stats_materialized 
-- WHERE avg_response_time_seconds IS NOT NULL 
-- GROUP BY form_type;

-- 6. Удовлетворенность клиентов по категориям
-- SELECT category, avg_satisfaction, total_count 
-- FROM category_stats_materialized 
-- WHERE avg_satisfaction IS NOT NULL 
-- ORDER BY avg_satisfaction DESC;

-- 7. Активность за последние 30 дней
-- SELECT date, SUM(total_feedbacks) as daily_total 
-- FROM daily_stats_materialized 
-- WHERE date >= CURRENT_DATE - INTERVAL "30 days" 
-- GROUP BY date 
-- ORDER BY date DESC;

-- 8. Нерешенные критические отзывы
-- SELECT id, client_name, problem_text, created_at 
-- FROM feedbacks 
-- WHERE urgency = "critical" AND status != "resolved" 
-- ORDER BY created_at ASC;

-- 9. Производительность команды
-- SELECT assigned_to, COUNT(*) as assigned_count, 
--        COUNT(CASE WHEN status = "resolved" THEN 1 END) as resolved_count,
--        ROUND(COUNT(CASE WHEN status = "resolved" THEN 1 END) * 100.0 / COUNT(*), 2) as resolution_rate
-- FROM feedbacks 
-- WHERE assigned_to IS NOT NULL 
-- GROUP BY assigned_to 
-- ORDER BY resolved_count DESC;

-- 10. Прогноз нагрузки (отзывы по дням недели)
-- SELECT EXTRACT(DOW FROM created_at) as day_of_week,
--        COUNT(*) as feedback_count,
--        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
-- FROM feedbacks 
-- WHERE created_at >= CURRENT_DATE - INTERVAL "90 days"
-- GROUP BY EXTRACT(DOW FROM created_at)
-- ORDER BY day_of_week;

-- 6. Автоматическое обновление материализованных представлений
-- =============================================================

-- Создаем триггер для автоматического обновления при изменении данных
CREATE OR REPLACE FUNCTION auto_refresh_materialized_views()
RETURNS TRIGGER AS $$
BEGIN
    -- Обновляем только при значительных изменениях
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
        -- Можно добавить логику для обновления по расписанию вместо каждого изменения
        -- REFRESH MATERIALIZED VIEW CONCURRENTLY daily_stats_materialized;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Включаем триггер (опционально, можно обновлять по расписанию)
-- CREATE TRIGGER trigger_auto_refresh AFTER INSERT OR UPDATE OR DELETE ON feedbacks
--     FOR EACH STATEMENT EXECUTE FUNCTION auto_refresh_materialized_views();

-- Рекомендация: Обновлять материализованные представления по расписанию:
-- Запускать REFRESH MATERIALIZED VIEW CONCURRENTLY daily_stats_materialized каждый час
-- Запускать REFRESH MATERIALIZED VIEW CONCURRENTLY weekly_stats_materialized каждый день
-- Запускать REFRESH MATERIALIZED VIEW CONCURRENTLY category_stats_materialized каждые 4 часа
