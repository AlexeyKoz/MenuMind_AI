from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import random
import string

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate collaboration keys for existing users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of keys for users who already have them',
        )

    def handle(self, *args, **options):
        self.stdout.write('🔑 Generating collaboration keys for users...')

        users = User.objects.all()
        if not options['force']:
            users = users.filter(collaboration_key__isnull=True)

        updated_count = 0
        colors = ['#4F46E5', '#7C3AED', '#DC2626',
                  '#059669', '#D97706', '#0284C7']

        for i, user in enumerate(users):
            # Generate collaboration key
            key = self.generate_unique_key()

            # Assign color if user doesn't have one
            if not user.personal_color or user.personal_color == '#4F46E5':
                user.personal_color = colors[i % len(colors)]

            user.collaboration_key = key
            user.save()

            updated_count += 1
            self.stdout.write(
                f'✅ Updated user {user.username}: key={key}, color={user.personal_color}'
            )

        self.stdout.write(
            self.style.SUCCESS(f'✨ Successfully updated {updated_count} users')
        )

    def generate_unique_key(self):
        """Generate unique 6-digit collaboration key"""
        while True:
            key = ''.join(random.choices(string.digits, k=6))
            if not User.objects.filter(collaboration_key=key).exists():
                return key



























