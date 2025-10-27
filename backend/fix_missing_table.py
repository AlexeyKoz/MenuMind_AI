#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix missing shopping_list_ownership_transfers table
"""
from django.core.management import call_command
from django.db import connection
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
django.setup()


def check_and_fix_table():
    """Check if table exists and fix if needed"""

    table_name = 'shopping_list_ownership_transfers'

    with connection.cursor() as cursor:
        # Check if table exists (SQLite specific)
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=%s",
            [table_name]
        )
        result = cursor.fetchone()

        if result:
            print(f"[OK] Table '{table_name}' exists")
            return True
        else:
            print(f"[MISSING] Table '{table_name}' does NOT exist")
            print(f"[FIX] Creating table...")

            # Create the table manually
            cursor.execute("""
                CREATE TABLE shopping_list_ownership_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shopping_list_id CHAR(32) NOT NULL,
                    from_user_id CHAR(32),
                    to_user_id CHAR(32) NOT NULL,
                    reason VARCHAR(100) NOT NULL DEFAULT 'creator_deleted',
                    transferred_at DATETIME NOT NULL,
                    FOREIGN KEY (shopping_list_id) REFERENCES shopping_lists (id) ON DELETE CASCADE,
                    FOREIGN KEY (from_user_id) REFERENCES users (id) ON DELETE SET NULL,
                    FOREIGN KEY (to_user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)

            # Create index
            cursor.execute("""
                CREATE INDEX shopping_list_ownership_transfers_transferred_at 
                ON shopping_list_ownership_transfers (transferred_at DESC)
            """)

            print(f"[SUCCESS] Table '{table_name}' created successfully")
            return True


if __name__ == '__main__':
    try:
        check_and_fix_table()
        print("\n[COMPLETE] Database check complete!")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
