from allauth.account.adapter import DefaultAccountAdapter
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class MultilingualAccountAdapter(DefaultAccountAdapter):
    """Send account emails using the user's preferred language when available."""

    fallback_language = 'en'

    def get_user_language(self, user):
        if hasattr(user, 'preferred_language') and user.preferred_language:
            return user.preferred_language
        return self.fallback_language

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        user = emailconfirmation.email_address.user
        language = self.get_user_language(user)

        activate_url = self.get_email_confirmation_url(request, emailconfirmation)
        context = {
            'user': user,
            'activate_url': activate_url,
            'current_site': self.get_current_site(request),
            'key': emailconfirmation.key,
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

        emailconfirmation.send(
            request=request,
            signup=signup,
            subject=subject,
            message=text_message,
            html_message=html_message,
        )

    @staticmethod
    def template_exists(path: str) -> bool:
        try:
            render_to_string(path, {})
            return True
        except Exception:  # pragma: no cover - render failure indicates missing template
            return False
