# -*- coding: utf-8 -*-
"""
Simple Mailjet Email Service - Plain HTML (No Templates)
Works immediately without template configuration!
"""
import logging
from typing import Tuple
from django.conf import settings

try:
    from mailjet_rest import Client
    MAILJET_AVAILABLE = True
except ImportError:
    MAILJET_AVAILABLE = False

logger = logging.getLogger(__name__)


class SimpleMailjetService:
    """Simple Mailjet service using plain HTML (no templates)"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'MAILJET_API_KEY', None)
        self.secret_key = getattr(settings, 'MAILJET_SECRET_KEY', None)
        self.sender_email = getattr(settings, 'MAILJET_SENDER_EMAIL', None)
        self.sender_name = getattr(settings, 'MAILJET_SENDER_NAME', 'MenuMind AI')
        
        self.enabled = all([self.api_key, self.secret_key, self.sender_email])
        
        if self.enabled and MAILJET_AVAILABLE:
            self.client = Client(auth=(self.api_key, self.secret_key), version='v3.1')
        else:
            self.client = None
    
    def send_verification_email(self, to_email: str, user_name: str, activate_url: str, language: str = 'en') -> Tuple[bool, str]:
        """Send verification email using plain HTML"""
        if not self.enabled or not self.client:
            return False, "Mailjet not configured"
        
        # Get email content in correct language
        subject, html_content = self._get_verification_email_content(user_name, activate_url, language)
        
        data = {
            'Messages': [{
                "From": {
                    "Email": self.sender_email,
                    "Name": self.sender_name
                },
                "To": [{"Email": to_email}],
                "Subject": subject,
                "HTMLPart": html_content
            }]
        }
        
        try:
            result = self.client.send.create(data=data)
            
            if result.status_code == 200:
                return True, "Email sent successfully"
            else:
                return False, f"Mailjet error: {result.status_code}"
                
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False, str(e)
    
    def _get_verification_email_content(self, user_name: str, activate_url: str, language: str) -> Tuple[str, str]:
        """Get email subject and HTML content based on language"""
        
        if language == 'ru':
            subject = "Подтвердите ваш email - MenuMind AI"
            html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="margin: 0;">MenuMind AI</h1>
    </div>
    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
        <h2>Здравствуйте, {user_name}! 👋</h2>
        <p>Добро пожаловать в MenuMind AI! Мы рады приветствовать вас.</p>
        <p>Чтобы начать использовать ваш аккаунт, пожалуйста, подтвердите ваш email адрес:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{activate_url}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white !important; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">Подтвердить Email</a>
        </div>
        <p style="color: #666; font-size: 14px;">Если кнопка не работает, скопируйте эту ссылку:</p>
        <p style="color: #667eea; word-break: break-all; font-size: 13px;">{activate_url}</p>
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        <p style="color: #999; font-size: 13px;">© 2025 MenuMind AI. Все права защищены.</p>
    </div>
</body>
</html>
"""
        elif language == 'he':
            subject = "אמת את כתובת האימייל שלך - MenuMind AI"
            html = f"""
<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; direction: rtl;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="margin: 0;">MenuMind AI</h1>
    </div>
    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
        <h2>שלום {user_name}! 👋</h2>
        <p>ברוכים הבאים ל-MenuMind AI! אנחנו שמחים שהצטרפת אלינו.</p>
        <p>כדי להתחיל להשתמש בחשבון שלך, אנא אמת את כתובת האימייל שלך:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{activate_url}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white !important; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">אמת כתובת אימייל</a>
        </div>
        <p style="color: #666; font-size: 14px;">אם הכפתור לא עובד, העתק קישור זה:</p>
        <p style="color: #667eea; word-break: break-all; font-size: 13px; direction: ltr; display: inline-block;">{activate_url}</p>
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        <p style="color: #999; font-size: 13px;">© 2025 MenuMind AI. כל הזכויות שמורות.</p>
    </div>
</body>
</html>
"""
        else:  # English (default)
            subject = "Verify your email address - MenuMind AI"
            html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="margin: 0;">MenuMind AI</h1>
    </div>
    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
        <h2>Hello {user_name}! 👋</h2>
        <p>Welcome to MenuMind AI! We're excited to have you on board.</p>
        <p>To start using your account, please verify your email address by clicking the button below:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{activate_url}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white !important; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">Verify Email Address</a>
        </div>
        <p style="color: #666; font-size: 14px;">If the button doesn't work, copy and paste this link:</p>
        <p style="color: #667eea; word-break: break-all; font-size: 13px;">{activate_url}</p>
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        <p style="color: #999; font-size: 13px;">© 2025 MenuMind AI. All rights reserved.</p>
    </div>
</body>
</html>
"""
        
        return subject, html


_simple_mailjet_service = None

def get_simple_mailjet_service():
    global _simple_mailjet_service
    if _simple_mailjet_service is None:
        _simple_mailjet_service = SimpleMailjetService()
    return _simple_mailjet_service

