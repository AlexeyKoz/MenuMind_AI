"""
Management command to set user's preferred language
Usage: python manage.py set_user_language <username> <language>
Example: python manage.py set_user_language admin he
"""

from django.core.management.base import BaseCommand
from apps.users.models import User


class Command(BaseCommand):
    help = 'Set user preferred language'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username')
        parser.add_argument('language', type=str, choices=[
                            'en', 'ru', 'he'], help='Language code (en/ru/he)')

    def handle(self, *args, **options):
        username = options['username']
        language = options['language']

        try:
            user = User.objects.get(username=username)
            old_lang = user.preferred_language
            user.preferred_language = language
            user.save()

            self.stdout.write(self.style.SUCCESS(
                f'Successfully updated {username}: {old_lang} → {language}'
            ))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f'User "{username}" not found'
            ))
