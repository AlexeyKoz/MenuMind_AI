# 🚀 Quick Setup Guide

## Step 1: Get Gemini API Key (2 minutes)

1. **Go to**: https://ai.google.dev/
2. **Click**: "Get API Key in Google AI Studio"
3. **Sign in** with your Google account
4. **Click**: "Create API Key"
5. **Copy** the API key (starts with `AIza...`)

## Step 2: Add to .env (1 minute)

1. Open `backend/.env` file (create if doesn't exist)
2. Add this line:
   ```
   GEMINI_API_KEY=AIzaSy...your_key_here
   ```
3. Save the file

## Step 3: Test (5 minutes)

### ✅ Backend should already be running!

If not, start it:
```bash
cd backend
python manage.py runserver
```

### Test Russian Translation:
1. Open app in browser
2. Click language dropdown → Select **Русский**
3. Go to **Discovery** page  
4. Search: **пельмени**
5. Wait 30 seconds for generation
6. **Expected**: Recipe in Russian with translated ingredients! 🎉

### Check Console Logs:
Look for these messages (means it's working):
```
[BRAVE] Searching: пельмени recipe step by step
[ENRICH] 1/10: Mapped 'flour' → synthetic_flour
[GEMINI] Translating 10 synthetic ingredients to ru
[GEMINI] Translated: flour → мука
[TRANSLATION] ✅ Completed immediate translation to ru
```

## ⚠️ Important Notes

1. **First Recipe**: May take ~1 minute (AI processing + Gemini translation)
2. **Subsequent Recipes**: Faster due to caching
3. **Language Switching**: Auto-translates on the fly
4. **No Gemini Key**: Recipes stay in English (IML only)

## 🎯 Quick Test Checklist

- [ ] Gemini API key added to `.env`
- [ ] Backend restarted (or running)
- [ ] Generated recipe in Russian → ingredients in Russian ✅
- [ ] Switched to Hebrew → recipe updated to Hebrew ✅
- [ ] Switched to English → recipe in English ✅

## 🐛 If Something's Wrong

**Recipes still in English?**
→ Check backend logs for `[GEMINI] Initialized`

**Brave Search fails?**
→ Don't worry! It auto-falls back to DuckDuckGo

**Gemini API errors?**
→ Check your API key is correct in `.env`

---

**That's it! You're done!** 🎉

Your recipes will now translate properly to Russian, Hebrew, and English.

