"""
Management command to sync IML SQLite to PostgreSQL
Usage: python manage.py sync_iml_to_postgres [--force]
"""
from django.core.management.base import BaseCommand
from apps.core.services import IMLSyncService


class Command(BaseCommand):
    help = 'Sync ingredients from IML SQLite database to PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force full sync (ignore last sync timestamp)',
        )

        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show sync statistics only (no sync)',
        )

    def handle(self, *args, **options):
        service = IMLSyncService()

        if options['stats']:
            self.stdout.write(self.style.SUCCESS('\n📊 Sync Statistics:'))
            stats = service.get_sync_stats()

            self.stdout.write(
                f"\n📦 Total ingredients: {stats['total_ingredients']}")
            self.stdout.write(
                f"🌍 Total translations: {stats['total_translations']}")
            self.stdout.write(f"\n   EN: {stats['languages']['en']}")
            self.stdout.write(f"   RU: {stats['languages']['ru']}")
            self.stdout.write(f"   HE: {stats['languages']['he']}")
            self.stdout.write(f"\n📚 Sources: {', '.join(stats['sources'])}")
            self.stdout.write(
                f"📂 Categories: {', '.join(stats['categories'][:10])}...")
            if stats['last_sync']:
                self.stdout.write(f"\n⏰ Last sync: {stats['last_sync']}")

            return

        force = options['force']

        if force:
            self.stdout.write(self.style.WARNING(
                '\n⚠️  Force sync enabled - will sync all ingredients'))
        else:
            self.stdout.write(self.style.SUCCESS(
                '\n🔄 Incremental sync - only modified ingredients'))

        self.stdout.write('\n🚀 Starting sync...\n')

        created, updated, errors = service.sync_all(force=force)

        if errors > 0:
            self.stdout.write(self.style.ERROR(
                f'\n❌ Sync completed with errors!'))
            self.stdout.write(f'   Created: {created}')
            self.stdout.write(f'   Updated: {updated}')
            self.stdout.write(f'   Errors: {errors}')
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Sync successful!'))
            self.stdout.write(f'   Created: {created}')
            self.stdout.write(f'   Updated: {updated}')

        # Show stats
        self.stdout.write('\n📊 Current database state:')
        stats = service.get_sync_stats()
        self.stdout.write(
            f'   Total ingredients: {stats["total_ingredients"]}')
        self.stdout.write(
            f'   Total translations: {stats["total_translations"]}')
