# 🎯 BishulMe WSL2 Development - Setup Instructions

## What This Setup Gives You

✅ **Instant Code Changes** - No container rebuilds  
✅ **Hot Reload** - Both frontend and backend reload automatically  
✅ **Linux Environment** - No Windows compatibility issues  
✅ **Fast Performance** - Native Linux file system  
✅ **Easy Development** - Simple scripts to start/stop  

---

## 📋 Step-by-Step Setup (One Time)

### Step 1: Install WSL2

**Open PowerShell as Administrator and run:**
```powershell
wsl --install
```

**Restart your computer when prompted.**

**After restart, open PowerShell again and run:**
```powershell
wsl --set-default-version 2
wsl --install -d Ubuntu-22.04
```

**Ubuntu will open and ask you to:**
1. Create a username (e.g., `developer`)
2. Create a password
3. Remember these!

### Step 2: Install Docker Desktop

1. Download: https://www.docker.com/products/docker-desktop/
2. Install and restart computer
3. Open Docker Desktop
4. Go to: **Settings → General**
5. ✅ Enable: **"Use the WSL 2 based engine"**
6. Go to: **Resources → WSL Integration**
7. ✅ Enable: **Ubuntu-22.04**
8. Click: **"Apply & Restart"**

### Step 3: Copy Project to WSL2 (Recommended for Speed)

**Open Ubuntu (WSL2) terminal:**
```bash
# Copy project from Windows to WSL2 (much faster!)
cp -r /mnt/c/Users/al7ko/Desktop/after-deploy/MenuMind_AI ~/MenuMind_AI

# Navigate to project
cd ~/MenuMind_AI

# Make scripts executable
chmod +x start_dev_wsl.sh stop_dev_wsl.sh
```

**Or keep on Windows drive (slower but easier for Windows tools):**
```bash
# Navigate to Windows path
cd /mnt/c/Users/al7ko/Desktop/after-deploy/MenuMind_AI

# Make scripts executable
chmod +x start_dev_wsl.sh stop_dev_wsl.sh
```

### Step 4: First-Time Setup

**In WSL2 terminal:**
```bash
# Install Docker Compose plugin if not installed
sudo apt update
sudo apt install docker-compose-plugin -y

# Verify Docker works
docker ps
# Should show empty list or running containers

# Start development environment (first time takes 2-3 minutes)
./start_dev_wsl.sh
```

**That's it!** ✅

---

## 🚀 Daily Usage

### Option A: Use Windows Script (Easiest)

**Double-click:** `open_wsl_dev.bat`

This will:
1. ✅ Check WSL2 is installed
2. ✅ Check Docker is running
3. ✅ Open WSL2 terminal
4. ✅ Start development environment
5. ✅ Show you service status

### Option B: Use WSL2 Terminal Directly

**Open Ubuntu terminal and run:**
```bash
cd ~/MenuMind_AI  # or your project path
./start_dev_wsl.sh
```

---

## 🎨 Making Changes

### Edit Code
**Use any editor you like:**
- VSCode: `code .` (in WSL2 terminal)
- Nano: `nano backend/apps/users/views.py`
- Any Windows editor (Notepad++, Sublime, etc.)

### See Changes
**Just save the file!**
- Backend changes → Django auto-reloads
- Frontend changes → React auto-reloads in browser
- **No rebuild needed!** 🎉

---

## 📱 Access Your App

**Open in browser:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Admin: http://localhost:8000/admin/

---

## 🛑 Stopping Development

### Option A: In WSL2 Terminal
```bash
./stop_dev_wsl.sh
```

### Option B: Manual
```bash
docker compose -f docker-compose.dev.yml down
```

---

## 🔧 Common Tasks

### View Logs
```bash
# All services
docker compose -f docker-compose.dev.yml logs -f

# Just backend
docker compose -f docker-compose.dev.yml logs -f backend

# Just frontend
docker compose -f docker-compose.dev.yml logs -f frontend
```

### Run Django Commands
```bash
# Shell
docker compose -f docker-compose.dev.yml exec backend python manage.py shell

# Migrations
docker compose -f docker-compose.dev.yml exec backend python manage.py migrate

# Create superuser
docker compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser
```

### Restart Service
```bash
# Restart backend
docker compose -f docker-compose.dev.yml restart backend

# Restart frontend
docker compose -f docker-compose.dev.yml restart frontend

# Restart all
docker compose -f docker-compose.dev.yml restart
```

---

## ❓ Troubleshooting

### "Docker is not running"
**Fix:** Start Docker Desktop in Windows

### "Permission denied"
**Fix:**
```bash
chmod +x start_dev_wsl.sh stop_dev_wsl.sh
```

### "Port already in use"
**Fix:**
```bash
# Find what's using the port
sudo lsof -i :8000
sudo lsof -i :3000

# Kill it
sudo kill -9 <PID>
```

### "Changes not showing"
**Fix:**
```bash
# Restart the service
docker compose -f docker-compose.dev.yml restart backend
# or
docker compose -f docker-compose.dev.yml restart frontend
```

### "Slow performance"
**Fix:** Copy project to WSL2 filesystem:
```bash
cp -r /mnt/c/Users/al7ko/Desktop/after-deploy/MenuMind_AI ~/MenuMind_AI
cd ~/MenuMind_AI
```
**Much faster!** (Windows filesystem `/mnt/c/` is slower)

---

## 📚 Additional Resources

- **Full Guide:** `WSL_DEVELOPMENT_GUIDE.md`
- **Quick Reference:** `WSL_QUICK_REFERENCE.md`

---

## 🎉 Benefits Summary

### Before (Windows + Production Containers):
- ❌ 2-3 minutes rebuild for every change
- ❌ Windows compatibility issues
- ❌ Slow iteration

### After (WSL2 + Development Containers):
- ✅ **Instant changes** (just save file)
- ✅ **Hot reload** (auto-refresh)
- ✅ **No rebuilds** needed
- ✅ **Fast** native Linux performance

---

## 🚀 Quick Start (TL;DR)

```bash
# 1. Install WSL2 + Docker Desktop (one time)
# 2. Open WSL2:
wsl

# 3. Go to project:
cd ~/MenuMind_AI

# 4. Start:
./start_dev_wsl.sh

# 5. Edit code → See changes instantly!
```

**No more waiting for rebuilds!** 🎉

---

## 📞 Need Help?

1. Check `WSL_DEVELOPMENT_GUIDE.md` for detailed instructions
2. Check `WSL_QUICK_REFERENCE.md` for command reference
3. Check troubleshooting section above

---

**Ready to code! Happy developing!** 🚀

