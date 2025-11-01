#!/usr/bin/env python
"""
Export SQLite data for PostgreSQL migration
Handles Unicode characters properly
"""
import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
django.setup()

from django.core.management import call_command

def export_data():
    """Export all data from SQLite"""
    print("\n" + "="*80)
    print("[EXPORT] Exporting data from SQLite database")
    print("="*80 + "\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data_export_{timestamp}.json"
    
    try:
        print(f"[INFO] Exporting to: {output_file}")
        print("[INFO] This may take a few minutes...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            call_command(
                'dumpdata',
                '--natural-foreign',
                '--natural-primary',
                '--exclude', 'contenttypes',
                '--exclude', 'auth.permission',
                '--exclude', 'sessions.session',
                '--format', 'json',
                stdout=f
            )
        
        # Get file size
        file_size = os.path.getsize(output_file)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\n[SUCCESS] Data exported successfully!")
        print(f"[INFO] File: {output_file}")
        print(f"[INFO] Size: {file_size_mb:.2f} MB")
        
        # Count records by app
        import json
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"[INFO] Total records: {len(data)}")
        
        # Count by model
        models = {}
        for record in data:
            model = record.get('model', 'unknown')
            models[model] = models.get(model, 0) + 1
        
        print("\n[INFO] Records by model:")
        for model, count in sorted(models.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {model}: {count}")
        
        print("\n" + "="*80)
        print("[SUCCESS] Export complete!")
        print("="*80 + "\n")
        
        return output_file
        
    except Exception as e:
        print(f"\n[ERROR] Export failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    result = export_data()
    if result:
        print(f"\nNext step: Start PostgreSQL with Docker")
        print(f"Command: docker-compose up -d db redis")
    else:
        sys.exit(1)

