# -*- coding: utf-8 -*-
"""
Mailjet Email Service Integration

This service handles all transactional emails via Mailjet API v3.1.
Supports multilingual templates and proper error handling.

Environment Variables Required:
- MAILJET_API_KEY: Your Mailjet API key (public key)
- MAILJET_SECRET_KEY: Your Mailjet secret key
- MAILJET_SENDER_EMAIL: Verified sender email address
- MAILJET_SENDER_NAME: Sender name (e.g., "MenuMind AI")
- MAILJET_TEMPLATE_VERIFY_EN: Template ID for English verification
- MAILJET_TEMPLATE_VERIFY_RU: Template ID for Russian verification
- MAILJET_TEMPLATE_VERIFY_HE: Template ID for Hebrew verification
"""

import logging
import time
from typing import Dict, Optional, Any, Tuple
from django.conf import settings

# Try to import Mailjet library
try:
    from mailjet_rest import Client
    MAILJET_AVAILABLE = True
except ImportError:
    MAILJET_AVAILABLE = False
    # Fallback to requests library
    import requests
    import base64

logger = logging.getLogger(__name__)


class MailjetEmailService:
    """
    Mailjet transactional email service with multilingual support.

    Handles email sending through Mailjet API v3.1 with automatic retry logic,
    comprehensive error handling, and support for multiple languages.
    """

    # Mailjet API endpoint (used when library not available)
    API_URL = "https://api.mailjet.com/v3.1/send"

    def __init__(self):
        """Initialize Mailjet email service with credentials from settings."""
        self.api_key = getattr(settings, 'MAILJET_API_KEY', None)
        self.secret_key = getattr(settings, 'MAILJET_SECRET_KEY', None)
        self.sender_email = getattr(settings, 'MAILJET_SENDER_EMAIL', None)
        self.sender_name = getattr(
            settings, 'MAILJET_SENDER_NAME', 'MenuMind AI')

        # Template IDs for different email types and languages
        self.templates = {
            'verification': {
                'en': getattr(settings, 'MAILJET_TEMPLATE_VERIFY_EN', None),
                'ru': getattr(settings, 'MAILJET_TEMPLATE_VERIFY_RU', None),
                'he': getattr(settings, 'MAILJET_TEMPLATE_VERIFY_HE', None),
            },
            'welcome': {
                'en': getattr(settings, 'MAILJET_TEMPLATE_WELCOME_EN', None),
                'ru': getattr(settings, 'MAILJET_TEMPLATE_WELCOME_RU', None),
                'he': getattr(settings, 'MAILJET_TEMPLATE_WELCOME_HE', None),
            },
            'password_reset': {
                'en': getattr(settings, 'MAILJET_TEMPLATE_PASSWORD_RESET_EN', None),
                'ru': getattr(settings, 'MAILJET_TEMPLATE_PASSWORD_RESET_RU', None),
                'he': getattr(settings, 'MAILJET_TEMPLATE_PASSWORD_RESET_HE', None),
            },
            'notification': {
                'en': getattr(settings, 'MAILJET_TEMPLATE_NOTIFICATION_EN', None),
                'ru': getattr(settings, 'MAILJET_TEMPLATE_NOTIFICATION_RU', None),
                'he': getattr(settings, 'MAILJET_TEMPLATE_NOTIFICATION_HE', None),
            }
        }

        # Check if service is properly configured
        self.enabled = all([
            self.api_key,
            self.secret_key,
            self.sender_email,
            # At least English template required
            self.templates['verification']['en']
        ])

        if not self.enabled:
            logger.warning(
                "[Mailjet] ⚠️ Service not fully configured. Missing credentials or templates. "
                "Emails will not be sent via Mailjet."
            )
        else:
            logger.info(
                f"[Mailjet] ✅ Service initialized successfully. "
                f"Sender: {self.sender_name} <{self.sender_email}>"
            )

        # Initialize Mailjet client if library available
        if MAILJET_AVAILABLE and self.enabled:
            self.client = Client(
                auth=(self.api_key, self.secret_key), version='v3.1')
        else:
            self.client = None

    def _get_template_id_for_language(
        self,
        email_type: str,
        language: str = 'en'
    ) -> Optional[int]:
        """
        Get Mailjet template ID for specific email type and language.

        Args:
            email_type: Type of email ('verification', 'welcome', etc.)
            language: Language code ('en', 'ru', 'he')

        Returns:
            Template ID as integer or None if not configured
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
                f"[Mailjet] Template for {email_type}/{language} not found, "
                f"falling back to English"
            )

        # Convert to int if it's a string
        if template_id:
            try:
                return int(template_id)
            except (ValueError, TypeError):
                logger.error(
                    f"[Mailjet] Invalid template ID format: {template_id}"
                )
                return None

        return None

    def send_verification_email(
        self,
        to_email: str,
        user_name: str,
        activate_url: str,
        language: str = 'en'
    ) -> Tuple[bool, str]:
        """
        Send email verification message via Mailjet.

        Args:
            to_email: Recipient email address
            user_name: User's display name
            activate_url: Full verification URL
            language: Language code ('en', 'ru', 'he')

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.enabled:
            error_msg = "Mailjet service not configured"
            logger.error(f"[Mailjet] ❌ {error_msg}")
            return False, error_msg

        # Get template ID for language
        template_id = self._get_template_id_for_language(
            'verification', language)

        if not template_id:
            error_msg = f"No template configured for verification/{language}"
            logger.error(f"[Mailjet] ❌ {error_msg}")
            return False, error_msg

        # Prepare template variables
        template_vars = {
            'user_name': user_name or 'there',
            'activate_url': activate_url,
            'site_name': 'MenuMind AI',
            'user_email': to_email,
        }

        # Send email via Mailjet
        return self._send_transactional_email(
            to_email=to_email,
            template_id=template_id,
            template_vars=template_vars,
            language=language,
            email_type='verification'
        )

    def send_welcome_email(
        self,
        to_email: str,
        user_name: str,
        language: str = 'en'
    ) -> Tuple[bool, str]:
        """Send welcome email after successful verification."""
        if not self.enabled:
            return False, "Mailjet service not configured"

        template_id = self._get_template_id_for_language('welcome', language)
        if not template_id:
            return False, f"No template configured for welcome/{language}"

        template_vars = {
            'user_name': user_name or 'there',
            'site_name': 'MenuMind AI',
            'dashboard_url': f"{settings.FRONTEND_URL}/dashboard",
        }

        return self._send_transactional_email(
            to_email=to_email,
            template_id=template_id,
            template_vars=template_vars,
            language=language,
            email_type='welcome'
        )

    def send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_url: str,
        language: str = 'en'
    ) -> Tuple[bool, str]:
        """Send password reset email."""
        if not self.enabled:
            return False, "Mailjet service not configured"

        template_id = self._get_template_id_for_language(
            'password_reset', language)
        if not template_id:
            return False, f"No template configured for password_reset/{language}"

        template_vars = {
            'user_name': user_name or 'there',
            'reset_url': reset_url,
            'site_name': 'MenuMind AI',
        }

        return self._send_transactional_email(
            to_email=to_email,
            template_id=template_id,
            template_vars=template_vars,
            language=language,
            email_type='password_reset'
        )

    def send_notification_email(
        self,
        to_email: str,
        user_name: str,
        subject: str,
        message: str,
        language: str = 'en',
        action_url: str = None,
        action_text: str = None
    ) -> Tuple[bool, str]:
        """Send generic notification email."""
        if not self.enabled:
            return False, "Mailjet service not configured"

        template_id = self._get_template_id_for_language(
            'notification', language)
        if not template_id:
            return False, f"No template configured for notification/{language}"

        template_vars = {
            'user_name': user_name or 'there',
            'subject': subject,
            'message': message,
            'site_name': 'MenuMind AI',
        }

        if action_url:
            template_vars['action_url'] = action_url
        if action_text:
            template_vars['action_text'] = action_text

        return self._send_transactional_email(
            to_email=to_email,
            template_id=template_id,
            template_vars=template_vars,
            language=language,
            email_type='notification'
        )

    def _send_transactional_email(
        self,
        to_email: str,
        template_id: int,
        template_vars: Dict[str, Any],
        language: str = 'en',
        email_type: str = 'email',
        max_retries: int = 2
    ) -> Tuple[bool, str]:
        """
        Send transactional email via Mailjet API with retry logic.

        Args:
            to_email: Recipient email address
            template_id: Mailjet template ID
            template_vars: Variables for template rendering
            language: Language code for logging
            email_type: Type of email (verification, welcome, etc.)
            max_retries: Maximum number of retry attempts

        Returns:
            Tuple of (success: bool, message: str)
        """
        logger.info(
            f"[Mailjet] 📧 Sending {email_type} email to {to_email} "
            f"using template {template_id} (language: {language})"
        )

        for attempt in range(max_retries + 1):
            try:
                if MAILJET_AVAILABLE and self.client:
                    # Use official library
                    success, message = self._send_via_library(
                        to_email, template_id, template_vars
                    )
                else:
                    # Use REST API directly
                    success, message = self._send_via_rest(
                        to_email, template_id, template_vars
                    )

                if success:
                    logger.info(
                        f"[Mailjet] ✅ Successfully sent email to {to_email}"
                    )
                    return True, message

                # If not successful and not last attempt, continue to retry
                if attempt < max_retries:
                    logger.warning(
                        f"[Mailjet] ⚠️ Attempt {attempt + 1} failed: {message}. "
                        f"Retrying..."
                    )
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(
                        f"[Mailjet] ❌ Failed to send email after {max_retries + 1} "
                        f"attempts: {message}"
                    )
                    return False, message

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(
                    f"[Mailjet] ❌ Exception on attempt {attempt + 1}: {error_msg}",
                    exc_info=True
                )

                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                else:
                    return False, error_msg

        return False, "Maximum retries exceeded"

    def _send_via_library(
        self,
        to_email: str,
        template_id: int,
        template_vars: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Send email using Mailjet library.

        Args:
            to_email: Recipient email address
            template_id: Mailjet template ID
            template_vars: Template variables

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            data = {
                'Messages': [
                    {
                        "From": {
                            "Email": self.sender_email,
                            "Name": self.sender_name
                        },
                        "To": [
                            {
                                "Email": to_email
                            }
                        ],
                        "TemplateID": template_id,
                        "TemplateLanguage": True,
                        "Variables": template_vars
                    }
                ]
            }

            result = self.client.send.create(data=data)

            if result.status_code == 200:
                response_data = result.json()
                message_info = response_data.get('Messages', [{}])[0]
                status = message_info.get('Status', 'unknown')

                logger.info(
                    f"[Mailjet] Library Response: Status={status}"
                )

                if status == 'success':
                    return True, f"Email sent successfully via Mailjet"
                else:
                    return False, f"Mailjet returned status: {status}"
            else:
                error_msg = f"HTTP {result.status_code}: {result.text}"
                logger.error(f"[Mailjet] ❌ Library error: {error_msg}")

                if result.status_code == 401:
                    return False, "Invalid API credentials"
                elif result.status_code == 400:
                    return False, "Invalid request parameters"
                else:
                    return False, error_msg

        except Exception as e:
            error_msg = f"Library error: {str(e)}"
            logger.error(f"[Mailjet] ❌ {error_msg}")
            return False, error_msg

    def _send_via_rest(
        self,
        to_email: str,
        template_id: int,
        template_vars: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Send email using REST API directly (fallback when library not available).

        Args:
            to_email: Recipient email address
            template_id: Mailjet template ID
            template_vars: Template variables

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Prepare request payload
            payload = {
                "Messages": [
                    {
                        "From": {
                            "Email": self.sender_email,
                            "Name": self.sender_name
                        },
                        "To": [
                            {
                                "Email": to_email
                            }
                        ],
                        "TemplateID": template_id,
                        "TemplateLanguage": True,
                        "Variables": template_vars
                    }
                ]
            }

            # Prepare Basic Auth
            auth_string = f"{self.api_key}:{self.secret_key}"
            auth_bytes = auth_string.encode('utf-8')
            auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Basic {auth_b64}"
            }

            # Send request
            import requests
            response = requests.post(
                self.API_URL,
                json=payload,
                headers=headers,
                timeout=10
            )

            # Check response
            if response.status_code == 200:
                response_data = response.json()
                message_info = response_data.get('Messages', [{}])[0]
                status = message_info.get('Status', 'unknown')

                logger.info(
                    f"[Mailjet] REST API success. Status: {status}"
                )

                if status == 'success':
                    return True, f"Email sent successfully via Mailjet"
                else:
                    return False, f"Mailjet returned status: {status}"
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(
                    f"[Mailjet] ❌ REST API error: {error_msg}"
                )

                if response.status_code == 401:
                    return False, "Invalid API credentials"
                elif response.status_code == 400:
                    return False, f"Invalid request: {response.text}"
                else:
                    return False, error_msg

        except requests.exceptions.Timeout:
            error_msg = "Request timeout"
            logger.error(f"[Mailjet] ❌ {error_msg}")
            return False, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(f"[Mailjet] ❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"[Mailjet] ❌ {error_msg}")
            return False, error_msg


# Global service instance
_mailjet_service = None


def get_mailjet_service() -> MailjetEmailService:
    """Get or create Mailjet email service singleton."""
    global _mailjet_service
    if _mailjet_service is None:
        _mailjet_service = MailjetEmailService()
    return _mailjet_service
