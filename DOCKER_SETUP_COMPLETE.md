# 🎉 Docker Setup Complete - MenuMind AI

> **Your Docker environment is ready! This document summarizes what has been created.**

---

## ✅ What Was Created

### 📚 Documentation Files

1. **[DOCKER_GUIDE.md](DOCKER_GUIDE.md)** (20+ pages)
   - Complete Docker reference
   - All commands explained
   - Development & production workflows
   - Debugging & troubleshooting
   - Database operations
   - Advanced commands
   - Best practices

2. **[DOCKER_CHEATSHEET.md](DOCKER_CHEATSHEET.md)** (Quick Reference)
   - One-page cheat sheet
   - Daily commands
   - Emergency procedures
   - Quick troubleshooting

3. **[DOCKER_README.md](DOCKER_README.md)** (Getting Started)
   - Quick start guide
   - Script usage
   - Common workflows
   - Troubleshooting

### 🛠️ Helper Scripts

**Windows:**
- `docker-dev.bat` - Development environment manager
- `docker-prod.bat` - Production environment manager

**Linux/Mac:**
- `docker-dev.sh` - Development environment manager
- `docker-prod.sh` - Production environment manager

---

## 🚀 Quick Start Guide

### 1. Install Docker (If Not Already Installed)

**Windows:**
- Download: https://www.docker.com/products/docker-desktop/
- Install and restart computer
- Verify: `docker --version`

**Linux (Ubuntu/Debian):**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

**Your Current Setup:**
- ✅ Docker: 28.4.0
- ✅ Docker Compose: v2.39.4

---

### 2. Configure Environment

```bash
# Navigate to project
cd C:\Users\al7ko\Desktop\after-deploy\MenuMind_AI

# Create backend .env file
cd backend
notepad .env  # On Windows
# OR
nano .env     # On Linux
```

**Minimal .env configuration:**
```env
# Django
SECRET_KEY=your-secret-key-change-this
DEBUG=True

# Database (Docker)
DATABASE_URL=postgresql://postgres:password@db:5432/menumine_ai
DB_HOST=db
DB_PORT=5432

# Redis (Docker)
REDIS_URL=redis://redis:6379/0

# AI Services (Get your keys)
GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=your-gemini-api-key

# Frontend
FRONTEND_URL=http://localhost:3000
```

---

### 3. Start Development Environment

**Windows:**
```bash
# Option 1: Using helper script (Interactive menu)
docker-dev.bat

# Option 2: Direct command
docker-dev.bat start

# Option 3: Docker Compose directly
docker compose up -d
```

**Linux/Mac:**
```bash
# Make scripts executable (first time only)
chmod +x docker-dev.sh docker-prod.sh

# Option 1: Using helper script (Interactive menu)
./docker-dev.sh

# Option 2: Direct command
./docker-dev.sh start

# Option 3: Docker Compose directly
docker compose up -d
```

**What Happens:**
1. ✅ PostgreSQL database starts (port 5432)
2. ✅ Redis cache starts (port 6379)
3. ✅ Backend builds and starts (port 8000)
4. ✅ Frontend builds and starts (port 3000)
5. ✅ Migrations run automatically

**Access Your Application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Admin Panel: http://localhost:8000/admin
- Database: localhost:5432 (from host)
- Redis: localhost:6379 (from host)

---

### 4. Verify Services Are Running

```bash
# Check service status
docker compose ps

# View logs
docker compose logs -f

# Or use helper script
docker-dev.bat status  # Windows
./docker-dev.sh status # Linux/Mac
```

**Expected Output:**
```
NAME                    IMAGE                   STATUS          PORTS
menumine_backend        menumine_backend:dev    Up 30 seconds   0.0.0.0:8000->8000/tcp
menumine_db             postgres:15-alpine      Up 30 seconds   0.0.0.0:5432->5432/tcp
menumine_frontend       menumine_frontend:dev   Up 30 seconds   0.0.0.0:3000->3000/tcp
menumine_redis          redis:7-alpine          Up 30 seconds   0.0.0.0:6379->6379/tcp
```

---

## 📋 Daily Workflow

### Morning (Start Work)

```bash
# Windows
docker-dev.bat start

# Linux/Mac
./docker-dev.sh start

# Or manually
docker compose up -d
```

### Working on Code

**Backend Changes (Python/Django):**
- Edit files in `backend/`
- Changes auto-reload (no restart needed)
- If you change `requirements.txt`:
  ```bash
  docker compose build backend
  docker compose up -d
  ```

**Frontend Changes (React/TypeScript):**
- Edit files in `frontend/src/`
- Changes auto-reload (no restart needed)
- If you change `package.json`:
  ```bash
  docker compose build frontend
  docker compose up -d
  ```

**Database Models Changed:**
```bash
# Create migration
docker compose exec backend python manage.py makemigrations

# Apply migration
docker compose exec backend python manage.py migrate
```

### View Logs

```bash
# Real-time logs (all services)
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend

# Or using helper
docker-dev.bat logs  # Windows
./docker-dev.sh logs # Linux/Mac
```

### End of Day (Stop Work)

```bash
# Stop services (keeps data)
docker compose down

# Or using helper
docker-dev.bat stop  # Windows
./docker-dev.sh stop # Linux/Mac
```

---

## 🔧 Common Tasks

### Access Backend Shell

```bash
# Django shell
docker compose exec backend python manage.py shell

# Bash shell
docker compose exec backend bash

# Or using helper
docker-dev.bat shell  # Windows
./docker-dev.sh shell # Linux/Mac
```

### Access Database

```bash
# PostgreSQL shell
docker compose exec db psql -U postgres -d menumine_ai

# Or using helper
docker-dev.bat db  # Windows
./docker-dev.sh db # Linux/Mac
```

### Create Superuser

```bash
docker compose exec backend python manage.py createsuperuser
```

### Run Tests

```bash
# Pytest
docker compose exec backend pytest

# Django tests
docker compose exec backend python manage.py test
```

### Backup Database

```bash
# Windows
docker compose exec db pg_dump -U postgres menumine_ai > backup.sql

# Linux/Mac
docker compose exec db pg_dump -U postgres menumine_ai > backup_$(date +%Y%m%d).sql

# Or using production helper
docker-prod.bat backup  # Windows
./docker-prod.sh backup # Linux/Mac
```

---

## 🏭 Production Deployment

### Build for Production

```bash
# Windows
docker-prod.bat build

# Linux/Mac
./docker-prod.sh build

# Or manually
docker compose -f docker-compose.prod.yml build --no-cache
```

### Start Production Stack

```bash
# Windows
docker-prod.bat start

# Linux/Mac
./docker-prod.sh start

# Or manually
docker compose -f docker-compose.prod.yml up -d
```

**Production Services:**
- Frontend (nginx): Port 80
- Backend (gunicorn): Port 8000
- Daphne (websocket): Port 8001
- Celery Worker: Background tasks
- Celery Beat: Scheduled tasks
- PostgreSQL: Internal
- Redis: Internal

### Deploy to Server

**Method 1: Using Git (Recommended)**

```bash
# On local machine
git add .
git commit -m "Update application"
git push origin main

# On server (Linux)
ssh user@your-server
cd /path/to/MenuMind_AI
git pull origin main
./docker-prod.sh deploy  # Auto: pull + build + restart
```

**Method 2: Manual Docker Commands**

```bash
# On server
cd /path/to/MenuMind_AI
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# View logs
docker compose logs backend

# Rebuild from scratch
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### Database Connection Issues

```bash
# Check database is running
docker compose ps db

# Restart database
docker compose restart db

# View database logs
docker compose logs db
```

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux
sudo lsof -i :8000
sudo kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Host:Container
```

### Clean Up Docker

```bash
# Remove stopped containers, unused images
docker system prune -a

# Using helper
docker-dev.bat clean  # Windows
./docker-dev.sh clean # Linux/Mac
```

---

## 📖 Documentation Reference

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **DOCKER_GUIDE.md** | Complete reference (20+ pages) | Learning Docker in depth |
| **DOCKER_CHEATSHEET.md** | Quick reference (1 page) | Daily work, quick lookup |
| **DOCKER_README.md** | Getting started guide | First time setup |
| **This file** | Setup summary | Overview of what was created |

---

## 🎯 Next Steps

### 1. Configure Environment

```bash
cd backend
# Create .env file with your API keys and settings
```

### 2. Start Development

```bash
# Start services
docker-dev.bat start  # Windows
./docker-dev.sh start # Linux/Mac

# Check status
docker compose ps
```

### 3. Access Application

- Open browser: http://localhost:3000
- Backend API: http://localhost:8000
- Admin: http://localhost:8000/admin

### 4. Create Superuser

```bash
docker compose exec backend python manage.py createsuperuser
```

### 5. Start Coding!

- Backend code: `backend/apps/`
- Frontend code: `frontend/src/`
- Changes auto-reload!

---

## 🔄 Workflow Summary

```bash
# START WORK
docker compose up -d

# MAKE CHANGES
# - Edit files
# - Changes auto-reload

# VIEW LOGS (if needed)
docker compose logs -f backend

# RUN TESTS
docker compose exec backend pytest

# ACCESS SHELL (if needed)
docker compose exec backend bash

# STOP WORK
docker compose down
```

---

## 📚 Learn More

**Complete Guide:**
```bash
# Open full documentation
notepad DOCKER_GUIDE.md        # Windows
cat DOCKER_GUIDE.md            # Linux/Mac
```

**Quick Reference:**
```bash
# Open cheat sheet
notepad DOCKER_CHEATSHEET.md   # Windows
cat DOCKER_CHEATSHEET.md       # Linux/Mac
```

**Helper Scripts:**
```bash
# View help
docker-dev.bat help            # Windows
./docker-dev.sh help           # Linux/Mac
```

---

## 🆘 Getting Help

**Check versions:**
```bash
docker --version
docker compose version
```

**View command help:**
```bash
docker --help
docker compose --help
docker compose up --help
```

**Script help:**
```bash
docker-dev.bat help     # Windows
./docker-dev.sh help    # Linux/Mac
```

---

## ✨ Features Configured

✅ **Development Environment**
- Hot-reload for backend (Django)
- Hot-reload for frontend (React)
- PostgreSQL database
- Redis cache
- Volume mounts for code

✅ **Production Environment**
- Optimized Docker images
- Gunicorn for Django
- Nginx for React
- Daphne for WebSockets
- Celery for background tasks
- Celery Beat for scheduled tasks
- Health checks
- Restart policies

✅ **Helper Scripts**
- Interactive menus
- Direct commands
- Color-coded output (Linux/Mac)
- Error handling
- Status checking

✅ **Documentation**
- Complete guide (DOCKER_GUIDE.md)
- Quick reference (DOCKER_CHEATSHEET.md)
- Getting started (DOCKER_README.md)
- Setup summary (this file)

---

## 🎉 You're Ready to Go!

**Start developing:**
```bash
docker-dev.bat start  # Windows
./docker-dev.sh start # Linux/Mac
```

**Open in browser:**
- http://localhost:3000

**Happy coding! 🚀**

---

**Last Updated:** November 2, 2025  
**Docker Version:** 28.4.0  
**Docker Compose:** v2.39.4


