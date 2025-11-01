#!/usr/bin/env python
"""
Update .env to use PostgreSQL
"""
import os

def update_env_for_postgres():
    """Update .env file to use PostgreSQL"""
    env_path = '.env'
    
    print("\n" + "="*80)
    print("[ENV] Updating .env for PostgreSQL")
    print("="*80 + "\n")
    
    if not os.path.exists(env_path):
        print(f"[ERROR] {env_path} not found!")
        print("[INFO] Please copy .env.example to .env first")
        return False
    
    # Read current .env
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update specific settings
    new_lines = []
    updated = []
    
    for line in lines:
        if line.startswith('USE_POSTGRES='):
            new_lines.append('USE_POSTGRES=True\n')
            updated.append('USE_POSTGRES=True')
        elif line.startswith('DB_NAME='):
            new_lines.append('DB_NAME=menumine_ai\n')
            updated.append('DB_NAME=menumine_ai')
        elif line.startswith('DB_USER='):
            new_lines.append('DB_USER=postgres\n')
            updated.append('DB_USER=postgres')
        elif line.startswith('DB_PASSWORD='):
            new_lines.append('DB_PASSWORD=password\n')
            updated.append('DB_PASSWORD=password')
        elif line.startswith('DB_HOST='):
            new_lines.append('DB_HOST=localhost\n')
            updated.append('DB_HOST=localhost')
        elif line.startswith('DB_PORT='):
            new_lines.append('DB_PORT=5432\n')
            updated.append('DB_PORT=5432')
        else:
            new_lines.append(line)
    
    # Write updated .env
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("[SUCCESS] .env updated with PostgreSQL settings:")
    for item in updated:
        print(f"  [OK] {item}")
    
    print("\n" + "="*80)
    print("[SUCCESS] .env configuration complete!")
    print("="*80 + "\n")
    
    return True

if __name__ == '__main__':
    import sys
    success = update_env_for_postgres()
    sys.exit(0 if success else 1)

