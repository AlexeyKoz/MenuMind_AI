# 🚀 PRODUCTION DEPLOYMENT GUIDE - MenuMind AI (BishulMe)

## 📋 PRE-DEPLOYMENT CHECKLIST

### ✅ Development Complete
- [x] Multilingual support (EN, RU, HE)
- [x] Logo management system
- [x] AI token protection
- [x] Shopping list real-time sync
- [x] Recipe generation with fallbacks
- [x] Legal documents management
- [x] About Us page
- [x] Google Translate integration
- [x] Celery background tasks
- [x] WebSocket (Django Channels)

### ✅ Production Files Ready
- [x] `docker-compose.prod.yml` - Updated with media volumes
- [x] `backend/Dockerfile` - Production-ready
- [x] `frontend/Dockerfile` - Production-ready
- [x] `backend/requirements.txt` - All dependencies included

---

## 🔐 STEP 1: PREPARE ENVIRONMENT VARIABLES

### Backend `.env` File

Create `backend/.env` on your server with these variables:

```bash
# === CRITICAL: CHANGE THESE FOR PRODUCTION ===
SECRET_KEY=your-super-secret-django-key-here-minimum-50-characters
DEBUG=False
ALLOWED_HOSTS=bishulme.com,www.bishulme.com,your-server-ip

# Database
USE_POSTGRES=True
DB_NAME=menumindai_prod
DB_USER=postgres
DB_PASSWORD=STRONG_PASSWORD_HERE
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

# Email (Mailjet)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=in-v3.mailjet.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-mailjet-api-key
EMAIL_HOST_PASSWORD=your-mailjet-secret-key
DEFAULT_FROM_EMAIL=noreply@bishulme.com

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-secret

# AI Services
GOOGLE_CLOUD_API_KEY=AIzaSyDu9QQJrVR87f1WUgqinDCF1vjBnY9_SlA
GEMINI_API_KEY=your-gemini-key
GROQ_API_KEY=your-groq-key
BRAVE_SEARCH_API_KEY=your-brave-search-key

# Firecrawl (Recipe scraping)
FIRECRAWL_API_KEY=your-firecrawl-key

# Sentry (Error tracking)
SENTRY_DSN=your-sentry-dsn
SENTRY_ENVIRONMENT=production

# CORS
CORS_ALLOWED_ORIGINS=https://bishulme.com,https://www.bishulme.com

# Static/Media
STATIC_URL=/static/
MEDIA_URL=/media/
```

### Docker Compose Environment

Create `.env` in project root:

```bash
# Database
DB_NAME=menumindai_prod
DB_USER=postgres
DB_PASSWORD=STRONG_PASSWORD_HERE

# Compose
COMPOSE_PROJECT_NAME=menumine_prod
```

---

## 🗂️ STEP 2: PREPARE FILES ON SERVER

### 2.1 Sync Files to Server

```bash
# From your Windows machine (in WSL):
cd ~/MenuMind_AI/MenuMind_AI

# Create tarball (excluding node_modules, etc)
tar -czf menumine_deploy.tar.gz \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='.env' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache' \
  --exclude='backups' \
  --exclude='frontend_build' \
  backend/ frontend/ docker-compose.prod.yml nginx/ legal_documents/

# Copy to server
scp menumine_deploy.tar.gz user@your-server:/home/user/

# On server:
cd /home/user
tar -xzf menumine_deploy.tar.gz
mv backend frontend docker-compose.prod.yml nginx legal_documents /opt/menumine/
```

### 2.2 Set Up Directory Structure on Server

```bash
# On server:
sudo mkdir -p /opt/menumine/{backend,frontend,nginx,legal_documents}
sudo chown -R $USER:$USER /opt/menumine
cd /opt/menumine

# Copy files
# (after uploading)
```

---

## 🐳 STEP 3: DEPLOY WITH DOCKER

### 3.1 Build Images

```bash
cd /opt/menumine

# Pull base images first
docker compose -f docker-compose.prod.yml pull

# Build custom images
docker compose -f docker-compose.prod.yml build --no-cache
```

### 3.2 Start Services

```bash
# Start all services
docker compose -f docker-compose.prod.yml up -d

# Check status
docker compose -f docker-compose.prod.yml ps
```

### 3.3 Run Migrations

```bash
# Run database migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Create superuser
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Collect static files
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

### 3.4 Load Initial Data

```bash
# Load legal documents
docker compose -f docker-compose.prod.yml exec backend python manage.py load_bishulsheli_docs

# Load About Us pages
docker compose -f docker-compose.prod.yml exec backend python manage.py load_about_pages

# Import IML ingredients
docker compose -f docker-compose.prod.yml exec backend python manage.py import_iml_json

# Import CookLingo terms
docker compose -f docker-compose.prod.yml exec backend python manage.py import_cooklingo_json

# Seed recipes (optional)
docker compose -f docker-compose.prod.yml exec backend python manage.py seed_100_recipes
```

---

## 🔍 STEP 4: VERIFY DEPLOYMENT

### 4.1 Check All Containers Running

```bash
docker compose -f docker-compose.prod.yml ps

# Expected output:
# menumine_db_prod          Up (healthy)
# menumine_redis_prod       Up (healthy)
# menumine_backend_prod     Up (healthy)
# menumine_celery_prod      Up
# menumine_celery_beat_prod Up
# menumine_daphne_prod      Up
# menumine_frontend_prod    Up (healthy)
```

### 4.2 Check Logs

```bash
# Backend
docker compose -f docker-compose.prod.yml logs backend --tail 50

# Celery
docker compose -f docker-compose.prod.yml logs celery --tail 50

# Daphne (WebSocket)
docker compose -f docker-compose.prod.yml logs daphne --tail 50

# Frontend
docker compose -f docker-compose.prod.yml logs frontend --tail 20
```

### 4.3 Test Endpoints

```bash
# Health check
curl http://localhost:8000/health/

# API
curl http://localhost:8000/api/

# Frontend
curl http://localhost/
```

### 4.4 Test Admin Panel

1. Go to `http://your-server-ip:8000/admin/`
2. Login with superuser credentials
3. Check:
   - ✅ Legal Documents loaded
   - ✅ About Page content
   - ✅ IML Ingredients (~1710)
   - ✅ CookLingo Terms (~2068)
   - ✅ Site Logos can be uploaded

---

## 🌐 STEP 5: CONFIGURE NGINX/REVERSE PROXY

If you're using a reverse proxy (Nginx, Traefik, etc.), configure it to:

### Nginx Configuration Example

```nginx
upstream backend {
    server localhost:8000;
}

upstream websocket {
    server localhost:8001;
}

server {
    listen 80;
    server_name bishulme.com www.bishulme.com;

    # Redirect to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name bishulme.com www.bishulme.com;

    ssl_certificate /etc/letsencrypt/live/bishulme.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bishulme.com/privkey.pem;

    # Frontend (React)
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Django Admin
    location /admin/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files
    location /static/ {
        proxy_pass http://backend;
    }

    # Media files
    location /media/ {
        proxy_pass http://backend;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

---

## 🔐 STEP 6: SSL/HTTPS SETUP

### Using Let's Encrypt (Certbot)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d bishulme.com -d www.bishulme.com

# Auto-renewal is set up automatically
sudo certbot renew --dry-run
```

---

## 📊 STEP 7: MONITORING & MAINTENANCE

### 7.1 Set Up Logging

```bash
# Create log directory
mkdir -p /opt/menumine/logs

# Rotate logs (create /etc/logrotate.d/menumine)
/opt/menumine/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 root root
}
```

### 7.2 Database Backups

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
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /opt/menumine/media

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /opt/menumine/backup.sh

# Add to cron (daily at 2 AM)
echo "0 2 * * * /opt/menumine/backup.sh" | crontab -
```

### 7.3 Health Monitoring

```bash
# Create health check script
cat > /opt/menumine/healthcheck.sh << 'EOF'
#!/bin/bash
SERVICES="backend celery celery-beat daphne frontend db redis"

for service in $SERVICES; do
    STATUS=$(docker compose -f /opt/menumine/docker-compose.prod.yml ps $service --format json | jq -r '.[0].Health')
    if [[ "$STATUS" != "healthy" && "$STATUS" != "running" ]]; then
        echo "$(date): $service is $STATUS" >> /var/log/menumine_health.log
        # Send alert (email, Slack, etc.)
    fi
done
EOF

chmod +x /opt/menumine/healthcheck.sh

# Check every 5 minutes
echo "*/5 * * * * /opt/menumine/healthcheck.sh" | crontab -
```

---

## 🔄 STEP 8: UPDATES & ROLLBACKS

### Update Application

```bash
cd /opt/menumine

# Pull latest code
git pull origin main  # or your update method

# Rebuild images
docker compose -f docker-compose.prod.yml build --no-cache

# Stop services
docker compose -f docker-compose.prod.yml down

# Start with new images
docker compose -f docker-compose.prod.yml up -d

# Run migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Collect static
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

### Rollback

```bash
# Stop services
docker compose -f docker-compose.prod.yml down

# Restore database backup
docker compose -f docker-compose.prod.yml up -d db
cat /opt/menumine/backups/db_YYYYMMDD_HHMMSS.sql | \
  docker compose -f docker-compose.prod.yml exec -T db psql -U postgres -d menumindai_prod

# Restore media files
tar -xzf /opt/menumine/backups/media_YYYYMMDD_HHMMSS.tar.gz -C /

# Start all services
docker compose -f docker-compose.prod.yml up -d
```

---

## 🎯 STEP 9: POST-DEPLOYMENT TASKS

### 9.1 Upload Initial Logos

1. Go to admin panel: `https://bishulme.com/admin/`
2. Navigate to **Branding > Site logos**
3. Upload logos for each language:
   - Login logo (EN, RU, HE)
   - Navbar logo (EN, RU, HE)
   - Favicon (EN, RU, HE)

### 9.2 Verify All Features

- ✅ User registration
- ✅ Email verification
- ✅ Google OAuth login
- ✅ Shopping list creation
- ✅ Real-time WebSocket sync
- ✅ Recipe generation
- ✅ Multilingual switching (EN/RU/HE)
- ✅ Logo display for each language
- ✅ Legal documents display
- ✅ About Us page

### 9.3 Configure Google OAuth

Update Google Cloud Console:
- **Authorized JavaScript origins**:
  - `https://bishulme.com`
  - `https://www.bishulme.com`
- **Authorized redirect URIs**:
  - `https://bishulme.com/api/auth/google/callback/`
  - `https://www.bishulme.com/api/auth/google/callback/`

---

## 📝 USEFUL COMMANDS

### View Logs
```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs backend -f --tail 100

# Only errors
docker compose -f docker-compose.prod.yml logs | grep ERROR
```

### Restart Services
```bash
# Restart all
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.prod.yml restart celery
```

### Database Operations
```bash
# Django shell
docker compose -f docker-compose.prod.yml exec backend python manage.py shell

# Database shell
docker compose -f docker-compose.prod.yml exec db psql -U postgres -d menumindai_prod

# Create backup
docker compose -f docker-compose.prod.yml exec db pg_dump -U postgres menumindai_prod > backup.sql
```

### Performance Monitoring
```bash
# Container stats
docker stats

# Disk usage
docker system df

# Cleanup unused resources
docker system prune -a
```

---

## ⚠️ TROUBLESHOOTING

### Issue: Containers won't start
```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Remove and recreate
docker compose -f docker-compose.prod.yml down -v
docker compose -f docker-compose.prod.yml up -d
```

### Issue: Database connection errors
```bash
# Check database is healthy
docker compose -f docker-compose.prod.yml ps db

# Restart database
docker compose -f docker-compose.prod.yml restart db

# Check database logs
docker compose -f docker-compose.prod.yml logs db
```

### Issue: WebSocket not working
```bash
# Check Daphne logs
docker compose -f docker-compose.prod.yml logs daphne

# Restart Daphne
docker compose -f docker-compose.prod.yml restart daphne

# Check Redis connection
docker compose -f docker-compose.prod.yml exec backend python -c "import redis; r = redis.Redis(host='redis'); print(r.ping())"
```

---

## 🎉 DEPLOYMENT COMPLETE!

Your MenuMind AI (BishulMe) application is now running in production!

### Access Points:
- **Frontend**: `https://bishulme.com`
- **Admin Panel**: `https://bishulme.com/admin/`
- **API**: `https://bishulme.com/api/`

### Next Steps:
1. ✅ Monitor logs for first 24 hours
2. ✅ Test all critical features
3. ✅ Set up automated backups
4. ✅ Configure monitoring/alerts
5. ✅ Update DNS if needed
6. ✅ Announce launch! 🚀

---

**Need Help?** Check logs and contact your DevOps team if issues persist.

