"""
Management command to load legal documents from markdown files into database.

Usage:
    python manage.py load_legal_docs
"""
from django.core.management.base import BaseCommand, CommandError
from legal.models import LegalDocument
from datetime import date
import os


class Command(BaseCommand):
    help = 'Load legal documents from markdown files into database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default='legal_documents/',
            help='Path to legal documents directory'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if document exists'
        )

    def handle(self, *args, **options):
        docs_path = options['path']
        force = options['force']

        # Document mapping: (type, filename, version)
        documents = [
            ('terms', 'Terms-of-service-v2.md', '2.0'),
            ('privacy', 'Privacy-policy-v2.md', '2.0'),
            ('cookies', 'Cookie-policy-v2.md', '2.0'),
            ('copyright', 'COPYRIGHT.md', '1.0'),
            ('rcip', 'rcip-license.md', '1.0'),
        ]

        self.stdout.write('=' * 70)
        self.stdout.write('Loading Legal Documents')
        self.stdout.write('=' * 70)

        loaded_count = 0
        skipped_count = 0
        error_count = 0

        for doc_type, filename, version in documents:
            filepath = os.path.join(docs_path, filename)

            # Check if file exists
            if not os.path.exists(filepath):
                self.stdout.write(
                    self.style.WARNING(
                        f'File not found: {filepath}'
                    )
                )
                error_count += 1
                continue

            try:
                # Read file content
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check if document already exists
                # Copyright and RCIP don't have language codes, so use language_code='en' as default
                existing = LegalDocument.objects.filter(
                    document_type=doc_type,
                    language_code='en'
                ).first()

                if existing and not force:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipped: {doc_type} (already exists, use --force to update)'
                        )
                    )
                    skipped_count += 1
                    continue

                # Create or update document
                doc, created = LegalDocument.objects.update_or_create(
                    document_type=doc_type,
                    language_code='en',  # Use English as default language
                    defaults={
                        'content': content,
                        'version': version,
                        'effective_date': date(2025, 10, 28),
                        'is_active': True
                    }
                )

                action = 'Created' if created else 'Updated'
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{action}: {doc_type} v{version} '
                        f'({len(content)} chars, {len(content.split())} words)'
                    )
                )
                loaded_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error loading {doc_type}: {str(e)}'
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

        if error_count > 0:
            raise CommandError(
                f'Failed to load {error_count} document(s). '
                'Check file paths and try again.'
            )

        self.stdout.write(
            self.style.SUCCESS(
                'Legal documents loaded successfully!'
            )
        )
