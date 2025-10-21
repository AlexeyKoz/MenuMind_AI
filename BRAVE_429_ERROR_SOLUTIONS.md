# 🚨 Brave API 429 Error - Solutions

## Problem
You're getting **429 Too Many Requests** from Brave Search API.

## Possible Causes

### 1. API Key Not Activated Yet
- Brave API keys can take **5-10 minutes** to activate after signup
- **Solution:** Wait 10 minutes and try again

### 2. Rate Limit Hit
- Free tier: 2,500 queries/month
- **Solution:** Check your dashboard: https://api.search.brave.com/app/dashboard

### 3. Too Many Requests Too Fast
- Brave may have per-second limits
- **Solution:** We'll add rate limiting (see below)

### 4. Wrong API Key Type
- Make sure you got the **Search API** key, not another type
- **Solution:** Verify at https://api.search.brave.com/app/keys

---

## Quick Solutions

### Solution A: Use DuckDuckGo Instead (Temporary)

I kept the old DuckDuckGo code in `services.py` as a backup.

**Edit `backend/.env`:**
```bash
# Comment out Brave for now
# BRAVE_SEARCH_API_KEY=BSAoZQvNHRHGSTIFdULnrig85CHL4JS

# System will automatically fall back to DuckDuckGo
```

### Solution B: Wait for API Activation

If you just created the Brave account:
1. Wait 10-15 minutes
2. Try the test again:
```bash
cd backend
python test_brave_firecrawl.py
```

### Solution C: Check Your API Dashboard

1. Go to: https://api.search.brave.com/app/dashboard
2. Check:
   - ✅ API key is active
   - ✅ You haven't hit rate limits
   - ✅ Your plan shows "Free" or "Pro"
3. If it says "Pending", wait a few minutes

### Solution D: Regenerate API Key

If the key seems invalid:
1. Go to: https://api.search.brave.com/app/keys
2. Delete old key
3. Create new key
4. Update `.env`:
```bash
BRAVE_SEARCH_API_KEY=your_new_key_here
```

---

## Test Without Brave (Use Firecrawl Only)

Let me create a test that only uses Firecrawl:

```bash
cd backend
python -c "
from apps.recipes.brave_firecrawl_scraper import BraveFirecrawlScraper
scraper = BraveFirecrawlScraper()
print(f'Brave key: {\"Yes\" if scraper.brave_api_key else \"No\"}')
print(f'Firecrawl key: {\"Yes\" if scraper.firecrawl_api_key else \"No\"}')

# Test Firecrawl only
url = 'https://www.allrecipes.com/recipe/213937/shakshuka/'
content, success = scraper.scrape_url(url)
print(f'Firecrawl test: {\"PASS\" if success else \"FAIL\"}')
if success:
    print(f'Content length: {len(content)} chars')
"
```

---

## What I Recommend

### Option 1: Wait & Retry (Simplest)
```bash
# Wait 10-15 minutes for API activation
# Then retry:
cd backend
python test_brave_firecrawl.py
```

### Option 2: Use Hybrid Approach (Safest)
Keep both DuckDuckGo and Brave:
- Brave for quality
- DuckDuckGo as fallback if Brave fails

This is already implemented in `services.py`!

### Option 3: Brave Only When It Works
For now, you can test recipes without Brave:
1. Comment out `BRAVE_SEARCH_API_KEY` in `.env`
2. System uses DuckDuckGo automatically
3. When Brave works, uncomment the key

---

## Check API Status Now

Run this to check your Brave API status:

```bash
cd backend
python -c "
import requests
import os
from django.conf import settings

# Load Django
import django
import sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
django.setup()

api_key = settings.BRAVE_SEARCH_API_KEY
print(f'API Key (first 10 chars): {api_key[:10]}...')

# Test API
headers = {
    'Accept': 'application/json',
    'X-Subscription-Token': api_key
}
params = {'q': 'test', 'count': 1}

try:
    response = requests.get(
        'https://api.search.brave.com/res/v1/web/search',
        headers=headers,
        params=params,
        timeout=10
    )
    print(f'Status Code: {response.status_code}')
    if response.status_code == 200:
        print('✅ Brave API is working!')
    elif response.status_code == 429:
        print('❌ Rate limit hit or key not activated')
    elif response.status_code == 401:
        print('❌ Invalid API key')
    else:
        print(f'❌ Error: {response.text[:200]}')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

---

## My Recommendation

**For NOW:** Use DuckDuckGo (it works, just not as good)
**Later TODAY:** Once Brave activates, switch to it

The system will automatically use DuckDuckGo if Brave fails!

Let me know:
1. Did you just create the Brave account? (might need activation time)
2. Want to test with DuckDuckGo for now?
3. Want me to check the Brave API status?

