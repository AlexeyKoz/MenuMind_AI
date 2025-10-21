# 🔥 Brave Search + Firecrawl Integration

## Overview

Upgraded recipe scraping system from DuckDuckGo → **Brave Search API + Firecrawl**

### Why the Change?

**DuckDuckGo Problems:**
- ❌ Returned irrelevant results (Chinese sites for English queries)
- ❌ No control over search quality
- ❌ Free tier limitations
- ❌ Unreliable for recipe-specific searches

**New Stack Benefits:**
- ✅ **Brave Search**: Professional search API with recipe filtering
- ✅ **Firecrawl**: AI-powered scraper that handles JavaScript
- ✅ **Clean Markdown**: Structured content extraction
- ✅ **Better Quality**: Recipe-specific prioritization

---

## Architecture

### Old Flow (DuckDuckGo)
```
User Query → DuckDuckGo → URLs → BeautifulSoup Scraping → HTML → AI Conversion
          ❌ Chinese sites  ❌ 403 Forbidden    ❌ Messy
```

### New Flow (Brave + Firecrawl)
```
User Query → Brave Search API → Recipe URLs → Firecrawl API → Clean Markdown → AI Conversion
          ✅ Filtered         ✅ No blocking      ✅ Structured
```

---

## Setup

### 1. Get API Keys

**Brave Search API:**
1. Go to: https://brave.com/search/api/
2. Sign up for free tier (2,500 queries/month)
3. Get your API key

**Firecrawl API:**
1. Go to: https://firecrawl.dev
2. Sign up for free tier (500 scrapes/month)
3. Get your API key

### 2. Add to Environment

Create or update `backend/.env`:

```bash
# Search & Scraping APIs
BRAVE_SEARCH_API_KEY=your_brave_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
```

### 3. Install Dependencies

```bash
cd backend
pip install requests>=2.31.0
```

*(already in requirements.txt)*

---

## Files Changed

### 1. **backend/menumine_ai/settings.py**
- Added `BRAVE_SEARCH_API_KEY`
- Added `FIRECRAWL_API_KEY`

### 2. **backend/apps/recipes/brave_firecrawl_scraper.py** ✨ NEW
- `BraveFirecrawlScraper` class
- `search_recipes()`: Brave Search API integration
- `scrape_url()`: Firecrawl API integration
- `search_and_scrape()`: Combined flow

### 3. **backend/apps/recipes/services.py**
- Replaced `_search_recipes()` with `_search_and_scrape_recipes()`
- Updated `process_recipe_query()` to use new scraper
- Removed old DuckDuckGo/BeautifulSoup code

### 4. **backend/requirements.txt**
- Added `requests>=2.31.0` for API calls

---

## How It Works

### Brave Search
```python
# Search for recipe URLs
url = "https://api.search.brave.com/res/v1/web/search"
headers = {"X-Subscription-Token": BRAVE_API_KEY}
params = {"q": "beef stew recipe step by step", "count": 10}
```

**Filtering Logic:**
- ✅ Prioritizes: `recipe`, `cooking`, `food`, `allrecipes`, `foodnetwork`
- ❌ Skips: `youtube`, `pinterest`, `wikipedia`, `amazon`, `zhihu.com`

### Firecrawl Scraping
```python
# Scrape clean content
url = "https://api.firecrawl.dev/v1/scrape"
headers = {"Authorization": f"Bearer {FIRECRAWL_API_KEY}"}
payload = {
    "url": recipe_url,
    "formats": ["markdown"],
    "onlyMainContent": True,
    "waitFor": 2000  # Wait for JavaScript
}
```

**Output:**
- Clean markdown format
- Main content only (no ads/navigation)
- JavaScript-rendered content

---

## Usage Example

### In Code
```python
from apps.recipes.brave_firecrawl_scraper import search_and_scrape_recipe

# Quick search & scrape
recipes = search_and_scrape_recipe("beef stew", max_results=3)

for recipe in recipes:
    print(f"URL: {recipe['url']}")
    print(f"Content: {recipe['content'][:200]}...")
```

### From Agent Service
```python
# Automatically used in RecipeAgentService
agent = RecipeAgentService()
success, data, msg = await agent.process_recipe_query(
    user_query="borsch",
    user=user,
    user_preferences={'language': 'ru'}
)
```

---

## API Limits

### Brave Search (Free Tier)
- **2,500 queries/month**
- ~83 queries/day
- Sufficient for most usage

### Firecrawl (Free Tier)
- **500 scrapes/month**
- ~16 scrapes/day
- May need upgrade for heavy usage

**Cost Estimate (Paid):**
- Brave: $3/1000 queries after free tier
- Firecrawl: $49/month for 5,000 scrapes

---

## Error Handling

### Brave Search Fails
```python
if not self.brave_api_key:
    logger.error("[BRAVE] Cannot search - API key missing")
    return []
```

### Firecrawl Fails
```python
if not data.get('success'):
    logger.error(f"[FIRECRAWL] Scraping failed: {data.get('error')}")
    return None, False
```

### Fallback Strategy
1. Try up to 3 recipe URLs from Brave
2. If all fail, return error to user
3. User can retry with different query

---

## Testing

### Manual Test
```bash
cd backend
python manage.py shell
```

```python
from apps.recipes.brave_firecrawl_scraper import search_and_scrape_recipe

# Test search & scrape
recipes = search_and_scrape_recipe("shakshuka")
print(f"Found {len(recipes)} recipes")

for i, recipe in enumerate(recipes, 1):
    print(f"\n{i}. {recipe['url']}")
    print(f"   Content length: {len(recipe['content'])} chars")
```

### Test Recipe Generation
```bash
# Start backend
cd backend
python manage.py runserver

# In frontend, search for:
- "борщ" (Borscht)
- "шакшука" (Shakshuka)
- "Napoleon cake"
```

---

## Advantages

### 1. **Better Search Quality**
- Recipe-specific filtering
- English-prioritized results
- No Chinese/Wikipedia noise

### 2. **Reliable Scraping**
- No 403 Forbidden errors
- Handles JavaScript-heavy sites
- Clean, structured output

### 3. **Faster Development**
- No need to maintain scrapers
- No user-agent rotation
- No anti-blocking logic

### 4. **Better AI Conversion**
- Markdown format is easier for AI to parse
- Cleaner ingredient/step extraction
- Fewer parsing errors

---

## Monitoring

### Logs to Watch
```
[BRAVE] Searching: beef stew recipe step by step
[BRAVE] ✅ Recipe URL: https://www.foodnetwork.com/...
[BRAVE] ✅ Found 5 recipe URLs

[FIRECRAWL] Scraping: https://www.foodnetwork.com/...
[FIRECRAWL] ✅ Extracted 3542 characters

[SEARCH+SCRAPE] ✅ Got 3 recipes
```

### Common Issues
1. **API Key Missing**: Check `.env` file
2. **Rate Limit**: Upgrade API plan or reduce queries
3. **No Results**: Try more specific query

---

## Next Steps

1. ✅ Add API keys to `.env`
2. ✅ Test with common recipes
3. ✅ Monitor API usage
4. ⏳ Consider upgrading if hitting limits

---

## Rollback Plan

If something goes wrong, old code is still in `services.py`:
- `_search_with_duckduckgo()` - line ~1032
- `_search_with_brave()` (old scraping) - line ~958
- `_scrape_recipe()` - line ~1118

Can revert by changing line 481 in `process_recipe_query()`.

---

**Status: ✅ READY FOR TESTING**

Test with: `"борщ"`, `"שקשוקה"`, `"Napoleon cake"`

