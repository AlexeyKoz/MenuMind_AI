# MenuMindAI – Google OAuth & Email Verification Implementation

This document explains the four sprint implementation plan used to introduce Google OAuth login and email verification into the MenuMindAI platform. It is intended for external AI assistants reviewing or continuing the work and therefore highlights the exact code, configuration, and behavioural changes applied during each sprint.

---

## Sprint 1 – Backend Foundation Setup

**Objective:** Prepare Django to use `django-allauth` and `dj-rest-auth` with JWT, add Google provider scaffolding, and ensure email infrastructure is ready.

### Dependencies
- Installed (and pinned) packages: `django-allauth==0.63.0`, `dj-rest-auth==6.0.0`, `google-auth==2.35.0`. (`pip install …` + `pip freeze > requirements.txt`).

### Django Settings (`backend/menumine_ai/settings.py`)
- Added required apps: `django.contrib.sites`, `allauth` modules, `dj_rest_auth`, and `rest_framework.authtoken`.
- Added `AccountMiddleware` into `MIDDLEWARE`.
- Configured template directory: `DIRS = [BASE_DIR / 'templates']`.
- Appended site/account/JWT/email configuration:
  - `SITE_ID = 1`
  - Authentication backends include `allauth.account.auth_backends.AuthenticationBackend`.
  - `REST_USE_JWT = True`; cookies disabled for JWT.
  - Enforced account policies: email required, unique, mandatory verification, etc.
  - Configured `SOCIALACCOUNT_PROVIDERS['google']` to load credentials from environment variables.
  - Development email backend set to console; production section reads SMTP settings from env.
  - `FRONTEND_URL` variable introduced for template links.
  - Registered custom adapter placeholder (`ACCOUNT_ADAPTER = 'apps.users.adapters.MultilingualAccountAdapter'`) for later sprint use.

### URLs (`backend/menumine_ai/urls.py`)
- Added `accounts/` (allauth), `dj-rest-auth/`, and `dj-rest-auth/registration/` routes.

### Environment Variables (`backend/.env` – manually maintained)
- Added placeholders for Google credentials, SMTP settings, `DEFAULT_FROM_EMAIL`, and `FRONTEND_URL`.
- Note: `.env` is gitignored; changes must be applied manually by operators.

### Database & Site
- Ran `python manage.py migrate` to create tables (`account_*`, `socialaccount_*`, `authtoken_*`, etc.).
- Configured `Site` (id=1) via Django shell to `domain=localhost:8000`, `name=MenuMindAI`.

**Acceptance:** Django server starts without errors; `/dj-rest-auth/registration/` and `/accounts/` respond.

---

## Sprint 2 – Backend Custom Logic

**Objective:** Build project-specific integration pieces on top of the allauth/dj-rest-auth foundation.

### Google OAuth Endpoint (`backend/apps/users/views_google.py`)
- New API: `POST /api/users/auth/google/`.
- Verifies Google ID token (`google.oauth2.id_token.verify_oauth2_token()`), merges account by email, ensures profile names populated.
- Sets unusable password for new OAuth users, refreshes missing names on existing users.
- Auto-verifies email via `EmailAddress` (`allauth`) creation/updates.
- Returns SimpleJWT tokens + serialized user via `UserSerializer`.

### URL Exposure (`backend/apps/users/urls.py`)
- Added `path('auth/google/', google_login, name='google_login')` to user routes.

### Email Verification Decorator (`backend/apps/users/decorators.py`)
- Provides `@verified_email_required` decorator returning 401/403 if user unauthenticated or lacks verified address (allauth-aware).

### Multilingual Account Adapter (`backend/apps/users/adapters.py`)
- Extends `DefaultAccountAdapter` to:
  - Determine user language (defaults to `en`, uses `user.preferred_language` when available).
  - Render subject/body from language-specific templates, falling back to English.
  - Send both HTML and plain text (stripped) messages.

### Email Templates (`backend/templates/account/email/…`)
- Added localized confirmation templates:
  - `email_confirmation_en_subject.txt` / `_message.html`
  - `email_confirmation_he_subject.txt` / `_message.html`
  - `email_confirmation_ru_subject.txt` / `_message.html`
- Hebrew template uses `dir="rtl"` and localized copy; all languages include CTA button, fallback link, expiry notice.

### Settings Update
- `ACCOUNT_ADAPTER` already registered (Sprint 1).
- `TEMPLATES` directory path active from Sprint 1 ensures Django loads new templates.

**Acceptance:**
- `/api/users/auth/google/` returns 400 for invalid tokens (smoke test with dummy `credential`).
- Email confirmation messages render through console backend when registering new users.

---

## Sprint 3 – Frontend Foundation

**Objective:** Prepare React app to talk to new backend endpoints, support Google OAuth provider, and surface translations.

### Dependencies & Config
- Installed `@react-oauth/google` (using `--legacy-peer-deps` to satisfy React Scripts / TypeScript constraints).
- Added `.env` expectations (manual): `REACT_APP_GOOGLE_CLIENT_ID`, `REACT_APP_API_URL` (defaults to `http://localhost:8000` in code if unset).

### API Service (`frontend/src/services/api.ts`)
- Base URL now derived from `REACT_APP_API_URL`, automatically appending `/api` and trimming stray slashes.

### Google Provider Wrapper
- New component `AppWithProviders` wraps `<App />` inside `<GoogleOAuthProvider>` using the client ID.
- Updated entry point `src/index.tsx` to render `<AppWithProviders />`.

### Translations
- Added Google login & email verification strings to `en.json`, `he.json`, and `ru.json`. Keys cover button label, error states, verification statuses, resend messaging, etc.

**Acceptance:** App builds with provider wrapper (no usage yet). Translation keys available for upcoming UI.

---

## Sprint 4 – Frontend Integration

**Objective:** Wire UI flows (login, verification, banners) and integrate routing to support email verification page.

### Routing & Shell (`frontend/src/App.tsx`)
- Introduced `react-router-dom` routes:
  - Public users can access `/verify-email` and `/verify-email/:key` without being logged in.
  - Authenticated users route to dashboard/shopping/etc., defaulting to last visited section.
- Added `EmailVerificationBanner` to authenticated view.
- `BrowserRouter` now wraps the entire app.

### Provider Entry (`frontend/src/AppWithProviders.tsx`, `src/index.tsx`)
- Already created in Sprint 3; ensures Google OAuth context available before routers/auth providers run.

### Google Sign-In Button (`frontend/src/components/GoogleSignInButton.tsx`)
- Uses `useGoogleLogin` to request implicit OAuth tokens.
- Calls `POST /api/users/auth/google/` with `credential` (access token) and stores returned JWTs in `localStorage`.
- Exposes `onSuccess` / `onError` callbacks for parent components.

### Verification Banner (`frontend/src/components/EmailVerificationBanner.tsx`)
- Displays pending verification notice with resend action (calls backend `dj-rest-auth/registration/resend-email/`).
- Currently assumes users have `email_verified` flag (AuthContext now supports it); should be wired to actual flag once returned by backend.

### Verification Page (`frontend/src/pages/VerifyEmail.tsx`)
- Consumes `key` from path or query string.
- Posts to `dj-rest-auth/registration/verify-email/` and renders success/error states with localized copy.
- On completion, provides navigation back to main app.

### Auth Context (`frontend/src/contexts/AuthContext.tsx`)
- Reads all requests via `REACT_APP_API_URL` base.
- Persists `email_verified` when available from profile/login/register responses so the banner and future logic can react accordingly.

### Login Page (pending minor wiring)
- Google button component prepared; integrate into `pages/Login.tsx` with UI divider when ready.

**Acceptance:** Frontend recognizes environment-configured API base, uses Google provider, and surfaces verification UX. Further testing requires hooking Google button into login screen and verifying `email_verified` data flow from backend responses.

---

## Operational Notes & Next Steps

1. **Environment:**
   - Backend `.env` must define Google OAuth client ID/secret, SMTP credentials, and `FRONTEND_URL`.
   - Frontend `.env` must define `REACT_APP_GOOGLE_CLIENT_ID` and optionally `REACT_APP_API_URL` for non-local deployments.

2. **Backend follow-up:**
   - Expose `email_verified` field in `UserSerializer` / profile responses to fully support banner logic.
   - Provide resend endpoint (`dj-rest-auth` offers `registration/resend-email/`; ensure enabled or implement custom view).

3. **Frontend follow-up:**
   - Insert `GoogleSignInButton` into `Login.tsx` (and optionally `Registration.tsx`).
   - Finalize banner to hide once `email_verified` is true from auth context.
   - QA routing (particularly existing deep links) after router introduction.

4. **QA Checklist Recap:**
   - Registration triggers console email with localized template.
   - Visiting verification link (with `key=`) updates account status.
   - Google login merges existing accounts by email and issues JWTs.
   - Banner/resend logic available post-login for unverified users (once backend flag operational).

This document should provide sufficient context for external AI systems to understand the modifications applied during each sprint and how they interconnect across MenuMindAI’s backend and frontend stacks.
