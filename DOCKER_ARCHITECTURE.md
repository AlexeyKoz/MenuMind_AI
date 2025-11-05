# 🏗️ MenuMind AI - Docker Architecture

## 📊 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MENUMIND AI DOCKER STACK                     │
└─────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────────┐
                    │         USER/BROWSER         │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │      DOCKER NETWORK          │
                    │   (menumine_network)         │
                    └──────────────┬───────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        │                          │                          │
┌───────▼────────┐       ┌─────────▼─────────┐      ┌───────▼────────┐
│   FRONTEND     │       │     BACKEND       │      │    DAPHNE      │
│   (React)      │       │    (Django)       │      │  (WebSocket)   │
│                │       │                   │      │                │
│  Port: 3000    │◄─────►│   Port: 8000      │◄────►│  Port: 8001    │
│  (dev)         │       │                   │      │                │
│  Port: 80      │       │  • REST API       │      │  • Real-time   │
│  (prod+nginx)  │       │  • Admin Panel    │      │  • Channels    │
└────────────────┘       │  • Authentication │      └────────────────┘
                         └─────────┬─────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
            ┌───────▼──────┐  ┌────▼────┐  ┌─────▼──────┐
            │   DATABASE   │  │  REDIS  │  │   CELERY   │
            │ (PostgreSQL) │  │ (Cache) │  │  (Worker)  │
            │              │  │         │  │            │
            │ Port: 5432   │  │Port:6379│  │ • Tasks    │
            │              │  │         │  │ • Beat     │
            │ • Recipes    │  │• Cache  │  │ • Trans.   │
            │ • Users      │  │• Queue  │  └────────────┘
            │ • Lists      │  │• WS     │
            └──────────────┘  └─────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          PERSISTENT STORAGE                          │
├─────────────────────────────────────────────────────────────────────┤
│  postgres_data/     │  redis_data/    │  backend_static/           │
│  (Database files)   │  (Cache files)  │  (Static files)            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Development vs Production

### Development Environment (docker-compose.yml)

```
┌────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT MODE                         │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌───────┐    ┌────────┐ │
│  │ Frontend │    │ Backend  │    │  DB   │    │ Redis  │ │
│  │  :3000   │    │  :8000   │    │ :5432 │    │ :6379  │ │
│  └──────────┘    └──────────┘    └───────┘    └────────┘ │
│       │               │                                     │
│       │               │                                     │
│  ┌────▼──────────────▼─────┐                              │
│  │   Volume Mounts          │                              │
│  │   (Hot Reload)           │                              │
│  │                          │                              │
│  │  ./backend:/app          │                              │
│  │  ./frontend:/app         │                              │
│  └──────────────────────────┘                              │
│                                                             │
│  Features:                                                  │
│  ✓ Hot reload (code changes apply instantly)              │
│  ✓ Debug mode enabled                                      │
│  ✓ Ports exposed to host                                   │
│  ✓ Development dependencies                                │
│  ✓ Console email backend                                   │
└────────────────────────────────────────────────────────────┘
```

### Production Environment (docker-compose.prod.yml)

```
┌────────────────────────────────────────────────────────────┐
│                    PRODUCTION MODE                          │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │               Nginx Reverse Proxy                   │  │
│  │               :443 (SSL) / :80                      │  │
│  └──────┬────────────────────────────────────┬─────────┘  │
│         │                                    │             │
│    ┌────▼─────┐    ┌──────────┐    ┌────────▼──────┐    │
│    │ Frontend │    │ Backend  │    │   Daphne      │    │
│    │ (Nginx)  │    │(Gunicorn)│    │  (WebSocket)  │    │
│    │   :80    │    │  :8000   │    │    :8001      │    │
│    └──────────┘    └────┬─────┘    └───────────────┘    │
│                         │                                 │
│    ┌─────────┐    ┌─────▼────┐    ┌─────────────┐      │
│    │  Celery │    │ Database │    │   Redis     │      │
│    │ Worker  │    │  (PG)    │    │   (Cache)   │      │
│    └────┬────┘    └──────────┘    └─────────────┘      │
│         │                                                │
│    ┌────▼─────┐                                         │
│    │  Celery  │                                         │
│    │   Beat   │                                         │
│    └──────────┘                                         │
│                                                          │
│  Features:                                               │
│  ✓ Optimized builds (multi-stage)                      │
│  ✓ Production dependencies only                         │
│  ✓ Health checks                                        │
│  ✓ Restart policies                                     │
│  ✓ Resource limits                                      │
│  ✓ Internal network (no exposed ports)                 │
│  ✓ SSL/TLS support                                      │
└──────────────────────────────────────────────────────────┘
```

---

## 📦 Container Details

### Frontend Container

```
┌──────────────────────────────────────────────────┐
│              FRONTEND CONTAINER                   │
├──────────────────────────────────────────────────┤
│  Image: menumine_frontend:latest                 │
│  Base: node:18-alpine (dev) / nginx:alpine(prod)│
│                                                   │
│  Development:                                     │
│  • npm start (port 3000)                         │
│  • Hot reload enabled                            │
│  • Source maps enabled                           │
│                                                   │
│  Production:                                      │
│  • npm run build                                 │
│  • Serve with nginx (port 80)                   │
│  • Gzip compression                              │
│  • Cache headers                                 │
│                                                   │
│  Volumes:                                         │
│  • ./frontend:/app (dev)                         │
│  • /app/build → /usr/share/nginx/html (prod)    │
└──────────────────────────────────────────────────┘
```

### Backend Container

```
┌──────────────────────────────────────────────────┐
│              BACKEND CONTAINER                    │
├──────────────────────────────────────────────────┤
│  Image: menumine_backend:latest                  │
│  Base: python:3.11-slim                          │
│                                                   │
│  Development:                                     │
│  • python manage.py runserver 0.0.0.0:8000      │
│  • Auto-reload on file changes                   │
│  • Debug toolbar enabled                         │
│                                                   │
│  Production:                                      │
│  • gunicorn menumine_ai.wsgi:application        │
│  • 4 workers                                     │
│  • Optimized settings                            │
│                                                   │
│  Services:                                        │
│  • REST API (DRF)                                │
│  • Admin Panel                                   │
│  • JWT Authentication                            │
│                                                   │
│  Volumes:                                         │
│  • ./backend:/app (dev)                          │
│  • ./backend/data:/app/data (prod)               │
│  • backend_static:/app/staticfiles (prod)        │
└──────────────────────────────────────────────────┘
```

### Database Container

```
┌──────────────────────────────────────────────────┐
│             DATABASE CONTAINER                    │
├──────────────────────────────────────────────────┤
│  Image: postgres:15-alpine                       │
│                                                   │
│  Configuration:                                   │
│  • Database: menumine_ai                         │
│  • User: postgres                                │
│  • Port: 5432                                    │
│  • Encoding: UTF-8                               │
│                                                   │
│  Tables:                                          │
│  • recipes_canonicalrecipe                       │
│  • recipes_recipetranslation                     │
│  • shopping_shoppinglist                         │
│  • users_customuser                              │
│  • nutrition_nutritionentry                      │
│  • core_iml (Ingredient DB)                      │
│  • core_cooklingo (Cooking terms)                │
│                                                   │
│  Volume:                                          │
│  • postgres_data:/var/lib/postgresql/data        │
│                                                   │
│  Health Check:                                    │
│  • pg_isready -U postgres (every 10s)           │
└──────────────────────────────────────────────────┘
```

### Redis Container

```
┌──────────────────────────────────────────────────┐
│              REDIS CONTAINER                      │
├──────────────────────────────────────────────────┤
│  Image: redis:7-alpine                           │
│                                                   │
│  Configuration:                                   │
│  • Port: 6379                                    │
│  • Persistence: AOF enabled                      │
│  • Max Memory: 256mb (prod)                      │
│  • Eviction: allkeys-lru                         │
│                                                   │
│  Usage:                                           │
│  • Celery broker (task queue)                   │
│  • Celery results backend                        │
│  • Django cache                                  │
│  • WebSocket channel layer                       │
│  • Discovery cache (tier 1)                      │
│  • Session storage                               │
│                                                   │
│  Volume:                                          │
│  • redis_data:/data                              │
│                                                   │
│  Health Check:                                    │
│  • redis-cli ping (every 10s)                   │
└──────────────────────────────────────────────────┘
```

### Celery Worker (Production Only)

```
┌──────────────────────────────────────────────────┐
│            CELERY WORKER CONTAINER                │
├──────────────────────────────────────────────────┤
│  Image: menumine_backend:latest                  │
│  Command: celery -A menumine_ai worker           │
│                                                   │
│  Tasks:                                           │
│  • Recipe translation (3-phase)                  │
│  • Discovery cache refresh                       │
│  • Email sending                                 │
│  • Nutrition calculations                        │
│  • AI recipe generation                          │
│                                                   │
│  Configuration:                                   │
│  • Concurrency: 2 workers                        │
│  • Log level: info                               │
│  • Auto-reload: disabled                         │
│                                                   │
│  Connects to:                                     │
│  • Redis (broker & results)                      │
│  • PostgreSQL (database)                         │
└──────────────────────────────────────────────────┘
```

### Celery Beat (Production Only)

```
┌──────────────────────────────────────────────────┐
│            CELERY BEAT CONTAINER                  │
├──────────────────────────────────────────────────┤
│  Image: menumine_backend:latest                  │
│  Command: celery -A menumine_ai beat             │
│                                                   │
│  Scheduled Tasks:                                 │
│  • Hourly translation scan (:00)                │
│  • Hourly cache refresh (:30)                   │
│  • Daily translation cleanup (3:00 AM)          │
│  • Weekly cache cleanup (Sunday 4:00 AM)        │
│                                                   │
│  Configuration:                                   │
│  • Schedule: celery_beat_schedule.py            │
│  • Log level: info                               │
│                                                   │
│  Connects to:                                     │
│  • Redis (broker)                                │
│  • PostgreSQL (database)                         │
└──────────────────────────────────────────────────┘
```

### Daphne (Production Only)

```
┌──────────────────────────────────────────────────┐
│             DAPHNE CONTAINER                      │
├──────────────────────────────────────────────────┤
│  Image: menumine_backend:latest                  │
│  Command: daphne menumine_ai.asgi:application    │
│                                                   │
│  Purpose:                                         │
│  • WebSocket support (Django Channels)          │
│  • Real-time shopping list updates              │
│  • User notifications                            │
│                                                   │
│  Configuration:                                   │
│  • Port: 8001                                    │
│  • Bind: 0.0.0.0:8001                           │
│                                                   │
│  WebSocket Endpoints:                             │
│  • ws://host:8001/ws/shopping/<list_id>/        │
│  • ws://host:8001/ws/user/notifications/        │
│                                                   │
│  Connects to:                                     │
│  • Redis (channel layer)                         │
│  • PostgreSQL (database)                         │
└──────────────────────────────────────────────────┘
```

---

## 🔗 Network Communication

```
┌─────────────────────────────────────────────────────────┐
│              CONTAINER COMMUNICATION                     │
└─────────────────────────────────────────────────────────┘

Frontend Container:
  └─► Backend Container (http://backend:8000)
  └─► Daphne Container (ws://daphne:8001)

Backend Container:
  └─► Database (postgresql://db:5432/menumine_ai)
  └─► Redis (redis://redis:6379/0)

Daphne Container:
  └─► Database (postgresql://db:5432/menumine_ai)
  └─► Redis (redis://redis:6379/0)

Celery Worker:
  └─► Redis (broker: redis://redis:6379/0)
  └─► Database (postgresql://db:5432/menumine_ai)

Celery Beat:
  └─► Redis (broker: redis://redis:6379/0)
  └─► Database (postgresql://db:5432/menumine_ai)

User Browser:
  └─► Frontend (http://localhost:3000 or :80)
  └─► Backend (http://localhost:8000)
  └─► Daphne (ws://localhost:8001)
```

---

## 📊 Data Flow

### Recipe Translation Flow

```
User Request (RU/HE)
       │
       ▼
┌─────────────────┐
│ Frontend (React)│
└────────┬────────┘
         │ GET /api/recipes/canonical/?lang=ru
         ▼
┌─────────────────┐
│ Backend (Django)│
└────────┬────────┘
         │ Check cache
         ▼
┌─────────────────┐       ┌──────────────┐
│ PostgreSQL DB   │◄─────►│ Redis Cache  │
│ (Tier 2)        │       │ (Tier 1)     │
└────────┬────────┘       └──────────────┘
         │ If not cached
         ▼
┌─────────────────┐
│ Celery Worker   │
│ Translation Task│
└────────┬────────┘
         │ IML + CookLingo + AI
         ▼
┌─────────────────┐
│ Save to DB      │
│ Update Cache    │
└────────┬────────┘
         │ Return translated
         ▼
┌─────────────────┐
│ Frontend Display│
└─────────────────┘
```

### Real-time Shopping List Updates

```
User A adds item
       │
       ▼
┌─────────────────┐
│ Frontend (User A│
└────────┬────────┘
         │ POST /api/shopping/items/
         ▼
┌─────────────────┐
│ Backend (Django)│
└────────┬────────┘
         │ Save to DB
         ▼
┌─────────────────┐
│ PostgreSQL      │
└────────┬────────┘
         │ WebSocket message
         ▼
┌─────────────────┐
│ Daphne + Redis  │
│ Channel Layer   │
└────────┬────────┘
         │ Broadcast to group
         ▼
┌─────────────────┐
│ All connected   │
│ users (A, B, C) │
└─────────────────┘
```

---

## 🚀 Deployment Flow

### Development to Production

```
┌──────────────────────────────────────────────────┐
│              LOCAL DEVELOPMENT                    │
├──────────────────────────────────────────────────┤
│                                                   │
│  1. Code changes in ./backend or ./frontend      │
│  2. Test with: docker compose up -d              │
│  3. Commit to Git: git push origin main          │
└───────────────────┬──────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────┐
│              GIT REPOSITORY                       │
├──────────────────────────────────────────────────┤
│  • GitHub / GitLab / Bitbucket                   │
│  • Branch: main                                  │
└───────────────────┬──────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────┐
│              SERVER (Production)                  │
├──────────────────────────────────────────────────┤
│                                                   │
│  1. git pull origin main                         │
│  2. docker compose -f docker-compose.prod.yml \  │
│     build --no-cache                             │
│  3. docker compose -f docker-compose.prod.yml \  │
│     down                                          │
│  4. docker compose -f docker-compose.prod.yml \  │
│     up -d                                         │
│                                                   │
│  Or use: ./docker-prod.sh deploy                │
└──────────────────────────────────────────────────┘
```

---

**Created:** November 2, 2025  
**Project:** MenuMind AI  
**Docker Version:** 28.4.0


