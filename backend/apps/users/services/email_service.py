# -*- coding: utf-8 -*-
"""
EmailJS Integration Service for MenuMind AI

This service handles all email sending through EmailJS REST API.
Supports multilingual templates and proper error handling.

Environment Variables Required:
- EMAILJS_SERVICE_ID: Your EmailJS service ID
- EMAILJS_PUBLIC_KEY: Your EmailJS public key
- EMAILJS_PRIVATE_KEY: Your EmailJS private key (for server-side)
- EMAILJS_TEMPLATE_VERIFY_EN: Template ID for English verification
- EMAILJS_TEMPLATE_VERIFY_RU: Template ID for Russian verification
- EMAILJS_TEMPLATE_VERIFY_HE: Template ID for Hebrew verification
"""

import requests
import logging
from typing import Dict, Optional, Any
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class EmailJSService:
    """
    EmailJS REST API integration service.

    Handles server-side email sending through EmailJS with support for:
    - Multilingual templates
    - Retry logic
    - Error handling
    - Template rendering fallback
    """

    # EmailJS REST API endpoint
    API_URL = "https://api.emailjs.com/api/v1.0/email/send"

    def __init__(self):
        """Initialize EmailJS service with credentials from settings."""
        self.service_id = getattr(settings, 'EMAILJS_SERVICE_ID', None)
        self.public_key = getattr(settings, 'EMAILJS_PUBLIC_KEY', None)
        self.private_key = getattr(settings, 'EMAILJS_PRIVATE_KEY', None)

        # Template IDs for different languages
        self.templates = {
            'verification': {
                'en': getattr(settings, 'EMAILJS_TEMPLATE_VERIFY_EN', None),
                'ru': getattr(settings, 'EMAILJS_TEMPLATE_VERIFY_RU', None),
                'he': getattr(settings, 'EMAILJS_TEMPLATE_VERIFY_HE', None),
            }
        }

        self.enabled = all(
            [self.service_id, self.public_key, self.private_key])

        if not self.enabled:
            logger.warning(
                "[EmailJS] ⚠️ Service not fully configured. Missing credentials. "
                "Emails will not be sent."
            )

    def _get_template_id(self, email_type: str, language: str = 'en') -> Optional[str]:
        """
        Get EmailJS template ID for specific email type and language.

        Args:
            email_type: Type of email ('verification', 'welcome', etc.)
            language: Language code ('en', 'ru', 'he')

        Returns:
            Template ID or None if not configured
        """
        # Normalize language code
        language = language.lower()[:2]  # 'en-us' -> 'en'

        # Get template for email type and language
        template_config = self.templates.get(email_type, {})
        template_id = template_config.get(language)

        # Fallback to English if specific language not configured
        if not template_id and language != 'en':
            template_id = template_config.get('en')
            logger.info(
                f"[EmailJS] Template for {email_type}/{language} not found, "
                f"falling back to English"
            )

        return template_id

    def _prepare_payload(
        self,
        template_id: str,
        to_email: str,
        template_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare EmailJS API payload.

        Args:
            template_id: EmailJS template ID
            to_email: Recipient email address
            template_params: Parameters for template rendering

        Returns:
            Complete payload for EmailJS API
        """
        payload = {
            'service_id': self.service_id,
            'template_id': template_id,
            'user_id': self.public_key,
            'accessToken': self.private_key,
            'template_params': {
                'to_email': to_email,
                **template_params
            }
        }

        return payload

    def send_verification_email(
        self,
        to_email: str,
        user_name: str,
        activate_url: str,
        language: str = 'en'
    ) -> bool:
        """
        Send email verification message.

        Args:
            to_email: Recipient email address
            user_name: User's display name
            activate_url: Full verification URL
            language: Language code ('en', 'ru', 'he')

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.error(
                "[EmailJS] ❌ Service not configured. Cannot send email.")
            return False

        # Get template ID for language
        template_id = self._get_template_id('verification', language)

        if not template_id:
            logger.error(
                f"[EmailJS] ❌ No template configured for verification/{language}"
            )
            return False

        # Prepare template parameters
        template_params = {
            'user_name': user_name or 'there',
            'activate_url': activate_url,
            'site_name': 'MenuMind AI',
            'user_email': to_email,
            # Add language-specific texts
            'subject': self._get_subject(language),
            'greeting': self._get_greeting(user_name, language),
            'message': self._get_verification_message(language),
            'button_text': self._get_button_text(language),
            'footer_text': self._get_footer_text(language),
        }

        # Prepare payload
        payload = self._prepare_payload(template_id, to_email, template_params)

        # Send email via EmailJS API
        return self._send_email(payload, to_email, 'verification')

    def _send_email(
        self,
        payload: Dict[str, Any],
        to_email: str,
        email_type: str,
        max_retries: int = 2
    ) -> bool:
        """
        Send email via EmailJS REST API with retry logic.

        Args:
            payload: Complete EmailJS API payload
            to_email: Recipient email (for logging)
            email_type: Type of email (for logging)
            max_retries: Maximum number of retry attempts

        Returns:
            True if email sent successfully, False otherwise
        """
        for attempt in range(max_retries + 1):
            try:
                logger.info(
                    f"[EmailJS] 📧 Sending {email_type} email to {to_email} "
                    f"(attempt {attempt + 1}/{max_retries + 1})"
                )

                # Make API request
                response = requests.post(
                    self.API_URL,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )

                # Check response
                if response.status_code == 200:
                    logger.info(
                        f"[EmailJS] ✅ Successfully sent {email_type} email to {to_email}"
                    )
                    return True
                else:
                    logger.warning(
                        f"[EmailJS] ⚠️ Failed to send email. "
                        f"Status: {response.status_code}, "
                        f"Response: {response.text}"
                    )

                    # Don't retry on client errors (4xx)
                    if 400 <= response.status_code < 500:
                        logger.error(
                            f"[EmailJS] ❌ Client error ({response.status_code}). "
                            "Not retrying."
                        )
                        break

            except requests.exceptions.Timeout:
                logger.warning(
                    f"[EmailJS] ⏱️ Timeout sending email (attempt {attempt + 1})"
                )
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"[EmailJS] ⚠️ Request error: {str(e)} (attempt {attempt + 1})"
                )
            except Exception as e:
                logger.error(
                    f"[EmailJS] ❌ Unexpected error: {str(e)}"
                )
                break

        logger.error(
            f"[EmailJS] ❌ Failed to send {email_type} email to {to_email} "
            f"after {max_retries + 1} attempts"
        )
        return False

    # Language-specific text helpers

    def _get_subject(self, language: str) -> str:
        """Get email subject in specified language."""
        subjects = {
            'en': 'Verify your email address',
            'ru': 'Подтвердите ваш email адрес',
            'he': 'אמת את כתובת האימייל שלך'
        }
        return subjects.get(language, subjects['en'])

    def _get_greeting(self, user_name: str, language: str) -> str:
        """Get greeting text in specified language."""
        greetings = {
            'en': f'Hi {user_name}' if user_name else 'Hi there',
            'ru': f'Привет, {user_name}' if user_name else 'Привет',
            'he': f'שלום {user_name}' if user_name else 'שלום'
        }
        return greetings.get(language, greetings['en'])

    def _get_verification_message(self, language: str) -> str:
        """Get verification message text in specified language."""
        messages = {
            'en': (
                'Thank you for signing up for MenuMind AI! '
                'Please verify your email address by clicking the button below:'
            ),
            'ru': (
                'Спасибо за регистрацию в MenuMind AI! '
                'Пожалуйста, подтвердите ваш email адрес, нажав на кнопку ниже:'
            ),
            'he': (
                'תודה שנרשמת ל-MenuMind AI! '
                'אנא אמת את כתובת האימייל שלך על ידי לחיצה על הכפתור למטה:'
            )
        }
        return messages.get(language, messages['en'])

    def _get_button_text(self, language: str) -> str:
        """Get button text in specified language."""
        buttons = {
            'en': 'Verify Email Address',
            'ru': 'Подтвердить Email',
            'he': 'אמת אימייל'
        }
        return buttons.get(language, buttons['en'])

    def _get_footer_text(self, language: str) -> str:
        """Get footer text in specified language."""
        footers = {
            'en': (
                'If you did not create an account, please ignore this email. '
                'This link will expire in 24 hours.'
            ),
            'ru': (
                'Если вы не создавали аккаунт, пожалуйста, проигнорируйте это письмо. '
                'Эта ссылка истечёт через 24 часа.'
            ),
            'he': (
                'אם לא יצרת חשבון, אנא התעלם מאימייל זה. '
                'קישור זה יפוג בעוד 24 שעות.'
            )
        }
        return footers.get(language, footers['en'])


# Global service instance
_emailjs_service = None


def get_emailjs_service() -> EmailJSService:
    """Get or create EmailJS service singleton."""
    global _emailjs_service
    if _emailjs_service is None:
        _emailjs_service = EmailJSService()
    return _emailjs_service
