# MenuMind AI – EmailJS Integration Brief

This document captures the existing email verification implementation and requirements to help an external agent integrate EmailJS for real email delivery.

---

## 1. Technology Stack

- **Frontend:** React 18 SPA, TypeScript, React Router v6, Tailwind CSS, i18next, react-hot-toast.
- **State management:** Context providers (`AuthContext`, `CollaborationContext`); no Redux.
- **Backend:** Django 4.2, Django REST Framework, Django Channels, Celery 5.3, SimpleJWT, django-allauth, dj-rest-auth.
- **Runtime / Build:** Node.js 18+ (CRA/Webpack), Python 3.11. Redis used for cache/broker.

---

## 2. Current Verification Logic

- **Backend modules:**
  - `backend/apps/users/views.py`
    - `UserRegistrationView` (`create`) – registers user, creates `EmailAddress`, sends confirmation via allauth (`send_email_confirmation`).
    - `resend_verification_email` – authenticated endpoint to resend verification link.
  - `backend/apps/users/adapters.py` – `MultilingualAccountAdapter` builds multilingual templates, constructs `verify-email/{key}` URL, currently calls Django `send_mail`.
  - `backend/apps/users/urls.py` – registers auth routes including resend endpoint.
  - `backend/apps/users/serializers.py` – `UserRegistrationSerializer`, `UserSerializer` exposing `email_verified` flag.
  - `backend/apps/users/models.py` – custom `User` model extends `AbstractUser` with UUID PK and verification helpers.

- **Frontend components:**
  - `frontend/src/pages/VerifyEmail.tsx` – handles verification page, posts `{ key }` to `/dj-rest-auth/registration/verify-email/` and displays success/error states.
  - `frontend/src/components/EmailVerificationBanner.tsx` – displays banner for unverified users with `Resend` action calling `/api/users/auth/resend-verification/`.
  - `frontend/src/contexts/AuthContext.tsx` – fetches profile, merges `email_verified` flag; drives banner visibility.

- **Triggers & flow:**
  1. User registers via React registration form → POST `/api/users/auth/register/`.
  2. Backend creates `EmailAddress` (verified=False) and sends email via allauth adapter.
  3. Email contains URL `{FRONTEND_URL}/verify-email/{key}`. Templates localized (English/Russian/Hebrew).
  4. User clicks link; SPA `VerifyEmail.tsx` auto POSTs verification key to `/dj-rest-auth/registration/verify-email/`.
  5. Upon success, AuthContext reload ensures user flagged as verified; banner disappears. Certain endpoints use `@verified_email_required` decorator to enforce verification.

- **Token handling:** Managed by django-allauth (`EmailConfirmation`). Tokens stored in DB; `send_email_confirmation` handles generation.

---

## 3. Email Requirements

- **Email types currently in use:**
  - Email verification (mandatory). Templates exist under `backend/templates/account/email/` with multilingual support.
- **Likely upcoming emails:** Welcome/onboarding, password reset (dj-rest-auth endpoints available but templates not customized yet).
- **Email content:** Templates include user name, verification link (`activate_url`), site branding via `current_site`. HTML and text versions rendered via Django templates. Custom styling already in place.

---

## 4. Project Structure Snapshot

```
menumine-ai/
  frontend/
    src/pages/VerifyEmail.tsx
    src/components/EmailVerificationBanner.tsx
    src/contexts/AuthContext.tsx
  backend/
    apps/users/views.py
    apps/users/adapters.py
    apps/users/models.py
    apps/users/serializers.py
    apps/users/urls.py
    menumine_ai/settings.py
  docs/
  scripts/
  ...
```

- User/auth logic centered in `backend/apps/users/` and `frontend/src/pages|components|contexts`.
- External integrations (future EmailJS) would live under `backend/apps/users/services/` or similar.
- Environment variables stored in backend `.env` (loaded via `environ.Env`). Frontend uses `REACT_APP_*` variables for API URL, Google OAuth client ID.

---

## 5. User Registration & Verification Flow

1. User fills registration form (email, username, password, first/last name).
2. Submission to `/api/users/auth/register/` returns JWT tokens and message to verify email.
3. Allauth sends verification email from server with localized HTML template.
4. User clicks verification link. `VerifyEmail.tsx` handles both `/verify-email/:key` and `/verify-email?key=...` formats.
5. Component POSTs key to `/dj-rest-auth/registration/verify-email/`. On success, displays confirmation with “Continue to App” button (reload forces AuthContext refresh).
6. If verification fails, renders error state with “Back to Login”.
7. Logged-in users see `EmailVerificationBanner` until verified; clicking “Resend email” calls `/api/users/auth/resend-verification/`.

---

## 6. Current Configuration

- **Email service:** Django `send_mail` with credentials pulled from env vars (`EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, etc.). For development, logs verification details to console.
- **Environment variables:** Stored in backend `.env`; key ones include `SECRET_KEY`, `DATABASE_URL`, `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`, `FRONTEND_URL`, OAuth client IDs, AI provider keys.
- **Validation libraries:** Django form validation; frontend performs basic form checks but no dedicated email validation lib beyond HTML5.

---

## 7. Key Code References

- **Registration endpoint:** `backend/apps/users/views.py#26-62`.
- **Resend verification:** `backend/apps/users/views.py#266-331`.
- **Account adapter:** `backend/apps/users/adapters.py#7-76` (ideal hook to swap SMTP for EmailJS REST call).
- **Frontend verification page:** `frontend/src/pages/VerifyEmail.tsx#1-109`.
- **Verification banner:** `frontend/src/components/EmailVerificationBanner.tsx#5-78`.
- **User model:** `backend/apps/users/models.py#7-186` (UUID primary key, preferences, verification flags consumed elsewhere).
- **Verified decorator:** `backend/apps/users/decorators.py#7-27` (enforces email verification on protected views).

---

## 8. Considerations for EmailJS Integration

- Replace `send_mail` usage inside `MultilingualAccountAdapter.send_confirmation_mail` with EmailJS REST call (server-side recommended to keep keys secret).
- Keep verification tokens generated by allauth; only change transport mechanism.
- Store EmailJS service/template IDs and private key in backend environment variables; never expose via frontend.
- Consider reusable helper service (e.g., `backend/apps/users/services/email_service.py`) wrapping EmailJS requests, supporting future email types (welcome, password reset).
- Align templates: either continue rendering Django HTML (send via EmailJS composed body) or migrate to EmailJS template system.
- Update resend endpoint to use new service; handle logging/exception mapping for better observability.
- Verify `DEFAULT_FROM_EMAIL` matches verified sender in EmailJS.

---

## Outstanding Questions

To fully implement EmailJS, confirm:
1. Preferred EmailJS delivery method – server-to-server (recommended) vs client SDK.
2. Target email types beyond verification (welcome, password reset, recipe notifications, etc.).
3. Whether to keep existing Django templates or recreate in EmailJS template designer.
4. Requirements for localized content (EmailJS templates per language or render server-side before sending).
5. Error handling expectations (retry policies, logging, user messaging).
6. Budget/limits on EmailJS usage, fallback strategy if EmailJS fails.

---

Use this brief to onboard external collaborators to the current verification system and scope the EmailJS integration work.
