# MenuMind AI – External Agent Briefing

This document summarizes the current understanding of MenuMind AI for external collaborators (AI agents, contractors, tooling) who need high-level system context without full repository access.

---

## Project Overview

- **Purpose**: Multi-tenant food intelligence platform providing recipe discovery/generation, shopping collaboration, inventory tracking, and nutrition coaching with AI assistance.
- **Application type**: Full-stack web application with React SPA frontend and Django backend (REST + Channels).
- **Repository structure**: Monorepo containing `frontend/`, `backend/`, `docs/`, `scripts/`.
- **Primary languages**: TypeScript (frontend), Python (backend).
- **Frameworks**:
  - Frontend: React 18, React Router v6, Tailwind CSS, i18next, react-hot-toast.
  - Backend: Django 4.2, Django REST Framework, Channels, Celery, SimpleJWT, django-allauth/dj-rest-auth.
- **Runtime environments**:
  - Node.js 18+ for frontend tooling (Create React App stack).
  - Python 3.11 for backend services.
- **Build tooling**: CRA/Webpack, npm scripts, Tailwind; Celery workers with Redis broker.
- **Entry points**: `frontend/src/index.tsx` (SPA bootstrap), `backend/menumine_ai/asgi.py` for ASGI serving (Daphne) and `backend/menumine_ai/wsgi.py` for management commands.

### Architecture Highlights

- **Frontend** leverages `AuthContext` to persist JWT tokens in `localStorage`, orchestrates feature pages via React Router, and integrates Google OAuth (`@react-oauth/google`).
- **Backend** provides REST endpoints under `/api/`, Channels WebSockets for collaborative shopping lists, Celery background tasks for translation/AI pipelines, and AI services for recipe intelligence (Groq, Gemini, Anthropic integrations).
- **Internationalization**: English, Russian, Hebrew locales with RTL support.
- **Persistence**: PostgreSQL (production), SQLite (development), Redis for caching, WebSocket channel layer, and Celery broker.

---

## Rate Limiting & Quota Design Snapshot

Full specification in `docs/rate_limiting_quota_design.md`. Key elements:

- **Tiered Plans**: Free, Premium, Enterprise with configurable daily/hourly request limits, monthly token quotas, cooldown seconds, queue priorities.
- **Database schema**: Tables `PlanDefinition`, `UserPlan`, `UserUsageCounter`, `UserCooldown`, `UsageEvent`, `QueueTicket` track plan metadata, usage tallies, cooldowns, events, and queued jobs.
- **Caching strategy**: Redis maintains hot counters, plan lookups, cooldown flags, and queue stats with TTLs matching reset windows.
- **Enforcement flow**: Resolve plan → enforce cooldown → compare counters → optionally enqueue (Celery) → update Redis counters & audit logs → periodic persistence to PostgreSQL.
- **Queueing**: Celery priority queues (`high`, `default`, `low`) mapped to user tiers; queue tickets record status/position.
- **API responses**: 429 for limit/cooldown, 402 for quota exhaustion, 202 for queued, each returning helpful headers and messages.
- **Monitoring**: Prometheus metrics for requests, tokens, queue length, cooldown hits; alerts on spikes or capacity issues.
- **Rollout**: Shadow mode → enforce on Free tier → extend to Premium/Enterprise with overage rules.

---

## Sentry Integration Data Needed

Open questions to finalize Sentry setup (per information gathering prompt):

1. **Project context**: Confirm purpose, repo layout, languages, frameworks, runtimes (partially inferred above; awaiting confirmation).
2. **Current error handling/logging**: Existing tools, middleware, critical flows, and handling for AI/ML errors.
3. **Deployment environments**: Count (dev/stage/prod), hosting providers, CI/CD tools, infrastructure style (serverless/container), reverse proxies, database specifics.
4. **Sentry account details**: Organization setup, plan tier, DSN availability, team access requirements.
5. **Integration scope**: Surfaces to monitor (frontend, backend, workers), mobile components, third-party integrations, source maps, release tracking needs.
6. **Privacy & compliance**: Regulatory obligations (GDPR, CCPA, etc.), data scrubbing requirements, sensitive headers/cookies to exclude, anonymization expectations.
7. **Notifications & workflow**: Alert recipients & channels (email, Slack, PagerDuty), severity thresholds, project management integrations, ownership rules.
8. **Traffic & sampling**: Estimated MAUs/event volume, quota concerns, sampling strategies, endpoints needing reduced sampling.
9. **Testing & rollout**: Preferred environment rollout order, validation steps, documentation/training needs for the team.
10. **AI considerations**: Models/services in use, need to track AI-specific errors, response times, prompt/response capture (with sanitization).
11. **Package management**: npm/pnpm/pip usage, dependency restrictions, package manifest structure.
12. **Timeline & priorities**: Urgency, top priorities for error tracking, upcoming releases impacting implementation.

Collecting these responses from stakeholders is required before drafting the final Sentry integration plan.

---

## Next Actions for External Agents

1. Review the rate limiting blueprint (`docs/rate_limiting_quota_design.md`) to understand the quota system.
2. Coordinate with stakeholders to gather outstanding Sentry answers listed above.
3. Prepare final Sentry setup analysis summarizing collected data, recommendations, implementation checklist, risk assessment, and resource needs once information is complete.
4. Align planned Sentry integration with the Django + React + Celery deployment pipeline (SDK selection, release tracking, alerting, privacy controls).

---

*Update this briefing as new details are confirmed. Intended for external collaborators requiring condensed project context.*
