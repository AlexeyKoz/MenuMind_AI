#!/usr/bin/env python
"""
Create a clean .env file for PostgreSQL
"""
import os

def create_env_for_postgres():
    """Create a clean .env file"""
    print("\n" + "="*80)
    print("[ENV] Creating clean .env for PostgreSQL")
    print("="*80 + "\n")
    
    # Read API keys from existing .env.backup if it exists
    groq_key = "your-groq-api-key"
    gemini_key = "your-gemini-api-key"
    google_client_id = "your-google-client-id"
    google_secret = "your-google-secret"
    
    if os.path.exists('.env.backup'):
        print("[INFO] Found .env.backup, extracting API keys...")
        try:
            with open('.env.backup', 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line.startswith('GROQ_API_KEY='):
                        groq_key = line.split('=', 1)[1].strip()
                    elif line.startswith('GEMINI_API_KEY='):
                        gemini_key = line.split('=', 1)[1].strip()
                    elif line.startswith('GOOGLE_CLIENT_ID='):
                        google_client_id = line.split('=', 1)[1].strip()
                    elif line.startswith('GOOGLE_CLIENT_SECRET='):
                        google_secret = line.split('=', 1)[1].strip()
            print("[OK] API keys extracted")
        except Exception as e:
            print(f"[WARN] Could not read .env.backup: {e}")
    
    env_content = f"""# MenuMind AI - PostgreSQL Configuration
SECRET_KEY=8e-33bn)r_2=nsu%mhr7-*x$6jm#svuc#cwog2@5c@398on$bq
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

USE_POSTGRES=True
DB_NAME=menumine_ai
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0

GROQ_API_KEY={groq_key}
GEMINI_API_KEY={gemini_key}
GOOGLE_CLIENT_ID={google_client_id}
GOOGLE_CLIENT_SECRET={google_secret}

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

SENTRY_DSN=https://a286cf89396658abbc772704749dded4@o4510275117383680.ingest.de.sentry.io/4510275122823248
SENTRY_ENVIRONMENT=development

IML_DB_PATH=data/iml.db
COOKLINGO_DB_PATH=data/cooklingo.db

FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8001
"""
    
    with open('.env', 'w', encoding='utf-8', newline='\n') as f:
        f.write(env_content)
    
    print("[SUCCESS] Created clean .env file")
    print("[INFO] PostgreSQL configuration:")
    print("  DB_NAME: menumine_ai")
    print("  DB_USER: postgres")
    print("  DB_HOST: localhost")
    print("  DB_PORT: 5432")
    
    print("\n" + "="*80)
    print("[SUCCESS] .env file ready!")
    print("="*80 + "\n")
    
    return True

if __name__ == '__main__':
    import sys
    
    # Backup existing .env if it exists
    if os.path.exists('.env'):
        try:
            with open('.env', 'rb') as f:
                content = f.read()
            with open('.env.backup', 'wb') as f:
                f.write(content)
            print("[INFO] Backed up existing .env to .env.backup")
        except Exception as e:
            print(f"[WARN] Could not backup .env: {e}")
    
    success = create_env_for_postgres()
    sys.exit(0 if success else 1)

