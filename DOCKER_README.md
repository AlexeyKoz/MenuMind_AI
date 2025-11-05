# 🐳 Docker Scripts & Documentation

This directory contains Docker configuration files and helper scripts for MenuMind AI.

---

## 📚 Documentation

| File | Description |
|------|-------------|
| **[DOCKER_GUIDE.md](DOCKER_GUIDE.md)** | Complete Docker guide with all commands and workflows |
| **[DOCKER_CHEATSHEET.md](DOCKER_CHEATSHEET.md)** | Quick reference for daily Docker commands |

---

## 🛠️ Helper Scripts

### Windows Scripts

| Script | Description | Usage |
|--------|-------------|-------|
| **docker-dev.bat** | Development environment manager | `docker-dev.bat start` |
| **docker-prod.bat** | Production environment manager | `docker-prod.bat start` |

### Linux/Mac Scripts

| Script | Description | Usage |
|--------|-------------|-------|
| **docker-dev.sh** | Development environment manager | `./docker-dev.sh start` |
| **docker-prod.sh** | Production environment manager | `./docker-prod.sh start` |

---

## 🚀 Quick Start

### First Time Setup

**1. Install Docker:**
- Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Linux: See [DOCKER_GUIDE.md](DOCKER_GUIDE.md#prerequisites)

**2. Configure Environment:**
```bash
cd backend
cp .env.example .env
# Edit .env with your settings
```

**3. Start Services:**

**Windows:**
```bash
docker-dev.bat start
```

**Linux/Mac:**
```bash
chmod +x docker-dev.sh docker-prod.sh
./docker-dev.sh start
```

---

## 📋 Available Commands

### Development Mode

#### Interactive Menu
```bash
# Windows
docker-dev.bat

# Linux/Mac
./docker-dev.sh
```

#### Direct Commands
```bash
start     # Start all services
stop      # Stop all services
restart   # Restart all services
logs      # View logs
build     # Rebuild containers
status    # Check service status
shell     # Access backend shell
db        # Access database
clean     # Clean up Docker
```

### Production Mode

#### Interactive Menu
```bash
# Windows
docker-prod.bat

# Linux/Mac
./docker-prod.sh
```

#### Direct Commands
```bash
start     # Start production stack
stop      # Stop production stack
restart   # Restart services
logs      # View logs
build     # Rebuild containers
status    # Check service status
backup    # Backup database
health    # Check service health
deploy    # Full deployment (Linux/Mac only)
```

---

## 🌐 Services & Ports

### Development (docker-compose.yml)

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | React development server |
| Backend | 8000 | Django development server |
| Database | 5432 | PostgreSQL |
| Redis | 6379 | Redis cache |

### Production (docker-compose.prod.yml)

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 80 | React (nginx) |
| Backend | 8000 | Django (Gunicorn) |
| Daphne | 8001 | WebSocket server |
| Database | - | PostgreSQL (internal) |
| Redis | - | Redis (internal) |
| Nginx | 443, 8080 | Reverse proxy (optional) |
| Celery | - | Background tasks |
| Celery Beat | - | Scheduled tasks |

---

## 📁 Docker Configuration Files

```
MenuMind_AI/
├── docker-compose.yml              # Development configuration
├── docker-compose.prod.yml         # Production configuration
├── docker-compose.digitalocean.yml # DigitalOcean deployment
│
├── docker-dev.bat                  # Development helper (Windows)
├── docker-dev.sh                   # Development helper (Linux/Mac)
├── docker-prod.bat                 # Production helper (Windows)
├── docker-prod.sh                  # Production helper (Linux/Mac)
│
├── DOCKER_GUIDE.md                 # Complete Docker guide
├── DOCKER_CHEATSHEET.md            # Quick reference
├── DOCKER_README.md                # This file
│
├── backend/
│   ├── Dockerfile                  # Main production Dockerfile
│   ├── Dockerfile.dev             # Development Dockerfile
│   ├── Dockerfile.prod            # Multi-stage production
│   └── .env                       # Environment variables
│
├── frontend/
│   ├── Dockerfile                 # Production Dockerfile
│   ├── Dockerfile.dev             # Development Dockerfile
│   └── nginx.conf                 # Nginx configuration
│
└── nginx/
    ├── nginx.conf                 # Main nginx config
    └── default.conf               # Default site config
```

---

## 💡 Common Workflows

### Daily Development

```bash
# Morning: Start services
docker-dev.bat start  # or ./docker-dev.sh start

# Work on code (auto-reloads)

# View logs if needed
docker compose logs -f backend

# End of day: Stop services
docker-dev.bat stop  # or ./docker-dev.sh stop
```

### Making Changes

**Backend Code Changes:**
- Changes auto-reload (volume mounted)
- No restart needed

**Frontend Code Changes:**
- Changes auto-reload (development mode)
- No restart needed

**Dependencies Changed (requirements.txt or package.json):**
```bash
docker-dev.bat build  # or ./docker-dev.sh build
```

**Database Models Changed:**
```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
```

### Testing Changes

```bash
# Run tests
docker compose exec backend pytest

# Django tests
docker compose exec backend python manage.py test

# Access Django shell
docker compose exec backend python manage.py shell
```

### Deploying to Server

**Using Git (Recommended):**
```bash
# Local machine
git add .
git commit -m "Update application"
git push origin main

# On server
ssh user@your-server
cd /path/to/MenuMind_AI
git pull origin main
./docker-prod.sh deploy  # Pulls, rebuilds, restarts
```

**Manual Docker Commands:**
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
# Check Docker is running
docker --version

# View error logs
docker compose logs backend

# Try rebuilding
docker compose down
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

### Permission Issues (Linux)

```bash
# Fix file permissions
sudo chown -R $USER:$USER backend/
sudo chown -R $USER:$USER frontend/

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux
sudo lsof -i :8000
sudo kill -9 <PID>
```

### Out of Disk Space

```bash
# Clean up Docker
docker system prune -a --volumes

# View disk usage
docker system df
```

---

## 📊 Monitoring

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend
```

### Check Status

```bash
# Service status
docker compose ps

# Resource usage
docker stats

# Health checks
docker inspect menumine_backend --format='{{.State.Health.Status}}'
```

### Database Backup

```bash
# Using helper script
docker-prod.bat backup  # or ./docker-prod.sh backup

# Manual backup
docker compose exec db pg_dump -U postgres menumine_ai > backup.sql
```

---

## 🔒 Security Best Practices

1. **Never commit .env files**
   - Add to .gitignore
   - Use .env.example as template

2. **Use strong passwords**
   - Database passwords
   - Secret keys
   - API keys

3. **Keep images updated**
   ```bash
   docker compose pull
   docker compose up -d --build
   ```

4. **Regular backups**
   ```bash
   # Daily database backups
   docker-prod.bat backup
   ```

5. **Monitor logs**
   ```bash
   docker compose logs -f | grep ERROR
   ```

---

## 📚 Learn More

- **Full Guide:** [DOCKER_GUIDE.md](DOCKER_GUIDE.md) - Complete Docker documentation
- **Cheat Sheet:** [DOCKER_CHEATSHEET.md](DOCKER_CHEATSHEET.md) - Quick reference
- **Docker Docs:** https://docs.docker.com/
- **Compose Docs:** https://docs.docker.com/compose/

---

## 🆘 Getting Help

**View command help:**
```bash
docker --help
docker compose --help
docker compose up --help
```

**Script help:**
```bash
docker-dev.bat help     # or ./docker-dev.sh help
docker-prod.bat help    # or ./docker-prod.sh help
```

**Check versions:**
```bash
docker --version
docker compose version
```

---

**Made with ❤️ for MenuMind AI**  
Last Updated: November 2, 2025


