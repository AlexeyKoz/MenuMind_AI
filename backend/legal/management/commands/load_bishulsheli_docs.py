"""
Django management command to load BishulSheli legal documents from new folder structure.

This command loads the following documents:
- EN folder: Terms of Service, Privacy Policy, Cookie Policy, Copyright, RCIP License
- RU folder: Terms of Service, Privacy Policy, Cookie Policy, Copyright, RCIP License
- HE folder: Terms of Service, Privacy Policy, Cookie Policy, Copyright, RCIP License

Usage:
    python manage.py load_bishulsheli_docs --force
"""
from django.core.management.base import BaseCommand
from legal.models import LegalDocument
from datetime import date
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Load BishulSheli legal documents from EN/RU/HE folder structure'

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
        self.stdout.write('Loading BishulSheli Legal Documents (EN, RU, HE)')
        self.stdout.write('=' * 70)

        # Define document mappings for new folder structure
        documents = [
            # English documents
            {
                'folder': 'EN',
                'file': 'Terms-of-service-v2_en.md',
                'document_type': 'terms',
                'language_code': 'en',
                'version': '2.0',
                'title': 'Terms of Service'
            },
            {
                'folder': 'EN',
                'file': 'Privacy-policy_v2_en.md',
                'document_type': 'privacy',
                'language_code': 'en',
                'version': '2.0',
                'title': 'Privacy Policy'
            },
            {
                'folder': 'EN',
                'file': 'Cookie-policy_v2_en.md',
                'document_type': 'cookies',
                'language_code': 'en',
                'version': '2.0',
                'title': 'Cookie Policy'
            },
            {
                'folder': 'EN',
                'file': 'Copyright_en.md',
                'document_type': 'copyright',
                'language_code': 'en',
                'version': '2.0',
                'title': 'Copyright Notice'
            },
            {
                'folder': 'EN',
                'file': 'rcip-license_en.md',
                'document_type': 'rcip',
                'language_code': 'en',
                'version': '2.0',
                'title': 'RCIP License'
            },
            # Russian documents
            {
                'folder': 'RU',
                'file': 'Terms-of-service-v2_ru.md',
                'document_type': 'terms',
                'language_code': 'ru',
                'version': '2.0',
                'title': 'Условия использования'
            },
            {
                'folder': 'RU',
                'file': 'Privacy-policy_v2_ru.md',
                'document_type': 'privacy',
                'language_code': 'ru',
                'version': '2.0',
                'title': 'Политика конфиденциальности'
            },
            {
                'folder': 'RU',
                'file': 'Cookie-policy_v2_ru.md',
                'document_type': 'cookies',
                'language_code': 'ru',
                'version': '2.0',
                'title': 'Политика cookies'
            },
            {
                'folder': 'RU',
                'file': 'Copyright_ru.md',
                'document_type': 'copyright',
                'language_code': 'ru',
                'version': '2.0',
                'title': 'Авторские права'
            },
            {
                'folder': 'RU',
                'file': 'rcip-license-ru.md',
                'document_type': 'rcip',
                'language_code': 'ru',
                'version': '2.0',
                'title': 'Лицензия RCIP'
            },
            # Hebrew documents
            {
                'folder': 'HE',
                'file': 'Terms-of-service-v2_he.md',
                'document_type': 'terms',
                'language_code': 'he',
                'version': '2.0',
                'title': 'תנאי שימוש'
            },
            {
                'folder': 'HE',
                'file': 'Privacy-policy_v2_he.md',
                'document_type': 'privacy',
                'language_code': 'he',
                'version': '2.0',
                'title': 'מדיניות פרטיות'
            },
            {
                'folder': 'HE',
                'file': 'Cookie-policy_v2_he.md',
                'document_type': 'cookies',
                'language_code': 'he',
                'version': '2.0',
                'title': 'מדיניות עוגיות'
            },
            {
                'folder': 'HE',
                'file': 'Copyright_he.md',
                'document_type': 'copyright',
                'language_code': 'he',
                'version': '2.0',
                'title': 'זכויות יוצרים'
            },
            {
                'folder': 'HE',
                'file': 'rcip-license-he.md',
                'document_type': 'rcip',
                'language_code': 'he',
                'version': '2.0',
                'title': 'רישיון RCIP'
            },
        ]

        loaded_count = 0
        skipped_count = 0
        error_count = 0

        for doc_info in documents:
            filepath = os.path.join(docs_path, doc_info['folder'], doc_info['file'])

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
                        'effective_date': date(2025, 11, 3),  # Today's date
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
                import traceback
                traceback.print_exc()
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
            f'\nTotal legal documents in database: {total_docs}\n'
            f'  - English: {en_docs}\n'
            f'  - Russian: {ru_docs}\n'
            f'  - Hebrew: {he_docs}'
        )

        if error_count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    '\n✅ All BishulSheli documents loaded successfully!'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'\n❌ Completed with {error_count} error(s). Check file paths and try again.'
                )
            )


