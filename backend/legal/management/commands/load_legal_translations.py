"""
Django management command to load Russian and Hebrew legal document translations.

This command loads the following documents:
- Terms of Service (RU, HE)
- Privacy Policy (RU, HE)
- Cookie Policy (RU, HE)

Usage:
    python manage.py load_legal_translations
"""
from django.core.management.base import BaseCommand
from legal.models import LegalDocument
from datetime import date
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Load Russian and Hebrew legal document translations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing documents (will replace content)',
        )
        parser.add_argument(
            '--path',
            type=str,
            default='legal_documents/',
            help='Path to legal documents directory (relative to project root)',
        )

    def handle(self, *args, **options):
        force = options['force']
        docs_path = options['path']

        # Ensure path exists
        if not os.path.exists(docs_path):
            self.stdout.write(
                self.style.ERROR(f'Path not found: {docs_path}')
            )
            return

        self.stdout.write('=' * 70)
        self.stdout.write('Loading Legal Document Translations (RU + HE)')
        self.stdout.write('=' * 70)

        # Define translation files to load
        translations = [
            # Russian translations
            {
                'file': 'FINAL-terms-of-service-v2-RU.md',
                'document_type': 'terms',
                'language_code': 'ru',
                'version': '2.0',
                'title': 'Условия использования'
            },
            {
                'file': 'FINAL-privacy-policy-v2-RU.md',
                'document_type': 'privacy',
                'language_code': 'ru',
                'version': '2.0',
                'title': 'Политика конфиденциальности'
            },
            {
                'file': 'FINAL-cookie-policy-v2-RU.md',
                'document_type': 'cookies',
                'language_code': 'ru',
                'version': '2.0',
                'title': 'Политика cookies'
            },
            # Hebrew translations
            {
                'file': 'FINAL-terms-of-service-v2-HE.md',
                'document_type': 'terms',
                'language_code': 'he',
                'version': '2.0',
                'title': 'תנאי שימוש'
            },
            {
                'file': 'FINAL-privacy-policy-v2-HE.md',
                'document_type': 'privacy',
                'language_code': 'he',
                'version': '2.0',
                'title': 'מדיניות פרטיות'
            },
            {
                'file': 'FINAL-cookie-policy-v2-HE.md',
                'document_type': 'cookies',
                'language_code': 'he',
                'version': '2.0',
                'title': 'מדיניות עוגיות'
            },
        ]

        loaded_count = 0
        skipped_count = 0
        error_count = 0

        for doc_info in translations:
            filepath = os.path.join(docs_path, doc_info['file'])

            # Check if file exists
            if not os.path.exists(filepath):
                self.stdout.write(
                    self.style.WARNING(f'File not found: {filepath}')
                )
                error_count += 1
                continue

            try:
                # Read file content with UTF-8 encoding
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check if document already exists
                existing = LegalDocument.objects.filter(
                    document_type=doc_info['document_type'],
                    language_code=doc_info['language_code']
                ).first()

                if existing and not force:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipped: {doc_info["title"]} ({doc_info["language_code"].upper()}) '
                            f'- already exists (use --force to update)'
                        )
                    )
                    skipped_count += 1
                    continue

                # Create or update document
                doc, created = LegalDocument.objects.update_or_create(
                    document_type=doc_info['document_type'],
                    language_code=doc_info['language_code'],
                    defaults={
                        'content': content,
                        'version': doc_info['version'],
                        'effective_date': date(2025, 10, 28),
                        'is_active': True
                    }
                )

                action = 'Created' if created else 'Updated'
                words = len(content.split())
                chars = len(content)

                self.stdout.write(
                    self.style.SUCCESS(
                        f'{action}: {doc_info["title"]} ({doc_info["language_code"].upper()}) '
                        f'v{doc_info["version"]} - {chars} chars, {words} words'
                    )
                )
                loaded_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error loading {doc_info["file"]}: {str(e)}'
                    )
                )
                error_count += 1

        # Summary
        self.stdout.write('=' * 70)
        self.stdout.write(
            f'Loaded: {loaded_count} | '
            f'Skipped: {skipped_count} | '
            f'Errors: {error_count}'
        )
        self.stdout.write('=' * 70)

        # Verify total documents
        total_docs = LegalDocument.objects.count()
        ru_docs = LegalDocument.objects.filter(language_code='ru').count()
        he_docs = LegalDocument.objects.filter(language_code='he').count()
        en_docs = LegalDocument.objects.filter(language_code='en').count()

        self.stdout.write(
            f'Total legal documents in database: {total_docs}\n'
            f'  - English: {en_docs}\n'
            f'  - Russian: {ru_docs}\n'
            f'  - Hebrew: {he_docs}'
        )

        if error_count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    '\nTranslations loaded successfully!'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'\nCompleted with {error_count} error(s). Check file paths and try again.'
                )
            )
