# 🐳 Docker Quick Reference - MenuMind AI

> **One-page cheat sheet for common Docker commands**

---

## 🚀 Quick Start

### Windows
```bash
# Development
docker-dev.bat start

# Production
docker-prod.bat start
```

### Linux/Mac
```bash
# Make scripts executable (first time only)
chmod +x docker-dev.sh docker-prod.sh

# Development
./docker-dev.sh start

# Production
./docker-prod.sh start
```

---

## 📋 Daily Commands

### Start/Stop Services

```bash
# START - Development
docker compose up -d

# START - Production
docker compose -f docker-compose.prod.yml up -d

# STOP - Development
docker compose down

# STOP - Production
docker compose -f docker-compose.prod.yml down

# RESTART specific service
docker compose restart backend
```

### View Logs

```bash
# All services (follow mode)
docker compose logs -f

# Specific service
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend

# With timestamps
docker compose logs -f --timestamps backend
```

### Check Status

```bash
# List running containers
docker compose ps

# Detailed status
docker ps -a

# Resource usage
docker stats

# Health check
docker inspect menumine_backend --format='{{.State.Health.Status}}'
```

---

## 🔧 Container Access

### Shell Access

```bash
# Backend shell
docker compose exec backend bash

# Database shell
docker compose exec db psql -U postgres -d menumine_ai

# Redis CLI
docker compose exec redis redis-cli

# Execute single command
docker compose exec backend python manage.py showmigrations
```

### Common Backend Commands

```bash
# Django shell
docker compose exec backend python manage.py shell

# Create superuser
docker compose exec backend python manage.py createsuperuser

# Run migrations
docker compose exec backend python manage.py migrate

# Make migrations
docker compose exec backend python manage.py makemigrations

# Collect static files
docker compose exec backend python manage.py collectstatic --noinput

# Run tests
docker compose exec backend pytest
```

---

## 🔨 Build & Rebuild

```bash
# Build containers
docker compose build

# Build with no cache
docker compose build --no-cache

# Build specific service
docker compose build backend

# Rebuild and restart
docker compose up -d --build

# Full rebuild (clean)
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## 💾 Database Operations

### Backup

```bash
# Create backup
docker compose exec db pg_dump -U postgres menumine_ai > backup_$(date +%Y%m%d).sql

# Compressed backup
docker compose exec db pg_dump -U postgres menumine_ai | gzip > backup_$(date +%Y%m%d).sql.gz

# Windows PowerShell
docker compose exec db pg_dump -U postgres menumine_ai > backup.sql
```

### Restore

```bash
# Restore from backup (Linux/Mac)
cat backup.sql | docker compose exec -T db psql -U postgres -d menumine_ai

# Restore compressed (Linux/Mac)
gunzip < backup.sql.gz | docker compose exec -T db psql -U postgres -d menumine_ai

# Windows PowerShell
Get-Content backup.sql | docker compose exec -T db psql -U postgres -d menumine_ai
```

### Database Access

```bash
# Access PostgreSQL
docker compose exec db psql -U postgres -d menumine_ai

# Common SQL commands inside psql:
\dt              # List tables
\d+ table_name   # Describe table
\l               # List databases
\q               # Quit
```

---

## 🐛 Debugging

### View Logs

```bash
# Real-time logs (all services)
docker compose logs -f

# Filter by service
docker compose logs -f backend celery

# Grep logs
docker compose logs backend | grep ERROR

# Last 50 lines with timestamps
docker compose logs --tail=50 --timestamps backend
```

### Network Debugging

```bash
# Test connectivity
docker compose exec backend ping db
docker compose exec backend ping redis

# Test database connection
docker compose exec backend python manage.py dbshell

# Test Redis connection
docker compose exec redis redis-cli ping
```

### Container Inspection

```bash
# View container details
docker inspect menumine_backend

# View container processes
docker top menumine_backend

# View container logs
docker logs menumine_backend

# View container stats
docker stats menumine_backend
```

---

## 🧹 Cleanup

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes (DANGER!)
docker volume prune

# Remove everything (DANGER!)
docker system prune -a --volumes

# View disk usage
docker system df
```

---

## 🔥 Emergency Commands

### Service Not Responding

```bash
# Restart specific service
docker compose restart backend

# Force restart
docker compose stop backend
docker compose start backend

# View what's wrong
docker compose logs backend --tail=100
```

### Database Issues

```bash
# Restart database
docker compose restart db

# Check database health
docker compose exec db pg_isready -U postgres

# Reset database (DANGER: loses data!)
docker compose down -v
docker compose up -d db
docker compose exec backend python manage.py migrate
```

### Complete Reset (DANGER!)

```bash
# Stop and remove everything
docker compose down -v

# Remove all images
docker compose down --rmi all -v

# Rebuild from scratch
docker compose build --no-cache
docker compose up -d
```

---

## 📊 Monitoring

### Resource Usage

```bash
# Real-time stats
docker stats

# Specific container
docker stats menumine_backend

# Format output
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### Health Checks

```bash
# Check health
docker compose ps

# Inspect health
docker inspect menumine_backend --format='{{json .State.Health}}'

# View health logs
docker inspect menumine_backend --format='{{range .State.Health.Log}}{{.Output}}{{end}}'
```

---

## 🌐 Production-Specific

### Start Production Stack

```bash
# Start all services
docker compose -f docker-compose.prod.yml up -d

# With nginx (SSL)
docker compose -f docker-compose.prod.yml --profile with-nginx up -d

# Scale workers
docker compose -f docker-compose.prod.yml up -d --scale celery=3
```

### Production Logs

```bash
# All production logs
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend celery

# Error logs only
docker compose -f docker-compose.prod.yml logs backend | grep ERROR
```

### Production Health

```bash
# Service status
docker compose -f docker-compose.prod.yml ps

# Health checks
for service in backend celery daphne; do
  docker inspect menumine_${service}_prod --format='{{.Name}}: {{.State.Health.Status}}'
done
```

---

## 🔑 Environment Variables

### Set in docker-compose.yml

```yaml
environment:
  - DEBUG=False
  - DATABASE_URL=postgresql://postgres:password@db:5432/menumine_ai
  - REDIS_URL=redis://redis:6379/0
```

### Set in .env file (backend/)

```bash
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgresql://postgres:password@db:5432/menumine_ai
GROQ_API_KEY=your-api-key
```

### Override at runtime

```bash
# Single variable
docker compose run -e DEBUG=True backend python manage.py test

# From file
docker compose --env-file .env.production up -d
```

---

## 📦 Volume Management

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

# Remove volume (DANGER!)
docker volume rm menumine_ai_postgres_data
```

---

## 🚢 Deployment Workflow

### Local to Server

```bash
# 1. Test locally
docker compose -f docker-compose.prod.yml up -d

# 2. Commit changes
git add .
git commit -m "Update Docker configuration"
git push origin main

# 3. On server: Pull and deploy
ssh user@server
cd /path/to/MenuMind_AI
git pull origin main
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build

# 4. Check logs
docker compose -f docker-compose.prod.yml logs -f
```

---

## ⚡ Performance Tips

### Optimize Build

```bash
# Use BuildKit
DOCKER_BUILDKIT=1 docker compose build

# Parallel builds
docker compose build --parallel

# Build with progress
docker compose build --progress=plain
```

### Reduce Image Size

```dockerfile
# Use multi-stage builds
FROM python:3.11-slim AS builder
# Build dependencies
FROM python:3.11-slim AS production
# Copy only what's needed
```

### Cache Management

```bash
# Clear build cache
docker builder prune

# View cache usage
docker system df

# Keep useful cache
docker builder prune --filter "until=24h"
```

---

## 📱 Helper Scripts Usage

### Windows

```bash
# Interactive menu
docker-dev.bat

# Direct commands
docker-dev.bat start
docker-dev.bat stop
docker-dev.bat logs
docker-dev.bat shell
docker-dev.bat db

# Production
docker-prod.bat start
docker-prod.bat logs
docker-prod.bat backup
```

### Linux/Mac

```bash
# Make executable (first time)
chmod +x docker-dev.sh docker-prod.sh

# Interactive menu
./docker-dev.sh

# Direct commands
./docker-dev.sh start
./docker-dev.sh stop
./docker-dev.sh logs
./docker-dev.sh shell
./docker-dev.sh db

# Production
./docker-prod.sh start
./docker-prod.sh logs
./docker-prod.sh backup
./docker-prod.sh deploy
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port already in use | `docker compose down` then check `netstat -ano \| findstr :8000` |
| Database connection failed | `docker compose restart db` |
| Permission denied | `sudo chown -R $USER:$USER .` (Linux) |
| Out of memory | `docker system prune -a` |
| Container keeps restarting | `docker compose logs backend --tail=100` |
| Can't connect to Docker | Start Docker Desktop (Windows) or `sudo systemctl start docker` (Linux) |

---

## 📚 Resources

- Full Guide: [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
- Docker Docs: https://docs.docker.com/
- Compose Docs: https://docs.docker.com/compose/

---

**Quick Help:**
```bash
docker --help
docker compose --help
docker compose up --help
```

---

**Last Updated:** November 2, 2025


