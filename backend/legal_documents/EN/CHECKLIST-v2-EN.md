# Implementation Checklist - BishulMe Legal Framework

**Version:** 2.0  
**Date:** January 1, 2025  
**Use this checklist to track your progress through implementation**

---

## 📋 HOW TO USE THIS CHECKLIST

1. Print this document OR keep it open in a separate window
2. Check off items as you complete them
3. Don't skip items - order matters for some tasks
4. Estimated time shown for each phase
5. If stuck, refer to AI-AGENT-PROMPT files for code examples

---

## PHASE 1: BACKEND SETUP (2-3 hours)

### Database Models

- [ ] Create `legal/models.py` file
- [ ] Copy UserConsent model code
- [ ] Create `api/models.py` file (if doesn't exist)
- [ ] Copy AIUsageLog model code
- [ ] Create `accounts/models.py` additions
- [ ] Copy DataExportRequest model code
- [ ] Run `python manage.py makemigrations`
- [ ] Run `python manage.py migrate`
- [ ] Verify tables created in database

### Legal Views

- [ ] Create `legal/views.py` file
- [ ] Copy LegalPageView base class
- [ ] Add TermsOfServiceView
- [ ] Add PrivacyPolicyView
- [ ] Add CookiePolicyView
- [ ] Create `legal/urls.py` file
- [ ] Add URL patterns for legal pages
- [ ] Include legal URLs in main `urls.py`
- [ ] Test: Visit /terms, /privacy, /cookies URLs

### Legal Document Storage

- [ ] Create `legal_docs/` directory in project root
- [ ] Copy FINAL-terms-of-service-v3-EN.md to legal_docs/
- [ ] Copy FINAL-privacy-policy-v3-EN.md to legal_docs/
- [ ] Copy FINAL-cookie-policy-v3-EN.md to legal_docs/
- [ ] Install markdown package: `pip install markdown`
- [ ] Test: Legal pages render markdown correctly

### API Endpoints

- [ ] Create `api/views/consent.py` file
- [ ] Add CookieConsentView (POST endpoint)
- [ ] Add PrivacySettingsView (GET/PUT endpoints)
- [ ] Create URLs for consent endpoints
- [ ] Test endpoints with Postman/curl

**Phase 1 Complete? Move to Phase 2!**

---

## PHASE 2: COOKIE BANNER (2-3 hours)

### React Component

- [ ] Create `frontend/components/CookieBanner/` directory
- [ ] Create `CookieBanner.tsx` file
- [ ] Copy CookieBanner component code
- [ ] Create `frontend/utils/cookies.ts` utility
- [ ] Add getCookie, setCookie helper functions
- [ ] Import CookieBanner in main App.tsx
- [ ] Add CookieBanner to App layout

### Cookie Banner Logic

- [ ] Implement consent state management
- [ ] Add GPC (navigator.globalPrivacyControl) detection
- [ ] Create handleAcceptAll function
- [ ] Create handleRejectAll function
- [ ] Create handleCustomize function
- [ ] Connect to backend API (/api/consent/cookies/)
- [ ] Test: Banner shows on first visit

### Button Styling (CRITICAL)

- [ ] Verify Accept and Reject buttons are EQUAL size
- [ ] Verify Accept and Reject buttons have EQUAL prominence
- [ ] No green vs red colors (stay neutral)
- [ ] Test: Buttons look symmetric on desktop
- [ ] Test: Buttons look symmetric on mobile
- [ ] Screenshot banner for documentation

### Cookie Categories

- [ ] Add Essential cookies section (always on)
- [ ] Add Functional cookies toggle
- [ ] Add Analytics cookies toggle
- [ ] Add Performance cookies toggle
- [ ] Add descriptions for each category
- [ ] Test: Toggles work correctly

### GPC Support

- [ ] Test with GPC-enabled browser (Firefox/Brave)
- [ ] Verify automatic rejection of non-essential cookies
- [ ] Log GPC signal to backend
- [ ] Test: No banner shows if GPC enabled
- [ ] Document GPC behavior

### Google Analytics Integration

- [ ] Add conditional GA loading (only if consent given)
- [ ] Configure GA with IP anonymization
- [ ] Set cookie_flags: SameSite=None;Secure
- [ ] Test: GA loads when analytics accepted
- [ ] Test: GA doesn't load when analytics rejected

**Phase 2 Complete? Move to Phase 3!**

---

## PHASE 3: LEGAL PAGES (1 hour)

### Page Templates

- [ ] Create `legal/templates/legal/` directory
- [ ] Create `base.html` template
- [ ] Create `terms.html` template
- [ ] Create `privacy.html` template
- [ ] Create `cookies.html` template
- [ ] Add consistent styling across pages

### Content Display

- [ ] Test: Terms page renders correctly
- [ ] Test: Privacy page renders correctly
- [ ] Test: Cookies page renders correctly
- [ ] Test: Markdown formatting looks good
- [ ] Test: Links work within documents
- [ ] Test: Pages are readable on mobile

### Footer Links

- [ ] Add footer component to base template
- [ ] Add link to Terms of Service
- [ ] Add link to Privacy Policy
- [ ] Add link to Cookie Policy
- [ ] Add link to RCIP License (optional)
- [ ] Add contact email (bishulme@gmail.com)
- [ ] Test: Footer shows on all pages
- [ ] Test: Footer responsive on mobile

### Multilingual Support (if needed)

- [ ] Create Hebrew versions directory
- [ ] Create Russian versions directory
- [ ] Add language switcher (if applicable)
- [ ] Test language switching

**Phase 3 Complete? Move to Phase 4!**

---

## PHASE 4: REGISTRATION (1-2 hours)

### Registration Form

- [ ] Create `frontend/pages/Register.tsx` file
- [ ] Copy Register component code
- [ ] Add email input field
- [ ] Add password input field
- [ ] Add confirm password field
- [ ] Add name input field (optional)
- [ ] Add birthdate input field (REQUIRED for 18+)

### Legal Checkbox (CRITICAL)

- [ ] Add checkbox: "I agree to Terms, Privacy, Cookie Policy"
- [ ] Make checkbox REQUIRED
- [ ] Add links to Terms, Privacy, Cookies (open in new tab)
- [ ] Style checkbox prominently
- [ ] Test: Form won't submit without checkbox
- [ ] Test: Links open legal pages correctly

### Age Verification (CRITICAL)

- [ ] Add birthdate validation
- [ ] Calculate age from birthdate
- [ ] Reject if under 18 years old
- [ ] Show clear error message
- [ ] Test: 17-year-old gets rejected
- [ ] Test: 18-year-old is accepted
- [ ] Test: Future dates rejected

### Backend Registration

- [ ] Create `api/views/auth.py` registration view
- [ ] Validate email format
- [ ] Validate password strength (min 8 chars)
- [ ] Validate age (18+)
- [ ] Validate legal acceptance
- [ ] Create user account
- [ ] Create UserConsent record
- [ ] Send verification email

### Email Verification

- [ ] Create verification email template
- [ ] Generate verification token
- [ ] Send email with verification link
- [ ] Create email verification endpoint
- [ ] Handle token validation
- [ ] Activate user account on verification
- [ ] Test: Verification email received
- [ ] Test: Clicking link activates account

### Testing Registration Flow

- [ ] Test: Valid registration succeeds
- [ ] Test: Missing legal checkbox fails
- [ ] Test: Under 18 fails
- [ ] Test: Weak password fails
- [ ] Test: Invalid email fails
- [ ] Test: Duplicate email fails
- [ ] Test: Mobile registration works

**Phase 4 Complete? Move to Phase 5!**

---

## PHASE 5: PRIVACY SETTINGS (2-3 hours)

### Settings Page

- [ ] Create `frontend/pages/PrivacySettings.tsx` file
- [ ] Copy PrivacySettings component code
- [ ] Add page to routing
- [ ] Add link in user menu/settings
- [ ] Test: Page loads for logged-in users
- [ ] Test: Redirects to login if not authenticated

### Cookie Preferences Section

- [ ] Display current cookie preferences
- [ ] Add toggle for Functional cookies
- [ ] Add toggle for Analytics cookies
- [ ] Add toggle for Performance cookies
- [ ] Show "Always Active" for Essential cookies
- [ ] Add descriptions for each category
- [ ] Create Save button
- [ ] Connect to backend API

### Data Export (GDPR Article 20)

- [ ] Add "Export My Data" section
- [ ] Add explanation text
- [ ] Add "Export My Data" button
- [ ] Create backend export endpoint
- [ ] Create Celery task for data export
- [ ] Generate JSON export file
- [ ] Send email with download link
- [ ] Set 30-day expiration on download link
- [ ] Test: Export request created
- [ ] Test: Email received with link
- [ ] Test: Downloaded file contains all data

### Account Deletion (GDPR Article 17)

- [ ] Add "Delete My Account" section
- [ ] Add warning message (CANNOT BE UNDONE)
- [ ] Add confirmation dialog ("Type DELETE")
- [ ] Add second confirmation
- [ ] Create backend deletion endpoint
- [ ] Mark user for deletion (don't delete immediately)
- [ ] Schedule deletion (30 days)
- [ ] Send confirmation email
- [ ] Log out user after deletion request
- [ ] Test: Deletion request works
- [ ] Test: User data actually deleted after 30 days

### Additional Links

- [ ] Add link to Privacy Policy
- [ ] Add link to Cookie Policy
- [ ] Add link to Terms of Service
- [ ] Add contact email for privacy questions
- [ ] Test: All links work

### Mobile Responsiveness

- [ ] Test settings page on mobile
- [ ] Test toggles work on mobile
- [ ] Test buttons accessible on mobile
- [ ] Test confirmation dialogs on mobile

**Phase 5 Complete? Move to Phase 6!**

---

## PHASE 6: RATE LIMITING (1-2 hours)

### Rate Limiting Middleware

- [ ] Create `utils/rate_limiting.py` file
- [ ] Copy RateLimitMiddleware code
- [ ] Add middleware to MIDDLEWARE in settings.py
- [ ] Configure Redis connection
- [ ] Start Redis server
- [ ] Test: Middleware loads without errors

### AI Request Tracking

- [ ] Verify AIUsageLog model exists
- [ ] Add logging to AI endpoints
- [ ] Log request type, prompt, provider
- [ ] Log tokens used, latency, cost
- [ ] Log user plan (free/premium)
- [ ] Log IP address and user agent
- [ ] Test: AI requests create log entries

### Daily Limit Enforcement

- [ ] Implement get_daily_count() function
- [ ] Check limit: 10 for free, 100 for premium
- [ ] Return 429 status if exceeded
- [ ] Include limit info in error response
- [ ] Include reset time in error response
- [ ] Test: 11th request blocked (free user)
- [ ] Test: 101st request blocked (premium user)

### Cooldown Enforcement

- [ ] Create cooldown check function
- [ ] Use Redis for cooldown tracking
- [ ] Set 30-second cooldown (free users only)
- [ ] Skip cooldown for premium users
- [ ] Return wait time in error response
- [ ] Test: Requests blocked within 30 seconds
- [ ] Test: Requests allowed after 30 seconds
- [ ] Test: Premium users have no cooldown

### Error Messages

- [ ] Create clear rate limit error message
- [ ] Show daily limit and current count
- [ ] Show reset time (midnight Israel time)
- [ ] Create clear cooldown error message
- [ ] Show remaining wait time
- [ ] Test: Error messages are user-friendly

### Admin Dashboard (Optional)

- [ ] Create admin view for AIUsageLog
- [ ] Add filters by user, date, type
- [ ] Show daily usage statistics
- [ ] Identify abuse patterns
- [ ] Export usage data

**Phase 6 Complete? Move to Phase 7!**

---

## PHASE 7: TESTING (1-2 hours)

### Unit Tests

- [ ] Create `tests/test_legal_compliance.py` file
- [ ] Test: Cookie banner shows on first visit
- [ ] Test: Registration requires legal checkbox
- [ ] Test: Registration enforces 18+ age
- [ ] Test: AI rate limiting (free users)
- [ ] Test: AI rate limiting (premium users)
- [ ] Test: AI cooldown enforcement
- [ ] Test: Data export creates request
- [ ] Test: Account deletion works
- [ ] Test: GPC signal honored
- [ ] Run: `python manage.py test`
- [ ] Fix any failing tests

### Integration Tests

- [ ] Test full registration flow
- [ ] Test cookie consent flow
- [ ] Test data export flow
- [ ] Test account deletion flow
- [ ] Test AI request with rate limiting
- [ ] Test AI request with cooldown
- [ ] Test privacy settings changes

### Manual Testing

- [ ] Fresh browser test (clear cookies)
- [ ] Test with GPC-enabled browser
- [ ] Test all legal page links
- [ ] Test registration as new user
- [ ] Test rate limiting by making 11 requests
- [ ] Test data export request
- [ ] Test cookie preference changes
- [ ] Test account deletion (use test account!)

### Cross-Browser Testing

- [ ] Test in Chrome
- [ ] Test in Firefox
- [ ] Test in Safari
- [ ] Test in Edge
- [ ] Test in mobile Safari
- [ ] Test in mobile Chrome

### Mobile Testing

- [ ] Test cookie banner on mobile
- [ ] Test registration form on mobile
- [ ] Test legal pages on mobile
- [ ] Test privacy settings on mobile
- [ ] Test all buttons clickable on mobile
- [ ] Test form inputs work on mobile

### Compliance Verification

- [ ] Verify all consent timestamps logged
- [ ] Verify IP addresses recorded
- [ ] Verify user agents recorded
- [ ] Verify GPC signals honored
- [ ] Verify rate limits enforced
- [ ] Verify cooldowns enforced
- [ ] Verify data export works
- [ ] Verify deletion works

**Phase 7 Complete? Move to Final Checks!**

---

## FINAL PRE-LAUNCH CHECKS

### Legal Documents

- [ ] All 5 legal documents uploaded
- [ ] All pages render correctly
- [ ] No broken links in documents
- [ ] Contact email correct (bishulme@gmail.com)
- [ ] Effective date correct (January 1, 2025)
- [ ] Version numbers correct (v3.0)

### User Experience

- [ ] Cookie banner not annoying
- [ ] Legal documents readable
- [ ] Registration form intuitive
- [ ] Privacy settings easy to find
- [ ] Error messages helpful
- [ ] Mobile experience smooth

### Technical

- [ ] Database migrations applied
- [ ] Redis running for rate limiting
- [ ] Celery running for background tasks
- [ ] Email sending configured
- [ ] Google Analytics configured
- [ ] Error tracking configured (Sentry)
- [ ] Backups configured

### Security

- [ ] HTTPS enabled
- [ ] CSRF protection active
- [ ] XSS protection enabled
- [ ] SQL injection protection
- [ ] Rate limiting active
- [ ] Password hashing secure

### Documentation

- [ ] README updated
- [ ] Deployment docs updated
- [ ] Admin docs updated
- [ ] Legal compliance documented
- [ ] Incident response plan created

### Team Preparation

- [ ] Team trained on GDPR procedures
- [ ] Team knows how to handle data requests
- [ ] Support team has legal FAQ
- [ ] Escalation procedures defined

---

## 🎉 LAUNCH DAY CHECKLIST

### Pre-Launch (Morning)

- [ ] Run all tests one final time
- [ ] Check error logs (should be empty)
- [ ] Verify all services running
- [ ] Check database backups
- [ ] Verify email sending works
- [ ] Test registration end-to-end
- [ ] Test rate limiting works

### During Launch

- [ ] Monitor error logs
- [ ] Monitor user registrations
- [ ] Monitor cookie banner acceptance rate
- [ ] Check for any consent issues
- [ ] Be ready to rollback if needed

### Post-Launch (First Week)

- [ ] Review consent logs daily
- [ ] Check for any GDPR requests
- [ ] Monitor rate limit violations
- [ ] Review user feedback
- [ ] Fix any issues immediately
- [ ] Document any problems

---

## 📊 SUCCESS METRICS

After 1 week, you should see:

- [ ] >90% cookie consent completion rate
- [ ] 0 registration failures due to legal checkbox
- [ ] 0 minors registered (age verification working)
- [ ] Rate limiting preventing abuse
- [ ] 0 GDPR compliance issues
- [ ] Users can export data successfully
- [ ] Users can delete accounts successfully

---

## 🆘 ROLLBACK PLAN

If critical issues occur:

### Immediate Actions:
1. Stop new user registrations
2. Review error logs
3. Identify the issue
4. Fix or rollback problematic code
5. Test fix thoroughly
6. Re-enable registrations

### When to Rollback:
- [ ] Cookie banner causing errors
- [ ] Registration failing >10%
- [ ] Rate limiting too aggressive
- [ ] Data export/delete not working
- [ ] Legal pages inaccessible

---

## 📧 POST-LAUNCH CONTACTS

**If issues arise:**

**Technical Issues:**
- Check logs first
- Review implementation guides
- Contact: bishulme@gmail.com

**Legal/Compliance Issues:**
- Review legal documents
- Consult legal advisor if serious
- Document all incidents

**User Issues:**
- Check support inbox
- Review user feedback
- Update FAQ if needed

---

## ✅ CONGRATULATIONS!

If you've completed this checklist, you've successfully implemented:

✅ Production-ready legal framework  
✅ GDPR + CCPA + Israel Amendment 13 compliance  
✅ 2025 cookie consent standards  
✅ AI usage limits and transparency  
✅ User privacy controls  
✅ Professional legal protection  

**Your platform is now legally compliant and ready to scale!** 🚀

---

**Total Items Completed:** ___ / 200+

**Estimated Time Invested:** ___ hours

**Legal Protection Gained:** Priceless! 💪

---

*Version: 2.0*  
*Date: January 1, 2025*  
*© 2025 BishulMe. All rights reserved.*
