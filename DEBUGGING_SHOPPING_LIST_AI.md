# Debugging: Shopping List AI Agent 500 Error

## Current Status
Getting 500 Internal Server Error but no detailed traceback visible.

## Changes Made to Help Debug

### Added Enhanced Logging

**Location:** `backend/apps/shopping/views.py` - `ai_add_items` method

**What was added:**
1. **Start marker:**
   ```python
   print("[FAST AI RECIPE] ========== START ai_add_items ==========")
   ```

2. **Request details:**
   ```python
   print(f"[FAST AI RECIPE] Query: '{query}'")
   print(f"[FAST AI RECIPE] Shopping list: {shopping_list.id}")
   ```

3. **Import tracking:**
   ```python
   print("[FAST AI RECIPE] Importing services...")
   # ... imports ...
   print("[FAST AI RECIPE] ✅ Services imported successfully")
   ```

4. **Full traceback on error:**
   ```python
   except Exception as e:
       print(f"[ERROR] Exception in ai_add_items: {e}")
       print(f"[ERROR] Full traceback:")
       traceback.print_exc()
   ```

## Next Steps

### 1. Restart Backend
```bash
# Stop current backend (Ctrl+C)
python manage.py runserver
```

### 2. Try Adding Recipe Again
- Go to shopping list
- Type a recipe name (e.g., "chicken soup")
- Click AI add

### 3. Check Backend Console
Look for these log markers:
- `[FAST AI RECIPE] ========== START ai_add_items ==========`
- `[FAST AI RECIPE] Query: '...'`
- `[FAST AI RECIPE] Importing services...`
- `[FAST AI RECIPE] ✅ Services imported successfully`

**If error occurs, you'll see:**
- `[ERROR] Exception in ai_add_items: ...`
- `[ERROR] Full traceback:` followed by detailed error

## Common Issues to Look For

### 1. Import Error
```
[ERROR] Required service not available: ...
```
**Solution:** Check if file exists and imports are correct

### 2. Groq API Key Missing
```
[FAST RECIPE] GROQ_API_KEY not found
```
**Solution:** Check `.env` file has `GROQ_API_KEY=your_key`

### 3. Database Field Error
```
Cannot resolve keyword '...' into field
```
**Solution:** Check field names match model

### 4. Async/Sync Error
```
...cannot be called from async context...
```
**Solution:** Wrap with `async_to_sync` or `sync_to_async`

## Files Changed
- ✅ `backend/apps/shopping/views.py` - Added extensive logging

## Status
✅ Ready for testing with enhanced logging

