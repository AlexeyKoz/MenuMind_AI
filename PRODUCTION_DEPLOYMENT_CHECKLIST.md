# ✅ PRODUCTION DEPLOYMENT CHECKLIST

## 📦 BEFORE YOU START

### Files to Upload to Server
```bash
✅ backend/                    # Django backend
✅ frontend/                   # React frontend
✅ docker-compose.prod.yml     # Production Docker config
✅ nginx/                      # Nginx config (if using)
✅ legal_documents/            # Legal docs in EN, RU, HE
✅ backend/data/iml_export.json        # Ingredients database
✅ backend/data/cooklingo_export.json  # Cooking terms database
```

### DO NOT Upload
```bash
❌ node_modules/
❌ __pycache__/
❌ *.pyc
❌ .env (create fresh on server)
❌ .pytest_cache/
❌ backups/
❌ frontend_build/
❌ *.log
```

---

## 🔐 CRITICAL: ENVIRONMENT VARIABLES

### Required on Production Server

Create `backend/.env` with:

```bash
# ⚠️  CRITICAL - MUST CHANGE
SECRET_KEY=                    # ← Generate new 50+ char random string
DB_PASSWORD=                   # ← Strong password for PostgreSQL
DEBUG=False                    # ← MUST be False in production
ALLOWED_HOSTS=                 # ← bishulme.com,www.bishulme.com,server-ip

# Email
EMAIL_HOST_USER=               # ← Mailjet API key
EMAIL_HOST_PASSWORD=           # ← Mailjet secret key
DEFAULT_FROM_EMAIL=            # ← noreply@bishulme.com

# Google OAuth
GOOGLE_CLIENT_ID=              # ← From Google Cloud Console
GOOGLE_CLIENT_SECRET=          # ← From Google Cloud Console

# AI Services (already have these)
GOOGLE_CLOUD_API_KEY=AIzaSyDu9QQJrVR87f1WUgqinDCF1vjBnY9_SlA
GEMINI_API_KEY=                # ← Your Gemini key
GROQ_API_KEY=                  # ← Your Groq key
BRAVE_SEARCH_API_KEY=          # ← Your Brave Search key (optional)

# Firecrawl
FIRECRAWL_API_KEY=             # ← Your Firecrawl key

# Sentry (Error tracking - optional but recommended)
SENTRY_DSN=                    # ← From Sentry.io
SENTRY_ENVIRONMENT=production

# CORS
CORS_ALLOWED_ORIGINS=https://bishulme.com,https://www.bishulme.com
```

---

## 🚀 DEPLOYMENT STEPS

### 1️⃣ On Your Windows Machine (WSL)

```bash
cd ~/MenuMind_AI/MenuMind_AI

# Create deployment package
tar -czf menumine_deploy.tar.gz \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='.env' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache' \
  --exclude='backups' \
  --exclude='frontend_build' \
  backend/ frontend/ docker-compose.prod.yml nginx/ legal_documents/ deploy-to-production.sh

# Copy to server
scp menumine_deploy.tar.gz root@your-server-ip:/root/
```

### 2️⃣ On Production Server

```bash
# Login to server
ssh root@your-server-ip

# Create application directory
mkdir -p /opt/menumine
cd /opt/menumine

# Extract files
tar -xzf /root/menumine_deploy.tar.gz

# Create .env file
nano backend/.env
# (Paste your production environment variables)

# Make deployment script executable
chmod +x deploy-to-production.sh

# Copy data files
cp /path/to/iml_export.json backend/data/
cp /path/to/cooklingo_export.json backend/data/

# Run deployment
./deploy-to-production.sh
```

### 3️⃣ Post-Deployment

```bash
# Create superuser
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Test services
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail 50

# Access admin panel
# http://your-server-ip:8000/admin/
```

---

## 🧪 VERIFICATION CHECKLIST

### Container Health

```bash
docker compose -f docker-compose.prod.yml ps

Expected status:
✅ menumine_db_prod          - Up (healthy)
✅ menumine_redis_prod       - Up (healthy)  
✅ menumine_backend_prod     - Up (healthy)
✅ menumine_celery_prod      - Up
✅ menumine_celery_beat_prod - Up
✅ menumine_daphne_prod      - Up
✅ menumine_frontend_prod    - Up (healthy)
```

### Data Verification

```bash
# Check databases loaded
docker compose -f docker-compose.prod.yml exec backend python manage.py shell

# In Django shell:
from legal.models import LegalDocument
from legal.models import AboutPage
from apps.core.models import IngredientCache, CookingTermCache

print(f"Legal Docs: {LegalDocument.objects.count()}")      # Should be ~15
print(f"About Pages: {AboutPage.objects.count()}")         # Should be 3
print(f"IML Ingredients: {IngredientCache.objects.count()}")  # Should be ~1710
print(f"CookLingo Terms: {CookingTermCache.objects.count()}")  # Should be ~2068
```

### Feature Testing

Access: `http://your-server-ip/`

- ✅ Frontend loads
- ✅ Language switcher (EN/RU/HE)
- ✅ User registration
- ✅ Email verification
- ✅ Google OAuth login
- ✅ Shopping list creation
- ✅ Real-time sync (open 2 browsers)
- ✅ Recipe generation
- ✅ Legal documents accessible
- ✅ About Us page

### Admin Panel

Access: `http://your-server-ip:8000/admin/`

- ✅ Upload logos (Login, Navbar, Favicon for each language)
- ✅ Check legal documents
- ✅ Check IML data
- ✅ Check CookLingo data

---

## 🌐 DOMAIN & SSL SETUP

### Update DNS

Point your domain to the server:
```
A Record: bishulme.com → your-server-ip
A Record: www.bishulme.com → your-server-ip
```

### Install SSL Certificate

```bash
# Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d bishulme.com -d www.bishulme.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Update Google OAuth

Go to Google Cloud Console:
1. **Authorized JavaScript origins**:
   - Add: `https://bishulme.com`
   - Add: `https://www.bishulme.com`
   
2. **Authorized redirect URIs**:
   - Add: `https://bishulme.com/api/auth/google/callback/`
   - Add: `https://www.bishulme.com/api/auth/google/callback/`

---

## 📊 MONITORING & BACKUPS

### Set Up Automatic Backups

```bash
# Create backup script
cat > /opt/menumine/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/menumine/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
docker compose -f /opt/menumine/docker-compose.prod.yml exec -T db \
  pg_dump -U postgres menumindai_prod > $BACKUP_DIR/db_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C /opt/menumine media

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/menumine/backup.sh

# Schedule daily at 2 AM
crontab -e
# Add: 0 2 * * * /opt/menumine/backup.sh >> /var/log/menumine_backup.log 2>&1
```

### Monitor Logs

```bash
# Real-time logs
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs backend -f --tail 100

# Errors only
docker compose -f docker-compose.prod.yml logs | grep ERROR
```

---

## 🔄 UPDATES

### Deploy New Version

```bash
cd /opt/menumine

# Upload new code
# (same process as initial deployment)

# Rebuild and restart
./deploy-to-production.sh

# Or manually:
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

---

## 🆘 EMERGENCY ROLLBACK

```bash
# Stop services
docker compose -f docker-compose.prod.yml down

# Restore database
cd /opt/menumine/backups
cat db_YYYYMMDD_HHMMSS.sql | docker compose -f /opt/menumine/docker-compose.prod.yml exec -T db psql -U postgres -d menumindai_prod

# Restore media
tar -xzf media_YYYYMMDD_HHMMSS.tar.gz -C /opt/menumine

# Start services
docker compose -f docker-compose.prod.yml up -d
```

---

## 📝 QUICK REFERENCE

### Useful Commands

```bash
# View all containers
docker compose -f docker-compose.prod.yml ps

# Restart service
docker compose -f docker-compose.prod.yml restart backend

# View logs
docker compose -f docker-compose.prod.yml logs backend --tail 100 -f

# Django shell
docker compose -f docker-compose.prod.yml exec backend python manage.py shell

# Database shell
docker compose -f docker-compose.prod.yml exec db psql -U postgres -d menumindai_prod

# Check disk usage
docker system df

# Clean up
docker system prune -a
```

---

## 🎯 FINAL CHECKLIST

Before announcing launch:

- [ ] All containers running and healthy
- [ ] SSL certificate installed
- [ ] Domain pointing to server
- [ ] Google OAuth configured
- [ ] Logos uploaded in admin
- [ ] Test user registration
- [ ] Test shopping list sync
- [ ] Test recipe generation
- [ ] Test all 3 languages
- [ ] Backups configured
- [ ] Monitoring set up
- [ ] Error tracking (Sentry) configured

---

## 🎉 LAUNCH!

Once everything is checked:

1. ✅ Announce on social media
2. ✅ Send launch emails
3. ✅ Monitor logs closely for first 24 hours
4. ✅ Be ready for user feedback

---

**Your MenuMind AI (BishulMe) is ready for production!** 🚀

