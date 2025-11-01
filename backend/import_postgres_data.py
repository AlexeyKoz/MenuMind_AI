#!/usr/bin/env python
"""
Import data into PostgreSQL from JSON export
"""
import os
import sys
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
os.environ['USE_POSTGRES'] = 'True'
os.environ['DB_NAME'] = 'menumine_ai'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'password'
os.environ['DB_HOST'] = 'db'
os.environ['DB_PORT'] = '5432'
os.environ['SECRET_KEY'] = 'temp'
os.environ['DEBUG'] = 'True'

import django
django.setup()

from django.core.management import call_command

def import_data():
    """Import data from JSON file"""
    print("\n" + "="*80)
    print("[IMPORT] Importing data into PostgreSQL")
    print("="*80 + "\n")
    
    data_file = 'data/data_export.json'
    
    if not os.path.exists(data_file):
        print(f"[ERROR] Data file not found: {data_file}")
        return False
    
    print(f"[INFO] Loading data from: {data_file}")
    print("[INFO] This may take several minutes...")
    print()
    
    try:
        # Use loaddata with UTF-8 encoding
        call_command('loaddata', data_file, verbosity=2)
        
        print("\n" + "="*80)
        print("[SUCCESS] Data import complete!")
        print("="*80 + "\n")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = import_data()
    sys.exit(0 if success else 1)

