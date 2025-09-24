from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.shopping.models import ShoppingList
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class Command(BaseCommand):
    help = 'Clean up archived lists older than 60 days with automatic ownership transfer'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=60,
            help='Number of days after which archived lists are cleaned up (default: 60)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        cleanup_days = options['days']

        self.stdout.write(
            self.style.SUCCESS(
                f'Starting archived lists cleanup (older than {cleanup_days} days)')
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    'DRY RUN MODE - No actual changes will be made')
            )

        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=cleanup_days)
        warning_cutoff_date = timezone.now() - timedelta(days=cleanup_days - 3)

        # Find archived lists older than the cutoff that haven't been processed
        try:
            archived_lists = ShoppingList.objects.filter(
                deleted_at__lt=cutoff_date,
                deleted_at__isnull=False,
                permanently_deleted_at__isnull=True  # Not already permanently deleted
            )
        except Exception as e:
            # Fallback for when new fields don't exist yet
            archived_lists = ShoppingList.objects.filter(
                deleted_at__lt=cutoff_date,
                deleted_at__isnull=False
            )

        # Find lists that need warnings (57+ days old)
        # Note: For now, skip warning system until migration is properly applied
        warning_lists = ShoppingList.objects.none()

        self.stdout.write(f'Found {archived_lists.count()} lists for cleanup')
        self.stdout.write(
            f'Found {warning_lists.count()} lists for warning notifications')

        # Process warning notifications first
        for shopping_list in warning_lists:
            if dry_run:
                self.stdout.write(
                    f'[DRY RUN] Would send warning for: {shopping_list.name}')
            else:
                self._send_deletion_warning(shopping_list)
                # TODO: Enable after migration is properly applied
                # shopping_list.deletion_warning_sent = True
                # shopping_list.deletion_warning_sent_at = timezone.now()
                # shopping_list.save()
                self.stdout.write(f'Warning sent for: {shopping_list.name}')

        # Process cleanup
        total_processed = 0
        transferred = 0
        deleted = 0

        for shopping_list in archived_lists:
            if dry_run:
                participants_count = shopping_list.participants.exclude(
                    user=shopping_list.creator).count()
                if participants_count > 0:
                    next_owner = shopping_list.get_next_owner()
                    self.stdout.write(
                        f'[DRY RUN] Would transfer "{shopping_list.name}" to {next_owner.user.username if next_owner else "NO_OWNER"}'
                    )
                else:
                    self.stdout.write(
                        f'[DRY RUN] Would permanently delete: {shopping_list.name}')
            else:
                result = self._process_old_archived_list(shopping_list)
                if result == 'transferred':
                    transferred += 1
                elif result == 'deleted':
                    deleted += 1
                total_processed += 1

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Cleanup completed: {total_processed} lists processed, '
                    f'{transferred} transferred, {deleted} deleted'
                )
            )

    def _send_deletion_warning(self, shopping_list):
        """Send warning notification to all participants about upcoming deletion"""
        try:
            channel_layer = get_channel_layer()
            if not channel_layer:
                return

            message = f'List "{shopping_list.name}" will be automatically deleted in 3 days due to inactivity. Transfer ownership or restore it to keep it.'

            # Send to all participants
            for participant in shopping_list.participants.all():
                async_to_sync(channel_layer.group_send)(
                    f'user_{participant.user.id}',
                    {
                        'type': 'deletion_warning',
                        'list': {
                            'id': str(shopping_list.id),
                            'name': shopping_list.name,
                        },
                        'message': message,
                        'days_remaining': 3
                    }
                )

            self.stdout.write(
                f'Deletion warning sent for: {shopping_list.name}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Failed to send warning for {shopping_list.name}: {e}')
            )

    def _process_old_archived_list(self, shopping_list):
        """Process an old archived list - transfer ownership or delete"""
        try:
            participants_count = shopping_list.participants.exclude(
                user=shopping_list.creator).count()

            if participants_count > 0:
                # Try to transfer ownership
                success, new_owner, message = shopping_list.transfer_ownership_to_next_participant(
                    'auto_cleanup')

                if success:
                    self.stdout.write(
                        f'Transferred "{shopping_list.name}" to {new_owner.username}')

                    # Send notification to new owner
                    try:
                        channel_layer = get_channel_layer()
                        if channel_layer:
                            async_to_sync(channel_layer.group_send)(
                                f'user_{new_owner.id}',
                                {
                                    'type': 'ownership_transferred',
                                    'list': {
                                        'id': str(shopping_list.id),
                                        'name': shopping_list.name,
                                    },
                                    'new_owner': {
                                        'username': new_owner.username,
                                        'first_name': new_owner.first_name,
                                    },
                                    'previous_owner': {
                                        'username': 'System (Auto-cleanup)',
                                        'first_name': 'System',
                                    },
                                    'message': f'You became owner of list "{shopping_list.name}" due to auto-cleanup after 60 days of inactivity'
                                }
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Failed to send notification: {e}')
                        )

                    return 'transferred'
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Failed to transfer "{shopping_list.name}": {message}')
                    )

            # No participants or transfer failed - delete permanently
            shopping_list.delete()
            self.stdout.write(f'Permanently deleted: {shopping_list.name}')
            return 'deleted'

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing {shopping_list.name}: {e}')
            )
            return 'error'
