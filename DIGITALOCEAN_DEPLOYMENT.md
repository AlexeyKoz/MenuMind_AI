# 🚀 DigitalOcean Deployment Guide

Complete guide to deploy MenuMine AI on DigitalOcean Droplet.

## 📋 Prerequisites

- DigitalOcean account
- Domain name (optional, but recommended)
- SSH key configured in DigitalOcean

## 🖥️ Step 1: Create a Droplet

1. **Go to DigitalOcean Dashboard** → Create → Droplets

2. **Choose Configuration:**
   - **Image**: Ubuntu 22.04 (LTS) x64
   - **Plan**: Basic
   - **CPU Options**: Regular (Recommend: 4GB RAM / 2 vCPUs or higher)
   - **Datacenter**: Choose closest to your users
   - **Authentication**: SSH Key (recommended)
   - **Hostname**: menumine-prod

3. **Click "Create Droplet"**

4. **Note your Droplet IP address** (e.g., `165.227.123.45`)

## 🔧 Step 2: Initial Server Setup

SSH into your droplet:

```bash
ssh root@YOUR_DROPLET_IP
```

### Update System

```bash
apt update && apt upgrade -y
```

### Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Verify installation
docker --version
docker-compose --version
```

### Install Git

```bash
apt install git -y
```

### Create Non-Root User (Recommended)

```bash
adduser menumine
usermod -aG sudo menumine
usermod -aG docker menumine

# Switch to new user
su - menumine
```

## 📦 Step 3: Clone Your Project

```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/menumine-ai.git
cd menumine-ai

# Or upload your project using SCP/SFTP
```

## ⚙️ Step 4: Configure Environment

### Create Backend Environment File

```bash
cd ~/menumine-ai
cp ENV.digitalocean.example backend/.env
nano backend/.env
```

**Edit the following important values:**

```bash
# Database
DB_PASSWORD=YourStrongPasswordHere123!

# Django
SECRET_KEY=your-random-50-character-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,YOUR_DROPLET_IP

# Frontend URLs (Replace YOUR_DROPLET_IP or your-domain.com)
FRONTEND_API_URL=http://YOUR_DROPLET_IP:8000
FRONTEND_WS_URL=ws://YOUR_DROPLET_IP:8001

# CORS
CORS_ALLOWED_ORIGINS=http://YOUR_DROPLET_IP,http://your-domain.com
CORS_ALLOW_ALL_ORIGINS=False

# Google OAuth
GOOGLE_CLIENT_SECRET=your-actual-google-client-secret
```

**To generate a SECRET_KEY:**

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

### Update Google OAuth Credentials

Go to [Google Cloud Console](https://console.cloud.google.com/):

1. **APIs & Services** → **Credentials**
2. Click your OAuth 2.0 Client ID
3. **Add Authorized JavaScript origins:**
   - `http://YOUR_DROPLET_IP`
   - `http://your-domain.com` (if you have a domain)
4. **Add Authorized redirect URIs:**
   - `http://YOUR_DROPLET_IP/accounts/google/login/callback/`
   - `http://your-domain.com/accounts/google/login/callback/`

## 🐳 Step 5: Build and Start Containers

```bash
cd ~/menumine-ai

# Build images (this will take 5-10 minutes)
docker-compose -f docker-compose.digitalocean.yml build

# Start all services
docker-compose -f docker-compose.digitalocean.yml up -d

# Check status
docker-compose -f docker-compose.digitalocean.yml ps
```

**Expected output:**

```
NAME                   STATUS              PORTS
menumine_backend       Up (healthy)        0.0.0.0:8000->8000/tcp
menumine_celery        Up
menumine_celery_beat   Up
menumine_daphne        Up                  0.0.0.0:8001->8001/tcp
menumine_db            Up (healthy)
menumine_frontend      Up (healthy)        0.0.0.0:80->80/tcp
menumine_redis         Up (healthy)
```

## 📊 Step 6: Initialize Database

```bash
# Run migrations
docker exec menumine_backend python manage.py migrate

# Create superuser (for Django admin)
docker exec -it menumine_backend python manage.py createsuperuser

# Import canonical recipes (if you have data)
docker cp backend/data/canonical_recipes_export.json menumine_backend:/app/data/
docker exec menumine_backend python import_canonical_recipes.py

# Import IML and CookLingo data (if you have data)
docker cp backend/data/iml_export.json menumine_backend:/app/data/
docker cp backend/data/cooklingo_export.json menumine_backend:/app/data/
docker exec menumine_backend python import_iml_cooklingo.py
```

## 🔥 Step 7: Configure Firewall

```bash
# Allow HTTP, HTTPS, SSH, and application ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP (Frontend)
ufw allow 443/tcp   # HTTPS (for future SSL)
ufw allow 8000/tcp  # Backend API
ufw allow 8001/tcp  # WebSocket

# Enable firewall
ufw enable

# Check status
ufw status
```

## 🌐 Step 8: Access Your Application

Open your browser and navigate to:

- **Frontend**: `http://YOUR_DROPLET_IP`
- **Backend API**: `http://YOUR_DROPLET_IP:8000/api/`
- **Django Admin**: `http://YOUR_DROPLET_IP:8000/admin/`

## 🔍 Step 9: Verify Everything Works

### Check Container Logs

```bash
# View all logs
docker-compose -f docker-compose.digitalocean.yml logs

# View specific service logs
docker-compose -f docker-compose.digitalocean.yml logs backend
docker-compose -f docker-compose.digitalocean.yml logs frontend
docker-compose -f docker-compose.digitalocean.yml logs daphne

# Follow logs in real-time
docker-compose -f docker-compose.digitalocean.yml logs -f
```

### Test Health Endpoints

```bash
# Test backend API
curl http://YOUR_DROPLET_IP:8000/health/

# Test frontend
curl http://YOUR_DROPLET_IP/health
```

### Check Container Status

```bash
docker ps
docker stats
```

## 🔄 Step 10: Setup Auto-Restart

Create a systemd service to auto-start containers on boot:

```bash
sudo nano /etc/systemd/system/menumine.service
```

**Add:**

```ini
[Unit]
Description=MenuMine AI Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/menumine/menumine-ai
ExecStart=/usr/bin/docker-compose -f docker-compose.digitalocean.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.digitalocean.yml down
User=menumine

[Install]
WantedBy=multi-user.target
```

**Enable the service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable menumine
sudo systemctl start menumine
sudo systemctl status menumine
```

## 📝 Common Commands

### Start/Stop Application

```bash
cd ~/menumine-ai

# Start
docker-compose -f docker-compose.digitalocean.yml up -d

# Stop
docker-compose -f docker-compose.digitalocean.yml down

# Restart
docker-compose -f docker-compose.digitalocean.yml restart

# Restart specific service
docker-compose -f docker-compose.digitalocean.yml restart backend
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.digitalocean.yml logs -f

# Specific service
docker logs menumine_backend -f
docker logs menumine_frontend -f
docker logs menumine_daphne -f
```

### Update Application

```bash
cd ~/menumine-ai

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.digitalocean.yml up -d --build

# Run migrations
docker exec menumine_backend python manage.py migrate
```

### Database Backup

```bash
# Create backup
docker exec menumine_db pg_dump -U postgres menumine_ai > backup_$(date +%Y%m%d).sql

# Restore backup
docker exec -i menumine_db psql -U postgres menumine_ai < backup_20251101.sql
```

### Clean Up

```bash
# Remove unused images/containers
docker system prune -a

# View disk usage
docker system df
```

## 🔒 Step 11: Add SSL/HTTPS (Recommended)

### Option 1: Using Certbot (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot

# Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Certificates will be in: /etc/letsencrypt/live/your-domain.com/
```

Then update your firewall:

```bash
ufw allow 443/tcp
```

### Option 2: Using DigitalOcean Load Balancer

1. Go to DigitalOcean Dashboard → Networking → Load Balancers
2. Create Load Balancer
3. Add SSL certificate
4. Forward HTTPS → HTTP to your droplet

## 🎯 Next Steps

1. **Add a domain name** and update DNS records
2. **Enable SSL/HTTPS** for secure connections
3. **Setup monitoring** (DigitalOcean Monitoring or external)
4. **Configure backups** (DigitalOcean Backups or custom scripts)
5. **Setup email notifications** for system alerts

## 🐛 Troubleshooting

### Containers Won't Start

```bash
# Check logs
docker-compose -f docker-compose.digitalocean.yml logs

# Check individual container
docker logs menumine_backend
```

### Cannot Connect to Database

```bash
# Check if PostgreSQL is running
docker exec menumine_db psql -U postgres -c "SELECT 1;"

# Check environment variables
docker exec menumine_backend env | grep DB_
```

### Frontend Shows "Failed to fetch"

1. Check `ALLOWED_HOSTS` in backend/.env
2. Check `CORS_ALLOWED_ORIGINS` includes your frontend URL
3. Verify firewall allows ports 8000 and 8001

### Out of Memory

```bash
# Check memory usage
free -h
docker stats

# Increase droplet size or add swap:
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 📞 Support

If you encounter issues:

1. Check logs: `docker-compose logs`
2. Verify environment variables
3. Check firewall rules: `ufw status`
4. Ensure all ports are open and accessible

---

**🎉 Congratulations! Your MenuMine AI is now running on DigitalOcean!**

Access it at: `http://YOUR_DROPLET_IP`

