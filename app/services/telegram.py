"""
Telegram Notification Service for Arenadata Feedback System
Отправка уведомлений в Telegram о критических отзывах
"""

import os
from typing import Dict, Any
import httpx
from app.models import Feedback


class TelegramNotifier:
    """Класс для отправки уведомлений в Telegram"""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Проверка настроек
        if not self.bot_token or not self.chat_id:
            print("WARNING: Telegram credentials not configured")
    
    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Отправить сообщение в Telegram
        
        Args:
            text: Текст сообщения
            parse_mode: Режим форматирования (HTML/Markdown)
            
        Returns:
            True если успешно, иначе False
        """
        if not self.bot_token or not self.chat_id:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": True
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return True
                else:
                    print(f"Telegram API error: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False
    
    def format_critical_feedback(self, feedback: Feedback) -> str:
        """
        Отформатировать критический отзыв для Telegram
        
        Args:
            feedback: Объект отзыва
            
        Returns:
            Отформатированное сообщение
        """
        urgency_emoji = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '📋',
            'low': 'ℹ️'
        }
        
        form_type_emoji = {
            'tech': '👨‍💻',
            'business': '💼',
            'exec': '👔'
        }
        
        emoji = urgency_emoji.get(feedback.urgency, '📝')
        type_emoji = form_type_emoji.get(feedback.form_type, '📋')
        
        message = f"{emoji} <b>Высокий приоритет</b> {type_emoji}\n\n"
        
        if feedback.client_name:
            message += f"<b>Клиент:</b> {feedback.client_name}\n"
        
        if feedback.client_email:
            message += f"<b>Email:</b> {feedback.client_email}\n"
        
        message += f"<b>Тип:</b> {feedback.form_type}\n"
        message += f"<b>Срочность:</b> {feedback.urgency}\n"
        
        if feedback.category:
            message += f"<b>Категория:</b> {feedback.category}\n"
        
        # Обрезаем длинный текст
        problem_text = feedback.problem_text or ""
        if len(problem_text) > 300:
            problem_text = problem_text[:300] + "..."
        
        message += f"\n<b>Проблема:</b>\n{problem_text}\n\n"

        # Идентификаторы для быстрого поиска
        message += f"<b>ID:</b> {feedback.id}\n"
        if getattr(feedback, 'uuid', None):
            message += f"<b>UUID:</b> {feedback.uuid}\n"
        message += f"<b>Время:</b> {feedback.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"

        # Прямая ссылка в Adminer на запись в таблице feedbacks по ID
        adminer_url = (
            "http://localhost:8080/?pgsql=postgres"
            "&db=arenadata_feedback&ns=public&select=feedbacks"
            f"&where[id]={feedback.id}"
        )
        message += f"🔗 <a href='{adminer_url}'>Открыть в SQL Admin (feedbacks)</a> 🛠(в разработке)"
        
        return message
    
    def format_daily_summary(self, stats: Dict[str, Any]) -> str:
        """
        Отформатировать ежедневную статистику
        
        Args:
            stats: Статистика
            
        Returns:
            Отформатированное сообщение
        """
        message = "📊 <b>Ежедневная статистика</b>\n\n"
        message += f"📝 Всего отзывов: {stats.get('total_feedbacks', 0)}\n"
        message += f"🚨 Критических: {stats.get('critical_feedbacks', 0)}\n"
        message += f"✅ Решено: {stats.get('resolved_feedbacks', 0)}\n"
        
        if stats.get('avg_response_time_minutes'):
            message += f"⏱️ Среднее время: {stats['avg_response_time_minutes']} мин\n"
        
        if stats.get('satisfaction_avg'):
            message += f"😊 Удовлетворенность: {stats['satisfaction_avg']}/5\n"
        
        return message
    
    async def notify_critical_feedback(self, feedback: Feedback) -> bool:
        """
        Отправить уведомление о критическом отзыве
        
        Args:
            feedback: Объект отзыва
            
        Returns:
            True если успешно
        """
        if feedback.urgency not in ['high']:
            return False  # Не отправляем для некритических
        
        message = self.format_critical_feedback(feedback)
        return await self.send_message(message)
    
    async def notify_daily_summary(self, stats: Dict[str, Any]) -> bool:
        """
        Отправить ежедневную статистику
        
        Args:
            stats: Статистика
            
        Returns:
            True если успешно
        """
        message = self.format_daily_summary(stats)
        return await self.send_message(message)
    
    async def test_connection(self) -> bool:
        """
        Проверить соединение с Telegram API
        
        Returns:
            True если соединение работает
        """
        if not self.bot_token:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/getMe",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Telegram connection test failed: {e}")
            return False


# Глобальный экземпляр нотификатора
notifier = TelegramNotifier()


async def send_critical_notification(feedback: Feedback) -> bool:
    """
    Отправить уведомление о критическом отзыве
    
    Args:
        feedback: Объект отзыва
        
    Returns:
        True если успешно
    """
    return await notifier.notify_critical_feedback(feedback)


async def send_daily_summary(stats: Dict[str, Any]) -> bool:
    """
    Отправить ежедневную статистику
    
    Args:
        stats: Статистика
        
    Returns:
        True если успешно
    """
    return await notifier.notify_daily_summary(stats)


async def test_telegram_connection() -> bool:
    """
    Проверить соединение с Telegram
    
    Returns:
        True если соединение работает
    """
    return await notifier.test_connection()
