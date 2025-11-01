# 🚀 Pre-Deployment Checklist & Migration Guide

**Project:** MenuMind AI
**Version:** 0.9.0
**Target:** Docker Containerization + PostgreSQL Migration
**Date:** November 1, 2025

---

## ✅ Current Status Analysis

### What We Have:
- ✅ Working SQLite database (`db.sqlite3`)
- ✅ Docker Compose files (dev + prod)
- ✅ Dockerfiles for backend and frontend
- ✅ PostgreSQL-ready settings (with `USE_POSTGRES` flag)
- ✅ Redis configuration with fallback
- ✅ Sentry monitoring configured
- ✅ All dependencies up to date

### Critical Issues Found:
1. ❌ **Hardcoded Windows path** in `settings.py` (line 131)
2. ❌ **Missing `.env.example`** template for deployment
3. ⚠️ **IML database** on external path (needs to be bundled)
4. ⚠️ **Celery not in docker-compose** (needs workers + beat)
5. ⚠️ **Missing health check endpoint** (referenced in Dockerfile)
6. ⚠️ **No database migration script** from SQLite to PostgreSQL

---

## 📋 Pre-Deployment Tasks

### Phase 1: Clean Up & Prepare Code (Estimated: 1-2 hours)

#### 1.1 Fix Hardcoded Paths ❌ **CRITICAL**

**File:** `backend/menumine_ai/settings.py` (line 131)

**Current (BAD):**
```python
IML_DB_PATH = os.getenv(
    'IML_DB_PATH', r'C:\Users\al7ko\Desktop\ingredients-master-list-new\ingredient-master-list\data\iml.db')
```

**Fixed (GOOD):**
```python
# IML Integration - Use relative path for Docker
IML_DB_PATH = env(
    'IML_DB_PATH', 
    default=os.path.join(BASE_DIR, 'data', 'iml.db')
)
```

**Action Items:**
- [ ] Move IML database to `backend/data/iml.db`
- [ ] Update settings.py with relative path
- [ ] Add `backend/data/` to git (with `.gitkeep` but exclude `*.db` if sensitive)

---

#### 1.2 Fix CookLingo Path

**File:** `backend/menumine_ai/settings.py` (line 134)

**Current (OK but can be improved):**
```python
COOKLINGO_DB_PATH = os.getenv(
    'COOKLINGO_DB_PATH', os.path.join(BASE_DIR, 'cooklingo.db'))
```

**Better:**
```python
# CookLingo Database Path - Move to data directory
COOKLINGO_DB_PATH = env(
    'COOKLINGO_DB_PATH',
    default=os.path.join(BASE_DIR, 'data', 'cooklingo.db')
)
```

**Action Items:**
- [ ] Move `backend/cooklingo.db` → `backend/data/cooklingo.db`
- [ ] Update settings.py

---

#### 1.3 Create `.env.example` Template ❌ **CRITICAL**

**File:** `backend/.env.example` (CREATE THIS)

```bash
# ============================================
# MENUMINE AI - Environment Configuration
# ============================================

# ============================================
# DJANGO SETTINGS
# ============================================
SECRET_KEY=your-secret-key-here-generate-new-one
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# ============================================
# DATABASE (PostgreSQL for Production)
# ============================================
USE_POSTGRES=True
DB_NAME=menumine_ai
DB_USER=postgres
DB_PASSWORD=your-secure-password-here
DB_HOST=db  # 'db' for Docker, 'localhost' for local
DB_PORT=5432

# ============================================
# REDIS
# ============================================
REDIS_URL=redis://redis:6379/0  # 'redis' for Docker, 'localhost' for local
REDIS_PASSWORD=your-redis-password  # Optional for production

# ============================================
# CELERY
# ============================================
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# ============================================
# AI SERVICES (REQUIRED)
# ============================================
GROQ_API_KEY=your-groq-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here  # Optional

# ============================================
# GOOGLE OAUTH
# ============================================
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# ============================================
# EMAIL SETTINGS (Production)
# ============================================
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@menumine.ai

# ============================================
# SENTRY ERROR TRACKING
# ============================================
SENTRY_DSN=https://a286cf89396658abbc772704749dded4@o4510275117383680.ingest.de.sentry.io/4510275122823248
SENTRY_ENVIRONMENT=production  # development, staging, production

# ============================================
# EXTERNAL DATABASES (IML, CookLingo)
# ============================================
IML_DB_PATH=/app/data/iml.db  # Path inside Docker container
COOKLINGO_DB_PATH=/app/data/cooklingo.db

# ============================================
# STATIC & MEDIA FILES
# ============================================
STATIC_URL=/static/
MEDIA_URL=/media/
STATIC_ROOT=/app/staticfiles
MEDIA_ROOT=/app/media

# ============================================
# CORS (Frontend URL)
# ============================================
FRONTEND_URL=https://yourdomain.com  # http://localhost:3000 for dev
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

**Action Items:**
- [ ] Create `backend/.env.example`
- [ ] Copy to `backend/.env` and fill in actual values
- [ ] Add `.env` to `.gitignore` (should already be there)

---

#### 1.4 Create Frontend `.env.example`

**File:** `frontend/.env.example` (CREATE THIS)

```bash
# ============================================
# MENUMINE AI FRONTEND - Environment Config
# ============================================

# Backend API URL
REACT_APP_API_URL=http://localhost:8000  # Change to your domain in production

# Google OAuth
REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id-here

# Sentry (Optional - auto-enabled in production)
REACT_APP_SENTRY_ENABLED=false  # Set to 'true' to enable in development

# WebSocket URL (optional if different from API)
REACT_APP_WS_URL=ws://localhost:8000  # Change to wss://yourdomain.com in production
```

**Action Items:**
- [ ] Create `frontend/.env.example`
- [ ] Copy to `frontend/.env` and fill in actual values

---

#### 1.5 Add Health Check Endpoint ❌ **CRITICAL**

**File:** `backend/menumine_ai/urls.py`

Add this endpoint (referenced in Dockerfile but missing):

```python
from django.http import JsonResponse

def health_check(request):
    """Health check endpoint for Docker"""
    return JsonResponse({
        'status': 'healthy',
        'version': '0.9.0',
        'database': 'ok',  # Could check actual DB connection
        'redis': 'ok'      # Could check actual Redis connection
    })

urlpatterns = [
    # ... existing patterns ...
    path('health/', health_check, name='health'),
]
```

**Action Items:**
- [ ] Add health check endpoint to `urls.py`
- [ ] Test endpoint: `curl http://localhost:8000/health/`

---

### Phase 2: Database Migration (Estimated: 2-3 hours)

#### 2.1 Create SQLite → PostgreSQL Migration Script ❌ **CRITICAL**

**File:** `backend/migrate_sqlite_to_postgres.py` (CREATE THIS)

```python
#!/usr/bin/env python
"""
Migrate data from SQLite to PostgreSQL
Usage: python migrate_sqlite_to_postgres.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
os.environ['USE_POSTGRES'] = 'False'  # Start with SQLite
django.setup()

from django.core.management import call_command
from django.db import connections
import subprocess

def main():
    print("\n" + "="*80)
    print("🔄 SQLite → PostgreSQL Migration Script")
    print("="*80 + "\n")

    # Step 1: Dump data from SQLite
    print("[1/5] 📦 Exporting data from SQLite...")
    try:
        call_command('dumpdata', 
                     '--natural-foreign', 
                     '--natural-primary',
                     '--exclude', 'contenttypes',
                     '--exclude', 'auth.permission',
                     '--exclude', 'sessions.session',
                     '--output', 'data_export.json',
                     '--indent', 2)
        print("✅ Data exported to data_export.json")
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return

    # Step 2: Switch to PostgreSQL
    print("\n[2/5] 🔄 Switching to PostgreSQL...")
    os.environ['USE_POSTGRES'] = 'True'
    
    # Reload Django settings
    from importlib import reload
    from django.conf import settings
    reload(sys.modules['menumine_ai.settings'])
    
    # Close old connections
    connections.close_all()
    
    print("✅ Switched to PostgreSQL")

    # Step 3: Create fresh PostgreSQL schema
    print("\n[3/5] 🏗️  Creating PostgreSQL schema...")
    try:
        call_command('migrate', '--run-syncdb')
        print("✅ PostgreSQL schema created")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return

    # Step 4: Import data into PostgreSQL
    print("\n[4/5] 📥 Importing data into PostgreSQL...")
    try:
        call_command('loaddata', 'data_export.json')
        print("✅ Data imported successfully")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        print("⚠️  You may need to manually fix data inconsistencies")
        return

    # Step 5: Verify migration
    print("\n[5/5] ✅ Verifying migration...")
    from django.contrib.auth import get_user_model
    from apps.recipes.models import Recipe, CanonicalRecipe
    from apps.shopping.models import ShoppingList
    
    User = get_user_model()
    
    users_count = User.objects.count()
    recipes_count = Recipe.objects.count()
    canonical_count = CanonicalRecipe.objects.count()
    lists_count = ShoppingList.objects.count()
    
    print(f"\n📊 Migration Summary:")
    print(f"   Users: {users_count}")
    print(f"   Recipes: {recipes_count}")
    print(f"   Canonical Recipes: {canonical_count}")
    print(f"   Shopping Lists: {lists_count}")
    
    print("\n" + "="*80)
    print("🎉 Migration Complete!")
    print("="*80)
    print("\n⚠️  Important:")
    print("1. Test the application thoroughly")
    print("2. Backup data_export.json (keep as backup)")
    print("3. Update .env to USE_POSTGRES=True")
    print("4. Restart all services\n")

if __name__ == '__main__':
    main()
```

**Action Items:**
- [ ] Create migration script
- [ ] Test on a copy of the database first
- [ ] Run migration: `python migrate_sqlite_to_postgres.py`

---

#### 2.2 Alternative: Use Django's Native Tools

**Simpler approach using Django management commands:**

```bash
# Step 1: Export from SQLite
cd backend
venv\Scripts\activate
python manage.py dumpdata --natural-foreign --natural-primary \
    --exclude contenttypes --exclude auth.permission \
    --output backup_$(date +%Y%m%d).json

# Step 2: Setup PostgreSQL
docker-compose up -d db redis

# Step 3: Update .env
# Set USE_POSTGRES=True
# Set DB credentials

# Step 4: Run migrations on PostgreSQL
python manage.py migrate

# Step 5: Import data
python manage.py loaddata backup_20251101.json
```

**Action Items:**
- [ ] Backup current SQLite: `cp db.sqlite3 db.sqlite3.backup`
- [ ] Export data with dumpdata
- [ ] Import into PostgreSQL
- [ ] Verify data integrity

---

### Phase 3: Docker Configuration (Estimated: 2-3 hours)

#### 3.1 Update `docker-compose.yml` - Add Celery ❌ **CRITICAL**

**Current `docker-compose.yml` is missing:**
- Celery worker
- Celery beat (for scheduled tasks)
- Proper volume mounts for data files

**Updated `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: menumine_db
    environment:
      POSTGRES_DB: ${DB_NAME:-menumine_ai}
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-password}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - menumine_network
      
  redis:
    image: redis:7-alpine
    container_name: menumine_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - menumine_network
      
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: menumine_backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    volumes:
      - ./backend:/app
      - ./backend/data:/app/data  # Mount data directory for IML/CookLingo
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: >
      sh -c "
        python manage.py migrate &&
        daphne -b 0.0.0.0 -p 8000 menumine_ai.asgi:application
      "
    networks:
      - menumine_network

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: menumine_celery_worker
    env_file:
      - ./backend/.env
    volumes:
      - ./backend:/app
      - ./backend/data:/app/data
    depends_on:
      - db
      - redis
    command: celery -A menumine_ai worker --loglevel=info
    networks:
      - menumine_network

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: menumine_celery_beat
    env_file:
      - ./backend/.env
    volumes:
      - ./backend:/app
      - ./backend/data:/app/data
    depends_on:
      - db
      - redis
    command: celery -A menumine_ai beat --loglevel=info
    networks:
      - menumine_network
      
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: menumine_frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    env_file:
      - ./frontend/.env
    depends_on:
      - backend
    command: npm start
    networks:
      - menumine_network

volumes:
  postgres_data:
  redis_data:

networks:
  menumine_network:
    driver: bridge
```

**Action Items:**
- [ ] Update `docker-compose.yml` with Celery services
- [ ] Test: `docker-compose up -d`

---

#### 3.2 Update Production `docker-compose.prod.yml`

**Add to `docker-compose.prod.yml`:**

```yaml
  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: menumine_celery_worker_prod
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - GROQ_API_KEY=${GROQ_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./backend/data:/app/data:ro
    depends_on:
      - db
      - redis
    restart: unless-stopped
    command: celery -A menumine_ai worker --loglevel=info
    networks:
      - menumine_network

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: menumine_celery_beat_prod
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - GROQ_API_KEY=${GROQ_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./backend/data:/app/data:ro
    depends_on:
      - db
      - redis
    restart: unless-stopped
    command: celery -A menumine_ai beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    networks:
      - menumine_network
```

**Action Items:**
- [ ] Update `docker-compose.prod.yml`

---

#### 3.3 Update Backend `Dockerfile.prod`

**Add data directory copy:**

```dockerfile
# ... existing content ...

# Copy application code
COPY . .

# Copy data files (IML, CookLingo databases)
COPY data /app/data

# ... rest of Dockerfile ...
```

**Action Items:**
- [ ] Update `Dockerfile.prod` to copy data directory

---

### Phase 4: Security Hardening (Estimated: 1 hour)

#### 4.1 Generate New SECRET_KEY ❌ **CRITICAL**

**Current:** `django-insecure-dev-key-change-in-production`

**Generate new key:**

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

**Action Items:**
- [ ] Generate new SECRET_KEY
- [ ] Update `.env` (NOT `.env.example`)
- [ ] NEVER commit real SECRET_KEY to git

---

#### 4.2 Update `.gitignore`

Ensure these are ignored:

```
# Environment files
.env
.env.local
.env.production

# Databases
*.db
*.sqlite3
db.sqlite3
db.sqlite3.backup

# Data exports
data_export.json
backup_*.json

# Secrets
secrets/
*.pem
*.key
ssl/
```

**Action Items:**
- [ ] Review `.gitignore`
- [ ] Add any missing entries

---

#### 4.3 Remove Hardcoded Credentials

**Check for hardcoded secrets:**

```bash
# Search for potential secrets
grep -r "password" --include="*.py" backend/
grep -r "api_key" --include="*.py" backend/
grep -r "secret" --include="*.py" backend/
```

**Action Items:**
- [ ] Audit codebase for hardcoded secrets
- [ ] Move all secrets to `.env`

---

### Phase 5: Testing & Validation (Estimated: 2-3 hours)

#### 5.1 Local Docker Testing

```bash
# Build and start all services
docker-compose build
docker-compose up -d

# Check logs
docker-compose logs -f backend
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Test endpoints
curl http://localhost:8000/health/
curl http://localhost:8000/api/recipes/canonical/
```

**Action Items:**
- [ ] Build Docker images
- [ ] Start all services
- [ ] Verify all containers are running
- [ ] Test API endpoints
- [ ] Test WebSocket connections
- [ ] Test Celery tasks

---

#### 5.2 Data Integrity Verification

**SQL queries to verify migration:**

```sql
-- Connect to PostgreSQL
docker-compose exec db psql -U postgres -d menumine_ai

-- Check record counts
SELECT COUNT(*) FROM auth_user;
SELECT COUNT(*) FROM recipes_recipe;
SELECT COUNT(*) FROM recipes_canonicalrecipe;
SELECT COUNT(*) FROM shopping_shoppinglist;
SELECT COUNT(*) FROM recipes_recipetranslation;

-- Check for orphaned records
SELECT COUNT(*) FROM recipes_recipe WHERE created_by_id NOT IN (SELECT id FROM auth_user);
```

**Action Items:**
- [ ] Verify record counts match SQLite
- [ ] Check for data integrity issues
- [ ] Test user login
- [ ] Test recipe creation
- [ ] Test shopping lists

---

### Phase 6: Production Preparation (Estimated: 1-2 hours)

#### 6.1 SSL/TLS Configuration

**Create SSL directory:**

```bash
mkdir -p ssl
# Copy your SSL certificates
cp /path/to/fullchain.pem ssl/
cp /path/to/privkey.pem ssl/
```

**Action Items:**
- [ ] Obtain SSL certificates (Let's Encrypt recommended)
- [ ] Place certificates in `ssl/` directory
- [ ] Update nginx config to use SSL

---

#### 6.2 Production Environment Variables

**Create `backend/.env.production`:**

```bash
# Copy from .env.example and update with PRODUCTION values
cp backend/.env.example backend/.env.production

# Important production settings:
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
USE_POSTGRES=True
SENTRY_ENVIRONMENT=production
```

**Action Items:**
- [ ] Create production `.env` file
- [ ] Update all URLs to production domain
- [ ] Enable HTTPS
- [ ] Configure production email

---

#### 6.3 Backup Strategy

**Create backup script:**

```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker-compose exec -T db pg_dump -U postgres menumine_ai > "$BACKUP_DIR/db_$DATE.sql"

# Backup Redis
docker-compose exec -T redis redis-cli SAVE
docker cp menumine_redis:/data/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"

echo "✅ Backup complete: $BACKUP_DIR"
```

**Action Items:**
- [ ] Create backup script
- [ ] Setup automated daily backups (cron)
- [ ] Test restore procedure

---

## 📊 Migration Checklist Summary

### Must Do Before Docker (CRITICAL)
- [ ] Fix hardcoded Windows paths in settings.py
- [ ] Create `.env.example` templates
- [ ] Move IML/CookLingo databases to `backend/data/`
- [ ] Add health check endpoint
- [ ] Generate new SECRET_KEY
- [ ] Migrate SQLite → PostgreSQL

### Should Do Before Docker (HIGH PRIORITY)
- [ ] Add Celery services to docker-compose
- [ ] Update Dockerfiles to copy data directory
- [ ] Create database backup
- [ ] Test migration on development copy first

### Nice to Have (MEDIUM PRIORITY)
- [ ] Setup SSL certificates
- [ ] Configure production email
- [ ] Setup automated backups
- [ ] Configure monitoring/alerting

### Can Do Later (LOW PRIORITY)
- [ ] Performance optimization
- [ ] CDN setup
- [ ] Load balancer configuration
- [ ] Multi-region deployment

---

## 🚨 Critical Warnings

1. **⚠️ NEVER commit `.env` files with real secrets to Git**
2. **⚠️ Backup SQLite database before migration**
3. **⚠️ Test migration on a copy first, not production data**
4. **⚠️ Update all absolute paths to relative/environment-based**
5. **⚠️ Generate new SECRET_KEY for production (never reuse dev key)**

---

## 📈 Estimated Timeline

| Phase | Tasks | Time | Priority |
|-------|-------|------|----------|
| Phase 1 | Code Cleanup | 1-2h | 🔴 CRITICAL |
| Phase 2 | DB Migration | 2-3h | 🔴 CRITICAL |
| Phase 3 | Docker Config | 2-3h | 🔴 CRITICAL |
| Phase 4 | Security | 1h | 🟠 HIGH |
| Phase 5 | Testing | 2-3h | 🟠 HIGH |
| Phase 6 | Production Prep | 1-2h | 🟡 MEDIUM |
| **Total** | **All Phases** | **9-14h** | |

---

## 🎯 Next Steps

1. **Review this checklist** and confirm approach
2. **Start with Phase 1** (Code Cleanup) - no risk, just preparation
3. **Create backups** before any database operations
4. **Test everything locally** before production deployment
5. **Deploy to staging** first if available
6. **Monitor Sentry** for errors during/after migration

---

**Ready to start? Let me know which phase you want to begin with!** 🚀

