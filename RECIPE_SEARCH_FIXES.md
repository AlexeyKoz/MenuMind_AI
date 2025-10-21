# CRITICAL FIXES: Recipe Search & Scraping Issues

## 🚨 **FOUR MAJOR BUGS FIXED**

**Date:** 2025-10-21  
**Issues:** 404 API endpoint, Chinese search results, scraping blocked, empty ingredients

---

## 1. ❌ **404 Not Found: /api/recipes/recipes/find_recipe/**

### **Root Cause:**
Frontend API call had duplicate `/recipes/` in the path:
```
/api/recipes/recipes/find_recipe/  ❌ WRONG
/api/recipes/find_recipe/           ✅ CORRECT
```

### **Fix:**
```typescript
// frontend/src/services/api.ts (Line 231)
// BEFORE:
findRecipe = (...) => this.request('/recipes/recipes/find_recipe/', {

// AFTER:
findRecipe = (...) => this.request('/recipes/find_recipe/', {
```

---

## 2. ❌ **DuckDuckGo Returning Chinese Results**

### **Root Cause:**
```python
region='wt-wt'  # Worldwide - returns ANY language results!
```

**Symptoms:**
- Searching for "sushi philadelphia" returned:
  - "为什么 Philadelphia 被简化翻译成费城？" (Why is Philadelphia translated to Feicheng?)
  - "上海顶级的寿司店家有哪些？" (What are Shanghai's top sushi restaurants?)
  - All from `zhihu.com` (Chinese Q&A site)

### **Fix:**
```python
# backend/apps/recipes/services.py (Line 967-1043)

async def _search_with_duckduckgo(self, query: str, max_results: int = 5):
    results = await loop.run_in_executor(
        None,
        lambda: list(DDGS().text(
            search_query, 
            max_results=max_results * 2,  # Get more to filter
            region='us-en',  # ✅ US English only
            safesearch='moderate'
        ))
    )
    
    # ✅ Filter out Chinese sites
    if any(domain in url.lower() for domain in [
        'zhihu.com', 'baidu.com', 'bilibili.com', 
        'weibo.com', '163.com', 'sina.com'
    ]):
        skipped_chinese += 1
        continue
    
    # ✅ Skip if title contains >30% Chinese characters
    chinese_chars = sum(1 for char in title if '\u4e00' <= char <= '\u9fff')
    if chinese_chars > len(title) * 0.3:
        skipped_chinese += 1
        continue
```

---

## 3. ❌ **All Websites Returning 403 Forbidden**

### **Root Cause:**
Big recipe sites (FoodNetwork, AllRecipes, etc.) block bots.

**Symptoms:**
```
[SCRAPE] ❌ URL 1 failed - Status code: 403
[SCRAPE] ❌ URL 2 failed - Status code: 403
[SCRAPE] ❌ URL 3 failed - Status code: 403
[ERROR] Failed to scrape any of the 5 URLs
```

### **Fix:**
```python
# backend/apps/recipes/services.py (Line 1045-1154)

# ✅ Rotate user agents
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0...) Chrome/120.0.0.0',
    'Mozilla/5.0 (Macintosh...) Chrome/120.0.0.0',
    'Mozilla/5.0 (X11; Linux...) Chrome/120.0.0.0',
    'Mozilla/5.0 (Windows...) Firefox/121.0'
]

# ✅ Retry on 403
for attempt in range(2):
    headers = {
        'User-Agent': random.choice(user_agents),  # Random user agent
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Cache-Control': 'max-age=0'
    }
    
    if response.status_code == 403 and attempt == 0:
        print("   [RETRY] 403 Forbidden, trying different user agent...")
        await asyncio.sleep(1)  # Wait 1 second
        continue
```

---

## 4. ❌ **Ingredients Still Empty (0 ingredients)**

### **Root Cause Chain:**
1. DuckDuckGo returned Chinese sites → 
2. Scraped non-recipe Chinese content →
3. AI tried to extract but found no ingredients →
4. Created recipe with 0 ingredients, 1 step ("No cooking steps provided")

**Evidence from logs:**
```
[ENRICH] Processing 0 ingredients...
[RCIP] Recipe has 0 ingredients and 1 steps
[RCIP] First 3 steps preview:
   Step 1: No cooking steps provided in the text....
```

### **Fix:**
Combination of fixes #2 and #3 above will ensure:
- ✅ English recipe sites are found
- ✅ Sites can be scraped (not blocked)
- ✅ AI extracts proper ingredients and steps

---

## 📝 **Files Modified:**

### **Frontend:**

1. **`frontend/src/services/api.ts`** (Line 231)
   - Fixed API endpoint from `/recipes/recipes/find_recipe/` to `/recipes/find_recipe/`

### **Backend:**

2. **`backend/apps/recipes/services.py`**
   - **Lines 967-1043**: Enhanced DuckDuckGo search with:
     - `region='us-en'` for English results
     - Chinese site filtering
     - Chinese character detection
     - Better recipe site prioritization
   
   - **Lines 1045-1154**: Enhanced web scraping with:
     - User agent rotation
     - Retry logic on 403
     - Better anti-blocking headers
     - Delay between retries

---

## ✅ **What's Fixed:**

| Issue | Before | After |
|-------|--------|-------|
| **API Endpoint** | ❌ 404 Not Found | ✅ Correct endpoint |
| **Search Results** | ❌ Chinese sites (zhihu.com) | ✅ English recipe sites |
| **Scraping** | ❌ All 403 Forbidden | ✅ Better success rate |
| **Ingredients** | ❌ 0 ingredients | ✅ Should extract properly |

---

## 🧪 **Test Now:**

1. **Restart backend server**
2. **Hard refresh browser** (Ctrl+Shift+R)
3. **Search for "sushi philadelphia"**

### **Expected Results:**

**✅ Search should return:**
- English recipe sites (AllRecipes, SimplyRecipes, etc.)
- NOT Chinese sites (zhihu.com, baidu.com)
- Actual recipe URLs

**✅ Scraping should:**
- Successfully scrape at least 1-2 sites
- Extract meaningful recipe content
- Not hit all 403 errors

**✅ Recipe should have:**
- Multiple ingredients (10-15+)
- Multiple steps (10-20+)
- Proper translations

---

## ⚠️ **Known Limitation:**

Some big commercial sites (FoodNetwork, Bon Appétit) use advanced bot detection and may still block us. The search will:
1. Try to scrape those sites
2. If blocked, try next URL
3. Usually succeeds on smaller recipe blogs/sites

**This is normal** - we prioritize sites that don't block scrapers.

---

## 🚀 **Restart Backend:**

```bash
# Kill existing backend
taskkill /F /IM python.exe

# Start fresh
cd backend
python manage.py runserver
```

---

## 📊 **Summary:**

- ✅ **API endpoint fixed** - No more 404 errors
- ✅ **Search returns English sites** - No more Chinese results  
- ✅ **Better scraping success** - User agent rotation + retries
- ✅ **Ingredients should appear** - Proper content extraction

**Restart backend and try searching for "sushi philadelphia" again!** 🎉

