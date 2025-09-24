#!/usr/bin/env python
"""
Test script to verify collaboration key regeneration
"""
from apps.shopping.models import ShoppingList
from apps.users.models import User
import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
django.setup()


def test_key_regeneration():
    print("🧪 Testing collaboration key regeneration...")

    # Get test users
    try:
        user1 = User.objects.get(username='testuser1')
        user2 = User.objects.get(username='testuser2')
        print(f"✅ Found users: {user1.username}, {user2.username}")
    except User.DoesNotExist:
        print("❌ Test users not found")
        return

    # Check current keys
    print(f"🔑 User1 current key: {user1.collaboration_key}")
    print(f"🔑 User2 current key: {user2.collaboration_key}")

    # Test key regeneration for user2
    old_key = user2.collaboration_key
    new_key = user2.generate_collaboration_key()

    print(f"🔄 Key regeneration test:")
    print(f"   Old key: {old_key}")
    print(f"   New key: {new_key}")
    print(f"   Changed: {old_key != new_key}")

    # Refresh from database
    user2.refresh_from_db()
    print(f"🔍 Key in database: {user2.collaboration_key}")
    print(f"✅ Saved correctly: {user2.collaboration_key == new_key}")


if __name__ == "__main__":
    test_key_regeneration()
