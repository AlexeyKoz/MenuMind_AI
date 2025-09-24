#!/usr/bin/env python3
"""Debug script to check list status and which delete endpoint to use"""

from apps.shopping.models import ShoppingList
from apps.users.models import User
import os
import sys
import django

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')

django.setup()


def debug_delete_endpoints():
    print("🔍 Debugging delete endpoints...")

    # Find a test user
    user = User.objects.filter(username__in=['testuser1', 'testuser2']).first()
    if not user:
        print("❌ No test users found")
        return

    print(f"👤 Testing with user: {user.username}")

    # Get all lists for this user
    active_lists = ShoppingList.objects.filter(
        creator=user,
        is_active=True,
        deleted_at__isnull=True
    )

    archived_lists = ShoppingList.objects.filter(
        creator=user,
        deleted_at__isnull=False
    )

    print(f"\n📊 Lists Summary:")
    print(f"  ✅ Active lists: {active_lists.count()}")
    print(f"  🗄️ Archived lists: {archived_lists.count()}")

    print(f"\n📋 Active Lists (use DELETE /lists/{{id}}/):")
    for lst in active_lists[:5]:  # Show first 5
        print(f"  - {lst.name} (ID: {lst.id})")

    print(f"\n🗄️ Archived Lists (use DELETE /lists/{{id}}/permanent-delete/):")
    for lst in archived_lists[:5]:  # Show first 5
        status = "Permanently deleted" if lst.permanently_deleted_at else "Archived"
        print(f"  - {lst.name} (ID: {lst.id}) - {status}")

    print(f"\n💡 Usage:")
    print(f"  • To archive an active list: DELETE /api/shopping/lists/{{id}}/")
    print(
        f"  • To permanently delete archived list: DELETE /api/shopping/lists/{{id}}/permanent-delete/")


if __name__ == '__main__':
    debug_delete_endpoints()
