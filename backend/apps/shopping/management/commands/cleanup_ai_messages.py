"""
Management command to clean up AI messages that were incorrectly added as shopping items
"""
from django.core.management.base import BaseCommand
from apps.shopping.models import ShoppingItem


class Command(BaseCommand):
    help = 'Remove AI message items from shopping lists'

    def handle(self, *args, **options):
        self.stdout.write(
            '[CLEANUP] Cleaning up AI messages from shopping lists...')

        # Detection patterns for AI messages
        message_patterns = [
            'there are no', 'however,', 'i can provide', 'the text appears',
            'wikipedia', 'article about', 'i cannot', 'unfortunately',
            'please note', 'here are the', 'standard recipe'
        ]

        # Find all items that match AI message patterns
        items_to_delete = []

        for item in ShoppingItem.objects.all():
            item_name_lower = item.name.lower()

            # Check if this is a message (long text or contains message phrases)
            if len(item.name) > 100 or any(phrase in item_name_lower for phrase in message_patterns):
                items_to_delete.append(item)
                self.stdout.write(
                    f'  [FOUND] Message item: "{item.name[:80]}..."')

        # Delete the message items
        if items_to_delete:
            count = len(items_to_delete)
            for item in items_to_delete:
                item.delete()

            self.stdout.write(self.style.SUCCESS(
                f'[SUCCESS] Cleaned up {count} AI message items'))
        else:
            self.stdout.write(self.style.SUCCESS(
                '[SUCCESS] No AI message items found - all clean!'))
