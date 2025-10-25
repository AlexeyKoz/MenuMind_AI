# MenuMind AI Rate Limiting & Quota Control Blueprint

This guide consolidates the production-ready design for implementing a tiered rate limiting, quota tracking, cooldown, and queueing system tailored to MenuMind AI.

---

## 1. Database Schema Design

### Core Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `billing_plandefinition` | Stores standard limits per tier (Free, Premium, Enterprise) | `plan (PK)`, `daily_request_limit`, `hourly_request_limit`, `monthly_token_limit`, `cooldown_seconds`, `queue_priority`, `burst_limit`, `additional_limits JSONB` |
| `billing_userplan` | Assigns a plan to each user and allows overrides | `user (PK, FK)`, `plan (FK)`, `custom_limits JSONB`, `effective_from`, `effective_to` |
| `billing_userusagecounter` | Canonical daily+monthly usage tallies | `user (FK)`, `date`, `month`, `request_count`, `token_count` (unique on `(user, date)` & `(user, month)`) |
| `billing_usercooldown` | Tracks last AI request timestamp per user | `user (PK, FK)`, `last_request_at TIMESTAMPTZ` |
| `billing_usageevent` | Detailed audit log of each AI interaction | `user`, `event_type`, `tokens_consumed`, `status`, `metadata JSONB`, `created_at` |
| `billing_queueticket` | Represents queued AI generation jobs | `user`, `status`, `priority`, `cost_estimate`, `requested_at`, `started_at`, `finished_at` |

### Migration Snippet (PostgreSQL)

```sql
CREATE TABLE billing_plandefinition (
    plan VARCHAR(32) PRIMARY KEY,
    daily_request_limit INT NOT NULL,
    hourly_request_limit INT NOT NULL,
    monthly_token_limit BIGINT NOT NULL,
    cooldown_seconds INT NOT NULL,
    queue_priority INT NOT NULL,
    burst_limit INT NOT NULL,
    additional_limits JSONB DEFAULT '{}'
);

CREATE TABLE billing_userplan (
    user_id UUID PRIMARY KEY REFERENCES auth_user(id),
    plan VARCHAR(32) REFERENCES billing_plandefinition(plan),
    custom_limits JSONB DEFAULT '{}',
    effective_from TIMESTAMPTZ DEFAULT now(),
    effective_to TIMESTAMPTZ
);

CREATE TABLE billing_userusagecounter (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth_user(id),
    date DATE NOT NULL,
    month DATE NOT NULL,
    request_count INT DEFAULT 0,
    token_count BIGINT DEFAULT 0,
    UNIQUE(user_id, date),
    UNIQUE(user_id, month)
);
CREATE INDEX idx_userusagecounter_user ON billing_userusagecounter (user_id);
CREATE INDEX idx_userusagecounter_month ON billing_userusagecounter (user_id, month);

CREATE TABLE billing_usercooldown (
    user_id UUID PRIMARY KEY REFERENCES auth_user(id),
    last_request_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE billing_usageevent (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth_user(id),
    event_type VARCHAR(32) NOT NULL,
    tokens_consumed BIGINT DEFAULT 0,
    status VARCHAR(16) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_usageevent_user_created ON billing_usageevent (user_id, created_at);

CREATE TABLE billing_queueticket (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth_user(id),
    status VARCHAR(16) NOT NULL,
    priority INT NOT NULL,
    cost_estimate BIGINT,
    requested_at TIMESTAMPTZ DEFAULT now(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);
CREATE INDEX idx_queueticket_status_priority ON billing_queueticket (status, priority, requested_at);
```

---

## 2. Backend Architecture Overview

- **Framework**: Django / DRF for API, Celery for background jobs.
- **Data Stores**: PostgreSQL (persistent quotas), Redis (hot caches, cooldowns, queue state).
- **Queueing**: Celery queues partitioned by priority (`high`, `default`, `low`).
- **Plan Resolution**: Cached plan data per user in Redis (`plan:user:{id}`) with TTL.
- **Rate Enforcement Flow**:
  1. Resolve plan.
  2. Check cooldown key (`cooldown:user:{id}`) in Redis.
  3. Read usage counters from Redis (hydrate from DB if missing).
  4. Compare against plan limits (daily/hourly/monthly).
  5. Decide: process immediately or enqueue (priority queue).
  6. Update counters in Redis; schedule async flush to DB.

---

## 3. Implementation Logic Highlights

### Resetting Limits
- Redis counters use TTL aligned with reset boundaries (local midnight for daily, month end for monthly).
- Nightly Celery beat tasks reconcile Redis state with PostgreSQL to prevent drift.

### Cooldown Enforcement
```python
def enforce_cooldown(user_id, cooldown_seconds):
    key = f"cooldown:user:{user_id}"
    ttl = redis_client.ttl(key)
    if ttl > 0:
        raise CooldownActive(wait_seconds=ttl)
    redis_client.setex(key, cooldown_seconds, "1")
```

### Queue Strategy
- Queue tickets stored in DB + Redis.
- Celery workers subscribe to queue by priority.
- `queue_priority` derived from plan: Enterprise > Premium > Free.

### Token Accounting
1. Pre-estimate tokens using prompt length → stored on queue ticket.
2. Actual tokens from provider logged into `UsageEvent` and counters.
3. Failed requests recorded with zero tokens unless provider billed partial usage.

---

## 4. Caching Strategy

| Cache Key | Contents | TTL | Notes |
|-----------|----------|-----|-------|
| `plan:{plan}` | PlanDefinition JSON | 24h | Warmed on startup; invalidated on admin change. |
| `plan:user:{id}` | User merged plan limits | 1h | Deleted on upgrade/downgrade. |
| `usage:user:{id}` | Hash: `daily_requests`, `hourly_requests`, `monthly_tokens` | Daily/hourly TTLs | Primary read path. |
| `cooldown:user:{id}` | Cooldown flag | `cooldown_seconds` | Controls 30s delay. |
| `queue_stats` | Current queue lengths | short TTL (e.g., 10s) | For status endpoint & monitoring. |

---

## 5. API Responses

| Condition | Status | Headers | Body |
|-----------|--------|---------|------|
| Daily limit hit | `429` | `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After` | `{ "error": "daily_limit_exceeded", "detail": "Resets in 04:32:18" }` |
| Cooldown active | `429` | `Retry-After` | `{ "error": "cooldown_active", "detail": "Wait 25 seconds" }` |
| Monthly quota exceeded | `402` | — | `{ "error": "quota_exceeded", "detail": "Upgrade or wait for reset" }` |
| Queued request | `202` | `X-Queue-Position` | `{ "status": "queued", "position": 3, "eta_seconds": 60 }` |

---

## 6. Edge Case Handling

- **Plan Changes**: Invalidate plan & usage caches; apply new limits instantly. Optionally reset counters or clamp to new limit.
- **Timezone**: Store resets in UTC but compute TTL based on user’s preferred timezone.
- **Failed Requests**: Count the request; tokens = 0 unless model consumed tokens.
- **Partial Completions**: Count tokens consumed; optionally mark event status `partial`.

---

## 7. Monitoring & Analytics

Metrics (Prometheus):
- `ai_requests_total{plan,status}`
- `ai_tokens_consumed_total{plan}`
- `ai_queue_length{queue}`
- `ai_cooldown_hits_total`
- `ai_rate_limit_exceeded_total`
- `ai_cost_estimated` vs `ai_cost_actual`

Alerts:
- Queue length sustained > threshold.
- Monthly consumption > 90% budget.
- Sudden request bursts per user/IP.

Abuse patterns:
- Multiple accounts sharing IP hitting limits.
- Token/request ratio anomalies.
- Free-tier users hitting limit at identical intervals.

---

## 8. Code Snippets

### Plan Lookup
```python
from django.core.cache import cache

def get_user_plan(user):
    cache_key = f"user_plan:{user.id}"
    plan = cache.get(cache_key)
    if plan is None:
        user_plan = UserPlan.objects.select_related("plan").get(user=user)
        plan = {**user_plan.plan.as_dict(), **(user_plan.custom_limits or {})}
        cache.set(cache_key, plan, timeout=3600)
    return plan
```

### DRF Rate Enforcement Decorator
```python
from rest_framework.response import Response
from rest_framework import status

def enforce_limits(view_func):
    def _wrapped(view, request, *args, **kwargs):
        user = request.user
        plan = get_user_plan(user)
        usage = get_usage_counters(user, plan)
        cooldown_seconds = plan["cooldown_seconds"]

        if cooldown_remaining(user) > 0:
            return Response(
                {"error": "cooldown_active", "detail": f"Retry in {cooldown_remaining(user)}s"},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        if usage.daily_requests >= plan["daily_request_limit"]:
            return rate_limit_response("daily_limit_exceeded", usage.daily_reset_in)

        if usage.hourly_requests >= plan["hourly_request_limit"]:
            return rate_limit_response("hourly_limit_exceeded", usage.hourly_reset_in)

        if usage.monthly_tokens >= plan["monthly_token_limit"]:
            return Response({"error": "quota_exceeded"}, status=status.HTTP_402_PAYMENT_REQUIRED)

        ticket = enqueue_if_needed(user, plan)
        if ticket:
            return Response({"status": "queued", "position": ticket.position}, status=status.HTTP_202_ACCEPTED)

        set_cooldown(user, cooldown_seconds)
        return view_func(view, request, *args, **kwargs)
    return _wrapped
```

### Usage Persistence
```python
def record_usage(user, tokens_used, status="success"):
    now = timezone.now()
    redis_client.hincrby(f"usage:user:{user.id}", "daily_requests", 1)
    redis_client.hincrby(f"usage:user:{user.id}", "hourly_requests", 1)
    redis_client.hincrby(f"usage:user:{user.id}", "monthly_tokens", tokens_used)

    UsageEvent.objects.create(
        user=user,
        event_type="ai_recipe_generation",
        tokens_consumed=tokens_used,
        status=status,
        metadata={"model": "gpt-4o"}
    )

    upsert_usage_counter(user, now.date(), tokens_used)
```

### Celery Task
```python
@app.task(bind=True)
def process_recipe_generation(self, request_id, user_id, payload):
    try:
        tokens_consumed = call_ai(payload)
        record_usage(user_id, tokens_consumed)
    except CooldownActive as e:
        raise self.retry(countdown=e.wait_seconds)
    except RateLimitExceeded:
        update_ticket(request_id, status="failed")
        raise
    else:
        update_ticket(request_id, status="done")
```

---

## 9. Cost Management

- **Pre-estimation**: Estimate token cost from prompt length and plan limits; block if estimated cost exceeds remaining quota.
- **Budget Alerts**: Notify at 80%, 95%, 100% of monthly quota.
- **Overage Policy**:
  - Free: hard stop.
  - Premium: allow short overage, bill afterwards.
  - Enterprise: unlimited with monthly reconciliation.

---

## 10. Best Practices & Rollout

- **Security**: All counters maintained server-side; avoid client manipulation.
- **Scalability**: Keep quota checks in Redis, persist to DB via batched tasks.
- **Pitfalls**: Redis eviction, stale caches on plan change, time drift.

### Testing
- Unit: limit calculations, plan overrides.
- Integration: API throttling flows per tier.
- Load: concurrency tests with Locust/k6.
- Chaos: simulate Redis outage; ensure graceful degradation.

### Rollout Plan
1. Shadow mode logging without enforcement.
2. Communicate upcoming enforcement to users.
3. Enforce Free tier; monitor metrics.
4. Enforce Premium/Enterprise with overage handling.
5. Continuously tune queue priorities and limits.

---

## Suggested Tier Limits

| Tier | Daily Requests | Hourly Requests | Monthly Tokens | Cooldown | Queue Priority |
|------|----------------|-----------------|----------------|----------|----------------|
| Free | 10 | 5 | 50k | 30 sec | Low |
| Premium | 50 | 20 | 500k | 15 sec | Medium |
| Enterprise | Custom (e.g., 200) | 60 | 5M | 5 sec | High |

`custom_limits` field handles enterprise-specific overrides.

---

This markdown document serves as the authoritative reference for implementing robust quota and rate limiting in MenuMind AI.
