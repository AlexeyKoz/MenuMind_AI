# 🐳 Docker Complete Guide for MenuMind AI

> **Complete reference for working with Docker in MenuMind AI project**  
> This guide covers all Docker commands, workflows, and best practices for development and production.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Docker Structure](#project-docker-structure)
3. [Environment Setup](#environment-setup)
4. [Basic Docker Commands](#basic-docker-commands)
5. [Development Workflow](#development-workflow)
6. [Production Workflow](#production-workflow)
7. [Container Management](#container-management)
8. [Debugging & Troubleshooting](#debugging--troubleshooting)
9. [Database Operations](#database-operations)
10. [Advanced Commands](#advanced-commands)
11. [Best Practices](#best-practices)

---

## 🔧 Prerequisites

### Install Docker

**Windows:**
```bash
# Download Docker Desktop from:
https://www.docker.com/products/docker-desktop/

# After installation, verify:
docker --version
docker-compose --version
```

**Linux (Ubuntu/Debian):**
```bash
# Install Docker Engine
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

**Minimum Requirements:**
- Docker: 20.10+
- Docker Compose: 2.0+
- RAM: 4GB+ (8GB recommended)
- Disk Space: 10GB+ free

---

## 📁 Project Docker Structure

```
MenuMind_AI/
├── docker-compose.yml              # Development configuration
├── docker-compose.prod.yml         # Production configuration
├── docker-compose.digitalocean.yml # DigitalOcean deployment
│
├── backend/
│   ├── Dockerfile                  # Main production Dockerfile
│   ├── Dockerfile.dev             # Development Dockerfile
│   ├── Dockerfile.prod            # Multi-stage production Dockerfile
│   ├── Dockerfile.migrate         # Database migration Dockerfile
│   └── requirements.txt           # Python dependencies
│
├── frontend/
│   ├── Dockerfile                 # Production Dockerfile (nginx)
│   ├── Dockerfile.dev            # Development Dockerfile
│   └── nginx.conf                # Nginx configuration
│
└── nginx/
    ├── Dockerfile                 # Nginx reverse proxy
    ├── nginx.conf                # Main nginx config
    └── default.conf              # Default site config
```

### Docker Compose Files

| File | Purpose | Use Case |
|------|---------|----------|
| `docker-compose.yml` | Development setup | Local development with hot-reload |
| `docker-compose.prod.yml` | Production setup | Full production stack with all services |
| `docker-compose.digitalocean.yml` | Cloud deployment | DigitalOcean-specific configuration |

---

## 🌍 Environment Setup

### 1. Create Backend `.env` File

```bash
cd backend
cat > .env << 'EOF'
# Django Settings
SECRET_KEY=your-secret-key-change-this-in-production
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database (Docker container)
DATABASE_URL=postgresql://postgres:password@db:5432/menumine_ai
USE_POSTGRES=True
DB_HOST=db
DB_PORT=5432
DB_NAME=menumine_ai
DB_USER=postgres
DB_PASSWORD=password

# Redis (Docker container)
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# Frontend URL
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:80

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@menumine.ai

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# AI Services
GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=your-gemini-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Sentry (Error Tracking)
SENTRY_DSN=your-sentry-dsn-here
SENTRY_ENVIRONMENT=development

# Security
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://localhost:80
EOF
```

### 2. Create Frontend `.env` File (Optional)

```bash
cd frontend
cat > .env << 'EOF'
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id
REACT_APP_SENTRY_ENABLED=false
EOF
```

---

## 🚀 Basic Docker Commands

### Essential Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `docker ps` | List running containers | `docker ps` |
| `docker ps -a` | List all containers (including stopped) | `docker ps -a` |
| `docker images` | List all images | `docker images` |
| `docker logs <container>` | View container logs | `docker logs menumine_backend` |
| `docker exec -it <container> <command>` | Execute command in container | `docker exec -it menumine_backend bash` |
| `docker stop <container>` | Stop a running container | `docker stop menumine_backend` |
| `docker rm <container>` | Remove a stopped container | `docker rm menumine_backend` |
| `docker rmi <image>` | Remove an image | `docker rmi menumine_backend:latest` |

### Docker Compose Commands

| Command | Description | Example |
|---------|-------------|---------|
| `docker compose up` | Start all services | `docker compose up` |
| `docker compose up -d` | Start services in background | `docker compose up -d` |
| `docker compose down` | Stop and remove containers | `docker compose down` |
| `docker compose build` | Build/rebuild images | `docker compose build` |
| `docker compose logs` | View logs from all services | `docker compose logs -f` |
| `docker compose restart` | Restart services | `docker compose restart` |
| `docker compose ps` | List running services | `docker compose ps` |
| `docker compose exec` | Execute command in service | `docker compose exec backend bash` |

---

## 💻 Development Workflow

### 1. First Time Setup

```bash
# Navigate to project root
cd MenuMind_AI

# Build and start all services
docker compose up --build

# Or start in background (detached mode)
docker compose up -d --build
```

**What happens:**
- ✅ PostgreSQL database starts on port 5432
- ✅ Redis cache starts on port 6379
- ✅ Backend builds and starts on port 8000
- ✅ Frontend builds and starts on port 3000
- ✅ Migrations run automatically
- ✅ Services connect via Docker network

### 2. Daily Development Workflow

```bash
# Start all services (morning)
docker compose up -d

# View logs in real-time
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop all services (end of day)
docker compose down
```

### 3. Making Code Changes

**Backend Changes (Python/Django):**
```bash
# Code changes are automatically detected (volume mounted)
# If you change requirements.txt:
docker compose down
docker compose build backend
docker compose up -d

# Run migrations after model changes:
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
```

**Frontend Changes (React):**
```bash
# Code changes auto-reload (development mode)
# If you change package.json:
docker compose down
docker compose build frontend
docker compose up -d
```

### 4. Common Development Commands

```bash
# Access Django shell
docker compose exec backend python manage.py shell

# Create superuser
docker compose exec backend python manage.py createsuperuser

# Run tests
docker compose exec backend pytest
docker compose exec backend python manage.py test

# Collect static files
docker compose exec backend python manage.py collectstatic --noinput

# Access database
docker compose exec db psql -U postgres -d menumine_ai

# Access Redis CLI
docker compose exec redis redis-cli

# Check Celery worker status
docker compose exec backend celery -A menumine_ai inspect active

# View all running processes
docker compose ps
```

---

## 🏭 Production Workflow

### 1. Production Build

```bash
# Build production images
docker compose -f docker-compose.prod.yml build --no-cache

# Start production stack
docker compose -f docker-compose.prod.yml up -d

# View production logs
docker compose -f docker-compose.prod.yml logs -f
```

### 2. Production Services

The production stack includes:
- **db** - PostgreSQL 15 (port 5432)
- **redis** - Redis 7 with persistence (port 6379)
- **backend** - Django with Gunicorn (port 8000)
- **celery** - Celery worker for background tasks
- **celery-beat** - Celery scheduler for periodic tasks
- **daphne** - WebSocket server (port 8001)
- **frontend** - React app with Nginx (port 80)
- **nginx** - Reverse proxy with SSL (ports 443, 8080) [optional]

### 3. Production Commands

```bash
# Start production stack
docker compose -f docker-compose.prod.yml up -d

# View service status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f celery

# Restart specific service
docker compose -f docker-compose.prod.yml restart backend

# Scale Celery workers
docker compose -f docker-compose.prod.yml up -d --scale celery=3

# Stop production stack
docker compose -f docker-compose.prod.yml down

# Stop and remove volumes (DANGER: deletes data!)
docker compose -f docker-compose.prod.yml down -v
```

### 4. Production with Nginx (SSL)

```bash
# Start with Nginx reverse proxy
docker compose -f docker-compose.prod.yml --profile with-nginx up -d

# Place SSL certificates in nginx/ssl/ directory
# - nginx/ssl/cert.pem
# - nginx/ssl/key.pem

# View nginx logs
docker compose -f docker-compose.prod.yml logs -f nginx
```

---

## 🎛️ Container Management

### Inspect Containers

```bash
# View detailed container information
docker inspect menumine_backend

# View container resource usage
docker stats

# View container processes
docker top menumine_backend

# View container logs with timestamps
docker logs --timestamps menumine_backend

# Follow logs (like tail -f)
docker logs -f menumine_backend

# View last 100 lines
docker logs --tail 100 menumine_backend
```

### Access Container Shell

```bash
# Access backend container
docker compose exec backend bash

# Or directly:
docker exec -it menumine_backend bash

# Access as specific user
docker exec -it --user appuser menumine_backend bash

# Run single command
docker compose exec backend python manage.py showmigrations

# Access database container
docker compose exec db psql -U postgres -d menumine_ai

# Access Redis
docker compose exec redis redis-cli
```

### Container Lifecycle

```bash
# Start stopped container
docker start menumine_backend

# Stop running container
docker stop menumine_backend

# Restart container
docker restart menumine_backend

# Pause container (freeze processes)
docker pause menumine_backend
docker unpause menumine_backend

# Remove stopped container
docker rm menumine_backend

# Force remove running container
docker rm -f menumine_backend
```

---

## 🐛 Debugging & Troubleshooting

### View Logs

```bash
# All services logs
docker compose logs -f

# Specific service with timestamps
docker compose logs -f --timestamps backend

# Last 50 lines from all services
docker compose logs --tail=50

# Grep through logs
docker compose logs backend | grep ERROR
docker compose logs backend | grep -i "database"
```

### Check Service Health

```bash
# View service status
docker compose ps

# Check health status
docker inspect menumine_backend --format='{{.State.Health.Status}}'

# View health check logs
docker inspect menumine_backend --format='{{range .State.Health.Log}}{{.Output}}{{end}}'
```

### Network Debugging

```bash
# List Docker networks
docker network ls

# Inspect network
docker network inspect menumine_network

# Test connectivity between containers
docker compose exec backend ping db
docker compose exec backend ping redis

# Check if backend can connect to database
docker compose exec backend python manage.py dbshell

# Check Redis connection
docker compose exec backend python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

### Common Issues

#### Issue 1: Port Already in Use

```bash
# Check what's using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux:
sudo lsof -i :8000
sudo kill -9 <PID>

# Or change port in docker-compose.yml:
ports:
  - "8001:8000"  # Host:Container
```

#### Issue 2: Database Connection Failed

```bash
# Check if database is running
docker compose ps db

# Check database logs
docker compose logs db

# Verify connection from backend
docker compose exec backend python manage.py dbshell

# Reset database
docker compose down -v
docker compose up -d db
docker compose exec backend python manage.py migrate
```

#### Issue 3: Permission Denied

```bash
# Fix volume permissions (Linux)
sudo chown -R $USER:$USER backend/
sudo chown -R $USER:$USER frontend/

# Or rebuild with proper user
docker compose down
docker compose build --no-cache
docker compose up -d
```

#### Issue 4: Out of Memory

```bash
# Check Docker resource usage
docker stats

# Clean up unused images/containers
docker system prune -a

# Increase Docker memory limit (Docker Desktop > Settings > Resources)
```

#### Issue 5: Container Keeps Restarting

```bash
# View why container is failing
docker compose logs backend --tail=100

# Check container exit code
docker ps -a

# Disable restart to debug
docker compose up --no-start backend
docker compose start backend
docker compose logs -f backend
```

---

## 💾 Database Operations

### Backup Database

```bash
# Backup to file
docker compose exec db pg_dump -U postgres menumine_ai > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup with compression
docker compose exec db pg_dump -U postgres menumine_ai | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Backup specific tables
docker compose exec db pg_dump -U postgres -t recipes_canonicalrecipe menumine_ai > recipes_backup.sql
```

### Restore Database

```bash
# Restore from backup
cat backup.sql | docker compose exec -T db psql -U postgres -d menumine_ai

# Restore compressed backup
gunzip < backup.sql.gz | docker compose exec -T db psql -U postgres -d menumine_ai

# Drop and recreate database before restore
docker compose exec db psql -U postgres -c "DROP DATABASE menumine_ai;"
docker compose exec db psql -U postgres -c "CREATE DATABASE menumine_ai;"
cat backup.sql | docker compose exec -T db psql -U postgres -d menumine_ai
```

### Database Migrations

```bash
# Create new migration
docker compose exec backend python manage.py makemigrations

# Apply migrations
docker compose exec backend python manage.py migrate

# View migration status
docker compose exec backend python manage.py showmigrations

# Revert migration
docker compose exec backend python manage.py migrate recipes 0005_previous_migration

# Create empty migration (for data migrations)
docker compose exec backend python manage.py makemigrations --empty recipes
```

### Database Access

```bash
# PostgreSQL shell
docker compose exec db psql -U postgres -d menumine_ai

# Useful SQL commands:
# \dt              - List tables
# \d+ table_name   - Describe table
# \l               - List databases
# \du              - List users
# \q               - Quit

# Run SQL query directly
docker compose exec db psql -U postgres -d menumine_ai -c "SELECT COUNT(*) FROM recipes_canonicalrecipe;"
```

---

## 🔥 Advanced Commands

### Multi-Environment Management

```bash
# Run development and production side-by-side
docker compose -f docker-compose.yml up -d
docker compose -f docker-compose.prod.yml up -d

# Different project names to avoid conflicts
docker compose -p menumine_dev up -d
docker compose -p menumine_prod -f docker-compose.prod.yml up -d

# List all projects
docker compose ls
```

### Build Optimization

```bash
# Build with no cache (clean build)
docker compose build --no-cache

# Build specific service
docker compose build backend

# Build with progress output
docker compose build --progress=plain

# Build with specific Dockerfile
docker compose build --build-arg DOCKERFILE=Dockerfile.prod backend

# Pull latest base images before building
docker compose build --pull
```

### Container Resource Management

```bash
# Limit container resources
docker compose up -d --scale backend=2

# View resource usage
docker stats menumine_backend

# Set memory limit (in docker-compose.yml):
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect menumine_ai_postgres_data

# Backup volume
docker run --rm \
  -v menumine_ai_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volume
docker run --rm \
  -v menumine_ai_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_backup.tar.gz -C /data

# Remove unused volumes
docker volume prune

# Remove specific volume
docker volume rm menumine_ai_postgres_data
```

### Image Management

```bash
# List images
docker images

# Remove unused images
docker image prune -a

# Tag image for registry
docker tag menumine_backend:latest registry.example.com/menumine_backend:v1.0.0

# Push to registry
docker push registry.example.com/menumine_backend:v1.0.0

# Pull from registry
docker pull registry.example.com/menumine_backend:v1.0.0

# Save image to file
docker save menumine_backend:latest | gzip > menumine_backend.tar.gz

# Load image from file
docker load < menumine_backend.tar.gz
```

### Docker System Cleanup

```bash
# Remove all stopped containers
docker container prune

# Remove all unused images
docker image prune -a

# Remove all unused volumes
docker volume prune

# Remove all unused networks
docker network prune

# Remove everything (DANGER!)
docker system prune -a --volumes

# View disk usage
docker system df
```

---

## 📊 Monitoring & Performance

### Real-time Monitoring

```bash
# Watch container resources
docker stats

# Continuous logs
docker compose logs -f --tail=100

# Monitor specific metrics
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### Performance Tuning

```bash
# Check container startup time
time docker compose up -d

# View image layers
docker history menumine_backend:latest

# Analyze build cache
docker compose build --progress=plain 2>&1 | grep "CACHED"

# Profile container
docker run --rm -it menumine_backend:latest python -m cProfile manage.py test
```

---

## 🛡️ Best Practices

### 1. Development Best Practices

✅ **DO:**
- Use `docker-compose.yml` for development
- Mount code as volumes for hot-reload
- Use `.env` files for secrets
- Keep containers running in background (`-d`)
- Regularly clean up (`docker system prune`)

❌ **DON'T:**
- Run as root in containers
- Store secrets in Dockerfiles
- Use `:latest` tag in production
- Share database volumes between dev/prod

### 2. Production Best Practices

✅ **DO:**
- Use `docker-compose.prod.yml` for production
- Set specific version tags
- Use health checks
- Enable restart policies (`restart: unless-stopped`)
- Use secrets management
- Monitor container logs
- Regular backups of volumes

❌ **DON'T:**
- Use development Dockerfiles in production
- Expose unnecessary ports
- Run containers as root
- Skip health checks

### 3. Security Best Practices

```dockerfile
# Use specific versions, not 'latest'
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# Use multi-stage builds
FROM node:18-alpine AS builder
# Build stage
FROM nginx:alpine AS production
# Production stage
```

### 4. Common Workflows

**Morning Startup:**
```bash
docker compose up -d
docker compose logs -f
```

**Code Changes:**
```bash
# Backend changes - auto-reload
# Just save file and refresh

# Frontend changes - auto-reload
# Just save file and refresh

# Requirements change:
docker compose down
docker compose build backend
docker compose up -d
```

**End of Day:**
```bash
docker compose down
# Or keep running:
docker compose logs -f --tail=0 &
```

**Deploy to Server:**
```bash
# Build locally
docker compose -f docker-compose.prod.yml build

# Save images
docker save menumine_backend:latest | gzip > backend.tar.gz
docker save menumine_frontend:latest | gzip > frontend.tar.gz

# Transfer to server (scp, rsync, etc.)
scp backend.tar.gz user@server:/path/
scp frontend.tar.gz user@server:/path/

# On server:
docker load < backend.tar.gz
docker load < frontend.tar.gz
docker compose -f docker-compose.prod.yml up -d
```

---

## 🚢 Deployment to Server

### Method 1: Using Docker Compose (Recommended)

```bash
# On local machine: Build and test
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up

# Commit to Git
git add .
git commit -m "Update Docker configuration"
git push origin main

# On server: Pull and deploy
ssh user@your-server
cd /path/to/MenuMind_AI
git pull origin main
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

### Method 2: Using Docker Registry

```bash
# Tag images
docker tag menumine_backend:latest your-registry.com/menumine_backend:v1.0.0
docker tag menumine_frontend:latest your-registry.com/menumine_frontend:v1.0.0

# Push to registry
docker push your-registry.com/menumine_backend:v1.0.0
docker push your-registry.com/menumine_frontend:v1.0.0

# On server: Pull and run
docker pull your-registry.com/menumine_backend:v1.0.0
docker pull your-registry.com/menumine_frontend:v1.0.0
docker compose -f docker-compose.prod.yml up -d
```

---

## 📖 Quick Reference Card

### Daily Commands

```bash
# Start
docker compose up -d

# Logs
docker compose logs -f

# Stop
docker compose down

# Restart service
docker compose restart backend

# Rebuild
docker compose up -d --build

# Shell access
docker compose exec backend bash

# Database backup
docker compose exec db pg_dump -U postgres menumine_ai > backup.sql
```

### Emergency Commands

```bash
# Service not responding
docker compose restart backend

# Database issues
docker compose down
docker compose up -d db
docker compose exec backend python manage.py migrate

# Complete reset (DANGER: loses data!)
docker compose down -v
docker compose up -d --build

# View what's wrong
docker compose logs backend --tail=100
```

---

## 🎓 Learning Resources

- [Docker Official Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Django Docker Guide](https://docs.djangoproject.com/en/4.2/howto/deployment/)

---

## 🆘 Getting Help

```bash
# Docker help
docker --help
docker compose --help

# Command-specific help
docker compose up --help
docker logs --help

# View Docker version
docker version
docker compose version
```

---

**Made with ❤️ for MenuMind AI Team**  
Last Updated: November 2, 2025


