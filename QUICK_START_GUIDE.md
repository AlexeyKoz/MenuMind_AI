# 🚀 MenuMind AI - Quick Start Guide (Post-Refactoring)

## ⚡ Get Up and Running in 5 Minutes

---

## 📋 Prerequisites

- ✅ Python 3.9+
- ✅ Node.js 16+
- ✅ Redis server (optional for caching)

---

## 🏃 Quick Start Steps

### 1. Backend Setup (2 minutes)

```bash
# Navigate to backend
cd backend

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install new dependencies (django-redis)
pip install django-redis==5.4.0

# Run migrations (includes all 3 migrations: initial, social features, indexes)
python manage.py migrate

# Start Django server
python manage.py runserver
```

**Expected Output:**
```
Running migrations:
  Applying recipes.0002_add_canonical_recipes_and_social_features... OK
  Applying recipes.0003_add_performance_indexes... OK
Starting development server at http://127.0.0.1:8000/
```

### 2. Frontend Setup (1 minute)

```bash
# Navigate to frontend (in new terminal)
cd frontend

# Start React development server
npm start
```

**Expected Output:**
```
Compiled successfully!
App running at http://localhost:3000
```

### 3. Access the Application (30 seconds)

Open your browser to:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/api
- **Admin:** http://localhost:8000/admin

### 4. Test New Features (1.5 minutes)

1. **Login** with your existing account
2. Click **"Discover"** in navigation (new!)
3. Try **filtering** recipes by cuisine or diet
4. **Like** a recipe (heart icon)
5. **Rate** a recipe (stars)
6. **Write a review**
7. Click **"Create Recipe"** to try the AI builder wizard

---

## 🎯 What's New? (Phase Overview)

### ✨ New Features Available NOW

| Feature | Location | What It Does |
|---------|----------|--------------|
| **Discover Page** | Nav → "Discover" | Browse ALL recipes (no duplicates!) |
| **Recipe Builder** | Discover → "Create Recipe" | 4-step AI-assisted recipe creation |
| **Like Recipes** | Recipe cards (heart icon) | Save favorites |
| **Rate Recipes** | Recipe cards (stars) | 5-star rating system |
| **Write Reviews** | Recipe detail page | Share your thoughts |
| **Advanced Filters** | Discover page | Cuisine, difficulty, diet labels |
| **Smart Sorting** | Discover page | Popular, top rated, most cooked |

---

## 🛠️ Optional: Enable Full Optimization (5-10 minutes)

Want caching & background tasks? Follow these steps:

### A. Start Redis (for caching)

**Windows (WSL):**
```bash
wsl sudo service redis-server start
```

**Mac:**
```bash
brew services start redis
```

**Linux:**
```bash
sudo systemctl start redis
```

**Verify Redis:**
```bash
redis-cli ping
# Should return: PONG
```

### B. Configure Django Settings

Add to `backend/menumine_ai/settings.py`:

```python
# Add after existing DATABASES config
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'KEY_PREFIX': 'menumine',
        'TIMEOUT': 300,
    }
}

# Add after existing config
REST_FRAMEWORK = {
    # ... keep existing settings ...
    
    # Add throttle rates
    'DEFAULT_THROTTLE_RATES': {
        'review': '5/hour',
        'review_daily': '20/day',
        'like': '100/hour',
        'rating': '50/hour',
        'recipe_builder': '10/hour',
        'recipe_builder_daily': '30/day',
        'recipe_search': '20/hour',
        'recipe_search_daily': '100/day',
        'mark_helpful': '50/hour',
    },
}
```

### C. Start Celery (optional - for background tasks)

**Terminal 3:**
```bash
cd backend
celery -A menumine_ai worker --loglevel=info
```

**Terminal 4:**
```bash
cd backend
celery -A menumine_ai beat --loglevel=info
```

---

## 🧪 Quick Testing Checklist

### Test Recipe Discovery
- [ ] Navigate to "Discover"
- [ ] Filter by cuisine (e.g., Italian)
- [ ] Sort by "Top Rated"
- [ ] Click a recipe card

### Test Recipe Builder
- [ ] Click "Create Recipe" button
- [ ] Enter recipe name
- [ ] Add ingredients
- [ ] Describe cooking steps
- [ ] Submit and see your recipe!

### Test Social Features
- [ ] Like a recipe (heart icon)
- [ ] Rate with 5 stars
- [ ] Write a review
- [ ] Mark someone's review as helpful

### Test Deduplication
- [ ] Search for "spaghetti carbonara" (AI search)
- [ ] Note the recipe created
- [ ] Search again for "carbonara pasta"
- [ ] Verify it returns the same canonical recipe
- [ ] Check "My Recipes" to see your personal fork

---

## 🐛 Troubleshooting

### Issue: "No module named 'django_redis'"
**Solution:**
```bash
pip install django-redis
```

### Issue: "Connection refused to Redis"
**Solution:** Start Redis server first:
```bash
redis-server
# OR
wsl sudo service redis-server start
```

### Issue: Migration fails
**Solution:** Check that you're in the right directory and venv is activated:
```bash
cd backend
venv\Scripts\activate  # Windows
python manage.py migrate
```

### Issue: Frontend errors on Discover page
**Solution:** Make sure backend is running:
```bash
# In backend directory
python manage.py runserver
```

---

## 📖 Need More Details?

Comprehensive documentation is available:

1. **`REFACTORING_IMPLEMENTATION_SUMMARY.md`**
   - Complete overview of all changes
   - API endpoint documentation
   - Architecture explanations

2. **`PHASE5_OPTIMIZATION_GUIDE.md`**
   - Detailed optimization setup
   - Configuration examples
   - Monitoring & troubleshooting

3. **`PROJECT_COMPLETE.md`**
   - Project completion summary
   - Deployment checklist
   - Future enhancement ideas

---

## 🎉 You're All Set!

Your MenuMind AI application now includes:

✅ **Deduplicated recipes** - No more duplicates!  
✅ **Social features** - Likes, ratings, reviews  
✅ **AI Recipe Builder** - Create recipes with AI assistance  
✅ **Advanced filtering** - Find recipes by cuisine, diet, difficulty  
✅ **Performance optimizations** - Fast and scalable  

**Enjoy your upgraded recipe management system!** 🍳👨‍🍳

---

## 💡 Pro Tips

1. **Rate Limiting:** If you get "429 Too Many Requests", wait a few minutes. This prevents spam.

2. **Caching:** First load might be slow, subsequent loads will be lightning fast (if Redis is running).

3. **Background Tasks:** Celery is optional but recommended for production. Recipe statistics update automatically in the background.

4. **Admin Panel:** Visit `/admin` to manage recipes, moderate reviews, and view system health.

---

**Questions?** Check the comprehensive guides in the project root!

**Happy Cooking! 🎊**


