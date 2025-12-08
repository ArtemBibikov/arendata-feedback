# SQL Admin (Adminer) в Arenadata Feedback System

## 1. Доступ к Adminer

- URL: `http://localhost:8080`
- System: `PostgreSQL`
- Server:
  - внутри Docker: `postgres`
  - с хоста: `localhost:5433`

### Аккаунты

- Админский пользователь (для Dev / админов):
  - Username: `arenadata_admin`
  - Password: `admin_password_123`
  - Database: `arenadata_feedback`

- Пользователь приложения (для безопасного чтения / простых запросов):
  - Username: `arenadata_app`
  - Password: `secure_password_123`
  - Database: `arenadata_feedback`

## 2. Основные таблицы

- `form_configs` — конфигурации динамических форм
- `feedbacks` — все отзывы
- `clients` — клиенты
- `analytics` — агрегированная аналитика

## 3. Представления (VIEWS)

- `active_form_configs` — активные конфигурации форм
- `today_feedbacks` — статистика отзывов за текущий день
- `critical_feedbacks_24h` — критические и высокие отзывы за 24 часа
- `top_problems_by_category` — топ проблем по категориям за 7 дней
- `client_stats` — статистика по активным клиентам

## 4. Материализованные представления (матвью)

- `daily_stats_materialized` — ежедневная статистика
- `weekly_stats_materialized` — еженедельная статистика
- `category_stats_materialized` — статистика по категориям проблем

> Обновление матвью (только для админов):
>
> ```sql
> SELECT refresh_all_materialized_views();
> ```

## 5. Готовые SQL-запросы для менеджеров

См. файл `sql/admin_reports.sql` в репозитории. Его можно открыть и копировать запросы напрямую в Adminer.

Примеры:

- Критические отзывы за 24 часа:

```sql
SELECT * FROM critical_feedbacks_24h;
```

- Статистика за сегодня:

```sql
SELECT * FROM today_feedbacks;
```

- Топ проблем по категориям:

```sql
SELECT * FROM top_problems_by_category;
```

## 6. Рекомендации по безопасности Adminer

- Не публиковать Adminer напрямую в интернет.
- Доступ только через VPN / SSH-туннель / закрытую сеть.
- Для боевого окружения использовать reverse-proxy (nginx/Traefik) с:
  - HTTPS (валидный сертификат или корпоративный CA)
  - базовой аутентификацией (Basic Auth) или SSO.

В текущем Dev-окружении Adminer предназначен **только для локальной разработки**.
