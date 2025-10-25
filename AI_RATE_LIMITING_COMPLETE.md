# AI Recipe Generation Rate Limiting - COMPLETE ✅

## Overview

Implemented comprehensive rate limiting for AI recipe generation to prevent abuse while allowing unlimited access for test users.

## Rate Limits

### For Regular Users:
- **Per-Minute Limit**: Maximum 5 recipes per minute
- **Daily Limit**: Maximum 25 recipes per day

### Exempt Users (Unlimited Access):
- `testuser1`
- `testuser2`

## Features

### 1. **Smart Rate Limiting**
- ✅ Tracks recipe generation requests per user
- ✅ Separate limits for per-minute and daily usage
- ✅ Friendly error messages with remaining time
- ✅ User exemption system for test accounts
- ✅ Cached recipes DON'T count against limits

### 2. **Database Models**

#### `AIRateLimitLog`
Tracks every AI recipe generation request:
- User who made the request
- Endpoint used (recipe_generation)
- Number of recipes generated
- Timestamp

#### `AIRateLimitSettings`
Global configuration (editable in Django Admin):
- `max_recipes_per_minute` (default: 5)
- `max_recipes_per_day` (default: 25)
- `exempted_users` (default: "testuser1,testuser2")

### 3. **Protected Endpoints**

Both recipe generation endpoints are now rate-limited:

#### `/api/ai_agents/generate_recipes/`
- Generates recipes from user preferences (Recipes page)
- Checks rate limit BEFORE generation
- Logs successful generations
- Returns rate limit stats in response

#### `/api/shopping/inventory/generate_recipes/`
- Generates recipes from inventory
- Cached responses bypass rate limits (smart!)
- Only counts NEW AI generations against limits
- Logs successful generations

### 4. **User-Friendly Error Messages**

#### Per-Minute Limit Exceeded:
```json
{
  "error": "You've reached the limit of 5 recipes per minute. Please wait 42 seconds and try again.",
  "limit_type": "minute",
  "rate_limited": true
}
```

#### Daily Limit Approaching:
```json
{
  "error": "You're close to your daily limit! You can generate 3 more recipe(s) today. Daily limit: 25 recipes. Resets in approximately 8 hour(s).",
  "limit_type": "daily",
  "rate_limited": true
}
```

#### Daily Limit Exceeded:
```json
{
  "error": "You've reached your daily limit of 25 recipes. Your limit will reset in approximately 8 hour(s). Try again tomorrow!",
  "limit_type": "daily",
  "rate_limited": true
}
```

### 5. **Rate Limit Statistics**

Successful responses include current usage stats:

```json
{
  "success": true,
  "recipes": [...],
  "rate_limit_stats": {
    "exempt": false,
    "recipes_last_minute": 3,
    "recipes_today": 12,
    "limit_per_minute": 5,
    "limit_per_day": 25,
    "remaining_today": 13
  }
}
```

For exempt users:
```json
{
  "rate_limit_stats": {
    "exempt": true,
    "recipes_last_minute": 0,
    "recipes_today": 0,
    "limit_per_minute": "unlimited",
    "limit_per_day": "unlimited"
  }
}
```

## Backend Logging

Console output shows detailed rate limit checks:

```
[RATE LIMIT] User testuser1 is EXEMPT from rate limits
[RATE LIMIT] ✅ regularuser allowed: 3/5 per minute, 12/25 today
[RATE LIMIT] 📝 Logged 3 recipe(s) for regularuser
[RATE LIMIT] ❌ regularuser exceeded per-minute limit: 6/5
[RATE LIMIT] ❌ regularuser exceeded daily limit: 26/25
```

## Admin Interface

### Django Admin `/admin/ai_agents/`

**AI Rate Limit Settings:**
- Edit global rate limits
- Update exempted users list (comma-separated)
- View last update timestamp
- Cannot delete (only one instance allowed)

**AI Rate Limit Logs:**
- View all generation requests
- Filter by user, endpoint, date
- Search by username/email
- Cannot edit or delete (audit trail)

## How It Works

### 1. Request Flow:

```
User requests recipes
    ↓
Check if user is exempt (testuser1, testuser2)
    ↓ (if not exempt)
Check per-minute limit (last 60 seconds)
    ↓
Check daily limit (last 24 hours)
    ↓
If allowed: Generate recipes
    ↓
Log the request
    ↓
Return recipes + stats
```

### 2. Cache Optimization:

- **Cached recipes = FREE**: Don't count against limits
- Only NEW AI generations are tracked
- Encourages efficient use of caching system

## Files Created/Modified

### New Files:
1. `backend/apps/ai_agents/models.py` - Rate limit models
2. `backend/apps/ai_agents/rate_limiter.py` - Rate limiting service
3. `backend/apps/ai_agents/admin.py` - Admin configuration
4. `backend/apps/ai_agents/migrations/0001_initial.py` - Database migration

### Modified Files:
1. `backend/apps/ai_agents/views.py` - Added rate limiting to generate_recipes_from_inventory
2. `backend/apps/shopping/inventory_views.py` - Added rate limiting to inventory recipe generation

## Testing

### Test as Regular User:

```bash
# Should work (within limits)
curl -X POST http://localhost:8000/api/ai_agents/generate_recipes/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"max_recipes": 3}'

# Try 2 times quickly (per-minute limit)
# Try 26 times in a day (daily limit)
```

### Test as Exempt User (testuser1/testuser2):

```bash
# Should always work (unlimited)
# Login as testuser1 or testuser2
# Generate as many recipes as you want!
```

## Configuration

### Add More Exempt Users:

1. Go to Django Admin: `/admin/ai_agents/airatelimitsettings/`
2. Edit the "exempted_users" field
3. Add usernames separated by commas: `testuser1,testuser2,newuser,anotheruser`
4. Save

### Change Rate Limits:

1. Go to Django Admin: `/admin/ai_agents/airatelimitsettings/`
2. Change `max_recipes_per_minute` or `max_recipes_per_day`
3. Save (takes effect immediately)

## Benefits

1. **Cost Control**: Prevents excessive AI API usage
2. **Fair Usage**: Ensures all users get fair access
3. **Test Flexibility**: Unlimited access for testing
4. **Cache Efficiency**: Encourages use of caching
5. **User-Friendly**: Clear error messages with wait times
6. **Transparent**: Users see their usage statistics
7. **Auditable**: All requests are logged

## HTTP Status Codes

- `200 OK`: Request successful (within limits)
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Next Steps

1. ✅ **DONE**: Database models created
2. ✅ **DONE**: Rate limiter service implemented
3. ✅ **DONE**: Applied to both recipe endpoints
4. ✅ **DONE**: Admin interface configured
5. ✅ **DONE**: Migrations applied
6. ✅ **DONE**: User-friendly error messages

**Status**: ✅ **COMPLETE AND PRODUCTION-READY!**

---

## Quick Reference

**Exempt Users**: testuser1, testuser2 (unlimited)
**Regular Users**: 5/minute, 25/day
**Cached Recipes**: Don't count against limits
**Error Code**: HTTP 429
**Admin**: `/admin/ai_agents/`

