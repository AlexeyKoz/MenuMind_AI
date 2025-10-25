# Rate Limiting Improvements - Testing Guide

## ✅ Completed Improvements

We've successfully implemented three major rate limiting improvements:

1. **HTTP Headers on API Responses** - Standard rate limit headers added to all recipe generation responses
2. **User Rate Limit Status Endpoint** - GET endpoint for users to check their current usage
3. **Admin Metrics Dashboard** - Comprehensive analytics endpoint for administrators

---

## 🧪 Manual Testing Instructions

### Prerequisites
- Backend server running on `http://localhost:8000`
- Valid user credentials (testuser1 or testuser2)
- Tool for API testing (Postman, curl, or browser console)

---

### Test 1: HTTP Headers on Recipe Generation

**Expected Headers:**
- `X-RateLimit-Limit-Minute`: Maximum recipes per minute (e.g., 5)
- `X-RateLimit-Remaining-Minute`: Remaining recipes this minute
- `X-RateLimit-Reset-Minute`: Unix timestamp when minute limit resets
- `X-RateLimit-Limit-Daily`: Maximum recipes per day (e.g., 25)
- `X-RateLimit-Remaining-Daily`: Remaining recipes today
- `X-RateLimit-Reset-Daily`: Unix timestamp when daily limit resets
- `Retry-After`: Seconds to wait (only when rate limited)

**How to Test:**

1. Login and get your token:
```bash
POST http://localhost:8000/api/users/auth/login/
Body: {
  "username": "testuser1",
  "password": "TestPassword123!"
}
```

2. Make a recipe generation request and check response headers:
```bash
POST http://localhost:8000/api/ai_agents/generate_recipes/
Headers: Authorization: Bearer YOUR_TOKEN
Body: {
  "max_recipes": 1,
  "cuisine": "Italian"
}
```

3. **Verify**: Check response headers for all X-RateLimit-* headers

---

### Test 2: User Rate Limit Status Endpoint

**Endpoint:** `GET /api/ai/rate-limit-status/`

**Expected Response:**
```json
{
  "user": "testuser1",
  "plan": "unlimited",  // or "standard"
  "limits": {
    "per_minute": 5,
    "per_day": 25
  },
  "usage": {
    "last_minute": 1,
    "today": 5
  },
  "remaining": {
    "minute": 4,
    "daily": 20
  },
  "resets_at": {
    "minute": "2025-10-26T00:45:00Z",
    "daily": "2025-10-27T00:00:00Z"
  },
  "reset_in_seconds": {
    "minute": 45,
    "daily": 86400
  },
  "exempt": false  // true for testuser1 and testuser2
}
```

**How to Test:**

```bash
GET http://localhost:8000/api/ai/rate-limit-status/
Headers: Authorization: Bearer YOUR_TOKEN
```

**Verify:**
- Response contains all usage statistics
- For exempt users (testuser1, testuser2), `exempt` should be `true`
- Limits show "unlimited" for exempt users

---

### Test 3: Admin Metrics Dashboard

**Endpoint:** `GET /api/ai/admin/metrics/`

**Requires:** User must have `is_staff=True` in database

**Expected Response:**
```json
{
  "overview": {
    "total_requests_today": 15,
    "total_requests_last_hour": 5,
    "total_requests_last_24h": 42,
    "total_requests_last_7days": 127,
    "unique_users_today": 3,
    "unique_users_last_24h": 5,
    "total_recipes_generated_today": 38,
    "total_recipes_generated_last_24h": 105
  },
  "by_endpoint": [
    {
      "endpoint": "recipe_generation",
      "request_count": 42,
      "total_recipes": 105,
      "unique_users": 5
    }
  ],
  "top_users": [
    {
      "user__username": "testuser1",
      "requests": 20,
      "recipes": 50
    }
  ],
  "hourly_stats": [
    {
      "hour": "2025-10-25 23:00",
      "requests": 8
    }
  ],
  "current_settings": {
    "max_recipes_per_minute": 5,
    "max_recipes_per_day": 25,
    "exempted_users": ["testuser1", "testuser2"]
  },
  "recent_activity": [
    {
      "user": "testuser1",
      "endpoint": "recipe_generation",
      "recipes_generated": 3,
      "timestamp": "2025-10-25T23:15:30Z",
      "time_ago": "2m ago"
    }
  ],
  "generated_at": "2025-10-25T23:17:45Z"
}
```

**How to Test:**

1. First, make testuser1 a staff user:
```bash
python manage.py shell
>>> from apps.users.models import User
>>> user = User.objects.get(username='testuser1')
>>> user.is_staff = True
>>> user.save()
>>> exit()
```

2. Make the request:
```bash
GET http://localhost:8000/api/ai/admin/metrics/
Headers: Authorization: Bearer YOUR_TOKEN
```

3. **Verify:**
   - Response contains comprehensive analytics
   - All statistics are accurate
   - Hourly breakdown shows 24 hours
   - Top users are sorted by request count
   - Recent activity shows latest requests

---

## 🎯 Quick Verification Checklist

- [ ] **HTTP Headers**: Recipe generation responses include all 6 rate limit headers
- [ ] **HTTP Headers**: Rate-limited requests (429) include `Retry-After` header
- [ ] **Status Endpoint**: Returns correct usage for current user
- [ ] **Status Endpoint**: Exempt users show `unlimited` plan
- [ ] **Status Endpoint**: Reset times are accurate
- [ ] **Admin Metrics**: Returns comprehensive statistics
- [ ] **Admin Metrics**: Non-admin users get 403 Forbidden
- [ ] **Admin Metrics**: All data fields are populated correctly

---

## 📊 Example Usage Scenarios

### Scenario 1: Normal User Checking Their Quota

```javascript
// Frontend code example
const checkQuota = async () => {
  const response = await fetch('http://localhost:8000/api/ai/rate-limit-status/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  
  // Display to user
  console.log(`You have ${data.remaining.daily} recipes remaining today`);
  console.log(`Resets in ${data.reset_in_seconds.daily} seconds`);
};
```

### Scenario 2: Handling Rate Limit Headers

```javascript
// Frontend code example
const generateRecipes = async () => {
  const response = await fetch('http://localhost:8000/api/ai_agents/generate_recipes/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ max_recipes: 3 })
  });
  
  // Read rate limit headers
  const remaining = response.headers.get('X-RateLimit-Remaining-Daily');
  const resetTime = response.headers.get('X-RateLimit-Reset-Daily');
  
  // Update UI
  updateQuotaDisplay(remaining, resetTime);
  
  if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After');
    showMessage(`Rate limited. Retry in ${retryAfter} seconds`);
  }
};
```

### Scenario 3: Admin Dashboard

```javascript
// Admin dashboard code example
const loadMetrics = async () => {
  const response = await fetch('http://localhost:8000/api/ai/admin/metrics/', {
    headers: {
      'Authorization': `Bearer ${adminToken}`
    }
  });
  
  const metrics = await response.json();
  
  // Display metrics
  console.log(`Total requests today: ${metrics.overview.total_requests_today}`);
  console.log(`Active users: ${metrics.overview.unique_users_today}`);
  
  // Show top users
  metrics.top_users.forEach((user, index) => {
    console.log(`${index + 1}. ${user.user__username}: ${user.requests} requests`);
  });
};
```

---

## 🔧 Implementation Details

### Files Modified

1. **backend/apps/ai_agents/rate_limiter.py**
   - Added `get_rate_limit_headers()` method
   - Returns dictionary of HTTP headers

2. **backend/apps/ai_agents/views.py**
   - Updated recipe generation endpoint to add headers
   - Added `rate_limit_status()` endpoint
   - Added `admin_metrics()` endpoint with comprehensive analytics
   - Enhanced rate limit error responses with headers

3. **backend/apps/shopping/inventory_views.py**
   - Updated inventory recipe generation to add headers

4. **backend/apps/ai_agents/urls.py**
   - Added route: `rate-limit-status/`
   - Added route: `admin/metrics/`

### Key Features

**HTTP Headers:**
- Added to all successful recipe generation responses
- Added to rate-limited error responses (429)
- Includes `Retry-After` header on 429 errors
- Compatible with standard rate limiting conventions

**User Status Endpoint:**
- Real-time usage statistics
- Reset time calculations
- Exemption status
- User-friendly time remaining

**Admin Metrics:**
- Overview statistics (today, 24h, 7d)
- Usage by endpoint
- Top 20 users by requests
- Hourly breakdown (24 hours)
- Recent activity (last 10 requests)
- Current rate limit settings

---

## 🚀 Next Steps: Redis Caching

After verifying these improvements work correctly, the next enhancement will be:

**Redis Caching Layer**
- 10-100x faster rate limit checks
- Reduced database load
- Graceful fallback to PostgreSQL if Redis unavailable
- Atomic counter operations
- Automatic TTL for daily/hourly limits

**Benefits:**
- Sub-millisecond rate limit checks
- Supports high-concurrency scenarios
- Scalable to 100K+ users
- Industry standard approach

---

## 📝 Summary

All three improvements are now implemented and ready for testing! The rate limiting system now provides:

✅ **Better Developer Experience** - Standard HTTP headers for client-side quota management
✅ **User Visibility** - API endpoint for users to check their usage
✅ **Admin Insights** - Comprehensive analytics dashboard for monitoring

**Implementation Time:** ~5 hours
**Test Complexity:** Medium
**Production Ready:** Yes (after manual testing)

Enjoy your enhanced rate limiting system! 🎉

