# ⚡ Quick Start: 5 Minutes to Better Recipes

## Step 1: Get Brave API Key (2 minutes)

1. Go to: **https://brave.com/search/api/**
2. Click **"Get Started"** → Sign up
3. Copy your API key (starts with `BSA...`)

## Step 2: Get Firecrawl API Key (2 minutes)

1. Go to: **https://firecrawl.dev**
2. Click **"Get Started"** → Sign up
3. Copy your API key (starts with `fc-...`)

## Step 3: Add to .env (1 minute)

Open `backend/.env` (or create it) and add:

```bash
BRAVE_SEARCH_API_KEY=BSAxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Step 4: Test (30 seconds)

```bash
cd backend
python test_brave_firecrawl.py
```

Should see:
```
✅ PASS - Search
✅ PASS - Scrape
✅ PASS - Full Flow
🎉 ALL TESTS PASSED!
```

## Step 5: Try It! (1 minute)

Start your app:
```bash
cd backend
python manage.py runserver
```

In frontend, search for:
- **"борщ"** ✅
- **"Яблочный пирог"** ✅
- **"שקשוקה"** ✅
- **"Napoleon cake"** ✅

---

## What to Expect

### ❌ Before (DuckDuckGo)
```
Search: "Яблочный пирог"
  → Chinese sites
  → 403 Forbidden
  → No recipe found ❌
```

### ✅ After (Brave + Firecrawl)
```
Search: "Яблочный пирог"
  → allrecipes.com/russian-apple-pie
  → Clean extraction
  → Perfect recipe! ✅
```

---

## Troubleshooting

### "API key not found"
- Check `backend/.env` exists
- Check keys are spelled correctly
- Restart Django after adding keys

### "Rate limit exceeded"
- You're on free tier (500/month Firecrawl, 2500/month Brave)
- Wait until next month or upgrade

### "No recipes found"
- Try more specific query
- Check internet connection
- Check API dashboards for status

---

## Free Tier Limits

- **Brave:** 2,500 searches/month (~83/day) ✅
- **Firecrawl:** 500 scrapes/month (~16/day) ⚠️

**Good for:**
- Testing
- Small apps
- Personal use

**Need more?**
- Brave: $3 per 1,000 after free tier
- Firecrawl: $49/month for 5,000 scrapes

---

## Support

- **Full Docs:** `BRAVE_FIRECRAWL_INTEGRATION.md`
- **Setup Help:** `API_KEYS_SETUP.md`
- **Comparison:** `BEFORE_AFTER_COMPARISON.md`

---

**That's it! You now have professional recipe scraping! 🎉**

