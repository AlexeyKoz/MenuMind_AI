# ✅ AI Provider Strategy & Search/Scraper Configuration

**Date**: October 22, 2025  
**Status**: ✅ **UPDATED & CONFIRMED**

---

## 🤖 AI Provider Strategy

### **PRIMARY: Gemini 2.0 Flash Lite**
- **Model**: `gemini-2.0-flash-lite`
- **Provider**: Google Gemini
- **Priority**: PRIMARY (tried first)
- **Strengths**: More accurate, better understanding
- **Performance**: ~2-2.5s
- **Usage**: Translation & Validation

### **FALLBACK: Groq**
- **Model**: `llama-3.3-70b-versatile`
- **Provider**: Groq
- **Priority**: FALLBACK (only if Gemini fails)
- **Strengths**: Higher free quota, faster
- **Performance**: ~1.5-2s
- **Usage**: Translation & Validation

---

## 🔄 Updated Services

### **1. Smart Translation Service** ✅
**File**: `backend/apps/core/services/smart_translation_service.py`

**Strategy**:
```python
# Try Gemini first (PRIMARY)
ai_result = self._translate_with_gemini(...)
ai_provider = 'gemini'

# Fallback to Groq if Gemini fails
if not ai_result:
    logger.warning("[TRANSLATION] Gemini failed, trying Groq fallback...")
    ai_result = self._translate_with_groq(...)
    ai_provider = 'groq'
```

**Methods**:
- `_translate_with_gemini()` - PRIMARY
- `_translate_with_groq()` - FALLBACK

---

### **2. Universal Validator** ✅
**File**: `backend/apps/core/services/universal_validator.py`

**Strategy**:
```python
# Try Gemini first
ai_result = self._call_gemini(prompt)

# Fallback to Groq if Gemini fails
if not ai_result:
    logger.warning("[VALIDATOR] Gemini failed, trying Groq...")
    ai_result = self._call_groq(prompt)
```

**Methods**:
- `_call_gemini()` - PRIMARY
- `_call_groq()` - FALLBACK

---

## 🔍 Search & Scraping Configuration

### **Search: Brave Search API** ✅
**File**: `backend/apps/recipes/brave_firecrawl_scraper.py`

**Features**:
- **API Endpoint**: `https://api.search.brave.com/res/v1/web/search`
- **API Key**: `BRAVE_SEARCH_API_KEY` (from settings)
- **Purpose**: Find recipe URLs from search queries
- **Fallback**: DuckDuckGo (if Brave API unavailable)

**Usage**:
```python
class BraveFirecrawlScraper:
    def search_recipes(self, query: str, max_results: int = 5):
        # Uses Brave Search API
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {"X-Subscription-Token": self.brave_api_key}
        # Returns list of recipe URLs
```

**Filtering**:
- ✅ Filters for recipe-related sites
- ✅ Skips video/social media (YouTube, Pinterest, etc.)
- ✅ Prioritizes known recipe sites (AllRecipes, Food Network, etc.)

---

### **Scraper: Firecrawl** ✅
**File**: `backend/apps/recipes/brave_firecrawl_scraper.py`

**Features**:
- **API Endpoint**: `https://api.firecrawl.dev/v1/scrape`
- **API Key**: `FIRECRAWL_API_KEY` (from settings)
- **Purpose**: Extract clean recipe content from URLs
- **Advantages**: Handles JavaScript, returns clean markdown
- **Fallback**: BeautifulSoup (if Firecrawl API unavailable)

**Usage**:
```python
class BraveFirecrawlScraper:
    def scrape_recipe(self, url: str):
        # Uses Firecrawl API
        api_url = "https://api.firecrawl.dev/v1/scrape"
        headers = {"Authorization": f"Bearer {self.firecrawl_api_key}"}
        # Returns clean recipe content (markdown format)
```

**Content Validation**:
- ✅ Checks for recipe keywords
- ✅ Validates minimum content length
- ✅ Extracts only relevant recipe data

---

## 🔄 Complete Workflow

### **Recipe Search & Scrape**
```
1. USER QUERY
   ↓
2. BRAVE SEARCH (PRIMARY)
   - Search API: Find recipe URLs
   - Filter: Recipe-related sites only
   - Result: List of URLs
   ↓
3. FIRECRAWL SCRAPE (PRIMARY)
   - For each URL: Scrape content
   - Clean: Markdown format
   - Validate: Recipe keywords
   - Result: Clean recipe data
   ↓
4. AI PROCESSING
   - Gemini PRIMARY: Parse & structure
   - Groq FALLBACK: If Gemini fails
   - Result: Structured recipe (RCIP 2.0)
   ↓
5. VALIDATION (Sprint 3)
   - IML: Ingredients (<1ms)
   - CookLingo: Terms (<1ms)
   - AI: Coherence (~2s, Gemini PRIMARY)
   ↓
6. TRANSLATION (Sprint 4)
   - Gemini PRIMARY: Translate
   - Groq FALLBACK: If Gemini fails
   - 3-phase workflow
   ↓
7. CACHE (Sprint 5)
   - Redis: <1ms
   - PostgreSQL: <50ms
   ↓
8. READY FOR USERS!
```

---

## ⚙️ Environment Variables Required

### **AI Providers**
```bash
# Gemini (PRIMARY)
GOOGLE_API_KEY=your_gemini_api_key_here

# Groq (FALLBACK)
GROQ_API_KEY=your_groq_api_key_here
```

### **Search & Scraping**
```bash
# Brave Search (for finding recipes)
BRAVE_SEARCH_API_KEY=your_brave_api_key_here

# Firecrawl (for scraping content)
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
```

---

## 📊 Strategy Benefits

### **Gemini PRIMARY**
✅ **Accuracy**: Better understanding of context  
✅ **Quality**: More accurate translations  
✅ **Reliability**: Stable API performance  
✅ **Features**: Advanced language understanding  

### **Groq FALLBACK**
✅ **Quota**: Higher free tier limits  
✅ **Speed**: Faster response times  
✅ **Reliability**: Fallback safety net  
✅ **Cost**: Free tier available  

### **Brave Search**
✅ **Quality**: Better than DuckDuckGo for recipes  
✅ **API**: Official API with consistent results  
✅ **Filtering**: Advanced search parameters  
✅ **Privacy**: Privacy-focused search engine  

### **Firecrawl**
✅ **JavaScript**: Handles dynamic content  
✅ **Clean**: Returns clean markdown format  
✅ **Reliable**: Better than BeautifulSoup  
✅ **Fast**: Optimized for web scraping  

---

## 🧪 Testing

### **Test AI Provider Strategy**
```bash
python backend/test_sprint4_translation.py
# Should show Gemini PRIMARY, Groq FALLBACK
```

### **Test Search & Scraping**
```python
from apps.recipes.brave_firecrawl_scraper import BraveFirecrawlScraper

scraper = BraveFirecrawlScraper()
recipes = scraper.search_and_scrape("pasta carbonara", max_results=3)
# Uses Brave Search + Firecrawl
```

---

## ✅ Configuration Summary

| Component | PRIMARY | FALLBACK | Status |
|-----------|---------|----------|--------|
| **Translation AI** | Gemini 2.0 Flash Lite | Groq (llama-3.3-70b) | ✅ Updated |
| **Validation AI** | Gemini 2.0 Flash Lite | Groq (llama-3.3-70b) | ✅ Already correct |
| **Recipe Search** | Brave Search API | DuckDuckGo | ✅ Already correct |
| **Content Scraper** | Firecrawl API | BeautifulSoup | ✅ Already correct |

---

## 🎯 Final Status

✅ **AI Provider Strategy**: Gemini PRIMARY, Groq FALLBACK  
✅ **Search Engine**: Brave Search API  
✅ **Content Scraper**: Firecrawl API  
✅ **Configuration**: All services updated  
✅ **Testing**: Ready for validation  

**System is now configured exactly as requested!** 🚀

