from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

# Import email services
from .services.simple_mailjet_service import get_simple_mailjet_service
from .services.mailjet_email_service import get_mailjet_service
from .services.brevo_email_service import get_brevo_service
from .services.email_service import get_emailjs_service


class MultilingualAccountAdapter(DefaultAccountAdapter):
    """Send account emails using the user's preferred language when available."""

    fallback_language = 'en'

    def get_user_language(self, user):
        """Get user's preferred language from UserPreferences"""
        try:
            # Import here to avoid circular imports
            from .models import UserPreferences
            prefs = UserPreferences.objects.filter(user=user).first()
            if prefs and prefs.language:
                print(f"[ADAPTER] User {user.username} language from UserPreferences: {prefs.language}", flush=True)
                return prefs.language
        except Exception as e:
            print(f"[ADAPTER] Error getting language from UserPreferences: {e}", flush=True)
        
        # Fallback: check if user model has preferred_language attribute
        if hasattr(user, 'preferred_language') and user.preferred_language:
            print(f"[ADAPTER] User {user.username} language from user attribute: {user.preferred_language}", flush=True)
            return user.preferred_language
        
        print(f"[ADAPTER] User {user.username} using fallback language: {self.fallback_language}", flush=True)
        return self.fallback_language

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        print(f"\n{'='*60}", flush=True)
        print(f"🔔 ADAPTER CALLED: send_confirmation_mail", flush=True)
        print(f"{'='*60}", flush=True)
        
        user = emailconfirmation.email_address.user
        language = self.get_user_language(user)

        # Get the confirmation key
        key = emailconfirmation.key

        # Build frontend URL for email verification
        frontend_url = getattr(settings, 'FRONTEND_URL',
                               'http://localhost:3000')
        activate_url = f"{frontend_url}/verify-email/{key}"

        current_site = get_current_site(request)
        to_email = emailconfirmation.email_address.email
        user_name = user.get_full_name() or user.username

        print(f"\n{'='*60}")
        print(f"📧 VERIFICATION EMAIL")
        print(f"{'='*60}")
        print(f"To: {to_email}")
        print(f"Language: {language}")
        print(f"Verification URL: {activate_url}")
        print(f"{'='*60}\n", flush=True)

        # Try Simple Mailjet first (plain HTML, no templates) - PRIMARY
        simple_mailjet = get_simple_mailjet_service()
        
        if simple_mailjet.enabled:
            success, message = simple_mailjet.send_verification_email(
                to_email=to_email,
                user_name=user_name,
                activate_url=activate_url,
                language=language
            )
            
            if success:
                print(f"[Simple Mailjet] ✅ Successfully sent verification email to {to_email}")
                print(f"[Simple Mailjet] Message: {message}")
                return
            else:
                print(f"[Simple Mailjet] ⚠️ Failed to send: {message}")
                print(f"[Simple Mailjet] ⚠️ Trying alternative services...")
        else:
            print(f"[Simple Mailjet] ⚠️ Not configured, trying alternatives")

        # Try Mailjet with templates (if configured) - SECONDARY
        mailjet_service = get_mailjet_service()

        if mailjet_service.enabled:
            success, message = mailjet_service.send_verification_email(
                to_email=to_email,
                user_name=user_name,
                activate_url=activate_url,
                language=language
            )

            if success:
                print(
                    f"[Mailjet] ✅ Successfully sent verification email to {to_email}")
                print(f"[Mailjet] Message: {message}")
                return
            else:
                print(f"[Mailjet] ⚠️ Failed to send via Mailjet: {message}")
                print(f"[Mailjet] ⚠️ Falling back to alternative email service")
        else:
            print(f"[Mailjet] ⚠️ Mailjet not configured, trying alternative services")

        # Try Brevo as secondary option (if configured)
        brevo_service = get_brevo_service()

        if brevo_service.enabled:
            success, message = brevo_service.send_verification_email(
                to_email=to_email,
                user_name=user_name,
                activate_url=activate_url,
                language=language
            )

            if success:
                print(
                    f"[Brevo] ✅ Successfully sent verification email to {to_email}")
                print(f"[Brevo] Message: {message}")
                return
            else:
                print(f"[Brevo] ⚠️ Failed to send via Brevo: {message}")
                print(f"[Brevo] ⚠️ Falling back to alternative email service")
        else:
            print(f"[Brevo] ⚠️ Brevo not configured, trying alternative services")

        # Try EmailJS as secondary option (if configured)
        emailjs_service = get_emailjs_service()

        if emailjs_service.enabled:
            success = emailjs_service.send_verification_email(
                to_email=to_email,
                user_name=user_name,
                activate_url=activate_url,
                language=language
            )

            if success:
                print(
                    f"[EmailJS] ✅ Successfully sent verification email to {to_email}")
                return
            else:
                print(
                    f"[EmailJS] ⚠️ Failed to send via EmailJS, falling back to Django SMTP")
        else:
            print(f"[EmailJS] ⚠️ EmailJS not configured, using Django SMTP fallback")

        # Final fallback to Django's SMTP (existing implementation)
        context = {
            'user': user,
            'activate_url': activate_url,
            'current_site': current_site,
            'key': key,
        }

        template_prefix = f'account/email/email_confirmation_{language}'
        message_template = f'{template_prefix}_message.html'
        subject_template = f'{template_prefix}_subject.txt'

        if not self.template_exists(message_template) or not self.template_exists(subject_template):
            message_template = 'account/email/email_confirmation_en_message.html'
            subject_template = 'account/email/email_confirmation_en_subject.txt'

        subject = render_to_string(subject_template, context)
        subject = ' '.join(subject.splitlines()).strip()

        html_message = render_to_string(message_template, context)
        text_message = strip_tags(html_message)

        from django.core.mail import send_mail
        send_mail(
            subject=subject,
            message=text_message,
            from_email=None,  # Will use DEFAULT_FROM_EMAIL
            recipient_list=[to_email],
            html_message=html_message,
        )

        print(f"[Django SMTP] ✅ Sent verification email to {to_email}")

    @staticmethod
    def template_exists(path: str) -> bool:
        try:
            render_to_string(path, {})
            return True
        except Exception:  # pragma: no cover - render failure indicates missing template
            return False
