# 🔑 API Keys Setup Instructions

## Required API Keys

### 1. Brave Search API
**Purpose:** Search for recipe URLs (replaces DuckDuckGo)

**Get your key:**
1. Visit: https://brave.com/search/api/
2. Click "Get Started" / "Sign Up"
3. Select free tier: **2,500 queries/month**
4. Verify email and get API key

**Add to `.env`:**
```bash
BRAVE_SEARCH_API_KEY=BSAxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### 2. Firecrawl API
**Purpose:** Scrape recipe content (handles JavaScript, no blocking)

**Get your key:**
1. Visit: https://firecrawl.dev
2. Click "Get Started"
3. Sign up with email/GitHub
4. Select free tier: **500 scrapes/month**
5. Get API key from dashboard

**Add to `.env`:**
```bash
FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Setup Steps

### 1. Create/Update `.env` file

In `backend/` directory, create or update `.env`:

```bash
# Navigate to backend
cd backend

# Create .env if it doesn't exist
# (Windows)
type nul > .env

# (Linux/Mac)
touch .env
```

### 2. Add API Keys

Open `backend/.env` and add:

```bash
# Existing keys (keep them)
GROQ_API_KEY=your_existing_groq_key
GEMINI_API_KEY=your_existing_gemini_key

# NEW: Add these lines
BRAVE_SEARCH_API_KEY=your_brave_key_here
FIRECRAWL_API_KEY=your_firecrawl_key_here
```

### 3. Test Integration

```bash
cd backend
python test_brave_firecrawl.py
```

**Expected output:**
```
🔥 BRAVE + FIRECRAWL INTEGRATION TEST
=======================================

TEST 1: Brave Search
[OK] API key found
[SUCCESS] Found 3 URLs

TEST 2: Firecrawl Scraping
[OK] API key found
[SUCCESS] Scraped 3542 characters

TEST 3: Full Search + Scrape Flow
[SUCCESS] Got 2 complete recipes

🎉 ALL TESTS PASSED!
```

---

## API Limits & Pricing

### Brave Search
- **Free:** 2,500 queries/month (~83/day)
- **Paid:** $3 per 1,000 queries after free tier
- **Good for:** Small to medium apps

### Firecrawl
- **Free:** 500 scrapes/month (~16/day)
- **Paid:** $49/month for 5,000 scrapes
- **Good for:** Testing, may need upgrade for production

### Estimated Usage
- Average user generates ~1-2 recipes/day
- Each generation = 1 search + 1-3 scrapes
- Free tier should handle ~300-400 recipes/month

---

## Troubleshooting

### Error: "API key not found"
```bash
# Check .env file exists
ls backend/.env

# Check keys are set
cat backend/.env | grep BRAVE
cat backend/.env | grep FIRECRAWL

# Restart Django after adding keys
```

### Error: "Rate limit exceeded"
- Brave: Wait until next month or upgrade plan
- Firecrawl: Wait or upgrade to paid plan
- Temporary: Use fewer scrapes per query

### Error: "No recipes found"
- Check internet connection
- Try different query (more specific)
- Check API dashboard for status

---

## Security Notes

⚠️ **IMPORTANT:**
- Never commit `.env` to git
- `.env` is in `.gitignore`
- Don't share API keys publicly
- Regenerate keys if exposed

---

## Support Links

- **Brave Search API Docs:** https://brave.com/search/api/docs/
- **Firecrawl Docs:** https://docs.firecrawl.dev
- **Rate Limits:** Check your API dashboard

---

**Status: Ready to use!**

After adding keys, test with:
```bash
cd backend
python test_brave_firecrawl.py
```

