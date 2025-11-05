# 📋 Quick Start - Local Development Summary

## ⚡ Fast Track (For Returning Developers)

If you've already set up once:

```bash
# 1. Start PostgreSQL and Redis (if not auto-starting)
# 2. Run the launcher
start_fullstack_complete.bat
```

That's it! The script handles everything else automatically.

---

## 🆕 First Time Setup (Complete Process)

### Prerequisites
- ✅ Python 3.11
- ✅ Node.js 18+
- ✅ PostgreSQL 15+ (with database `menumindai` created)
- ✅ Redis (Docker, Scoop, or manual)

### Setup Steps

1. **Run the automated setup:**
```bash
setup_local_dev.bat
```

2. **Create admin user:**
```bash
cd backend
venv\Scripts\activate
python manage.py createsuperuser
```

3. **Edit environment file (IMPORTANT):**
   - Open `backend\.env`
   - Update `DB_PASSWORD` with your PostgreSQL password
   - Save the file

4. **Start the application:**
```bash
start_fullstack_complete.bat
```

5. **Open your browser:**
   - http://localhost:3000

---

## 📁 Key Files Created

| File | Purpose |
|------|---------|
| `ENV_TEMPLATE_BACKEND.txt` | Template for backend configuration |
| `ENV_TEMPLATE_FRONTEND.txt` | Template for frontend configuration |
| `backend\.env` | Your actual backend config (DO NOT commit) |
| `frontend\.env` | Your actual frontend config (DO NOT commit) |
| `setup_local_dev.bat` | One-time setup script |
| `start_fullstack_complete.bat` | Daily launcher (updated for local dev) |
| `LOCAL_DEVELOPMENT_GUIDE.md` | Complete documentation |

---

## 🔑 What Changed From Docker Version?

| Aspect | Docker | Local Dev |
|--------|--------|-----------|
| Database | Container | Local PostgreSQL |
| Redis | Container | Local Redis |
| Backend | Container | Python venv |
| Frontend | Container (build) | npm start (dev mode) |
| Hot Reload | ❌ No | ✅ Yes |
| Setup Time | Fast | One-time setup needed |
| Performance | Good | Faster (native) |

---

## 🛠️ Common Tasks

### Daily Development
```bash
# Start everything
start_fullstack_complete.bat

# Make your changes in VS Code/Cursor
# Frontend auto-reloads
# Backend auto-reloads

# Stop everything
stop_servers_complete.bat
```

### Database Operations
```bash
cd backend
venv\Scripts\activate

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Open Django shell
python manage.py shell

# Create new superuser
python manage.py createsuperuser
```

### Frontend Tasks
```bash
cd frontend

# Start dev server manually
npm start

# Build for production
npm run build

# Reinstall dependencies
rm -rf node_modules
npm install --legacy-peer-deps
```

### Go Back to Docker
```bash
# Commit your changes
git add .
git commit -m "Your changes"
git push

# Switch to Docker
docker compose -f docker-compose.prod.yml up -d --build
```

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't connect to DB | Check PostgreSQL running, check `backend\.env` password |
| Redis errors | Start Redis: `redis-server` or `docker start redis` |
| Port 8000 in use | `netstat -ano | findstr :8000` then kill process |
| Frontend won't start | `cd frontend && npm install --legacy-peer-deps` |
| Migrations fail | Check database exists: `psql -U postgres -c "CREATE DATABASE menumindai;"` |

---

## 📞 Need More Help?

Read the complete guide: **`LOCAL_DEVELOPMENT_GUIDE.md`**

It includes:
- Detailed troubleshooting
- Advanced configuration
- Performance tips
- Security best practices
- VS Code integration
- And much more!

---

## ✨ What You Can Do Now

Since you're running locally without Docker:

✅ **Instant changes** - No rebuild needed
✅ **Full debugging** - Use VS Code debugger, breakpoints
✅ **Database access** - Use pgAdmin, query directly
✅ **Fast iteration** - Change → Save → See results
✅ **Easy testing** - Test APIs with Postman/Thunder Client
✅ **Learn the codebase** - Explore freely without container overhead

---

**Ready to code? Run `start_fullstack_complete.bat` and start building! 🚀**

