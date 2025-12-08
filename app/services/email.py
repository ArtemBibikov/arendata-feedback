"""
Email Notification Service for Arenadata Feedback System
Отправка email уведомлений клиентам
"""

import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from jinja2 import Template
from datetime import datetime
from app.models import Feedback


class EmailNotifier:
    """Класс для отправки email уведомлений"""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = os.getenv("SMTP_PORT", "587")
        self.smtp_port = int(smtp_port) if smtp_port else 587
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@arenadata.ru")
        
        # Получатели для HIGH приоритета по ролям
        self.recipients = {
            "exec_high": os.getenv("MANAGER_EMAIL", "product-lead@arenadata.ru"),
            "business_high": os.getenv("SUPPORT_EMAIL", "support@arenadata.ru"),
            "tech_high": os.getenv("TECH_LEAD_EMAIL", "tech-lead@arenadata.ru")
        }
        
        # Проверка настроек
        if not self.smtp_user or not self.smtp_password:
            print("WARNING: Email credentials not configured")
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Отправить email"""
        if not self.smtp_user or not self.smtp_password:
            return False
        
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email
            
            # Добавляем текстовую версию
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                message.attach(text_part)
            
            # Добавляем HTML версию
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)
            
            async with aiosmtplib.SMTP(
                host=self.smtp_host,
                port=self.smtp_port,
                use_tls=True
            ) as smtp:
                await smtp.login(self.smtp_user, self.smtp_password)
                await smtp.send_message(message)
                return True
                
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def format_confirmation_email(self, feedback: Feedback) -> Dict[str, str]:
        """Отформатировать email подтверждения"""
        subject = "Ваш отзыв принят - Arenadata"
        
        html_template = """
        <html>
        <body>
            <h2>Спасибо за ваш отзыв!</h2>
            <p>Мы получили ваше обращение и обязательно его рассмотрим.</p>
            
            <h3>Детали обращения:</h3>
            <ul>
                <li><strong>ID:</strong> {{ feedback.id }}</li>
                <li><strong>Тип:</strong> {{ feedback.form_type }}</li>
                <li><strong>Срочность:</strong> {{ feedback.urgency }}</li>
                <li><strong>Время:</strong> {{ feedback.created_at.strftime('%Y-%m-%d %H:%M') }}</li>
            </ul>
            
            {% if feedback.urgency == 'critical' %}
            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0;">
                <strong>🚨 Ваш отзыв отмечен как критический. Наша команда уже уведомлена и свяжется с вами в ближайшее время.</strong>
            </div>
            {% endif %}
            
            <p>С уважением,<br>Команда Arenadata</p>
        </body>
        </html>
        """
        
        text_template = """
        Спасибо за ваш отзыв!
        
        Мы получили ваше обращение и обязательно его рассмотрим.
        
        Детали обращения:
        ID: {{ feedback.id }}
        Тип: {{ feedback.form_type }}
        Срочность: {{ feedback.urgency }}
        Время: {{ feedback.created_at.strftime('%Y-%m-%d %H:%M') }}
        
        {% if feedback.urgency == 'critical' %}
        ВАЖНО: Ваш отзыв отмечен как критический. Наша команда уже уведомлена и свяжется с вами в ближайшее время.
        {% endif %}
        
        С уважением,
        Команда Arenadata
        """
        
        html_content = Template(html_template).render(feedback=feedback)
        text_content = Template(text_template).render(feedback=feedback)
        
        return {
            "subject": subject,
            "html": html_content,
            "text": text_content
        }
    
    async def send_confirmation(self, feedback: Feedback) -> bool:
        """Отправить подтверждение получения отзыва"""
        if not feedback.client_email:
            return True  # Нет email для отправки
        
        email_data = self.format_confirmation_email(feedback)
        
        return await self.send_email(
            to_email=feedback.client_email,
            subject=email_data["subject"],
            html_content=email_data["html"],
            text_content=email_data["text"]
        )
    
    def format_critical_email(self, feedback: Feedback) -> Dict[str, str]:
        """Форматирование критического email для команды"""
        # Определяем получателя на основе типа формы
        form_type_map = {
            'exec': ('exec_high', 'руководителя'),
            'business': ('business_high', 'бизнес-пользователя'),
            'tech': ('tech_high', 'технического специалиста')
        }
        
        recipient_key, role_name = form_type_map.get(feedback.form_type, ('exec_high', 'пользователя'))
        recipient_email = self.recipients[recipient_key]
        
        # Определяем тему письма
        urgency_icons = {
            'critical': '🚨 КРИТИЧЕСКИЙ',
            'high': '⚠️ ВЫСОКИЙ',
            'medium': '🔶 СРЕДНИЙ',
            'low': '📝 НИЗКИЙ'
        }
        urgency_display = urgency_icons.get(feedback.urgency, feedback.urgency)
        
        subject = f"{urgency_display} отзыв от {role_name} - ID: {feedback.id}"
        
        html_template = """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: #f8f9fa; padding: 20px; border-left: 5px solid #dc3545;">
                <h2 style="color: #dc3545;">{{ urgency_display }} ОТЗЫВ</h2>
                <p>Требует немедленного внимания!</p>
            </div>
            
            <h3>📋 Детали обращения:</h3>
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>ID:</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ feedback.id }}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Тип формы:</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ role_name }}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Срочность:</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px; color: #dc3545;"><strong>{{ feedback.urgency }}</strong></td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Клиент:</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ feedback.client_name or 'Не указано' }}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Email:</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ feedback.client_email or 'Не указано' }}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Время получения:</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ feedback.created_at.strftime('%Y-%m-%d %H:%M:%S') }}</td>
                </tr>
            </table>
            
            <h3>📝 Сообщение:</h3>
            <div style="background-color: #fff; border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
                {{ feedback.message }}
            </div>
            
            <h3>🎯 Необходимые действия:</h3>
            <ol>
                <li>Связаться с клиентом в течение <strong>1 часа</strong></li>
                <li>Оценить критичность ситуации</li>
                <li>Сообщить о предполагаемом времени решения</li>
                <li>Обновить статус в системе обратной связи</li>
            </ol>
            
            <div style="margin-top: 20px; padding: 10px; background-color: #e9ecef;">
                <p><strong>Ссылка для управления:</strong> 
                <a href="https://admin.arenadata.ru/feedback/{{ feedback.id }}">Перейти к обращению</a></p>
            </div>
            
            <hr>
            <p><em>Это письмо отправлено автоматически системой Continuous Feedback.</em></p>
        </body>
        </html>
        """
        
        text_template = """
{{ urgency_display }} ОТЗЫВ - Требует немедленного внимания!

Детали обращения:
ID: {{ feedback.id }}
Тип формы: {{ role_name }}
Срочность: {{ feedback.urgency }} (КРИТИЧЕСКИЙ)
Клиент: {{ feedback.client_name or 'Не указано' }}
Email: {{ feedback.client_email or 'Не указано' }}
Время получения: {{ feedback.created_at.strftime('%Y-%m-%d %H:%M:%S') }}

Сообщение:
{{ feedback.message }}

Необходимые действия:
1. Связаться с клиентом в течение 1 часа
2. Оценить критичность ситуации
3. Сообщить о предполагаемом времени решения
4. Обновить статус в системе обратной связи

Ссылка для управления: https://admin.arenadata.ru/feedback/{{ feedback.id }}

---
Это письмо отправлено автоматически системой Continuous Feedback.
        """
        
        html_content = Template(html_template).render(
            feedback=feedback,
            role_name=role_name,
            urgency_display=urgency_display
        )
        text_content = Template(text_template).render(
            feedback=feedback,
            role_name=role_name,
            urgency_display=urgency_display
        )
        
        return {
            "recipient": recipient_email,
            "subject": subject,
            "html": html_content,
            "text": text_content
        }
    
    async def send_critical_notification(self, feedback: Feedback) -> bool:
        """Отправить уведомление о критическом отзыве команде"""
        # Отправляем только для HIGH приоритета
        if feedback.urgency not in ['high']:
            return True  # Не отправляем для medium/low
        
        email_data = self.format_critical_email(feedback)
        
        return await self.send_email(
            to_email=email_data["recipient"],
            subject=email_data["subject"],
            html_content=email_data["html"],
            text_content=email_data["text"]
        )
    
    async def test_connection(self) -> bool:
        """Проверить соединение с SMTP сервером"""
        if not self.smtp_user or not self.smtp_password:
            return False
        
        try:
            async with aiosmtplib.SMTP(
                host=self.smtp_host,
                port=self.smtp_port,
                use_tls=True
            ) as smtp:
                await smtp.login(self.smtp_user, self.smtp_password)
                return True
        except Exception as e:
            print(f"Email connection test failed: {e}")
            return False


# Глобальный экземпляр нотификатора
email_notifier = EmailNotifier()


async def send_confirmation_email(feedback: Feedback) -> bool:
    """Отправить email подтверждения"""
    return await email_notifier.send_confirmation(feedback)


async def send_critical_team_email(feedback: Feedback) -> bool:
    """Отправить email уведомление команде о критическом отзыве"""
    return await email_notifier.send_critical_notification(feedback)


async def send_magic_link_email(email: str, magic_link: str) -> bool:
    """Отправить Magic Link для входа клиента"""
    subject = "Вход в Arenadata Feedback System"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Вход в Arenadata</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background: #f9f9f9; }}
            .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Arenadata Feedback System</h1>
                <p>Добро пожаловать!</p>
            </div>
            <div class="content">
                <h2>Вход в систему</h2>
                <p>Вы запросили вход в систему Arenadata Feedback System.</p>
                <p>Нажмите на кнопку ниже, чтобы войти:</p>
                <div style="text-align: center;">
                    <a href="{magic_link}" class="button">Войти в систему</a>
                </div>
                <p><strong>Важно:</strong></p>
                <ul>
                    <li>Ссылка действительна 1 час</li>
                    <li>Используйте её один раз</li>
                    <li>Не передавайте ссылку другим лицам</li>
                </ul>
                <p>Если вы не запрашивали вход, проигнорируйте это письмо.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 Arenadata. Все права защищены.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Arenadata Feedback System
    
    Вы запросили вход в систему Arenadata Feedback System.
    
    Для входа перейдите по ссылке:
    {magic_link}
    
    Важно:
    - Ссылка действительна 1 час
    - Используйте её один раз
    - Не передавайте ссылку другим лицам
    
    Если вы не запрашивали вход, проигнорируйте это письмо.
    
    © 2024 Arenadata. Все права защищены.
    """
    
    return await email_notifier.send_email(
        to_email=email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )


async def test_email_connection() -> bool:
    """Проверить соединение с email сервером"""
    return await email_notifier.test_connection()