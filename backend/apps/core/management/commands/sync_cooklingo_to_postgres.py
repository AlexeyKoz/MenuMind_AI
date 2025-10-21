"""
Django management command to sync CookLingo cooking terms to PostgreSQL
"""
from django.core.management.base import BaseCommand
from apps.core.services import CookLingoSyncService


class Command(BaseCommand):
    help = 'Sync cooking terms from CookLingo SQLite database to PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sync all terms (ignore timestamps)',
        )

    def handle(self, *args, **options):
        force = options['force']

        self.stdout.write(self.style.SUCCESS(
            '\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('COOKLINGO SYNC'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

        if force:
            self.stdout.write(
                '[FORCE] Force sync enabled - will sync all terms\n')

        # Create sync service
        sync_service = CookLingoSyncService()

        # Get current stats
        current_stats = sync_service.get_sync_stats()
        self.stdout.write('\n[BEFORE] Current database state:')
        self.stdout.write(f'   Total terms: {current_stats["total_terms"]}')
        self.stdout.write(
            f'   Total translations: {current_stats["total_translations"]}')

        # Run sync
        self.stdout.write('\n[START] Starting sync...\n')
        result = sync_service.sync_all(force=force)

        # Show results
        self.stdout.write('\n[OK] Sync successful!')
        self.stdout.write(f'   Created: {result["created"]}')
        self.stdout.write(f'   Updated: {result["updated"]}')
        self.stdout.write(f'   Errors: {result["errors"]}\n')

        # Get updated stats
        updated_stats = sync_service.get_sync_stats()
        self.stdout.write('[STATS] Current database state:')
        self.stdout.write(f'   Total terms: {updated_stats["total_terms"]}')
        self.stdout.write(
            f'   Total translations: {updated_stats["total_translations"]}')
        for lang, count in updated_stats['languages'].items():
            self.stdout.write(f'     - {lang.upper()}: {count}')
        self.stdout.write(f'   Categories: {len(updated_stats["categories"])}')
        self.stdout.write(
            f'   Term types: {len(updated_stats["term_types"])}\n')

        self.stdout.write(self.style.SUCCESS('[OK] CookLingo sync complete!'))
