# 🚀 BishulMe - Local Development Setup Guide (Without Docker)

## Overview
This guide will help you set up BishulMe for local development on your Windows PC without using Docker. This is useful when you need to make quick changes before deploying back to the server.

---

## 📋 Prerequisites

### 1. **Python 3.11**
- Download: https://www.python.org/downloads/
- During installation, check "Add Python to PATH"
- Verify: Open CMD and run `python --version`

### 2. **Node.js 18+**
- Download: https://nodejs.org/ (LTS version)
- Verify: `node --version` and `npm --version`

### 3. **PostgreSQL 15+**
- Download: https://www.postgresql.org/download/windows/
- During installation:
  - Remember your **postgres** user password
  - Default port: **5432**
  - Install pgAdmin 4 (GUI tool)

### 4. **Redis**
Choose one of these methods:

#### Option A: Docker (Easiest)
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

#### Option B: Scoop Package Manager
```powershell
# Install Scoop first (if not installed)
iwr -useb get.scoop.sh | iex

# Install Redis
scoop install redis

# Start Redis
redis-server
```

#### Option C: Manual Installation
1. Download from: https://github.com/tporadowski/redis/releases
2. Extract to `C:\redis\`
3. Run `C:\redis\redis-server.exe`

#### Option D: WSL (Windows Subsystem for Linux)
```bash
# In WSL terminal
sudo service redis-server start
```

---

## 🔧 Initial Setup

### Step 1: Create PostgreSQL Database

Open **pgAdmin** or use **psql** command line:

```sql
CREATE DATABASE menumindai;
```

Or using command line:
```bash
psql -U postgres
# Enter your postgres password
CREATE DATABASE menumindai;
\q
```

### Step 2: Configure Backend Environment

1. Copy the template:
```bash
copy ENV_TEMPLATE_BACKEND.txt backend\.env
```

2. Edit `backend\.env` and update these values:
```env
# IMPORTANT: Update these with your values!
DB_PASSWORD=your_postgres_password_here
SECRET_KEY=your-secret-key-generate-new-one
MAILJET_SECRET_KEY=your_mailjet_secret_key_here

# Optional: Add your API keys
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### Step 3: Configure Frontend Environment

1. Copy the template:
```bash
copy ENV_TEMPLATE_FRONTEND.txt frontend\.env
```

2. The default values should work, but you can customize if needed.

### Step 4: Install Backend Dependencies

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt --use-deprecated=legacy-resolver
```

### Step 5: Install Frontend Dependencies

```bash
cd frontend
npm install --legacy-peer-deps
```

### Step 6: Run Database Migrations

```bash
cd backend
venv\Scripts\activate
python manage.py migrate
```

### Step 7: Create Admin User

```bash
python manage.py createsuperuser
# Follow prompts to create your admin account
```

### Step 8: Load Initial Data

```bash
# Load IML and CookLingo data (ingredients and cooking terms)
python import_iml_cooklingo.py

# Load legal documents
python manage.py load_bishulsheli_docs --force
```

---

## 🎯 Running the Application

### Method 1: Use the Automated Script (Recommended)

Simply double-click or run:
```bash
start_fullstack_complete.bat
```

This script will:
- ✅ Check PostgreSQL and Redis are running
- ✅ Create `.env` files if missing
- ✅ Create virtual environment if needed
- ✅ Install dependencies if needed
- ✅ Run database migrations
- ✅ Start all 5 services automatically

### Method 2: Manual Start (For Fine Control)

Open 5 separate terminal windows:

**Terminal 1 - Django Backend:**
```bash
cd backend
venv\Scripts\activate
daphne -b 0.0.0.0 -p 8000 menumine_ai.asgi:application
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
venv\Scripts\activate
celery -A menumine_ai worker -l INFO --pool=solo
```

**Terminal 3 - Celery Beat:**
```bash
cd backend
venv\Scripts\activate
celery -A menumine_ai beat -l INFO
```

**Terminal 4 - React Frontend:**
```bash
cd frontend
set BROWSER=none
npm start
```

**Terminal 5 - Redis (if not auto-starting):**
```bash
redis-server
# Or: C:\redis\redis-server.exe
# Or: docker start redis
```

---

## 🌐 Access Your Application

Once everything is running:

- **Frontend**: http://localhost:3000
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/
- **WebSocket**: ws://localhost:8000/ws/

---

## 🔄 Development Workflow

### Making Changes

**Frontend Changes:**
1. Edit files in `frontend/src/`
2. Save - React auto-reloads instantly ✅
3. Check http://localhost:3000

**Backend Changes:**
1. Edit files in `backend/`
2. Save - Daphne auto-reloads ✅
3. Check http://localhost:8000/api/

**Database Changes:**
1. Modify models in `backend/apps/*/models.py`
2. Create migrations: `python manage.py makemigrations`
3. Apply migrations: `python manage.py migrate`

### Stopping Services

Run:
```bash
stop_servers_complete.bat
```

Or manually close all terminal windows.

---

## 🛠️ Common Tasks

### Reset Database
```bash
cd backend
venv\Scripts\activate
python manage.py flush
python manage.py migrate
python manage.py createsuperuser
python import_iml_cooklingo.py
python manage.py load_bishulsheli_docs --force
```

### Rebuild Frontend
```bash
cd frontend
npm run build
```

### Clear Redis Cache
```bash
redis-cli
FLUSHALL
exit
```

### View Logs
- **Django**: Check the terminal running Daphne
- **Celery**: Check Celery Worker terminal
- **Frontend**: Check npm start terminal
- **PostgreSQL**: Check pgAdmin or PostgreSQL logs

### Test API Endpoints
```bash
# Get CSRF token
curl http://localhost:8000/api/auth/csrf/

# Test health endpoint
curl http://localhost:8000/health/

# Test with token (after login)
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/recipes/
```

---

## 🐛 Troubleshooting

### PostgreSQL Connection Failed
```
Error: connection to server at "localhost", port 5432 failed
```

**Solution:**
1. Check PostgreSQL is running (check pgAdmin)
2. Verify `backend\.env` has correct password
3. Ensure database `menumindai` exists

### Redis Connection Failed
```
Error: Error 10061 connecting to localhost:6379
```

**Solution:**
1. Start Redis: `redis-server` or `docker start redis`
2. Check port: `netstat -an | findstr :6379`

### Port Already in Use
```
Error: Address already in use: bind
```

**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F
```

### Frontend Won't Start
```
Error: Cannot find module...
```

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

### Migrations Failed
```
Error: No such table...
```

**Solution:**
```bash
cd backend
venv\Scripts\activate
python manage.py migrate --run-syncdb
```

---

## 📦 Going Back to Docker

When you're done with local development and want to deploy:

### Step 1: Commit Your Changes
```bash
git add .
git commit -m "Your changes description"
git push
```

### Step 2: Rebuild Docker Containers
```bash
# Stop local services first
stop_servers_complete.bat

# Build and run with Docker
docker compose -f docker-compose.prod.yml down -v
docker compose -f docker-compose.prod.yml up -d --build
```

### Step 3: Verify Production
```bash
docker compose -f docker-compose.prod.yml logs -f
```

---

## 💡 Tips & Best Practices

### Performance
- ✅ Use SSD for database files (faster queries)
- ✅ Keep Redis running in background
- ✅ Use `--pool=solo` for Celery on Windows
- ✅ Close unused applications to free RAM

### Security
- ⚠️ Never commit `.env` files to git
- ⚠️ Use different `SECRET_KEY` for production
- ⚠️ Don't expose admin panel to internet
- ⚠️ Keep API keys private

### Database
- 📊 Use pgAdmin for visual database management
- 📊 Backup database before major migrations
- 📊 Monitor database size (IML + CookLingo = ~50MB)

### VS Code Integration
Create `.vscode/tasks.json` for one-click start:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start BishulMe",
      "type": "shell",
      "command": ".\\start_fullstack_complete.bat",
      "problemMatcher": []
    }
  ]
}
```

Press `Ctrl+Shift+P` → "Tasks: Run Task" → "Start BishulMe"

---

## 📞 Need Help?

If you encounter issues:
1. Check this guide's Troubleshooting section
2. Review terminal logs for error messages
3. Check `backend/.env` configuration
4. Verify PostgreSQL and Redis are running

---

## ✅ Quick Checklist

Before starting development:
- [ ] PostgreSQL installed and running
- [ ] Redis installed and running
- [ ] Database `menumindai` created
- [ ] `backend\.env` configured with correct password
- [ ] `frontend\.env` exists (can be default)
- [ ] Python 3.11 installed
- [ ] Node.js 18+ installed
- [ ] Virtual environment created in `backend/venv`
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Migrations applied
- [ ] Admin user created
- [ ] IML/CookLingo data loaded

After setup is complete:
- [ ] Run `start_fullstack_complete.bat`
- [ ] Open http://localhost:3000
- [ ] Login with admin credentials
- [ ] Check all features work
- [ ] Start making your changes! 🚀

---

**Happy Coding! 🎉**

