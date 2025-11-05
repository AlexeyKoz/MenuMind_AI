"""
Management command to load existing logos from frontend/logo directory
into the branding system.
"""
from django.core.management.base import BaseCommand
from django.core.files import File
from branding.models import SiteLogo
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Load existing logos from frontend/logo directory into the branding system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--logo-dir',
            type=str,
            default='../../frontend/logo',
            help='Path to logo directory (relative to backend/)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing logos'
        )

    def handle(self, *args, **options):
        logo_dir = Path(__file__).resolve().parent.parent.parent.parent / options['logo_dir']
        force = options['force']

        self.stdout.write(f"Looking for logos in: {logo_dir}")

        if not logo_dir.exists():
            self.stdout.write(self.style.ERROR(f"Logo directory not found: {logo_dir}"))
            return

        # Logo mappings
        logo_mappings = [
            # Navbar Desktop
            {
                'file': 'bishulsheli-logo-horizontal-en.svg',
                'logo_type': 'navbar_desktop',
                'language_code': 'en',
                'alt_text': 'BishulSheli'
            },
            {
                'file': 'bishulsheli-logo-horizontal-he.svg',
                'logo_type': 'navbar_desktop',
                'language_code': 'he',
                'alt_text': 'בישול שלי'
            },
            {
                'file': 'bishulsheli-logo-horizontal-en.svg',  # Use EN for RU
                'logo_type': 'navbar_desktop',
                'language_code': 'ru',
                'alt_text': 'BishulSheli'
            },
            # Navbar Mobile
            {
                'file': 'bishulsheli-logo-mobile-en.svg',
                'logo_type': 'navbar_mobile',
                'language_code': 'en',
                'alt_text': 'BishulSheli'
            },
            {
                'file': 'bishulsheli-logo-mobile-he.svg',
                'logo_type': 'navbar_mobile',
                'language_code': 'he',
                'alt_text': 'בישול שלי'
            },
            {
                'file': 'bishulsheli-logo-mobile-en.svg',
                'logo_type': 'navbar_mobile',
                'language_code': 'ru',
                'alt_text': 'BishulSheli'
            },
            # Login Page
            {
                'file': 'bishulsheli-logo-compact-en.svg',
                'logo_type': 'login_page',
                'language_code': 'en',
                'alt_text': 'BishulSheli - Sign In'
            },
            {
                'file': 'bishulsheli-logo-compact-he.svg',
                'logo_type': 'login_page',
                'language_code': 'he',
                'alt_text': 'בישול שלי - התחברות'
            },
            {
                'file': 'bishulsheli-logo-compact-en.svg',
                'logo_type': 'login_page',
                'language_code': 'ru',
                'alt_text': 'BishulSheli - Вход'
            },
            # Favicon
            {
                'file': 'bishulsheli-favicon.svg',
                'logo_type': 'favicon',
                'language_code': 'all',
                'alt_text': 'BishulSheli Icon'
            },
            # App Icon
            {
                'file': 'bishulsheli-icon.svg',
                'logo_type': 'app_icon',
                'language_code': 'all',
                'alt_text': 'BishulSheli App Icon'
            },
        ]

        uploaded_count = 0
        skipped_count = 0
        error_count = 0

        for mapping in logo_mappings:
            file_path = logo_dir / mapping['file']
            
            if not file_path.exists():
                self.stdout.write(
                    self.style.WARNING(f"File not found: {mapping['file']}")
                )
                error_count += 1
                continue

            # Check if logo already exists
            existing = SiteLogo.objects.filter(
                logo_type=mapping['logo_type'],
                language_code=mapping['language_code']
            ).first()

            if existing and not force:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping {mapping['logo_type']} ({mapping['language_code']}) - already exists"
                    )
                )
                skipped_count += 1
                continue

            try:
                # Create or update logo
                with open(file_path, 'rb') as f:
                    django_file = File(f)
                    
                    if existing:
                        # Update existing
                        existing.image_file = django_file
                        existing.alt_text = mapping['alt_text']
                        existing.is_active = True
                        existing.uploaded_by = 'system'
                        existing.save()
                        action = 'Updated'
                    else:
                        # Create new
                        logo = SiteLogo.objects.create(
                            logo_type=mapping['logo_type'],
                            language_code=mapping['language_code'],
                            image_file=django_file,
                            alt_text=mapping['alt_text'],
                            is_active=True,
                            uploaded_by='system'
                        )
                        action = 'Created'
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{action} {mapping['logo_type']} ({mapping['language_code']}) "
                            f"from {mapping['file']}"
                        )
                    )
                    uploaded_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error loading {mapping['file']}: {str(e)}"
                    )
                )
                error_count += 1

        # Summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"✓ Uploaded: {uploaded_count}"))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f"⊘ Skipped: {skipped_count}"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"✗ Errors: {error_count}"))
        self.stdout.write("="*60 + "\n")

        if uploaded_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nLogos loaded successfully! "
                    "Visit http://localhost:8000/admin/branding/sitelogo/ to manage them."
                )
            )

