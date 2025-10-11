# MenuMine AI - Startup Scripts Guide

This guide explains all the batch scripts for managing your MenuMine AI development environment.

---

## 📋 **Quick Reference**

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `start_fullstack.bat` | **Start everything** (Redis, Celery, Django, React) | Beginning of work session |
| `stop_servers.bat` | **Stop all services** | End of work session |
| `check_services.bat` | **Check status** of all services | Debugging/verification |
| `start_servers.bat` | Start only Django backend | Quick backend-only testing |

---

## 🚀 **Main Script: `start_fullstack.bat`**

### **What It Does:**
Automatically starts ALL services needed for full-stack development:

1. **Redis Server** (Port 6379) - Caching & message broker
2. **Celery Worker** - Background task processing
3. **Django Backend** (Port 8000) - API server with WebSocket support
4. **React Frontend** (Port 3000) - Web interface
5. **Test Server** (Port 8001) - API testing dashboard

### **How to Use:**
```batch
# Double-click the file or run from command line:
start_fullstack.bat
```

### **What Happens:**
- ✅ Checks if Redis is running, attempts to auto-start if not
- ✅ Starts Celery worker for background tasks (like statistics updates)
- ✅ Starts Django with Daphne ASGI server (WebSocket support)
- ✅ Starts React development server
- ✅ Opens browser automatically to frontend and test page
- ✅ Gives you options to Stop (S) or Restart (R) at the end

### **Redis Installation:**
If Redis is not installed, the script will show installation options:

**Option 1: Using Scoop (Recommended)**
```powershell
scoop install redis
```

**Option 2: Using Chocolatey**
```powershell
choco install redis-64
```

**Option 3: Manual Download**
Download from: https://github.com/tporadowski/redis/releases

**Option 4: Using WSL**
```bash
wsl sudo service redis-server start
```

---

## 🛑 **Stop Script: `stop_servers.bat`**

### **What It Does:**
Gracefully stops all running services:
- Django/Daphne backend
- Celery worker
- React frontend
- Redis server
- Test HTTP server

### **How to Use:**
```batch
# Double-click the file or run from command line:
stop_servers.bat
```

### **What Happens:**
- Kills all Python processes (Django, Celery)
- Kills all Node.js processes (React)
- Kills Redis server (if started by script)
- Frees up ports 3000, 8000, 8001, 6379

---

## 🔍 **Status Check: `check_services.bat`**

### **What It Does:**
Checks if each service is running and shows their status.

### **How to Use:**
```batch
# Double-click or run:
check_services.bat
```

### **Output Example:**
```
[1/5] Redis Server (Port 6379)
    ✅ RUNNING on port 6379

[2/5] Django Backend (Port 8000)
    ✅ RUNNING on port 8000

[3/5] Celery Worker
    ✅ RUNNING (Python process found with celery)

[4/5] React Frontend (Port 3000)
    ✅ RUNNING on port 3000

[5/5] Test HTTP Server (Port 8001)
    ✅ RUNNING on port 8001
```

---

## 🧪 **Backend Only: `start_servers.bat`**

### **What It Does:**
Starts ONLY Django backend for quick backend testing (no Redis, Celery, or React).

### **When to Use:**
- Quick API testing
- Backend development without frontend
- Debugging backend issues

### **How to Use:**
```batch
start_servers.bat
```

---

## 🏗️ **Architecture Overview**

```
┌─────────────────────────────────────────────────────┐
│                  MenuMine AI Stack                   │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────┐      ┌─────────────────────────┐  │
│  │   React     │◄────►│  Django + Daphne ASGI   │  │
│  │  Frontend   │      │    (WebSocket Support)   │  │
│  │  Port 3000  │      │      Port 8000           │  │
│  └─────────────┘      └─────────────────────────┘  │
│                                │                     │
│                                ▼                     │
│                       ┌────────────────┐            │
│                       │  Redis Server  │            │
│                       │   Port 6379    │            │
│                       │                 │            │
│                       │ • Caching      │            │
│                       │ • WebSockets   │            │
│                       │ • Celery Queue │            │
│                       └────────────────┘            │
│                                │                     │
│                                ▼                     │
│                       ┌────────────────┐            │
│                       │ Celery Worker  │            │
│                       │ (Background)   │            │
│                       │                 │            │
│                       │ • Statistics   │            │
│                       │ • AI Tasks     │            │
│                       │ • Notifications│            │
│                       └────────────────┘            │
│                                                       │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 **Troubleshooting**

### **Problem: Redis won't start**
**Solution 1:** Install Redis using Scoop:
```powershell
scoop install redis
```

**Solution 2:** Check if another service is using port 6379:
```batch
netstat -an | findstr :6379
```

**Solution 3:** The app will still work without Redis (degraded performance):
- No caching
- No background tasks
- Statistics update synchronously

### **Problem: Port already in use**
**Error:** "Address already in use" on ports 3000, 8000, 6379, or 8001

**Solution:** Run `stop_servers.bat` to free all ports, then start again.

### **Problem: Celery worker won't start**
**Solution 1:** Check if Redis is running (Celery requires Redis):
```batch
check_services.bat
```

**Solution 2:** Make sure you're in the backend directory:
```batch
cd backend
python -m celery -A menumine_ai worker -l info --pool=solo
```

### **Problem: Django crashes on startup**
**Solution:** Check the Django window for error messages. Common issues:
- Missing `.env` file in `backend/` directory
- Database migrations not applied
- Missing Python packages

**Fix:**
```batch
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```

---

## 📊 **Service Dependencies**

```
Django Backend (Required)
    ↓
Redis (Optional but recommended)
    ↓
Celery Worker (Optional - requires Redis)

React Frontend (Independent)
    ↓
Django Backend (API calls)
```

**Minimum to run:**
- Django Backend
- React Frontend

**Recommended:**
- All services (Redis + Celery for optimal performance)

---

## 🎯 **Common Workflows**

### **Full Development Session**
```batch
# Start of day
start_fullstack.bat

# Work on features...

# End of day
stop_servers.bat
```

### **Backend-Only Development**
```batch
# Start backend only
start_servers.bat

# Test API endpoints...

# Stop when done
stop_servers.bat
```

### **Quick Status Check**
```batch
check_services.bat
```

### **Restart Everything**
```batch
# Option 1: Use the restart option in start_fullstack.bat
start_fullstack.bat
# Press 'R' when prompted

# Option 2: Manual restart
stop_servers.bat
start_fullstack.bat
```

---

## 🌐 **Access URLs**

After running `start_fullstack.bat`, access your application at:

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Main application interface |
| **Backend API** | http://localhost:8000/api/ | REST API endpoints |
| **Admin Panel** | http://localhost:8000/admin/ | Django admin |
| **API Docs** | http://localhost:8000/api/docs/ | API documentation |
| **Health Check** | http://localhost:8000/health/ | Server health status |
| **Test Dashboard** | http://localhost:8001/test_backend.html | API testing interface |

### **WebSocket Endpoints:**
- Shopping Lists: `ws://localhost:8000/ws/shopping/{list_id}/`
- User Notifications: `ws://localhost:8000/ws/user/notifications/`

---

## ⚙️ **Environment Variables**

Make sure you have a `.env` file in the `backend/` directory:

```env
# Required
SECRET_KEY=your-secret-key-here
DEBUG=True

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# OpenAI (for AI features)
OPENAI_API_KEY=your-openai-api-key

# Database (optional, defaults to SQLite)
DATABASE_URL=sqlite:///db.sqlite3
```

---

## 📝 **Script Modifications**

### **Changing Redis Location**
Edit `start_fullstack.bat` and add your Redis path:

```batch
} else if exist "C:\your\custom\path\redis-server.exe" (
    echo    Found Redis in: Custom Location
    start "Redis Server" "C:\your\custom\path\redis-server.exe"
    timeout /t 3 /nobreak > nul
    echo ✅ Redis server started!
```

### **Changing Default Ports**
Edit the respective service:
- **Django:** Modify `-p 8000` in `start_fullstack.bat`
- **React:** Modify `.env` in `frontend/` directory
- **Redis:** Use `redis-server --port 6380` in startup command

---

## 🆘 **Getting Help**

If you encounter issues:

1. **Check service status:** Run `check_services.bat`
2. **View logs:** Look at the CMD windows opened by `start_fullstack.bat`
3. **Check ports:** Make sure no other apps are using ports 3000, 6379, 8000, 8001
4. **Restart fresh:** Run `stop_servers.bat` then `start_fullstack.bat`

---

## 🎉 **Summary**

- **Start everything:** `start_fullstack.bat`
- **Check status:** `check_services.bat`
- **Stop everything:** `stop_servers.bat`
- **Backend only:** `start_servers.bat`

**Happy coding! 🚀**

