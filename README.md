# MenuMind AI Platform

> Multi-tenant food intelligence platform combining collaborative shopping, inventory automation, personalized nutrition coaching, multilingual recipe discovery, and AI-powered assistance for households.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-4.9-blue.svg)](https://www.typescriptlang.org/)

MenuMind AI orchestrates advanced recipe intelligence, family shopping collaboration, inventory automation, and rich nutrition analytics in a single product experience. The stack spans a Django/DRF backend, React 18 + TypeScript frontend, AI services (Groq, Gemini, Anthropic), and a multilingual pipeline covering English, Russian, and Hebrew.

---

## Table of Contents
1. [Platform Overview](#platform-overview)
2. [Key Capabilities](#key-capabilities)
3. [System Architecture](#system-architecture)
4. [Directory Reference](#directory-reference)
5. [Backend Architecture](#backend-architecture)
6. [Frontend Architecture](#frontend-architecture)
7. [AI & Automation Services](#ai--automation-services)
8. [Internationalization](#internationalization)
9. [Data & Storage](#data--storage)
10. [Environment Configuration](#environment-configuration)
11. [Local Development](#local-development)
12. [Docker & Deployment](#docker--deployment)
13. [Testing & QA](#testing--qa)
14. [Utility Scripts](#utility-scripts)
15. [Additional Documentation](#additional-documentation)
16. [License](#license)

---

## Platform Overview

MenuMind AI is a full-stack food intelligence suite designed for coordinated household use. It connects shared shopping lists, inventory, recipe discovery, and nutrition tracking with AI assistants that translate, validate, and recommend content in multiple languages. 

**Authentication & Security:**
- **Email/Password Registration** with email verification flow
- **Google OAuth** for social login (via django-allauth + dj-rest-auth)
- **JWT Tokens** with refresh mechanism
- **Email Verification Required** for certain features
- **Legal Compliance** with GDPR, CCPA, and Israel Privacy Protection Law Amendment 13

---

## Key Capabilities

- **Collaborative shopping** – Real-time list editing, granular permissions, collaboration keys, WebSocket updates, archival workflows, and integration with inventory.
- **Recipe intelligence** – Canonical recipe catalog, AI-powered search/scraping, RCIP 2.0 ingestion/export, deduplication, cooking counters, and archiving.
- **Inventory & nutrition** – Inventory tracking, AI recipe generation from pantry contents, macro logging, nutrition coaching streaks, badges, and component dashboards.
- **AI & automation** – Groq/Gemini/Anthropic orchestration, smart translation cache (IML + CookLingo), validation pipeline, Celery background tasks, webhook-style agents.
- **Multilingual UX** – Full UI localization (en/ru/he) with RTL layout support, live language switching, and background translation jobs for recipe data.
- **User onboarding** – JWT authentication, refresh tokens, email verification flows, Google OAuth login, persistent AuthContext in frontend, toast feedback.

---

## System Architecture

- **Backend (apps/users, recipes, shopping, nutrition, core)** – Django 4.2 + DRF + SimpleJWT, Channels for WebSockets, Celery workers for asynchronous translation/AI pipelines, Redis for cache/broker.
- **Frontend (`frontend/src`)** – React 18 SPA with TypeScript, Tailwind styling, React Router v6, i18next, state via React context + localStorage tokens, Google OAuth provider.
- **AI layer** – Services coordinate Groq Llama 3.1/3.3, Google Gemini Flash 2.0 Lite, Anthropic, deep translators, duckduckgo_search for discovery.
- **Storage** – PostgreSQL (prod) / SQLite (dev) for relational data, Redis for realtime + cache, RCIP JSON exports for portability.
- **Automation** – Celery beat schedules translation refresh, discovery cache rebuilds, cleanup agents; scripts provide CLI operations for imports/fixes/testing.

---

## Directory Reference

| Path | Description |
| ---- | ----------- |
| `backend/apps/ai_agents` | Universal agent orchestration, Groq/Gemini integrations, RCIP validation utilities. |
| `backend/apps/core` | Shared services (ingredient mapper, translators, unit conversion), RCIP models, admin tooling. |
| `backend/apps/recipes` | Canonical recipe APIs, AI recipe workflows, discovery caching, translation endpoints. |
| `backend/apps/shopping` | Collaborative list models, WebSocket consumers, permissions, archive flows. |
| `backend/apps/nutrition` | Food log entries, AI meal logging, coaching analytics, dashboard metrics. |
| `backend/apps/users` | Authentication, profile preferences, Google OAuth endpoint, email adapters, verified-email decorator. |
| `backend/legal` | Legal compliance framework (GDPR/CCPA), legal documents, cookie consent, data export/deletion. |
| `frontend/src/components` | Shared UI (navigation, Google buttons, banners, legal viewers), i18n aware components, toast integration. |
| `frontend/src/pages` | Feature pages: dashboard, shopping, recipes, discover, nutrition, archive, settings, auth flows, legal pages. |
| `docs/` | Sprint guides, implementation playbooks, OAuth rollout notes, technical briefs (see [Additional Documentation](#additional-documentation)). |
| `legal_documents/` | Multilingual legal documents (EN, RU, HE) in Markdown format, master file list. |
| `scripts/` | Windows helper scripts for starting/stopping stacks, rebuilding frontend. |

---

## Backend Architecture

- **Frameworks**: Django 4.2, Django REST Framework, Channels 4.0, dj-rest-auth, django-allauth, celery 5.3, redis 5.
- **Auth**: SimpleJWT access/refresh tokens, email verification via dj-rest-auth registration, Google OAuth endpoint (`POST /api/users/auth/google/`) including code/ID token support, `verified_email_required` decorator for gated APIs.
- **Email Verification**:
  - Required for account activation
  - Multilingual email templates (EN, RU, HE)
  - Resend verification link functionality
  - Yellow banner reminder for unverified users
  - Email verification page with success/error states
- **Google OAuth Integration**:
  - One-click login with Google account
  - Automatic email verification for Google users
  - Multilingual Google button component
  - Fallback to traditional registration if OAuth fails
- **Apps & Responsibilities**:
  - `recipes`: canonical + user recipe CRUD, AI generation, translation triggers, RCIP export/import.
  - `shopping`: list collaboration, WebSocket consumer groups, permission management, archive lifecycles.
  - `nutrition`: AI nutrition entries, streaks, dashboard endpoints, report generation.
  - `core`: translation/validation services (IML, CookLingo), deduplication, unit conversion, admin imports.
  - `users`: profile preferences, SimpleJWT integration, multilingual account adapter for emails, Google login view.
- **Background workers**: Celery worker + beat handle translation queues, discovery cache refresh, cleanup tasks, AI validation pipelines. Redis acts as broker/result backend.
- **Logging & diagnostics**: Extensive logging in Google OAuth view for debugging, CLI scripts under `backend/` for translation and data audits (e.g., `check_translation.py`, `run_e2e_tests.py`).

---

## Frontend Architecture

- **Core stack**: React 18, TypeScript 4.9, Tailwind CSS, React Router v6, react-hot-toast, lucide-react icons.
- **State & auth**: `AuthContext` persists JWT tokens in `localStorage`, fetches profile/preferences, tracks `email_verified`. `CollaborationProvider` drives shopping list realtime state.
- **Routing**: BrowserRouter with explicit routes for dashboard, shopping, recipes, nutrition, inventory, archive, settings, `verify-email`, plus guest routes for login/registration.
- **Internationalization**: i18next with `en`, `ru`, `he`. Locale files located in `frontend/src/locales/`. RTL considerations handled for Hebrew.
- **AI UX**: Google OAuth button (`GoogleLogin` component), email verification banner + page, AI recipe generator flows, nutrition dashboards with charts.
- **Tooling**: `@react-oauth/google` provider wrapper keyed by locale, `react-hot-toast` for notifications, environment-driven API base URL.

---

## AI & Automation Services

- **Recipe translation pipeline**: Three-tier system combining Ingredient Multilingual Library (IML), CookLingo glossary, and Gemini→Groq fallbacks. Cached responses stored in database, served instantly after background jobs finish.
- **Universal Agent API**: Backed by RCIP 2.0 models ensuring structured recipes, validation scoring, and automatic translation/caching.
- **AI integrations**: Groq (Llama 3.x) for recipe generation/validation, Google Gemini Flash 2.0 Lite for translations, Anthropic & OpenAI adapters available for legacy flows, DuckDuckGo + web scraping for recipe discovery.
- **Background jobs**: Celery beat schedules hourly translation scan/cache refresh, daily/weekly cleanup, ensuring translation freshness and cost control.

---

## Legal Compliance Framework

MenuMind AI includes a comprehensive legal compliance system meeting GDPR, CCPA, and Israel Privacy Protection Law requirements.

### Legal Documents (Multilingual)
- **Terms of Service v2.0** - User agreement and service terms
- **Privacy Policy v2.0** - Data collection, usage, and rights
- **Cookie Policy v2.0** - Cookie usage and preferences
- **Copyright Notice v1.0** - Copyright and intellectual property
- **RCIP License v1.0** - Recipe Card Interchange Protocol license

All documents available in **English, Russian, and Hebrew** with proper RTL support for Hebrew.

### Cookie Consent System
- **2025 Symmetric Design Standards** - Equal prominence for accept/reject options
- **Granular Controls** - Essential, Functional, Analytics, Performance cookies
- **GPC Signal Detection** - Global Privacy Control support
- **User Preferences Management** - Persistent cookie settings

### User Data Rights (GDPR/CCPA Article 17-20)
- **Right to Data Portability** - Export all user data in JSON format
- **Right to Erasure** - Account deletion with 30-day grace period
- **Cookie Preferences** - Manage cookie consent at any time
- **Email Verification** - Required for account security

### Compliance Badges
- 🇮🇱 **Israel PPL Amendment 13** (August 2025)
- 🇺🇸 **CCPA/CPRA Compliant** (California)
- 🇪🇺 **GDPR Compliant** (European Union)

### API Endpoints
```http
GET    /api/legal/terms/?lang=en|ru|he          # Terms of Service
GET    /api/legal/privacy/?lang=en|ru|he        # Privacy Policy
GET    /api/legal/cookies/?lang=en|ru|he        # Cookie Policy
GET    /api/legal/copyright/?lang=en|ru|he      # Copyright Notice
GET    /api/legal/rcip/?lang=en|ru|he           # RCIP License
POST   /api/legal/accept/                        # Record legal acceptance
POST   /api/legal/cookie_consent/                # Save cookie preferences
GET    /api/legal/get_cookie_consent/            # Get current preferences
GET    /api/users/get-data/                      # Export user data
POST   /api/users/export-data/                   # Request data export (async)
POST   /api/users/delete-account/                # Request account deletion
POST   /api/users/cancel-deletion/               # Cancel deletion request
```

### Frontend Components
- `LegalDocumentViewer` - Displays legal documents with RTL support
- `CookieConsentBanner` - Symmetric design banner with preferences
- `Footer` - Multilingual footer with legal links and compliance badges

### Management Commands
```bash
# Load legal documents (initial setup)
python manage.py load_legal_translations --path ../legal_documents/

# Force update existing documents
python manage.py load_legal_translations --path ../legal_documents/ --force
```

---

## Internationalization

- **Supported locales**: English (`en`), Russian (`ru`), Hebrew (`he` with RTL). Language detection uses user preferences + i18next localStorage key.
- **Frontend**: Locale JSONs stored under `frontend/src/locales/`. Google login/localized UI respects language via provider re-rendering.
- **Backend**: Multilingual account adapter selects template per language, email templates under `backend/templates/account/email/` for en/he/ru.
- **Recipe translation**: DB tables cache translated names/steps. Discovery returns English immediately and queues translation tasks; detail pages poll until translation completes.

---

## Data & Storage

- **Primary DB**: PostgreSQL (production) / SQLite (dev) via Django ORM.
- **Caching & realtime**: Redis for Celery broker, caching, WebSocket channel layers.
- **Static assets**: Served via Django (dev) / Nginx (prod). RCIP exports available for recipe portability.
- **Files & scripts**: Extensive helper scripts under `backend/` for translation maintenance, recipe diagnostics, and admin imports.

---

## Environment Configuration

### Backend `.env`

```
SECRET_KEY=...
DEBUG=True
DATABASE_URL=postgres://user:pass@localhost:5432/menumine
REDIS_URL=redis://localhost:6379/0
FRONTEND_URL=http://localhost:3000
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@menumine.ai
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GROQ_API_KEY=...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
```

> **Notes**: Configure SMTP credentials in production. `SOCIALACCOUNT_PROVIDERS['google']` reads from env. Update `SITE_ID=1` domain to match deployment.

### Frontend `.env`

```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_GOOGLE_CLIENT_ID=...
```

Set production values per environment (e.g., Vite host/port if adapted, though current stack uses CRA).

---

## Local Development

### 1. Quick start scripts (Windows)

- `start_fullstack_complete.bat` – starts Redis (if available), Django via Daphne on :8000, React dev server on :3000, auxiliary test server on :8001.
- `stop_servers_complete.bat` – stops running backend/frontend/test servers.
- `rebuild_frontend.bat` – cleans and reinstalls frontend dependencies.

### 2. Manual setup

**Backend**

```powershell
cd backend
python -m venv venv
venv\Scripts\activate  # source venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env  # create from sample; populate secrets
python manage.py migrate
python manage.py createsuperuser
daphne -b 0.0.0.0 -p 8000 menumine_ai.asgi:application
```

Run Celery worker + beat in separate terminals:

```powershell
celery -A menumine_ai worker --loglevel=info
celery -A menumine_ai beat --loglevel=info
```

**Frontend**

```powershell
cd frontend
npm install
npm start
```

Access the app at http://localhost:3000. Backend API lives at http://localhost:8000.

### 3. Auxiliary tools

- API smoke tests: `http://localhost:8001/test_backend.html`
- Frontend automation harness: `http://localhost:8001/test_api.html`
- Default credentials: `testuser1/password123`, `testuser2/password123`.

---

## Docker & Deployment

- `docker-compose.yml` – Local stack (backend, frontend, Redis, Postgres, nginx) with volumes for persistence. Run `docker-compose up --build`.
- `docker-compose.prod.yml` – Production-oriented overrides.
- `backend/Dockerfile.dev` & `Dockerfile.prod` – Multi-stage Django images.
- Ensure `.env` files exist for backend/frontend containers; mount volumes or use environment variables from compose.
- Nginx config under `nginx/` handles reverse proxy, static serving, websocket upgrades.

---

## Testing & QA

- **Unit/Integration**: `cd backend && pytest` (uses `pytest-django`). Specific suites: `run_e2e_tests.py`, `run_nutrition_tests.py`, `test_dashboard_translation.py`.
- **Frontend**: `cd frontend && npm test` (CRA test runner). Visual regression via manual snapshots.
- **End-to-end**: Selenium-based flows orchestrated through HTML dashboards (`test_backend.html`, `test_api.html`).
- **CI considerations**: Ensure Redis/Postgres services available; Celery tasks may require eager mode for deterministic tests.

---

## Utility Scripts

- Translation maintenance: `check_translation.py`, `fix_translation.py`, `create_all_translations.py`.
- Recipe tooling: `rcip_converter.py`, `deduplication_service.py`, `debug_recipe.py` utilities.
- Diagnostics: `check_gemini_client.py`, `check_db_translations.py`, `debug_login.py`.
- Data imports: `admin_import_history.py`, `write_recipe_names.py`, numerous `fix_*` scripts for targeted adjustments.

---

## Additional Documentation

- `GOOGLE_OAUTH_COMPLETE_SETUP_GUIDE.md` – Full OAuth rollout checklist.
- `GOOGLE_OAUTH_IMPLEMENTATION_COMPLETE.md` – Implementation log for Sprints 1–4.
- `EMAIL_VERIFICATION_COMPLETE_FINAL.md` – Email verification implementation guide.
- `MULTILINGUAL_LEGAL_DOCS_COMPLETE.md` – Multilingual legal documents implementation summary.
- `FOOTER_MULTILINGUAL_COMPLETE.md` – Footer translation implementation details.
- `MULTILINGUAL_LEGAL_QUICK_REFERENCE.md` – Quick reference for legal documents system.
- `SPRINT_9_4_FRONTEND_COMPLETE.md`, `SPRINT_9_COMPLETE_SUMMARY.md` – Recent sprint retrospectives.
- `NUTRITION_COACH_USER_GUIDE.md`, `AI_COACH_AGENT_TECHNICAL_BRIEF.md` – Feature-specific guides.
- `docs/google_oauth_email_verification.md` – Consolidated OAuth + email verification timeline.
- `docs/rate_limiting_quota_design.md` – Rate limiting and quota design documentation.

---

## License

MenuMind AI is released under the [MIT License](LICENSE).

---

<details>
<summary>Legacy README (full historical detail)</summary>

# MenuMine AI 🥗🤖

> **A complete family food intelligence platform** combining collaborative shopping lists, intelligent recipe discovery, meal planning, inventory management, and personalized nutrition coaching powered by advanced AI.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)

---

## 🎯 Core Features

### 🍳 Recipe Management & Discovery

#### 🌐 **Recipe Discovery (Discover Page)**
- **Browse Canonical Recipes** - Community recipe database with social features
- **Advanced Sorting** - Sort by Most Popular, Top Rated, Most Cooked, or Most Recent
- **Smart Search** - Find recipes by name, ingredients, or cuisine
- **Social Interactions** - Like and rate recipes (1-5 stars)
- **Auto-Save to Collection** - Liked recipes automatically appear in "My Recipes"
- **Recipe Statistics** - See total likes, ratings, and times cooked by all users

#### 📚 **My Recipes (Personal Collection)**
- **Personal Recipe Library** - Your saved and generated recipes in one place
- **Cooking Tracker** - Mark recipes as cooked/uncooked (toggle system)
- **Archive System** - Move recipes to archive without losing them
- **Recipe Details** - Full RCIP-formatted recipes with ingredients, steps, and nutrition
- **Send to Shopping List** - Select recipe ingredients and add to any shopping list
- **Global Cooking Counter** - See how many times each recipe has been cooked by all users

#### 🗃️ **Recipe Archive**
- **Soft Archive** - Move recipes to archive with 5-second confirmation
- **Bulk Operations** - Select all and delete multiple recipes at once
- **Restore Anytime** - Bring archived recipes back to your collection
- **Permanent Deletion** - Remove from your collection (recipe stays in Discover page)
- **Auto-Archive** - Skip countdown and archive immediately

#### 🤖 **AI Recipe Agent (RCIP Format)**
- **AI Search** - Find and scrape recipes from the internet with natural language
  - Example: *"Find me an authentic Italian pasta carbonara"*
  - Automatically converts to RCIP format and saves to My Recipes
- **AI Generation from Inventory** - Generate recipes based on your pantry items
  - Analyzes your current inventory
  - Creates 3-5 personalized recipe suggestions
  - Auto-saves all generated recipes to My Recipes
- **RCIP Format** - Industry-standard Recipe Card Interchange Protocol
  - Structured ingredients with amounts, units, and notes
  - Step-by-step instructions with timers
  - Nutrition information and metadata
  - Version tracking and recipe forking
- **Web Scraping** - Intelligent recipe extraction from popular food websites
- **Deduplication** - Smart matching prevents duplicate recipes

### 🛒 Smart Collaborative Shopping Lists

#### Real-time Collaboration
- **Live Sync** - Multiple users edit lists simultaneously with instant WebSocket updates
- **Advanced Permissions** - Granular control over who can edit, add items, or invite others
- **Collaboration Keys** - Share lists securely using unique keys
- **Participant Awareness** - See who's online and editing in real-time
- **Live Updates** - Watch items being added, checked, and deleted live

#### Shopping List Archive
- **Smart Archive** - Soft delete lists with 5-second cancellation timer
- **Bulk Delete** - Select all and permanently delete multiple lists at once
- **Ownership Transfer** - When creators delete lists, ownership auto-transfers to oldest participant
- **Participant Protection** - Collaborators can remove lists from view without affecting others
- **Auto-Cleanup** - 60-day automatic cleanup with ownership transfer notifications

### 📊 Nutrition Intelligence
- **AI Meal Analysis** - Automatic macro and calorie tracking from meal descriptions
- **Weekly Reports** - Comprehensive nutrition insights and trends
- **Goal Setting** - Personalized nutrition goals and targets
- **AI Coaching** - Smart recommendations based on your eating patterns

### 💑 Family & Partner Features
- **Couple Sync** - Partners can share lists and coordinate meal planning
- **Nutrition Goals Sharing** - Coordinate dietary goals together
- **Collaboration Keys** - Secure family list sharing system
- **Personal Colors** - Visual identification of family members in shared lists

### 🌍 Multilingual Support & Smart Translation System

MenuMine AI features a **production-ready, enterprise-grade multilingual system** with intelligent caching, cost-optimized translation workflows, and RCIP 2.0 standardized format. Implemented across **6 sprints** with exceptional performance results.

#### Supported Languages
- 🇺🇸 **English (en)** - Default, all recipes stored in English
- 🇷🇺 **Russian (ru)** - Full UI and recipe translation
- 🇮🇱 **Hebrew (he)** - Full UI and recipe translation with RTL support

#### System Architecture Overview

**6-Sprint Implementation** (100% Complete):
- **Sprint 1**: Database Foundation & Admin Tools
- **Sprint 2**: Service Layer Optimization (1,000x faster)
- **Sprint 3**: Universal Validation System
- **Sprint 4**: 3-Phase Translation System (Gemini PRIMARY, Groq FALLBACK)
- **Sprint 5**: Discovery Cache & Background Agents (1,700x faster)
- **Sprint 6**: RCIP 2.0 & Universal Agent API

#### Smart Translation Architecture

**Problem**: Traditional translation systems make 500+ API calls per language switch, causing quota exhaustion and slow response times.

**Solution**: Multi-tier caching with 3-phase translation workflow and background processing:

1. **Discovery Page** (Recipe List)
   - ✅ Only translates recipe **names** (not full content)
   - ✅ Checks database cache first
   - ✅ Returns English immediately if no translation exists
   - ✅ Queues background Celery task to translate and save to DB
   - ✅ Future requests use cached translation (instant response)

2. **Recipe Detail Page** (Full Recipe)
   - ✅ Checks database for full translation
   - ✅ If cached → Returns instantly
   - ✅ If not cached → Shows loading spinner
   - ✅ Background task translates ingredients + steps
   - ✅ Frontend polls every 2 seconds until complete
   - ✅ Translation saved to DB forever

3. **Performance Metrics**
   | Metric | Before | After | Improvement |
   |--------|--------|-------|-------------|
   | Discovery Page Load | 30-60s | <1s | **60x faster** |
   | Recipe Detail Load | 20-40s | <1s | **40x faster** |
   | API Calls per Language Switch | 500+ | 0-10 | **50x reduction** |
   | API Quota Usage | 100% | <5% | **20x reduction** |

#### Translation Flow Diagram
```
User switches to Russian
    ↓
[Discovery Page]
    ↓
Check RecipeTranslation table for cached names
    ↓
    ├─ Found → Return immediately (< 100ms)
    └─ Not Found → Return English + Queue background task
                    ↓
                    [Celery Task]
                    ↓
                    Translate using IML + CookLingo + Gemini
                    ↓
                    Save to RecipeTranslation table
                    ↓
                    Next request uses cache (instant)

User clicks recipe
    ↓
[Recipe Detail Page]
    ↓
Check RecipeTranslation table for full translation
    ↓
    ├─ Found → Return translated recipe immediately
    └─ Not Found → Return English + "translation_status: pending"
                    ↓
                    [Frontend] Shows loading spinner
                    ↓
                    [Celery Task] Translates full recipe
                    ↓
                    [Frontend] Polls every 2s
                    ↓
                    Translation complete → UI updates automatically
```

#### Translation Services & Fallback Logic

MenuMine AI uses a **3-tier translation system** for maximum accuracy and cost-efficiency:

##### 1. **IML Database (Ingredient Multilingual Library)**
- **Purpose**: Instant, free, accurate ingredient name translation
- **Coverage**: 10,000+ common ingredients in en/ru/he
- **Examples**:
  ```
  tomato   → помидор (ru) → עגבנייה (he)
  olive oil → оливковое масло (ru) → שמן זית (he)
  chicken  → курица (ru) → עוף (he)
  ```
- **Fallback**: If ingredient not found → Use CookLingo DB

##### 2. **CookLingo Database (Cooking Terms Glossary)**
- **Purpose**: Context-aware translation of cooking actions and terms
- **Coverage**: 500+ cooking verbs, techniques, and kitchen terms
- **Examples**:
  ```
  "sauté the onions"    → "обжарить лук" (ru)
  "dice the carrots"    → "нарезать морковь кубиками" (ru)
  "bring to a boil"     → "довести до кипения" (ru)
  "fold in the flour"   → "вмешать муку" (ru)
  ```
- **Smart Context Matching**: 
  - Uses NLP to identify cooking actions in step instructions
  - Preserves cooking terminology consistency
  - Maintains imperative mood for instructions
- **Fallback**: If term not found → Use Gemini API

##### 3. **Gemini Flash 2.0 Lite API (PRIMARY)**
- **Purpose**: Handle complex sentences, recipe names, and contextual translation
- **Priority**: PRIMARY (tried first)
- **Cost**: ~$0.01 per 1000 tokens
- **Rate Limit**: 15 requests/min (free tier), 1500/day
- **Features**:
  - Context-aware translation
  - Preserves cooking instructions tone
  - Handles regional cuisine terminology
  - Maintains measurement units

##### 4. **Groq (Llama 3.3 70B) - FALLBACK**
- **Purpose**: Fallback translation when Gemini fails or quota exceeded
- **Priority**: FALLBACK (only if Gemini fails)
- **Rate Limit**: 30 requests/min (free tier), higher quota
- **Usage**:
  - AI recipe validation
  - Translation fallback
  - Recipe generation
  - Web scraping content extraction

#### Celery & Redis Background Processing

**Redis Configuration**:
- **Purpose**: Task queue backend, caching, and WebSocket layer
- **Host**: `localhost:6379` (development), configurable for production
- **Usage**:
  - Celery task broker and result backend
  - Discovery page caching (Tier 1, <1ms)
  - Real-time WebSocket message broker
  - Session storage

**Celery Workers**:
```bash
# Development (worker + beat together)
celery -A menumine_ai worker --beat --loglevel=info

# Production (separate processes)
celery -A menumine_ai worker --loglevel=info  # Terminal 1
celery -A menumine_ai beat --loglevel=info    # Terminal 2
```

**Background Agents** (Celery Beat Scheduled Tasks):
1. **Hourly Translation Scan** (every hour at :00)
   - Scans for recipes with incomplete translations
   - Queues translation tasks for missing languages
   - Ensures all popular recipes are fully translated

2. **Hourly Discovery Cache Refresh** (every hour at :30)
   - Updates discovery page cache with latest translations
   - Refreshes recipe metadata (likes, ratings, etc.)
   - Keeps cache fresh for fast page loads

3. **Daily Translation Cleanup** (daily at 3:00 AM)
   - Removes failed translations older than 7 days
   - Prevents database bloat
   - Queues retry for important recipes

4. **Weekly Cache Cleanup** (Sunday at 4:00 AM)
   - Removes stale cache entries older than 30 days
   - Optimizes database performance
   - Maintains cache freshness

**Translation Tasks**:
```python
# Phase 1: Immediate (user's language)
translate_recipe_immediate.delay(recipe_id, target_lang)
# ~2-3s, uses Gemini PRIMARY

# Phase 2: Background (3rd language)
translate_recipe_background.delay(recipe_id, target_lang)
# Async, queued after Phase 1

# Phase 3: On-demand (remaining languages)
translate_recipe_on_demand.delay(recipe_id, target_lang)
# User-triggered, shows loading state
```

#### RCIP 2.0 (Recipe Card Interchange Protocol)

MenuMine AI implements the **RCIP 2.0 standardized format** for recipe data interchange with full multilingual support.

**Key Features**:
- **Language-agnostic canonical structure** (IML ingredient keys, CookLingo action keys)
- **Full multilingual support** (embedded translations for en/he/ru)
- **Pydantic validation** (type-safe, validated data)
- **Export/Import support** (.rcip JSON files)
- **Universal Agent API** (single endpoint for all AI agents)

**RCIP 2.0 Structure**:
```json
{
  "rcip_version": "2.0",
  "recipe_id": "uuid",
  "canonical": {
    "metadata": {
      "title": "Recipe Title",
      "source_language": "en",
      "servings": 4,
      "tags": ["italian", "pasta"]
    },
    "structure": {
      "ingredients": [
        {
          "iml_key": "spaghetti",
          "amount": 400,
          "unit": "g",
          "processing": "al dente"
        }
      ],
      "steps": [
        {
          "step_id": "step-1",
          "order": 1,
          "instruction": "Boil water",
          "cooklingo_actions": ["boil"],
          "timing": "10min"
        }
      ]
    }
  },
  "translations": {
    "en": {
      "language": "en",
      "status": "completed",
      "ai_provider": "gemini",
      "content": {
        "title": "Simple Pasta",
        "ingredients_text": {"spaghetti": "400g spaghetti"},
        "steps_text": ["Boil water for pasta"]
      }
    },
    "he": { "..." },
    "ru": { "..." }
  },
  "validation": {
    "is_valid": true,
    "overall_score": 95,
    "issues": []
  }
}
```

**Universal Agent API**:
```python
from apps.core.services import get_universal_agent_service

agent = get_universal_agent_service()
result = agent.submit_recipe(
    recipe_data=recipe,
    agent_name="my-agent",
    skip_validation=False,  # Validate with 3-layer system
    auto_translate=True,    # Queue translations
    auto_cache=True         # Update discovery cache
)

# Complete workflow:
# 1. Normalize to RCIP 2.0
# 2. Validate (IML + CookLingo + AI)
# 3. Save to PostgreSQL
# 4. Queue translations (3-phase)
# 5. Update discovery cache (Redis + PostgreSQL)
# 6. Return recipe_id + status
```

#### 6-Sprint Implementation Summary

**Sprint 1: Database Foundation** ✅
- PostgreSQL schema with 6 tables
- IML + CookLingo tables for fast lookups
- DiscoveryCache table for performance
- Admin import tools (SQLite → PostgreSQL)

**Sprint 2: Service Layer Optimization** ✅ (1,000x faster)
- IMLService: In-memory caching (<1ms lookups)
- CookLingoService: In-memory caching (<1ms lookups)
- Django AppConfig initialization
- Performance: 1,000x faster than database queries

**Sprint 3: Universal Validation System** ✅
- Layer 1: IML validation (<1ms)
- Layer 2: CookLingo validation (<1ms)
- Layer 3: AI coherence validation (~2s, Gemini PRIMARY, Groq FALLBACK)
- Scoring: 0-100 with detailed issue detection

**Sprint 4: 3-Phase Translation System** ✅ (Gemini PRIMARY)
- Phase 1: Immediate translation (user's language, ~3s)
- Phase 2: Background translation (3rd language, async)
- Phase 3: On-demand translation (remaining languages)
- AI Strategy: Gemini PRIMARY (accurate), Groq FALLBACK (higher quota)
- Performance: 1.38s average (2.2x faster than 3s target)

**Sprint 5: Discovery Cache & Background Agents** ✅ (1,700x faster)
- Two-tier caching: Redis (0.29ms) + PostgreSQL (6.78ms)
- 4 background agents (Celery Beat scheduled tasks)
- Hourly translation scan + cache refresh
- Daily translation cleanup + weekly cache cleanup
- Performance: 1,724x faster than 500ms target

**Sprint 6: RCIP 2.0 & Universal Agent API** ✅
- RCIP 2.0 Pydantic models with full validation
- Universal Agent API (single endpoint for all agents)
- Complete workflow integration (validate → translate → cache)
- Export/Import support for .rcip files
- Performance: 2.4s complete workflow (2x faster than target)

#### Translation Quality & Validation

**AI Recipe Validation Flow**:
```
User creates recipe via Recipe Builder
    ↓
[Step 1] Basic Info → Detect language (en/ru/he)
    ↓
[Step 2] Ingredients → AI structures with IML mapping
    ↓
    ├─ IML DB: Normalize ingredient names
    ├─ Validation: Check if amounts/units are reasonable
    └─ Fallback: If ingredient not in IML → Store as custom
    ↓
[Step 3] Cooking Steps → AI structures + CookLingo translation
    ↓
    ├─ CookLingo DB: Translate cooking verbs/techniques
    ├─ Validation: Check if steps are logical sequence
    └─ Fallback: If complex sentence → Use Gemini
    ↓
[Step 4] Review → User can edit AI output
    ↓
[Step 5] Save → Recipe stored in source language
    ↓
Background: Translate to other languages using cache-first strategy
```

#### Database Schema for Translations

**RecipeTranslation Model**:
```python
class RecipeTranslation(models.Model):
    canonical_recipe = ForeignKey(CanonicalRecipe)
    language = CharField(choices=['en', 'ru', 'he'])
    
    # Cached translations
    name = CharField()                      # Recipe name
    description = TextField()               # Recipe description
    base_ingredients = JSONField()          # Translated ingredients
    base_steps = JSONField()                # Translated steps
    
    # Translation metadata
    status = CharField(choices=[
        'pending',      # Queued for translation
        'in_progress',  # Currently translating
        'completed',    # Translation ready
        'failed'        # Translation failed (will retry)
    ])
    completed_at = DateTimeField()
    
    # Unique constraint: one translation per recipe per language
    class Meta:
        unique_together = ['canonical_recipe', 'language']
```

#### Frontend Language Switching

**User Experience**:
1. User clicks language selector (🇺🇸 EN | 🇷🇺 RU | 🇮🇱 HE)
2. Frontend updates `i18n.language`
3. All UI text changes instantly (from i18next locales)
4. Recipe names update:
   - Cached → Instant update
   - Not cached → English shown, background task queued
5. User clicks recipe → Full translation loads:
   - Cached → Instant
   - Not cached → Loading spinner → Polls until complete

**Technical Implementation**:
```typescript
// Frontend: CanonicalRecipesPage.tsx
useEffect(() => {
    // Reload recipe list when language changes
    loadRecipes();
}, [i18n.language]);

// Backend: views.py - retrieve()
if user_language != 'en':
    translation = RecipeTranslation.objects.filter(
        canonical_recipe=instance,
        language=user_language,
        status='completed'
    ).first()
    
    if translation:
        # Cache hit - return immediately
        return translated_recipe
    else:
        # Cache miss - queue background task
        translate_recipe_to_language.delay(recipe_id, user_language)
        return english_recipe + {'translation_status': 'pending'}
```

#### Cost Optimization

**API Usage Comparison**:

| Action | Old Architecture | New Architecture |
|--------|------------------|------------------|
| First language switch | 500 Gemini calls = $5 | 10 Gemini calls = $0.10 |
| Second language switch | 500 Gemini calls = $5 | 0 calls (cached) = $0 |
| 100 users/day | $500/day | $10/day first time, $0 after |
| **Monthly cost** | **$15,000/month** 💸 | **$300 first month, $10 after** ✅ |

**Savings: 99% reduction in translation costs**

#### Error Handling & Retry Logic

```python
# Celery task with automatic retry
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def translate_recipe_to_language(self, recipe_id, language):
    try:
        # Try IML + CookLingo first (free)
        translation = smart_translator.translate_with_databases(...)
        
        if translation.coverage < 0.8:
            # < 80% coverage, use Gemini for remaining
            translation = gemini_translator.translate_gaps(...)
        
        save_to_database(translation)
        
    except GeminiQuotaExceeded:
        # Gemini quota hit, retry in 60 seconds
        raise self.retry(countdown=60)
        
    except Exception as e:
        # Other error, mark as failed
        RecipeTranslation.objects.update(status='failed')
        logger.error(f"Translation failed: {e}")
```

#### Future Enhancements

- [ ] **Add more languages**: French, Spanish, German, Arabic
- [ ] **User-contributed translations**: Allow users to improve translations
- [ ] **Translation quality scoring**: Track accuracy and user feedback
- [ ] **Offline translation**: Cache common phrases for offline use
- [ ] **Voice input**: Speak recipes in your language
- [ ] **Regional dialects**: Mexican Spanish vs. Spain Spanish

---

## 🚀 Tech Stack

### Backend
- **Django 4.2** - Modern Python web framework
- **Django REST Framework** - RESTful API development
- **Django Channels** - WebSocket and real-time features
- **Daphne** - ASGI HTTP/WebSocket server
- **PostgreSQL 15** - Primary database (production)
- **SQLite** - Development database
- **Redis 7** - Caching and WebSocket backend
- **Celery** - Background task processing for translations
- **Groq AI (Llama 3.1 70B)** - Primary LLM for recipe generation and validation
- **Google Gemini Flash 2.0 Lite** - Fallback translation service
- **OpenAI GPT-4** - Legacy support (optional)
- **BeautifulSoup4** - Web scraping for recipe extraction
- **LangChain** - AI agent orchestration

### Frontend
- **React 18** - Modern UI library
- **TypeScript 5** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first styling
- **i18next** - Internationalization framework
- **react-i18next** - React bindings for i18next
- **Zustand** - Lightweight state management
- **React Router v6** - Client-side routing
- **Recharts** - Data visualization
- **React Hot Toast** - Beautiful notifications
- **Lucide React** - Modern icon library

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **Nginx** - Reverse proxy and load balancing
- **WebSockets (ws://)** - Real-time bidirectional communication
- **JWT Authentication** - Secure token-based auth

---

## 📦 Quick Start

### Prerequisites
- **Windows 10/11** (or macOS/Linux)
- **Python 3.11+**
- **Node.js 18+**
- **Redis** (optional - graceful degradation)
- **Groq API Key** (for AI features)

### 🎬 One-Command Startup

**Windows:**
```bash
start_fullstack.bat
```

This script automatically:
1. ✅ Checks and starts Redis (if installed)
2. ✅ Starts Django backend (Daphne) on port 8000
3. ✅ Starts React frontend on port 3000
4. ✅ Starts test server on port 8001
5. ✅ Verifies all services are running

**Stopping Services:**
```bash
stop_servers.bat
```

**Check Service Status:**
```bash
check_services.bat
```

### 🔧 Manual Setup

#### 1. Clone Repository
```bash
git clone https://github.com/yourusername/menumine-ai.git
cd menumine-ai
```

#### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo GROQ_API_KEY=your_api_key_here > .env
echo SECRET_KEY=your_secret_key_here >> .env
echo DEBUG=True >> .env

# Run migrations
python manage.py migrate

# Create test users
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.create_user('testuser1', 'test1@example.com', 'password123')
>>> User.objects.create_user('testuser2', 'test2@example.com', 'password123')
>>> exit()

# Start backend
daphne -b 0.0.0.0 -p 8000 menumine_ai.asgi:application
```

#### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### 🌐 Access Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Testing:** http://localhost:8001/test_backend.html
- **Admin Panel:** http://localhost:8000/admin

### 🔑 Default Test Accounts

| Username | Password | Purpose |
|----------|----------|---------|
| `testuser1` | `password123` | Primary test user |
| `testuser2` | `password123` | Collaboration testing |

---

## 📖 User Workflows

### 🍳 Recipe Discovery & Management

#### 1️⃣ **Discover New Recipes**
```
1. Go to "Discover" page
2. Browse recipes or search (e.g., "pasta carbonara")
3. Sort by Popular, Top Rated, Most Cooked, or Recent
4. Click recipe card to view details
5. ❤️ Like the recipe → Auto-saves to "My Recipes"
6. ⭐ Rate the recipe (1-5 stars)
```

#### 2️⃣ **Use AI to Find Recipes**
```
1. Go to "My Recipes" page
2. Use AI Search field at top
3. Type: "authentic Italian pasta carbonara"
4. AI searches web, scrapes recipe, converts to RCIP
5. Recipe auto-saves to "My Recipes"
```

#### 3️⃣ **Generate Recipes from Inventory**
```
1. Go to "Inventory" and add your ingredients
2. Go to "My Recipes" page
3. Click "✨ Generate from Inventory"
4. AI creates 3-5 personalized recipes
5. All recipes auto-save to "My Recipes"
```

#### 4️⃣ **Cook & Track Recipes**
```
1. Open recipe from "My Recipes"
2. View ingredients and steps
3. Check off ingredients you need
4. Click "Add to Shopping List" → Select list → Confirm
5. After cooking, click "🍳 Mark as Cooked"
6. Global cooking counter increments
```

#### 5️⃣ **Archive Management**
```
1. In "My Recipes", click "🗃️ Move to Archive"
2. 5-second confirmation (click button to skip)
3. Go to "Archive" page → "Recipes" tab
4. Select recipes with checkboxes
5. Bulk delete or restore individually
```

### 🛒 Shopping List Collaboration

#### 1️⃣ **Create & Share List**
```
1. Create new shopping list
2. Copy collaboration key from sidebar
3. Share key with family/friends
4. They enter key to join instantly
5. Set permissions (edit, add items, invite others)
```

#### 2️⃣ **Real-time Collaboration**
```
1. All users see live updates
2. Items added/checked appear instantly
3. See who's online in participant list
4. Updates sync across all devices
```

#### 3️⃣ **Archive & Restore**
```
1. Delete list → 5-second countdown
2. Cancel within 5 seconds or auto-archives
3. Go to "Archive" page
4. Restore or permanently delete
5. If creator deletes, ownership auto-transfers
```

---

## 🔌 API Documentation

### 🔐 Authentication
```http
POST   /api/users/auth/login/           # Login and get JWT tokens
POST   /api/users/auth/register/        # Register new user
POST   /api/users/auth/token/refresh/   # Refresh access token
GET    /api/users/profile/              # Get user profile
```

### 🌐 Canonical Recipes (Discover)
```http
GET    /api/recipes/canonical/                    # List all canonical recipes
GET    /api/recipes/canonical/{id}/               # Get recipe details
POST   /api/recipes/canonical/{id}/like/          # Like/unlike recipe (auto-saves)
POST   /api/recipes/canonical/{id}/rate/          # Rate recipe (1-5 stars)

# Query Parameters for GET /api/recipes/canonical/
?sort=popular          # Sort by total saves
?sort=top_rated        # Sort by average rating
?sort=most_cooked      # Sort by times cooked
?sort=recent           # Sort by creation date (default)
?search=pasta          # Search by name/ingredients
?cuisine=italian       # Filter by cuisine
?difficulty=easy       # Filter by difficulty
```

### 📚 My Recipes (User Collection)
```http
GET    /api/recipes/recipes/my_recipes/          # Get user's saved recipes
GET    /api/recipes/recipes/archived_recipes/    # Get archived recipes
GET    /api/recipes/recipes/{id}/                # Get recipe detail
POST   /api/recipes/recipes/{id}/mark_cooked/    # Toggle cooked status
POST   /api/recipes/recipes/{id}/unsave_recipe/  # Archive recipe (move to archive)
POST   /api/recipes/recipes/{id}/restore_recipe/ # Restore from archive
DELETE /api/recipes/recipes/{id}/permanently_delete_recipe/ # Permanent delete
```

### 🤖 AI Recipe Agent
```http
POST   /api/recipes/recipes/find_recipe/         # AI search & scrape recipe
POST   /api/ai/recipes/                          # Generate from inventory

# AI Search Request Body:
{
    "query": "authentic Italian pasta carbonara",
    "shopping_list_id": "uuid",  # Optional: add ingredients to list
    "add_to_list": true          # Optional: auto-add ingredients
}

# Response includes:
{
    "success": true,
    "canonical_recipe": {...},    # Canonical recipe object
    "user_recipe": {...},         # User's fork
    "created": true,
    "ingredients_added": 5,
    "shopping_list_items": [...]
}
```

### 🛒 Shopping Lists
```http
GET    /api/shopping/lists/                      # List all active lists
POST   /api/shopping/lists/                      # Create new list
GET    /api/shopping/lists/{id}/                 # Get list details
DELETE /api/shopping/lists/{id}/delete/          # Archive list (soft delete)
POST   /api/shopping/lists/{id}/restore/         # Restore archived list
DELETE /api/shopping/lists/{id}/permanent_delete/ # Permanently delete
POST   /api/shopping/lists/{id}/add_item/        # Add item to list
GET    /api/shopping/lists/archived/             # Get archived lists
```

### 👥 Collaboration
```http
POST   /api/shopping/lists/{id}/add_collaborator/     # Add collaborator
POST   /api/shopping/lists/{id}/leave_list/           # Leave list
GET    /api/shopping/lists/{id}/collaborators/        # List collaborators
POST   /api/shopping/lists/{id}/update_collaborator_permissions/ # Update permissions
GET    /api/users/profile/my_collaboration_key/       # Get your collaboration key
POST   /api/users/profile/generate_collaboration_key/ # Generate new key
```

### 🛍️ Items
```http
POST   /api/shopping/items/{id}/toggle_complete/  # Toggle item completion
DELETE /api/shopping/items/{id}/                  # Delete item
PATCH  /api/shopping/items/{id}/                  # Update item details
```

### 📊 Nutrition
```http
GET    /api/nutrition/entries/today_summary/      # Today's nutrition summary
POST   /api/nutrition/entries/ai_log_meal/        # AI-powered meal logging
GET    /api/nutrition/entries/weekly_report/      # Weekly nutrition report
POST   /api/nutrition/entries/get_coaching/       # Get AI coaching advice
```

---

## 🔄 WebSocket Events

### Shopping List Collaboration
```javascript
// Connect to shopping list WebSocket
ws://localhost:8000/ws/shopping/{list_id}/?token={jwt_token}

// Events Received:
{
    "type": "item_added",           // Item added to list
    "type": "item_updated",         // Item modified
    "type": "item_deleted",         // Item removed
    "type": "list_updated",         // List metadata changed
    "type": "collaborator_added",   // New collaborator joined
    "type": "collaborator_updated", // Permissions changed
    "type": "list_deleted",         // List archived
    "type": "list_restored"         // List restored from archive
}
```

### User Notifications
```javascript
// Connect to user notification WebSocket
ws://localhost:8000/ws/user/notifications/?token={jwt_token}

// Events Received:
{
    "type": "list_access_granted",      // Added as collaborator
    "type": "participant_left",         // Someone left your list
    "type": "list_permanently_deleted", // List permanently deleted
    "type": "ownership_transferred",    // List ownership transferred
    "type": "deletion_warning",         // List auto-deletion warning
    "type": "collaboration_key_regenerated" // Security key regenerated
}
```

---

## 🧪 Testing

### Automated Testing Page
Open the comprehensive API testing interface:
```
http://localhost:8001/test_backend.html
```

**Features:**
- ✅ Live server status monitoring
- ✅ JWT authentication management (dual-user testing)
- ✅ All API endpoints organized by feature
- ✅ Canonical Recipes testing (Discover page)
- ✅ My Recipes testing (cooking, archiving)
- ✅ Recipe Archive testing (restore, delete)
- ✅ AI Recipe Agent testing
- ✅ Shopping list collaboration testing
- ✅ WebSocket connection testing
- ✅ Quick workflow automation
- ✅ CORS and performance testing

### Manual Testing Workflows

#### Complete Recipe Workflow
```bash
1. Login as testuser1
2. Browse canonical recipes (Discover page)
3. Like a recipe (auto-saves to My Recipes)
4. Go to My Recipes
5. Mark recipe as cooked
6. Archive recipe
7. Go to Archive page
8. Restore recipe
```

#### AI Recipe Workflow
```bash
1. Login as testuser1
2. Go to My Recipes
3. AI Search: "pasta carbonara"
4. Wait 10-30 seconds for AI to find recipe
5. Recipe auto-saved to My Recipes
6. Click recipe to view details
7. Select ingredients
8. Add to shopping list
```

---

## 📁 Project Structure

```
menumine-ai/
├── backend/                    # Django backend
│   ├── apps/
│   │   ├── ai_agents/         # AI services
│   │   ├── core/              # Core functionality
│   │   ├── nutrition/         # Nutrition tracking
│   │   ├── recipes/           # Recipe management (NEW)
│   │   │   ├── models.py      # Recipe, CanonicalRecipe, UserRecipe
│   │   │   ├── serializers.py # DRF serializers
│   │   │   ├── services.py    # RecipeAgentService (AI)
│   │   │   ├── builder.py     # Recipe builder service
│   │   │   └── views.py       # API endpoints
│   │   ├── shopping/          # Shopping lists
│   │   └── users/             # User management
│   ├── config/                # Configuration
│   │   ├── ai_config.py       # AI/LLM settings
│   │   └── nutrition_config.py
│   ├── menumine_ai/           # Django project
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py            # ASGI config
│   │   └── wsgi.py
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navigation.tsx
│   │   │   ├── RecipeFinder.tsx
│   │   │   ├── CollaboratorManager.tsx
│   │   │   └── ...
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Recipes.tsx            # My Recipes page
│   │   │   ├── RecipesPage.tsx        # Discover page (NEW)
│   │   │   ├── ArchivePage.tsx        # Archive page (NEW)
│   │   │   ├── ShoppingList.tsx
│   │   │   ├── Inventory.tsx
│   │   │   └── ...
│   │   ├── services/
│   │   │   ├── api.ts                 # API client
│   │   │   ├── websocket.ts           # Shopping list WS
│   │   │   └── userWebSocket.ts       # User notification WS
│   │   ├── contexts/
│   │   │   ├── AuthContext.tsx
│   │   │   └── CollaborationContext.tsx
│   │   └── App.tsx
│   ├── package.json
│   └── tsconfig.json
│
├── scripts/                    # Utility scripts
│   ├── deploy.sh
│   ├── backup.sh
│   └── restore.sh
│
├── start_fullstack.bat         # Windows startup script (NEW)
├── stop_servers.bat            # Stop all services (NEW)
├── check_services.bat          # Check service status (NEW)
├── test_backend.html           # API testing page (UPDATED)
├── docker-compose.yml          # Development docker config
├── docker-compose.prod.yml     # Production docker config
└── README.md                   # This file
```

---

## 🎨 RCIP Format (Recipe Card Interchange Protocol)

MenuMine AI uses the **RCIP standard** for all recipes, ensuring consistency and interoperability.

### RCIP Structure
```json
{
  "rcip_version": "1.0",
  "name": "Pasta Carbonara",
  "description": "Classic Italian pasta dish",
  "author": "Chef Mario",
  "source_url": "https://example.com/recipe",
  "prep_time": 10,
  "cook_time": 20,
  "total_time": 30,
  "servings": 4,
  "difficulty": "easy",
  "cuisine": "Italian",
  "diet_labels": ["vegetarian"],
  
  "ingredients": [
    {
      "name": "spaghetti",
      "amount": 400,
      "unit": "g",
      "notes": "dried pasta"
    },
    {
      "name": "eggs",
      "amount": 4,
      "unit": "whole",
      "notes": "room temperature"
    }
  ],
  
  "steps": [
    {
      "step_number": 1,
      "instruction": "Bring a large pot of salted water to boil",
      "timer_minutes": 0
    },
    {
      "step_number": 2,
      "instruction": "Cook pasta according to package directions",
      "timer_minutes": 10
    }
  ],
  
  "nutrition": {
    "calories": 450,
    "protein_g": 18,
    "carbs_g": 65,
    "fat_g": 12
  },
  
  "tags": ["quick", "easy", "italian", "pasta"],
  "equipment": ["large pot", "colander", "bowl"],
  "storage_instructions": "Refrigerate up to 3 days",
  "notes": "Best served immediately"
}
```

### RCIP Benefits
- ✅ Standardized format for all recipes
- ✅ Easy import/export
- ✅ Consistent ingredient parsing
- ✅ Automatic nutrition calculation
- ✅ Version control and recipe forking
- ✅ Web scraping compatibility

---

## 🚀 Advanced Features

### Recipe Forking System
When you like a canonical recipe:
1. **Canonical Recipe** - Master copy in Discover page
2. **User Fork** - Your personal copy in My Recipes
3. **Independent Tracking** - Your cooking history, notes, ratings
4. **Linked Statistics** - Global stats sync from canonical

### AI Recipe Deduplication
Prevents duplicate recipes using:
- Normalized name matching (case-insensitive, special chars removed)
- Multi-word matching algorithm (requires 2+ significant words)
- Example: "fried fish" won't match "fried potato" ✅

### Archive System Features
- **5-second confirmation** with skip option
- **Select all checkbox** for bulk operations
- **Individual restore/delete** buttons
- **Automatic state sync** when deleting individually
- **List-specific** archived recipe storage

### WebSocket Optimization
- **Heartbeat mechanism** - Keeps connections alive
- **Automatic reconnection** - Recovers from disconnections
- **Listener deduplication** - Prevents duplicate notifications
- **Graceful degradation** - Works without WebSocket

---

## 🔒 Security Features

- **JWT Authentication** - Secure token-based auth
- **Collaboration Keys** - Unique keys for list sharing
- **Permission System** - Granular access control
- **Key Regeneration** - Revoke access by regenerating keys
- **CORS Protection** - Configured for production
- **SQL Injection Protection** - Django ORM
- **XSS Protection** - React automatic escaping

---

## 🌍 Environment Variables

### Backend (.env)
```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Production)
DATABASE_URL=postgresql://user:password@localhost:5432/menumine

# AI Services
GROQ_API_KEY=your-groq-api-key-here                    # Primary LLM (recipe generation, validation)
GOOGLE_API_KEY=your-google-gemini-api-key-here         # Fallback translation service
OPENAI_API_KEY=your-openai-api-key-here                # Optional, legacy support

# External APIs (for web scraping)
BRAVE_SEARCH_API_KEY=your-brave-search-key-here        # Recipe web search
FIRECRAWL_API_KEY=your-firecrawl-key-here              # Advanced web scraping

# Redis (Optional but recommended for Celery)
REDIS_URL=redis://localhost:6379/0

# Celery (Background tasks)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8001
```

### API Keys Setup Guide

#### 1. **Groq API (Required - FREE)**
- **Purpose**: Primary LLM for recipe generation and validation
- **Get Key**: https://console.groq.com/keys
- **Free Tier**: 30 requests/min, 14,400/day
- **Model Used**: `llama-3.1-70b-versatile`

#### 2. **Google Gemini API (Required - FREE)**
- **Purpose**: Translation fallback when IML/CookLingo don't cover
- **Get Key**: https://makersuite.google.com/app/apikey
- **Free Tier**: 15 requests/min, 1,500/day
- **Model Used**: `gemini-2.0-flash-lite`
- **Note**: Used ONLY for translations, not recipe generation

#### 3. **Brave Search API (Optional - FREE)**
- **Purpose**: Web recipe search and discovery
- **Get Key**: https://brave.com/search/api/
- **Free Tier**: 2,000 queries/month
- **Fallback**: If not provided, AI recipe search is disabled

#### 4. **Firecrawl API (Optional - FREE)**
- **Purpose**: Advanced web scraping for recipe extraction
- **Get Key**: https://www.firecrawl.dev/
- **Free Tier**: 500 scrapes/month
- **Fallback**: Uses BeautifulSoup4 if not available

#### 5. **OpenAI API (Optional - PAID)**
- **Purpose**: Legacy support, not actively used
- **Get Key**: https://platform.openai.com/api-keys
- **Cost**: $0.03 per 1K tokens (GPT-4)
- **Note**: Can be omitted, system uses Groq instead

### Frontend (.env)
```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

---

## 📊 Performance Optimizations

- **Database Indexing** - Optimized queries for recipes and lists
- **Redis Caching** - Fast access to frequently used data
- **WebSocket Pooling** - Efficient connection management
- **Lazy Loading** - Components load on demand
- **Pagination** - Large lists split into pages
- **Query Optimization** - select_related and prefetch_related

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process using port
taskkill /PID <PID> /F

# Restart backend
cd backend
python manage.py runserver
```

### Frontend won't start
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear cache
npm cache clean --force

# Restart
npm start
```

### WebSocket connection fails
```bash
# Check Daphne is running (not runserver)
daphne -b 0.0.0.0 -p 8000 menumine_ai.asgi:application

# Check Redis is running (optional but recommended)
redis-cli ping
# Should return: PONG
```

### AI features not working
```bash
# Verify Groq API key in .env
echo %GROQ_API_KEY%

# Check logs for AI errors
cd backend
python manage.py shell
>>> from config.ai_config import settings
>>> print(settings.GROQ_API_KEY)
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create feature branch**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **Push to branch**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Open Pull Request**

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for all React components
- Write tests for new features
- Update documentation
- Add meaningful commit messages

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Authors

- **Your Name** - Initial work - [@yourhandle](https://github.com/yourhandle)

---

## 🙏 Acknowledgments

- **Django** - Excellent web framework
- **React** - Powerful UI library
- **Groq** - Fast LLM inference
- **Tailwind CSS** - Beautiful styling
- **RCIP Format** - Recipe standardization

---

## 📧 Support

- **Email:** support@menumine-ai.com
- **Issues:** [GitHub Issues](https://github.com/yourusername/menumine-ai/issues)
- **Documentation:** [Wiki](https://github.com/yourusername/menumine-ai/wiki)

---

## 🗺️ Roadmap

### ✅ Completed (Q4 2024)
- [x] **Multilingual Support** - English, Russian, Hebrew with smart caching
- [x] **IML/CookLingo Translation Databases** - 10,000+ ingredients, 500+ cooking terms
- [x] **Smart Translation Architecture** - 99% cost reduction with cache-first strategy
- [x] **AI Recipe Builder** - Multi-step wizard with duplicate detection
- [x] **Recipe Validation System** - AI-powered quality checks
- [x] **Background Translation Tasks** - Celery-based async translation

### Q1 2025
- [ ] Mobile app (React Native)
- [ ] Meal planning calendar
- [ ] Recipe video support
- [ ] Barcode scanning for inventory
- [ ] Pre-translation system (translate popular recipes overnight)

### Q2 2025
- [ ] Voice commands for shopping lists
- [ ] Smart grocery price comparison
- [ ] Recipe meal prep planning
- [ ] Family nutrition dashboard
- [ ] User-contributed translation improvements

### Q3 2025
- [ ] Integration with smart kitchen devices
- [ ] Recipe video generation with AI
- [ ] Advanced nutrition coaching
- [ ] Additional languages (French, Spanish, German, Arabic)
- [ ] Regional dialect support

---

## 📚 Quick Reference for Developers

### Complete System Files (6-Sprint Implementation)

**Sprint 1: Database Foundation**:
- `backend/apps/core/models.py` - IML, CookLingo, ImportHistory models
- `backend/apps/recipes/models.py` - Recipe, RecipeTranslation, DiscoveryCache models
- `backend/apps/core/services/admin_import_service.py` - Admin import/export
- `backend/apps/core/admin.py` - Django admin configuration
- Migrations: `0003_add_import_history.py`, `0004_add_validation_fields_to_ingredientcache.py`
- Migrations: `0009_add_discovery_cache.py`, `0010_add_enhanced_performance_indexes.py`

**Sprint 2: Service Layer Optimization**:
- `backend/apps/core/services/iml_service.py` - IML in-memory caching (<1ms)
- `backend/apps/core/services/cooklingo_service.py` - CookLingo in-memory caching (<1ms)
- `backend/apps/core/apps.py` - CoreConfig for service initialization
- `backend/apps/core/services/__init__.py` - Service exports
- `backend/test_sprint2_services.py` - Test suite

**Sprint 3: Universal Validation System**:
- `backend/apps/core/services/universal_validator.py` - 3-layer validator
- `backend/apps/core/enums.py` - Validation enums
- `backend/test_sprint3_validator.py` - Test suite

**Sprint 4: 3-Phase Translation System**:
- `backend/apps/core/services/smart_translation_service.py` - Translation orchestrator
- `backend/apps/core/gemini_translator.py` - Gemini PRIMARY
- `backend/apps/core/groq_translator.py` - Groq FALLBACK
- `backend/apps/recipes/tasks.py` - Celery tasks (3 phases)
- `backend/test_sprint4_translation.py` - Test suite

**Sprint 5: Discovery Cache & Background Agents**:
- `backend/apps/core/services/discovery_cache_service.py` - Two-tier caching
- `backend/apps/recipes/tasks.py` - Background agents (4 tasks)
- `backend/apps/recipes/celery_beat_schedule.py` - Celery Beat schedule
- `backend/test_sprint5_discovery.py` - Test suite

**Sprint 6: RCIP 2.0 & Universal Agent API**:
- `backend/apps/core/rcip_models.py` - Pydantic models for RCIP 2.0
- `backend/apps/core/services/universal_agent_service.py` - Universal API
- `backend/test_sprint6_complete.py` - Complete integration test

**Core Services** (used by all sprints):
- `backend/apps/core/services_old.py` - IMLSyncService, CookLingoSyncService (legacy)
- `backend/apps/recipes/builder.py` - Recipe builder with validation
- `backend/apps/recipes/views.py` - API endpoints
- `backend/menumine_ai/settings.py` - Django settings with CoreConfig

**Frontend**:
- `frontend/src/i18n.ts` - i18next configuration
- `frontend/src/locales/en.json` - English UI strings
- `frontend/src/locales/ru.json` - Russian UI strings
- `frontend/src/locales/he.json` - Hebrew UI strings
- `frontend/src/pages/CanonicalRecipesPage.tsx` - Discovery page with translation polling
- `frontend/src/components/RecipeBuilderWizard.tsx` - Recipe builder wizard

**Documentation**:
- `AI_IMPLEMENTATION_GUIDE_6_SPRINTS.md` - Complete implementation guide for AI models
- `SPRINT_1_COMPLETE_SUMMARY.md` - Sprint 1 summary
- `SPRINT_2_COMPLETE_SUMMARY.md` - Sprint 2 summary
- `SPRINT_3_COMPLETE_SUMMARY.md` - Sprint 3 summary
- `SPRINT_4_COMPLETE_SUMMARY.md` - Sprint 4 summary
- `SPRINT_5_COMPLETE_SUMMARY.md` - Sprint 5 summary
- `SPRINT_6_COMPLETE_SUMMARY.md` - Sprint 6 summary
- `ALL_SPRINTS_COMPLETE_FINAL_SUMMARY.md` - Final summary

### Key Database Tables

```sql
-- Core recipe storage (canonical, language-agnostic)
canonical_recipes (
    id UUID PRIMARY KEY,
    name VARCHAR(500),
    description TEXT,
    base_ingredients JSONB,  -- Canonical structure with IML keys
    base_steps JSONB,         -- Canonical structure with CookLingo keys
    tags JSONB,
    image_url TEXT,
    is_published BOOLEAN,
    source_language VARCHAR(2),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    author_id UUID
)

-- Translation cache (one row per recipe per language)
recipe_translations (
    id UUID PRIMARY KEY,
    canonical_recipe_id UUID REFERENCES canonical_recipes(id),
    language VARCHAR(2),  -- 'en', 'he', 'ru'
    name VARCHAR(500),
    description TEXT,
    content JSONB,  -- Full translated content
    status VARCHAR(50),  -- 'pending', 'in_progress', 'completed', 'failed'
    confidence INTEGER,  -- 0-100
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(canonical_recipe_id, language)
)

-- Discovery cache (pre-computed for fast page loads)
discovery_cache (
    id UUID PRIMARY KEY,
    canonical_recipe_id UUID REFERENCES canonical_recipes(id),
    language VARCHAR(2),
    title TEXT,
    brief TEXT,  -- First 200 chars
    image_url TEXT,
    tags JSONB,
    cached_at TIMESTAMP,
    UNIQUE(canonical_recipe_id, language)
)

-- IML: Ingredient Master List (10,000+ ingredients)
iml_ingredients (
    ingredient_key VARCHAR(100) PRIMARY KEY,
    en_name VARCHAR(200),
    he_name VARCHAR(200),
    ru_name VARCHAR(200),
    category VARCHAR(50),  -- 'grain', 'meat', 'vegetable', 'dairy', etc.
    aliases JSONB,
    -- Validation fields (Sprint 1)
    typical_amount_min INTEGER,
    typical_amount_max INTEGER,
    typical_amount_avg INTEGER,
    max_per_serving INTEGER,
    warning_threshold INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- CookLingo: Cooking terminology glossary (500+ terms)
cooklingo_terms (
    term_key VARCHAR(100) PRIMARY KEY,
    en_term VARCHAR(200),
    he_term VARCHAR(200),
    ru_term VARCHAR(200),
    category VARCHAR(50),  -- 'method', 'texture', 'temperature', 'equipment'
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- Import history (admin tracking)
import_history (
    import_id UUID PRIMARY KEY,
    import_type VARCHAR(50),  -- 'iml', 'cooklingo', 'iml_delete', etc.
    source_file VARCHAR(255),
    records_imported INTEGER,
    records_updated INTEGER,
    records_failed INTEGER,
    imported_by VARCHAR(100),
    imported_at TIMESTAMP,
    status VARCHAR(50),  -- 'success', 'partial', 'failed'
    error_log TEXT
)
```

### Testing the 6-Sprint System

```bash
# Test Sprint 2: Service Layer (IML + CookLingo in-memory caching)
python backend/test_sprint2_services.py

# Test Sprint 3: Universal Validation System
python backend/test_sprint3_validator.py

# Test Sprint 4: 3-Phase Translation System
python backend/test_sprint4_translation.py

# Test Sprint 5: Discovery Cache & Background Agents
python backend/test_sprint5_discovery.py

# Test Sprint 6: Complete Integration (RCIP 2.0 + Universal Agent API)
python backend/test_sprint6_complete.py
```

**Backend Shell Testing**:
```python
# Django shell
python manage.py shell

# Test IML Service (Sprint 2)
>>> from apps.core.services import get_iml_service
>>> iml = get_iml_service()
>>> iml.translate_ingredient("tomato", "ru")
"помидор"
>>> iml.translate_ingredient("tomato", "he")
"עגבנייה"

# Test CookLingo Service (Sprint 2)
>>> from apps.core.services import get_cooklingo_service
>>> cooklingo = get_cooklingo_service()
>>> cooklingo.translate_term("dice", "ru")
"нарезать кубиками"

# Test Universal Validator (Sprint 3)
>>> from apps.core.services import get_universal_validator
>>> validator = get_universal_validator()
>>> result = validator.validate_recipe(recipe_data)
>>> print(f"Valid: {result.is_valid}, Score: {result.overall_score}")

# Test Smart Translation Service (Sprint 4)
>>> from apps.core.services import get_smart_translation_service
>>> translator = get_smart_translation_service()
>>> result = translator.translate_recipe(recipe_data, "ru", phase="immediate")
>>> print(f"Success: {result.success}, Time: {result.execution_time_ms}ms")

# Test Discovery Cache Service (Sprint 5)
>>> from apps.core.services import get_discovery_cache_service
>>> cache = get_discovery_cache_service()
>>> recipes = cache.get_discovery_page("ru", page=1, page_size=20)
>>> print(f"Found {len(recipes)} recipes")

# Test Universal Agent API (Sprint 6)
>>> from apps.core.services import get_universal_agent_service
>>> agent = get_universal_agent_service()
>>> result = agent.submit_recipe(recipe_data, "my-agent")
>>> print(f"Recipe ID: {result['recipe_id']}, Validation Score: {result['validation']['score']}")
```

**Celery Testing**:
```bash
# Start Celery worker (in one terminal)
celery -A menumine_ai worker --loglevel=info

# Start Celery Beat (in another terminal)
celery -A menumine_ai beat --loglevel=info

# Or combined for development
celery -A menumine_ai worker --beat --loglevel=info

# Monitor active tasks
celery -A menumine_ai inspect active

# Monitor scheduled tasks
celery -A menumine_ai inspect scheduled

# Test translation tasks manually
python manage.py shell
>>> from apps.recipes.tasks import translate_recipe_immediate
>>> translate_recipe_immediate.delay("recipe-uuid", "ru")
```

### Monitoring System Performance

```python
# Check translation cache hit rate
>>> from apps.recipes.models import RecipeTranslation
>>> total = RecipeTranslation.objects.count()
>>> completed = RecipeTranslation.objects.filter(status='completed').count()
>>> print(f"Cache hit rate: {completed/total*100:.1f}%")

# Check service memory usage
>>> from apps.core.services import get_iml_service, get_cooklingo_service
>>> iml = get_iml_service()
>>> cooklingo = get_cooklingo_service()
>>> print(f"IML loaded: {len(iml._cache)} ingredients")
>>> print(f"CookLingo loaded: {len(cooklingo._cache)} terms")

# Check discovery cache performance
>>> from django.core.cache import cache
>>> from apps.recipes.models import DiscoveryCache
>>> redis_count = len(cache.keys('discovery:*'))
>>> pg_count = DiscoveryCache.objects.count()
>>> print(f"Redis cache: {redis_count} entries")
>>> print(f"PostgreSQL cache: {pg_count} entries")

# Monitor Celery task performance
>>> from celery.task.control import inspect
>>> i = inspect()
>>> active = i.active()
>>> scheduled = i.scheduled()
>>> print(f"Active tasks: {len(active)}")
>>> print(f"Scheduled tasks: {len(scheduled)}")
```

**Redis Monitoring**:
```bash
# Connect to Redis
redis-cli

# Check memory usage
INFO memory

# Check all keys
KEYS *

# Check discovery cache keys
KEYS discovery:*

# Check Celery task queue
LLEN celery

# Clear all cache (USE WITH CAUTION!)
FLUSHALL
```

### Common Issues & Solutions

#### 1. "Services not initialized" or "AttributeError: 'NoneType'"
```python
# Check if CoreConfig is being used in settings.py
# Should be: 'apps.core.apps.CoreConfig' NOT 'apps.core'

# Restart Django to trigger initialization
python manage.py runserver

# Check logs for initialization messages
# Should see: "🚀 Initializing core services..." and "✅ Core services initialized successfully."
```

#### 2. "Translation taking too long" or "stuck in 'pending' status"
```bash
# Check if Celery is running
celery -A menumine_ai worker --loglevel=info

# Check if Celery Beat is running (for background agents)
celery -A menumine_ai beat --loglevel=info

# Check Redis is running
redis-cli ping  # Should return PONG

# Monitor active Celery tasks
celery -A menumine_ai inspect active

# Check for failed tasks
python manage.py shell
>>> from apps.recipes.models import RecipeTranslation
>>> failed = RecipeTranslation.objects.filter(status='failed')
>>> for f in failed:
...     print(f"{f.canonical_recipe.name} - {f.language}: {f.error_message}")
```

#### 3. "Gemini quota exceeded" or "Translation failing"
```python
# System automatically falls back to Groq
# Check error messages in RecipeTranslation
>>> from apps.recipes.models import RecipeTranslation
>>> recent = RecipeTranslation.objects.filter(status='failed').order_by('-created_at')[:5]
>>> for r in recent:
...     print(f"Error: {r.error_message}")

# Check AI provider usage
>>> completed = RecipeTranslation.objects.filter(status='completed')
>>> gemini_count = completed.filter(content__ai_provider='gemini').count()
>>> groq_count = completed.filter(content__ai_provider='groq').count()
>>> print(f"Gemini: {gemini_count}, Groq: {groq_count}")

# Switch to Groq as PRIMARY if needed
# Edit: backend/apps/core/services/smart_translation_service.py
# Change order: try Groq first, then Gemini fallback
```

#### 4. "Translations not showing in frontend"
```javascript
// Check browser console for:

// 1. Language is set correctly
console.log(i18n.language);  // Should be 'ru' or 'he'

// 2. API is returning translated data
// Network tab → Check /api/recipes/discovery/ response

// 3. Polling is working (for on-demand translations)
// Should see requests every 2s when translation status is 'pending'

// 4. Check translation status in API response
// Should have: translation_status: 'completed' or 'pending'
```

#### 5. "Discovery page slow to load"
```bash
# Check if Redis is running
redis-cli ping

# Check Redis cache hit rate
redis-cli
> KEYS discovery:*
> GET discovery:he:page1

# If no cache, trigger manual refresh
python manage.py shell
>>> from apps.core.services import get_discovery_cache_service
>>> cache = get_discovery_cache_service()
>>> cache.refresh_all('en')
>>> cache.refresh_all('he')
>>> cache.refresh_all('ru')

# Start Celery Beat to enable automatic cache refresh
celery -A menumine_ai beat --loglevel=info
```

#### 6. "IML/CookLingo lookups slow or failing"
```python
# Check if services are initialized
>>> from apps.core.services import get_iml_service, get_cooklingo_service
>>> iml = get_iml_service()
>>> cooklingo = get_cooklingo_service()
>>> print(f"IML initialized: {iml._initialized}")
>>> print(f"CookLingo initialized: {cooklingo._initialized}")

# If not initialized, check Django settings.py
# Must use: 'apps.core.apps.CoreConfig'

# Reload services manually
>>> iml.reload()
>>> cooklingo.reload()
```

---

<div align="center">

**Made with ❤️ for families who love good food**

[Website](https://menumine-ai.com) • [Documentation](https://docs.menumine-ai.com) • [Blog](https://blog.menumine-ai.com)

</div>
