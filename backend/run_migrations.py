#!/usr/bin/env python
"""
Run Django migrations in PostgreSQL
Uses environment variables for database connection
"""
import os
import sys
import django

# Set environment for PostgreSQL
os.environ['USE_POSTGRES'] = 'True'
os.environ['DB_NAME'] = 'menumine_ai'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'password'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
django.setup()

from django.core.management import execute_from_command_line

def run_migrations():
    """Run Django migrations"""
    print("\n" + "="*80)
    print("[MIGRATE] Running PostgreSQL migrations")
    print("="*80 + "\n")
    
    print("[INFO] Database: menumine_ai@localhost:5432")
    print("[INFO] This will create all tables in PostgreSQL...")
    print()
    
    try:
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("\n" + "="*80)
        print("[SUCCESS] Migrations complete!")
        print("="*80 + "\n")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_migrations()
    sys.exit(0 if success else 1)

