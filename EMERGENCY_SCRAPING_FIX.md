# EMERGENCY FIX: Recipe Scraping Disaster + Filtering Adjustments

## ❌ **PROBLEM: Empty Recipes + Wikipedia Scraping**

**User Report:** "Ингредиенты не указаны" (Ingredients not specified)

**Root Causes:**
1. **Too aggressive filtering** → Removed valid ingredients like "eggs"
2. **Wikipedia scraping** → AI scraped Wikipedia page instead of recipe site

---

## ✅ **FIXES APPLIED:**

### **Fix #1: Reverted Aggressive Filtering**

**Problem:** Filtering out ingredients with unit="eggs", "potatoes", etc. was too broad

**Solution:** Reduced to only essential invalid units:
```python
invalid_units = [
    'as', 'needed', 'taste', 'quantity', 'optional'
]
# No longer filtering 'eggs', 'potatoes', etc.
```

**Why:** Unit="eggs" might be non-standard, but it's better than NO ingredients!

---

### **Fix #2: Skip Wikipedia and Non-Recipe Sites**

**Problem:** DuckDuckGo returning Wikipedia as top result for "карбонара"

**Solution:** Added skip list for non-recipe domains:
```python
skip_domains = ['wikipedia.org', 'wiki', 'amazon', 'youtube', 'pinterest']
if any(domain in url.lower() for domain in skip_domains):
    print(f"   [SKIP] Non-recipe site: {url[:60]}...")
    continue
```

**Result:** AI will skip Wikipedia and go to actual recipe sites!

---

## 📝 **Files Modified:**

1. **`backend/apps/recipes/services.py`** (Lines 244-253)
   - Reduced invalid_units list
   - Keep filtering minimal: only "as needed", "quantity", "optional"

2. **`backend/apps/recipes/services.py`** (Lines 1036-1040)
   - Skip Wikipedia, Amazon, YouTube, Pinterest
   - Only scrape actual recipe sites

---

## 🎯 **Expected Behavior Now:**

### **Search Priority:**
1. ✅ Skip Wikipedia, YouTube, Pinterest, Amazon
2. ✅ Prioritize recipe sites (allrecipes, foodnetwork, etc.)
3. ✅ Scrape actual recipe pages with ingredients and steps

### **Filtering:**
- ✅ Keep ingredients with unit="g", "kg", "ml", "pieces", "eggs", etc.
- ❌ Filter out only truly invalid: "as", "needed", "quantity", "optional"

---

## 🧪 **TEST NOW:**

**The backend auto-reloaded with the fixes!**

1. **Hard refresh browser** (Ctrl+Shift+R)
2. **Try generating "карбонара" again**
3. **Should now:**
   - ✅ Skip Wikipedia
   - ✅ Find actual recipe site
   - ✅ Show ingredients with quantities
   - ✅ Show cooking steps

---

## 📊 **What Changed:**

| Issue | Before | After |
|-------|--------|-------|
| **Filtering** | Too aggressive (filtered "eggs") | ✅ Balanced (keeps valid units) |
| **Search** | Scraped Wikipedia | ✅ Skips Wikipedia, finds recipes |
| **Result** | Empty ingredients | ✅ Full recipe with quantities |

---

## 💡 **Strategy:**

**Better to have:**
- "8 eggs eggs" (duplicate but readable)

**Than:**
- "Ингредиенты не указаны" (NO ingredients at all!)

**The user can understand "8 eggs" even if the format is weird. But empty recipes are useless!**

---

## 🚀 **Backend Status:**

✅ **Auto-reloaded** (StatReloader detected changes)  
✅ **Less aggressive filtering**  
✅ **Wikipedia skip list added**  
✅ **Ready to test**

---

**Try generating "карбонара" or any recipe again - should work now!** 🎉

