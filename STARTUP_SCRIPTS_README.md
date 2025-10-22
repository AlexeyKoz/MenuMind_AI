# MenuMind AI - System Startup Scripts

Complete set of batch scripts to manage your MenuMind AI full-stack application with all Sprint 7 features.

---

## 📁 Available Scripts

### 🚀 `start_fullstack_complete.bat` (RECOMMENDED)
**Complete system launcher with all services**

Starts:
- ✅ Redis (cache + WebSocket backend)
- ✅ Django Backend (Daphne ASGI) - Port 8000
- ✅ Celery Worker (background tasks)
- ✅ Celery Beat (scheduled tasks - daily cache cleanup)
- ✅ React Frontend - Port 3000
- ✅ Test Server - Port 8001

**Features:**
- Auto-detects and starts Redis
- Verifies ASGI configuration
- Interactive menu for management
- Opens browsers on demand
- Restart/Stop options

**Usage:**
```bash
start_fullstack_complete.bat
```

---

### 🛑 `stop_servers_complete.bat`
**Stop all MenuMind services**

Gracefully stops:
- Celery Beat (scheduler)
- Celery Worker (tasks)
- Django Backend
- React Frontend
- Test Server

**Usage:**
```bash
stop_servers_complete.bat
```

---

### 🏥 `check_system_health.bat`
**System health check and diagnostics**

Checks:
- ✅ Redis connection
- ✅ Django API health
- ✅ React frontend
- ✅ Celery Worker status
- ✅ Celery Beat status
- ✅ Database connection
- ✅ Gemini API key configuration

**Usage:**
```bash
check_system_health.bat
```

---

### 🔧 `test_gemini_diagnostic.py`
**Gemini AI diagnostic tool**

Tests:
- Environment variables (API keys)
- Gemini initialization
- Simple API requests
- Complex requests (recipe generation)
- Groq fallback
- Rate limiting behavior

**Usage:**
```bash
cd backend
python test_gemini_diagnostic.py
```

---

## 🎯 Quick Start Guide

### First Time Setup:

1. **Install Prerequisites:**
   ```bash
   # Install Redis
   scoop install redis
   # OR
   choco install redis-64
   ```

2. **Setup Python Virtual Environment:**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Setup Frontend:**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure Environment:**
   - Copy `backend/.env.example` to `backend/.env`
   - Add your API keys:
     ```
     GEMINI_API_KEY=your_key_here
     GROQ_API_KEY=your_key_here
     ```

5. **Run Migrations:**
   ```bash
   cd backend
   python manage.py migrate
   ```

### Daily Usage:

1. **Start System:**
   ```bash
   start_fullstack_complete.bat
   ```

2. **Access Application:**
   - Frontend: http://localhost:3000
   - Admin: http://localhost:8000/admin/
   - API: http://localhost:8000/api/

3. **Stop System:**
   ```bash
   stop_servers_complete.bat
   ```

---

## 🔍 Troubleshooting

### Redis Not Starting?
```bash
# Check if Redis is installed
redis-cli --version

# Start manually
redis-server

# Or install via Scoop
scoop install redis
```

### Django Not Responding?
```bash
# Check health
check_system_health.bat

# View logs
# Look at the "MenuMind - Django Backend" window
```

### Celery Not Running?
```bash
# Verify Redis is running
netstat -an | findstr :6379

# Check if Celery window shows errors
# Common issue: Redis not running
```

### Frontend Not Starting?
```bash
# Check Node/npm
node --version
npm --version

# Reinstall dependencies
cd frontend
npm install
```

---

## 📊 Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Django Backend | 8000 | REST API + WebSockets |
| React Frontend | 3000 | User Interface |
| Test Server | 8001 | Test Dashboard |
| Redis | 6379 | Cache + Task Queue |

---

## 🎯 Sprint 7 Features Enabled

### Phase 1: Validation Integration
- UniversalValidator for all recipes
- 3-layer validation (IML → CookLingo → AI)
- Gemini PRIMARY, Groq FALLBACK

### Phase 2: Single-Language Translation
- Generates in user's current language
- No pre-translation overhead
- 66% API cost savings

### Phase 3: Two-Tier Caching
- Redis (Tier 1) - <1ms cache hits
- PostgreSQL (Tier 2) - <50ms
- Auto-invalidation on inventory changes
- Daily cleanup at 3:30 AM (Celery Beat)

### Phase 4: Full Recipe Generation
- Recipe matching (prevents duplicates)
- Detailed cooking steps with AI
- Integration with translation system

---

## 🔧 Advanced Configuration

### Custom Celery Schedule
Edit: `backend/apps/recipes/celery_beat_schedule.py`

### Change Ports
Edit the batch files:
- Django: Change `-p 8000` in `start_fullstack_complete.bat`
- React: Set `PORT=3001` environment variable
- Test: Change `8001` to desired port

### Redis Configuration
Create `redis.conf` in Redis directory for custom settings

---

## 📝 Maintenance Tasks

### Daily (Automated by Celery Beat):
- 3:00 AM - Translation cleanup
- 3:30 AM - Inventory cache cleanup
- 4:00 AM - Discovery cache cleanup (weekly on Sunday)

### Manual Maintenance:
```bash
# Clear all cache
redis-cli FLUSHALL

# Restart Celery after code changes
stop_servers_complete.bat
start_fullstack_complete.bat

# Database migrations
cd backend
python manage.py makemigrations
python manage.py migrate
```

---

## 🐛 Common Issues

### "ASGI import order issue detected"
**Fix:** Move consumer imports AFTER `django.setup()` in `backend/menumine_ai/asgi.py`

### "Celery won't start"
**Fix:** Ensure Redis is running first

### "Cache not working"
**Fix:** Check Redis connection: `redis-cli ping` should return `PONG`

### "Gemini API failing"
**Fix:** Run `test_gemini_diagnostic.py` to diagnose

---

## 🎯 Production Deployment

For production, use proper process managers:

**Windows:**
- Use NSSM (Non-Sucking Service Manager)
- Or Windows Task Scheduler

**Linux:**
- Use systemd service files
- Or supervisord

**Docker:**
- See `docker-compose.yml` (if available)

---

## 📞 Support

If you encounter issues:

1. Run `check_system_health.bat` first
2. Check logs in the service windows
3. Run `test_gemini_diagnostic.py` for AI issues
4. Check `.env` file is configured correctly

---

## 🎉 Enjoy Your MenuMind AI System!

All Sprint 7 features are now production-ready:
- ✅ Validated recipe generation
- ✅ Multilingual support (en/he/ru)
- ✅ Lightning-fast caching
- ✅ Background task processing
- ✅ Duplicate prevention
- ✅ Full recipe generation

**Happy cooking! 🍳**

