-- Готовые SQL-запросы для менеджеров Arenadata Feedback System
-- Эти запросы можно выполнять в Adminer в БД arenadata_feedback

-- 1. Все критические отзывы за последние 24 часа
SELECT *
FROM critical_feedbacks_24h;

-- 2. Статистика отзывов за сегодня
SELECT *
FROM today_feedbacks;

-- 3. Топ-10 проблем по категориям за последние 7 дней
SELECT *
FROM top_problems_by_category;

-- 4. Статистика по активным клиентам
SELECT *
FROM client_stats
ORDER BY total_feedbacks DESC;

-- 5. Ежедневная статистика по отзывам за последние 30 дней
SELECT *
FROM daily_stats_materialized
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date DESC, form_type;

-- 6. Еженедельная статистика по отзывам за последние 12 недель
SELECT *
FROM weekly_stats_materialized
WHERE week_start >= date_trunc('week', CURRENT_DATE) - INTERVAL '12 weeks'
ORDER BY week_start DESC, form_type;

-- 7. Статистика по категориям проблем
SELECT *
FROM category_stats_materialized
ORDER BY total_count DESC;
