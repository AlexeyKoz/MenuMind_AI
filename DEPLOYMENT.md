# Production Deployment Guide

## 📋 Prerequisites

- Docker & Docker Compose installed
- Domain name (optional, for production)
- SSL certificates (optional, for HTTPS)
- API keys:
  - OpenAI API key
  - Google OAuth credentials (optional)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo>
cd menumine-ai
```

### 2. Configure Environment Variables

#### Backend (.env)
Create `backend/.env` with:

```env
# Django Core
SECRET_KEY=your-secret-key-here-generate-with-django-secret-key-generator
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,localhost

# Database
USE_POSTGRES=True
DB_NAME=menumine_ai
DB_USER=postgres
DB_PASSWORD=your-secure-database-password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# APIs
OPENAI_API_KEY=sk-your-openai-api-key-here

# Sentry
SENTRY_DSN=https://a286cf89396658abbc772704749dded4@o4510275117383680.ingest.de.sentry.io/4510275122823248
SENTRY_ENVIRONMENT=production
```

#### Frontend (.env.production)
Create `frontend/.env.production` with:

```env
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_WS_URL=wss://api.yourdomain.com
REACT_APP_SENTRY_ENABLED=true
NODE_ENV=production
```

### 3. Build and Deploy

```bash
# Build all services
docker-compose -f docker-compose.prod.yml build

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. Initialize Database

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Import IML & CookLingo data (optional)
docker-compose -f docker-compose.prod.yml exec backend python manage.py import_iml
docker-compose -f docker-compose.prod.yml exec backend python manage.py import_cooklingo
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  Nginx (80/443) │
                    └───────┬────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
  ┌─────▼──────┐   ┌────────▼────────┐   ┌─────▼──────┐
  │  Frontend  │   │    Backend      │   │   Daphne   │
  │  (React)   │   │    (Django)     │   │ (WebSocket)│
  │   Port 80  │   │   Gunicorn      │   │  Port 8001 │
  └────────────┘   └────────┬────────┘   └─────┬──────┘
                            │                   │
        ┌───────────────────┼───────────────────┘
        │                   │
  ┌─────▼──────┐   ┌────────▼────────┐
  │ PostgreSQL │   │     Redis       │
  │  Port 5432 │   │   Port 6379     │
  └────────────┘   └─────────────────┘
        │                   │
  ┌─────▼──────────────────▼──────┐
  │      Celery Workers           │
  │   (Background Tasks)          │
  └───────────────────────────────┘
```

## 🐳 Services

| Service | Container Name | Port | Description |
|---------|---------------|------|-------------|
| **Frontend** | menumine_frontend_prod | 80 | React app served by Nginx |
| **Backend** | menumine_backend_prod | 8000 | Django REST API with Gunicorn |
| **Daphne** | menumine_daphne_prod | 8001 | WebSocket server for real-time |
| **PostgreSQL** | menumine_db_prod | 5432 | Primary database |
| **Redis** | menumine_redis_prod | 6379 | Cache & message broker |
| **Celery** | menumine_celery_prod | - | Background task worker |
| **Celery Beat** | menumine_celery_beat_prod | - | Task scheduler |
| **Nginx** | menumine_nginx_prod | 443/8080 | Reverse proxy (optional) |

## 📊 Database

The production database comes **pre-populated with 83 canonical recipes**:
- 652 ingredients
- 892 preparation steps
- Multi-language support (EN, RU, HE)
- Nutrition data calculated

Users start with fresh accounts and can:
- Browse canonical recipes
- Fork and customize recipes
- Create shopping lists
- Track inventory

## 🔧 Management Commands

```bash
# Backup database
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres menumine_ai > backup.sql

# Restore database
cat backup.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres menumine_ai

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Restart services
docker-compose -f docker-compose.prod.yml restart backend
docker-compose -f docker-compose.prod.yml restart frontend

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Stop and remove volumes (⚠️ DESTRUCTIVE)
docker-compose -f docker-compose.prod.yml down -v
```

## 🔐 Security Checklist

- [ ] Change default database password
- [ ] Generate new Django SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Enable SSL/HTTPS
- [ ] Set secure cookie flags
- [ ] Configure CORS properly
- [ ] Set up firewall rules
- [ ] Enable Sentry error tracking
- [ ] Configure backup strategy

## 🌐 Domain Setup

### Option 1: Direct Access (Development/Testing)
Access via `http://localhost` (frontend) and `http://localhost:8000` (API)

### Option 2: With Domain (Production)
1. Point your domain to server IP
2. Configure SSL certificates
3. Update nginx configuration
4. Update environment variables with domain

## 📈 Monitoring

### Health Checks
- Frontend: `http://localhost/health`
- Backend: `http://localhost:8000/health/`

### Sentry Integration
Both frontend and backend send errors to Sentry:
- DSN already configured
- Set `SENTRY_ENVIRONMENT` to differentiate environments

### Logs
All services log to stdout/stderr, viewable via:
```bash
docker-compose -f docker-compose.prod.yml logs -f <service-name>
```

## 🔄 Updates & Maintenance

### Deploying Updates
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Run new migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### Database Maintenance
```bash
# Vacuum database (reclaim space)
docker-compose -f docker-compose.prod.yml exec db vacuumdb -U postgres -d menumine_ai -v

# Check database size
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -d menumine_ai -c "SELECT pg_size_pretty(pg_database_size('menumine_ai'));"
```

## ⚡ Performance Optimization

### Backend
- Gunicorn workers: 4 (adjust based on CPU cores)
- Celery workers: 2 (adjust based on workload)
- Redis maxmemory: 256MB (adjust based on usage)

### Frontend
- Gzip compression enabled
- Static asset caching (1 year)
- Service worker for PWA

### Database
- Connection pooling enabled
- Indexes on frequently queried fields
- Regular vacuuming scheduled

## 🆘 Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Common issues:
# - Database not ready → Wait for db health check
# - Missing .env file → Create from template
# - Port conflict → Check if port 8000 is free
```

### Frontend won't build
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs frontend

# Common issues:
# - Missing .env.production → Create from template
# - Build errors → Check package.json dependencies
# - Out of memory → Increase Docker memory limit
```

### Database connection failed
```bash
# Check PostgreSQL status
docker-compose -f docker-compose.prod.yml exec db pg_isready -U postgres

# Check connection from backend
docker-compose -f docker-compose.prod.yml exec backend python manage.py dbshell
```

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose -f docker-compose.prod.yml logs -f`
2. Review Sentry errors
3. Check health endpoints
4. Review this documentation

## 🎉 Success!

Once deployed, your MenuMine AI application will be running with:
- ✅ 83 canonical recipes ready for users
- ✅ Full-featured REST API
- ✅ Real-time WebSocket support
- ✅ Background task processing
- ✅ Production-grade database
- ✅ Error tracking with Sentry
- ✅ Optimized frontend performance

