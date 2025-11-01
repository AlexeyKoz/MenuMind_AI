#!/usr/bin/env python
"""
Clean and fix encoding issues in the exported JSON data
"""
import json
import sys

def clean_export_file():
    """Clean the data export file"""
    print("\n" + "="*80)
    print("[CLEAN] Cleaning data export file")
    print("="*80 + "\n")
    
    input_file = 'data_export_20251101_040317.json'
    output_file = 'data/data_export_clean.json'
    
    print(f"[INFO] Reading: {input_file}")
    
    try:
        # Try reading with different encodings
        data = None
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
            try:
                with open(input_file, 'r', encoding=encoding, errors='ignore') as f:
                    data = json.load(f)
                print(f"[OK] Successfully read with encoding: {encoding}")
                break
            except Exception as e:
                print(f"[WARN] Failed with {encoding}: {e}")
                continue
        
        if not data:
            print("[ERROR] Could not read file with any encoding")
            return False
        
        print(f"[INFO] Loaded {len(data)} objects")
        
        # Write with clean UTF-8
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[SUCCESS] Cleaned data written to: {output_file}")
        print(f"[INFO] File size: {len(json.dumps(data)) / (1024*1024):.2f} MB")
        
        print("\n" + "="*80)
        print("[SUCCESS] Data cleaned!")
        print("="*80 + "\n")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Cleaning failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = clean_export_file()
    sys.exit(0 if success else 1)

