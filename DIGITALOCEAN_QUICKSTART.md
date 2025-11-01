# 🚀 DigitalOcean Quick Reference

## 📦 What You Have

- **7 Docker Containers** (simplified, no Nginx reverse proxy):
  1. `menumine_db` - PostgreSQL database
  2. `menumine_redis` - Redis cache
  3. `menumine_backend` - Django API (port 8000)
  4. `menumine_celery` - Background tasks
  5. `menumine_celery_beat` - Scheduled tasks
  6. `menumine_daphne` - WebSocket server (port 8001)
  7. `menumine_frontend` - React app (port 80)

## 🌐 Ports

- **80** → Frontend (React)
- **8000** → Backend API (Django)
- **8001** → WebSocket (Daphne)

## ⚡ Quick Start

### Deploy for the First Time

```bash
# On your DigitalOcean droplet
git clone YOUR_REPO
cd menumine-ai
bash deploy-digitalocean.sh
```

### Manual Deployment

```bash
# 1. Setup environment
cp ENV.digitalocean.example backend/.env
nano backend/.env  # Edit with your values

# 2. Build and start
docker-compose -f docker-compose.digitalocean.yml up -d --build

# 3. Run migrations
docker exec menumine_backend python manage.py migrate

# 4. Create admin user
docker exec -it menumine_backend python manage.py createsuperuser
```

## 🔄 Common Commands

```bash
# Start all services
docker-compose -f docker-compose.digitalocean.yml up -d

# Stop all services
docker-compose -f docker-compose.digitalocean.yml down

# Restart a service
docker-compose -f docker-compose.digitalocean.yml restart backend

# View logs
docker-compose -f docker-compose.digitalocean.yml logs -f

# Check status
docker-compose -f docker-compose.digitalocean.yml ps
```

## 🔧 Maintenance

### Update Code

```bash
git pull
docker-compose -f docker-compose.digitalocean.yml up -d --build
docker exec menumine_backend python manage.py migrate
```

### Backup Database

```bash
docker exec menumine_db pg_dump -U postgres menumine_ai > backup.sql
```

### Restore Database

```bash
docker exec -i menumine_db psql -U postgres menumine_ai < backup.sql
```

### View Container Logs

```bash
docker logs menumine_backend -f       # Backend
docker logs menumine_frontend -f      # Frontend
docker logs menumine_daphne -f        # WebSocket
docker logs menumine_celery -f        # Background tasks
```

### Check Resource Usage

```bash
docker stats
free -h
df -h
```

## 🔥 Firewall Rules

```bash
ufw allow 22      # SSH
ufw allow 80      # HTTP
ufw allow 443     # HTTPS
ufw allow 8000    # Backend API
ufw allow 8001    # WebSocket
ufw enable
```

## 🐛 Troubleshooting

### Container won't start?
```bash
docker-compose -f docker-compose.digitalocean.yml logs SERVICE_NAME
```

### Database connection error?
```bash
docker exec menumine_db psql -U postgres -c "SELECT 1;"
```

### Frontend can't reach backend?
- Check `ALLOWED_HOSTS` in backend/.env
- Check `CORS_ALLOWED_ORIGINS` in backend/.env
- Verify firewall: `ufw status`

### Out of memory?
```bash
# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 📍 URLs

Replace `YOUR_IP` with your droplet IP:

- Frontend: `http://YOUR_IP`
- API: `http://YOUR_IP:8000/api/`
- Admin: `http://YOUR_IP:8000/admin/`
- Health: `http://YOUR_IP:8000/health/`

## 🔐 Security Checklist

- [ ] Change `DB_PASSWORD` to strong password
- [ ] Generate new `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Update `ALLOWED_HOSTS`
- [ ] Update `CORS_ALLOWED_ORIGINS`
- [ ] Add SSL certificate
- [ ] Enable firewall
- [ ] Setup automatic backups

## 📚 Full Documentation

See `DIGITALOCEAN_DEPLOYMENT.md` for complete step-by-step guide.

