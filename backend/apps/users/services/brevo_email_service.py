# -*- coding: utf-8 -*-
"""
Brevo (Sendinblue) Email Service Integration

This service handles all transactional emails via Brevo API v3.
Supports multilingual templates and proper error handling.

Environment Variables Required:
- BREVO_API_KEY: Your Brevo API key
- BREVO_SENDER_EMAIL: Verified sender email address
- BREVO_SENDER_NAME: Sender name (e.g., "MenuMind AI")
- BREVO_TEMPLATE_VERIFY_EN: Template ID for English verification
- BREVO_TEMPLATE_VERIFY_RU: Template ID for Russian verification
- BREVO_TEMPLATE_VERIFY_HE: Template ID for Hebrew verification
"""

import logging
import time
from typing import Dict, Optional, Any, Tuple
from django.conf import settings

# Try to import official Brevo SDK
try:
    import sib_api_v3_sdk
    from sib_api_v3_sdk.rest import ApiException
    BREVO_SDK_AVAILABLE = True
except ImportError:
    BREVO_SDK_AVAILABLE = False
    # Fallback to requests library
    import requests

logger = logging.getLogger(__name__)


class BrevoEmailService:
    """
    Brevo transactional email service with multilingual support.

    Handles email sending through Brevo API v3 with automatic retry logic,
    comprehensive error handling, and support for multiple languages.
    """

    # Brevo API endpoint (used when SDK not available)
    API_URL = "https://api.brevo.com/v3/smtp/email"

    def __init__(self):
        """Initialize Brevo email service with credentials from settings."""
        self.api_key = getattr(settings, 'BREVO_API_KEY', None)
        self.sender_email = getattr(settings, 'BREVO_SENDER_EMAIL', None)
        self.sender_name = getattr(
            settings, 'BREVO_SENDER_NAME', 'MenuMind AI')

        # Template IDs for different email types and languages
        self.templates = {
            'verification': {
                'en': getattr(settings, 'BREVO_TEMPLATE_VERIFY_EN', None),
                'ru': getattr(settings, 'BREVO_TEMPLATE_VERIFY_RU', None),
                'he': getattr(settings, 'BREVO_TEMPLATE_VERIFY_HE', None),
            },
            'welcome': {
                'en': getattr(settings, 'BREVO_TEMPLATE_WELCOME_EN', None),
                'ru': getattr(settings, 'BREVO_TEMPLATE_WELCOME_RU', None),
                'he': getattr(settings, 'BREVO_TEMPLATE_WELCOME_HE', None),
            },
            'password_reset': {
                'en': getattr(settings, 'BREVO_TEMPLATE_PASSWORD_RESET_EN', None),
                'ru': getattr(settings, 'BREVO_TEMPLATE_PASSWORD_RESET_RU', None),
                'he': getattr(settings, 'BREVO_TEMPLATE_PASSWORD_RESET_HE', None),
            },
            'notification': {
                'en': getattr(settings, 'BREVO_TEMPLATE_NOTIFICATION_EN', None),
                'ru': getattr(settings, 'BREVO_TEMPLATE_NOTIFICATION_RU', None),
                'he': getattr(settings, 'BREVO_TEMPLATE_NOTIFICATION_HE', None),
            }
        }

        # Check if service is properly configured
        self.enabled = all([
            self.api_key,
            self.sender_email,
            # At least English template required
            self.templates['verification']['en']
        ])

        if not self.enabled:
            logger.warning(
                "[Brevo] ⚠️ Service not fully configured. Missing credentials or templates. "
                "Emails will not be sent via Brevo."
            )
        else:
            logger.info(
                f"[Brevo] ✅ Service initialized successfully. "
                f"Sender: {self.sender_name} <{self.sender_email}>"
            )

        # Initialize SDK client if available
        if BREVO_SDK_AVAILABLE and self.enabled:
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = self.api_key
            self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )
        else:
            self.api_instance = None

    def _get_template_id_for_language(
        self,
        email_type: str,
        language: str = 'en'
    ) -> Optional[int]:
        """
        Get Brevo template ID for specific email type and language.

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
                f"[Brevo] Template for {email_type}/{language} not found, "
                f"falling back to English"
            )

        # Convert to int if it's a string
        if template_id:
            try:
                return int(template_id)
            except (ValueError, TypeError):
                logger.error(
                    f"[Brevo] Invalid template ID format: {template_id}"
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
        Send email verification message via Brevo.

        Args:
            to_email: Recipient email address
            user_name: User's display name
            activate_url: Full verification URL
            language: Language code ('en', 'ru', 'he')

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.enabled:
            error_msg = "Brevo service not configured"
            logger.error(f"[Brevo] ❌ {error_msg}")
            return False, error_msg

        # Get template ID for language
        template_id = self._get_template_id_for_language(
            'verification', language)

        if not template_id:
            error_msg = f"No template configured for verification/{language}"
            logger.error(f"[Brevo] ❌ {error_msg}")
            return False, error_msg

        # Prepare template parameters
        template_params = {
            'USER_NAME': user_name or 'there',
            'ACTIVATE_URL': activate_url,
            'SITE_NAME': 'MenuMind AI',
            'USER_EMAIL': to_email,
        }

        # Send email via Brevo
        return self._send_transactional_email(
            to_email=to_email,
            template_id=template_id,
            template_params=template_params,
            language=language,
            email_type='verification'
        )

    def send_welcome_email(
        self,
        to_email: str,
        user_name: str,
        language: str = 'en'
    ) -> Tuple[bool, str]:
        """
        Send welcome email after successful verification.

        Args:
            to_email: Recipient email address
            user_name: User's display name
            language: Language code ('en', 'ru', 'he')

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.enabled:
            error_msg = "Brevo service not configured"
            logger.error(f"[Brevo] ❌ {error_msg}")
            return False, error_msg

        template_id = self._get_template_id_for_language('welcome', language)

        if not template_id:
            error_msg = f"No template configured for welcome/{language}"
            logger.error(f"[Brevo] ❌ {error_msg}")
            return False, error_msg

        template_params = {
            'USER_NAME': user_name or 'there',
            'SITE_NAME': 'MenuMind AI',
            'USER_EMAIL': to_email,
            'DASHBOARD_URL': f"{settings.FRONTEND_URL}/dashboard",
        }

        return self._send_transactional_email(
            to_email=to_email,
            template_id=template_id,
            template_params=template_params,
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
        """
        Send password reset email.

        Args:
            to_email: Recipient email address
            user_name: User's display name
            reset_url: Password reset URL
            language: Language code ('en', 'ru', 'he')

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.enabled:
            error_msg = "Brevo service not configured"
            logger.error(f"[Brevo] ❌ {error_msg}")
            return False, error_msg

        template_id = self._get_template_id_for_language(
            'password_reset', language)

        if not template_id:
            error_msg = f"No template configured for password_reset/{language}"
            logger.error(f"[Brevo] ❌ {error_msg}")
            return False, error_msg

        template_params = {
            'USER_NAME': user_name or 'there',
            'RESET_URL': reset_url,
            'SITE_NAME': 'MenuMind AI',
            'USER_EMAIL': to_email,
        }

        return self._send_transactional_email(
            to_email=to_email,
            template_id=template_id,
            template_params=template_params,
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
        """
        Send generic notification email.

        Args:
            to_email: Recipient email address
            user_name: User's display name
            subject: Email subject
            message: Main message content
            language: Language code ('en', 'ru', 'he')
            action_url: Optional action button URL
            action_text: Optional action button text

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.enabled:
            error_msg = "Brevo service not configured"
            logger.error(f"[Brevo] ❌ {error_msg}")
            return False, error_msg

        template_id = self._get_template_id_for_language(
            'notification', language)

        if not template_id:
            error_msg = f"No template configured for notification/{language}"
            logger.error(f"[Brevo] ❌ {error_msg}")
            return False, error_msg

        template_params = {
            'USER_NAME': user_name or 'there',
            'SUBJECT': subject,
            'MESSAGE': message,
            'SITE_NAME': 'MenuMind AI',
            'USER_EMAIL': to_email,
        }

        if action_url:
            template_params['ACTION_URL'] = action_url
        if action_text:
            template_params['ACTION_TEXT'] = action_text

        return self._send_transactional_email(
            to_email=to_email,
            template_id=template_id,
            template_params=template_params,
            language=language,
            email_type='notification'
        )

    def _send_transactional_email(
        self,
        to_email: str,
        template_id: int,
        template_params: Dict[str, Any],
        language: str = 'en',
        email_type: str = 'email',
        max_retries: int = 2
    ) -> Tuple[bool, str]:
        """
        Send transactional email via Brevo API with retry logic.

        Args:
            to_email: Recipient email address
            template_id: Brevo template ID
            template_params: Parameters for template rendering
            language: Language code for logging
            email_type: Type of email (verification, welcome, etc.)
            max_retries: Maximum number of retry attempts

        Returns:
            Tuple of (success: bool, message: str)
        """
        logger.info(
            f"[Brevo] 📧 Sending {email_type} email to {to_email} "
            f"using template {template_id} (language: {language})"
        )

        for attempt in range(max_retries + 1):
            try:
                if BREVO_SDK_AVAILABLE and self.api_instance:
                    # Use official SDK
                    success, message = self._send_via_sdk(
                        to_email, template_id, template_params
                    )
                else:
                    # Use REST API directly
                    success, message = self._send_via_rest(
                        to_email, template_id, template_params
                    )

                if success:
                    logger.info(
                        f"[Brevo] ✅ Successfully sent email to {to_email}"
                    )
                    return True, message

                # If not successful and not last attempt, continue to retry
                if attempt < max_retries:
                    logger.warning(
                        f"[Brevo] ⚠️ Attempt {attempt + 1} failed: {message}. "
                        f"Retrying..."
                    )
                    time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                else:
                    logger.error(
                        f"[Brevo] ❌ Failed to send email after {max_retries + 1} "
                        f"attempts: {message}"
                    )
                    return False, message

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(
                    f"[Brevo] ❌ Exception on attempt {attempt + 1}: {error_msg}",
                    exc_info=True
                )

                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                else:
                    return False, error_msg

        return False, "Maximum retries exceeded"

    def _send_via_sdk(
        self,
        to_email: str,
        template_id: int,
        template_params: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Send email using official Brevo SDK.

        Args:
            to_email: Recipient email address
            template_id: Brevo template ID
            template_params: Template parameters

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Prepare email object
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": to_email}],
                template_id=template_id,
                params=template_params,
                sender={
                    "name": self.sender_name,
                    "email": self.sender_email
                }
            )

            # Send email
            api_response = self.api_instance.send_transac_email(
                send_smtp_email)

            logger.info(
                f"[Brevo] SDK Response: {api_response}"
            )

            return True, f"Email sent successfully. Message ID: {api_response.message_id}"

        except ApiException as e:
            error_msg = f"Brevo API error: {e.status} - {e.reason}"
            logger.error(
                f"[Brevo] ❌ API Exception: {error_msg}\n"
                f"Body: {e.body}"
            )

            # Parse specific error cases
            if e.status == 401:
                return False, "Invalid API key"
            elif e.status == 400:
                return False, "Invalid request parameters"
            elif e.status == 429:
                return False, "Rate limit exceeded"
            else:
                return False, error_msg

    def _send_via_rest(
        self,
        to_email: str,
        template_id: int,
        template_params: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Send email using REST API directly (fallback when SDK not available).

        Args:
            to_email: Recipient email address
            template_id: Brevo template ID
            template_params: Template parameters

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Prepare request payload
            payload = {
                "to": [{"email": to_email}],
                "templateId": template_id,
                "params": template_params,
                "sender": {
                    "name": self.sender_name,
                    "email": self.sender_email
                }
            }

            # Prepare headers
            headers = {
                "accept": "application/json",
                "api-key": self.api_key,
                "content-type": "application/json"
            }

            # Send request
            response = requests.post(
                self.API_URL,
                json=payload,
                headers=headers,
                timeout=10
            )

            # Check response
            if response.status_code == 201:
                response_data = response.json()
                message_id = response_data.get('messageId', 'unknown')
                logger.info(
                    f"[Brevo] REST API success. Message ID: {message_id}"
                )
                return True, f"Email sent successfully. Message ID: {message_id}"
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(
                    f"[Brevo] ❌ REST API error: {error_msg}"
                )

                # Parse specific error cases
                if response.status_code == 401:
                    return False, "Invalid API key"
                elif response.status_code == 400:
                    return False, f"Invalid request: {response.text}"
                elif response.status_code == 429:
                    return False, "Rate limit exceeded"
                else:
                    return False, error_msg

        except requests.exceptions.Timeout:
            error_msg = "Request timeout"
            logger.error(f"[Brevo] ❌ {error_msg}")
            return False, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(f"[Brevo] ❌ {error_msg}")
            return False, error_msg


# Global service instance
_brevo_service = None


def get_brevo_service() -> BrevoEmailService:
    """Get or create Brevo email service singleton."""
    global _brevo_service
    if _brevo_service is None:
        _brevo_service = BrevoEmailService()
    return _brevo_service
