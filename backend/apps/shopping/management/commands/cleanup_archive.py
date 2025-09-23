from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.shopping.models import ShoppingList


class Command(BaseCommand):
    help = 'Cleanup archived shopping lists older than 60 days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=60,
            help='Number of days after which to delete archived items (default: 60)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']

        self.stdout.write(
            f"🗂️ Starting archive cleanup (older than {days} days)...")

        # Find lists eligible for auto-deletion
        eligible_lists = []
        archived_lists = ShoppingList.objects.filter(deleted_at__isnull=False)

        for shopping_list in archived_lists:
            if shopping_list.is_auto_delete_eligible():
                eligible_lists.append(shopping_list)

        if not eligible_lists:
            self.stdout.write(
                self.style.SUCCESS("✅ No archived lists found for cleanup")
            )
            return

        self.stdout.write(f"📋 Found {len(eligible_lists)} lists for cleanup:")

        for shopping_list in eligible_lists:
            days_since_deletion = (
                timezone.now() - shopping_list.deleted_at).days
            self.stdout.write(
                f"  • {shopping_list.name} (deleted {days_since_deletion} days ago by {shopping_list.deleted_by.username if shopping_list.deleted_by else 'unknown'})"
            )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN: No actual deletion performed")
            )
            return

        # Perform actual deletion
        deleted_count = 0
        for shopping_list in eligible_lists:
            try:
                list_name = shopping_list.name
                shopping_list.delete()  # Permanent deletion
                deleted_count += 1
                self.stdout.write(f"🗑️ Permanently deleted: {list_name}")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Failed to delete {shopping_list.name}: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Cleanup completed: {deleted_count} lists permanently deleted")
        )


