# MenuMind AI - Start Script Documentation

## Quick Start

Double-click `start_fullstack.bat` to launch the complete development environment.

## What Gets Started

### 1. **Redis Check** (Step 0/5)
- Verifies Redis is running on port 6379
- **Important**: Redis must be running for optimal WebSocket performance
- Falls back to in-memory channels if Redis is not available

### 2. **ASGI Configuration Check** (Step 1/5)
- Validates that Django Channels consumer imports are in correct order
- Prevents runtime crashes from misconfigured ASGI app

### 3. **Django Backend with Daphne** (Step 2/5)
- **Port**: 8000
- **Server**: Daphne ASGI server (required for WebSocket support)
- **Features**:
  - HTTP/HTTPS requests
  - WebSocket connections
  - Redis-backed channel layer
  - Django REST Framework API

### 4. **React Frontend** (Step 4/5)
- **Port**: 3000
- **Auto-reload**: Yes (hot module replacement)
- **Browser**: Opens automatically

### 5. **Test Dashboard** (Step 5/5)
- **Port**: 8001
- **Purpose**: API testing and debugging
- **File**: `test_backend.html`

---

## Infrastructure Overview

```
┌─────────────────────────────────────────┐
│         React Frontend (Port 3000)      │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Daphne ASGI Server (Port 8000)         │
│  ├─ HTTP API Endpoints                  │
│  ├─ WebSocket Endpoints                 │
│  └─ Django Admin Panel                  │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│        Redis (Port 6379)                │
│  ├─ Django Cache                        │
│  ├─ WebSocket Channel Layer             │
│  └─ Celery Message Broker               │
└─────────────────────────────────────────┘
```

---

## Endpoints

### HTTP Endpoints

| Endpoint | URL | Description |
|----------|-----|-------------|
| Frontend | http://localhost:3000 | React application |
| Backend | http://localhost:8000 | Django REST API |
| Health Check | http://localhost:8000/health/ | Server status |
| Admin Panel | http://localhost:8000/admin/ | Django admin |
| Test Dashboard | http://localhost:8001/test_backend.html | API testing |

### WebSocket Endpoints

| Endpoint | URL Pattern | Purpose |
|----------|-------------|---------|
| Shopping List | `ws://localhost:8000/ws/shopping/{list_id}/` | Real-time shopping list updates |
| User Notifications | `ws://localhost:8000/ws/user/notifications/` | User-specific notifications |

---

## Redis Requirements

### Why Redis?

Redis is **REQUIRED** for production-quality WebSocket performance:

✅ **With Redis (Recommended)**:
- Fast message routing (1-5ms latency)
- Supports multiple Daphne workers
- Horizontal scaling possible
- Messages persist across restarts
- Production-ready

⚠️ **Without Redis (Fallback)**:
- In-memory channel layer only
- Single process only (no scaling)
- Lost messages on restart
- Development only

### Starting Redis

**Windows:**
```bash
# If using WSL:
wsl sudo service redis-server start

# If using Windows Redis:
redis-server.exe
```

**Check if Redis is running:**
```bash
netstat -an | findstr :6379
```

---

## Management Options

When script runs, you have 3 options:

### Option S - Stop All Servers
- Stops all Python processes (Django)
- Stops all Node.js processes (React)
- Closes all related command windows
- Exits script

### Option R - Restart All Servers
- Stops all servers
- Waits 3 seconds
- Restarts the script
- Fresh start with all servers

### Option (Other Key) - Keep Running
- Servers continue in background
- Script exits but servers stay alive
- Use `stop_servers.bat` to stop later

---

## Troubleshooting

### Redis Not Starting

**Error**: `Redis is NOT running on port 6379`

**Solutions**:
1. Install Redis for Windows: https://redis.io/download
2. Use WSL: `wsl sudo service redis-server start`
3. Check if port 6379 is blocked by firewall
4. Continue anyway (will use in-memory fallback)

### ASGI Configuration Error

**Error**: `ASGI imports are in wrong order`

**Solution**: Edit `backend/menumine_ai/asgi.py` and ensure:
```python
# CORRECT ORDER:
django_asgi_app = get_asgi_application()  # Initialize Django FIRST

# THEN import consumers:
from apps.shopping.consumers import ShoppingListConsumer
```

### WebSocket Connection Refused

**Symptoms**:
- Browser console shows `NS_ERROR_WEBSOCKET_CONNECTION_REFUSED`
- Real-time features don't work

**Solutions**:
1. Verify Daphne is running (not `runserver`)
2. Check Redis is running
3. Clear browser cache
4. Check firewall settings

### Port Already in Use

**Error**: `Address already in use: 8000`

**Solution**:
```bash
# Stop existing servers:
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# Or use stop_servers.bat
# Then restart
```

---

## Performance Tips

### 1. Run Redis Locally
- Keeps latency low (< 1ms)
- Better than remote Redis for development

### 2. Use Multiple Workers (Production)
```bash
# Run 4 Daphne workers:
daphne -w 4 -b 0.0.0.0 -p 8000 menumine_ai.asgi:application
```

### 3. Monitor Redis
```bash
# Connect to Redis CLI:
redis-cli

# Watch real-time commands:
MONITOR

# Check memory usage:
INFO memory

# See active channels:
KEYS asgi:*
```

### 4. Enable Redis Persistence (Production)
Edit `redis.conf`:
```
appendonly yes
appendfsync everysec
```

---

## What's Running?

After successful start, you'll see **5 command windows**:

1. **Django Backend (Daphne)** - Main server
2. **React Frontend** - Development server
3. **HTTP Server** - Test page server
4. **Start Script** - This launcher (can be closed)
5. **Optional**: Redis server window (if started separately)

---

## Environment Details

### Backend Stack
- **Python**: Django 4.2.7
- **ASGI Server**: Daphne 4.1.2
- **WebSockets**: Django Channels 4.0.0
- **Cache/Channels**: Redis
- **Database**: SQLite (development)

### Frontend Stack
- **Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Webpack (via Create React App)
- **Hot Reload**: Yes

### Infrastructure
- **Cache**: Redis
- **Channel Layer**: Redis (channels-redis)
- **Message Broker**: Redis (for Celery)
- **WebSocket Protocol**: WSS/WS

---

## Advanced Usage

### Custom Redis URL

Set in `.env` file:
```env
REDIS_URL=redis://localhost:6379/0
```

### Custom Ports

Edit the script:
```batch
REM Change Django port:
daphne -b 0.0.0.0 -p 8080 ...

REM Change React port:
set PORT=3001 && npm start
```

### Production Mode

For production deployment:
1. Use `gunicorn` with `uvicorn` workers, OR
2. Use `daphne` with multiple workers:
   ```bash
   daphne -w 4 -u /tmp/daphne.sock menumine_ai.asgi:application
   ```
3. Put behind Nginx reverse proxy
4. Enable Redis persistence
5. Use PostgreSQL instead of SQLite

---

## Support

For issues or questions:
1. Check console logs in command windows
2. Check browser console (F12)
3. Verify Redis is running
4. Check `backend/logs/` directory
5. Review Django logs in Daphne window

---

## Quick Reference Commands

```bash
# Check if Redis is running
netstat -an | findstr :6379

# Stop all servers
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# Test WebSocket connection
curl http://localhost:8000/health/

# View Redis keys
redis-cli KEYS "asgi:*"

# Monitor Redis in real-time
redis-cli MONITOR
```

---

**Last Updated**: 2025-10-07
**Script Version**: 2.0 (Redis-enabled)

