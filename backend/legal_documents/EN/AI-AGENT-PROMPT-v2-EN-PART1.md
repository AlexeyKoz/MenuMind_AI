# AI Agent Implementation Prompt - BishulMe Legal Framework

**Version:** 2.0  
**Date:** January 1, 2025  
**Platform:** BishulMe (bishul.me)  
**Target:** Cursor IDE + Claude Sonnet 4.5

---

## 🎯 MISSION

Implement comprehensive legal compliance framework for **BishulMe** including:
- GDPR + CCPA + Israel Amendment 13 compliance
- 2025 cookie consent standards
- AI data transparency
- Rate limiting and fair use enforcement
- User privacy controls

**All examples updated for:**
- ✅ New domain: bishul.me
- ✅ New branding: BishulMe / בישול שלי
- ✅ New email: bishulme@gmail.com

---

## 📋 TABLE OF CONTENTS

1. [System Architecture](#1-system-architecture)
2. [Database Models](#2-database-models)
3. [Cookie Banner Implementation](#3-cookie-banner-implementation)
4. [Legal Pages](#4-legal-pages)
5. [User Registration](#5-user-registration)
6. [Privacy Settings](#6-privacy-settings)
7. [Rate Limiting](#7-rate-limiting)
8. [Data Export/Delete](#8-data-exportdelete)
9. [Email Templates](#9-email-templates)
10. [Testing](#10-testing)

---

## 1. SYSTEM ARCHITECTURE

### Technology Stack

**Backend:**
- Django 4.2+ (Python 3.11+)
- PostgreSQL 14+
- Redis (for rate limiting)
- Celery (for background tasks)

**Frontend:**
- React 18+
- TypeScript
- Tailwind CSS
- React Router

**Deployment:**
- DigitalOcean (current)
- Docker containers
- Nginx reverse proxy

### Key Components

```
bishulme/
├── backend/
│   ├── core/              # Core Django settings
│   ├── accounts/          # User management
│   ├── legal/             # Legal pages & consent
│   ├── api/               # REST API
│   └── utils/             # Rate limiting, helpers
├── frontend/
│   ├── components/
│   │   ├── CookieBanner/
│   │   ├── LegalPages/
│   │   └── PrivacySettings/
│   └── pages/
└── docker/
```

---

## 2. DATABASE MODELS

### 2.1 User Consent Model

**Django Model** (`legal/models.py`):

```python
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserConsent(models.Model):
    """
    Tracks user consent for legal agreements and cookies.
    GDPR Article 7: Consent must be documented.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='consent'
    )
    
    # Legal agreements
    terms_accepted = models.BooleanField(default=False)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    terms_version = models.CharField(max_length=10, default='3.0')
    
    privacy_accepted = models.BooleanField(default=False)
    privacy_accepted_at = models.DateTimeField(null=True, blank=True)
    privacy_version = models.CharField(max_length=10, default='3.0')
    
    cookie_accepted = models.BooleanField(default=False)
    cookie_accepted_at = models.DateTimeField(null=True, blank=True)
    cookie_version = models.CharField(max_length=10, default='3.0')
    
    # Cookie preferences
    functional_cookies = models.BooleanField(default=False)
    analytics_cookies = models.BooleanField(default=False)
    performance_cookies = models.BooleanField(default=False)
    
    # GPC (Global Privacy Control)
    gpc_signal_detected = models.BooleanField(default=False)
    gpc_honored = models.BooleanField(default=False)
    
    # Tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    consent_method = models.CharField(
        max_length=50,
        choices=[
            ('banner', 'Cookie Banner'),
            ('registration', 'Registration Form'),
            ('settings', 'Privacy Settings'),
            ('gpc', 'Global Privacy Control'),
        ],
        default='banner'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_consent'
        verbose_name = 'User Consent'
        verbose_name_plural = 'User Consents'
    
    def __str__(self):
        return f"Consent for {self.user.email}"
    
    def update_consent(self, consent_type, accepted, version='3.0'):
        """Update specific consent with timestamp."""
        from django.utils import timezone
        
        if consent_type == 'terms':
            self.terms_accepted = accepted
            self.terms_accepted_at = timezone.now() if accepted else None
            self.terms_version = version
        elif consent_type == 'privacy':
            self.privacy_accepted = accepted
            self.privacy_accepted_at = timezone.now() if accepted else None
            self.privacy_version = version
        elif consent_type == 'cookies':
            self.cookie_accepted = accepted
            self.cookie_accepted_at = timezone.now() if accepted else None
            self.cookie_version = version
        
        self.save()
```

### 2.2 AI Usage Tracking Model

**Django Model** (`api/models.py`):

```python
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class AIUsageLog(models.Model):
    """
    Track AI requests for rate limiting and compliance.
    Helps enforce 10/day free, 100/day premium limits.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_usage'
    )
    
    # Request details
    request_type = models.CharField(
        max_length=50,
        choices=[
            ('recipe_gen', 'Recipe Generation'),
            ('meal_plan', 'Meal Planning'),
            ('ai_coach', 'AI Coach Chat'),
            ('nutrition', 'Nutrition Analysis'),
            ('substitution', 'Ingredient Substitution'),
        ]
    )
    
    prompt = models.TextField()  # What user asked
    response_summary = models.TextField(blank=True)  # Response preview
    
    # AI provider used
    ai_provider = models.CharField(
        max_length=50,
        choices=[
            ('gemini', 'Google Gemini'),
            ('groq', 'Groq'),
            ('translate', 'Google Translate'),
        ]
    )
    
    # Performance metrics
    tokens_used = models.IntegerField(default=0)
    latency_ms = models.IntegerField(default=0)  # Response time
    cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    
    # Rate limiting
    within_limit = models.BooleanField(default=True)
    user_plan = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free'),
            ('premium', 'Premium'),
        ],
        default='free'
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_usage_log'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.request_type} at {self.timestamp}"
    
    @classmethod
    def get_daily_count(cls, user, date=None):
        """Get AI request count for a specific day."""
        if date is None:
            date = timezone.now().date()
        
        return cls.objects.filter(
            user=user,
            timestamp__date=date
        ).count()
    
    @classmethod
    def can_make_request(cls, user):
        """Check if user can make another AI request."""
        daily_count = cls.get_daily_count(user)
        
        # Determine limit based on user plan
        limit = 100 if user.is_premium else 10
        
        return daily_count < limit
```

### 2.3 Data Export Request Model

**Django Model** (`accounts/models.py`):

```python
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class DataExportRequest(models.Model):
    """
    GDPR Article 20: Right to data portability.
    User can request full data export in machine-readable format.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='export_requests'
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('expired', 'Expired'),
        ],
        default='pending'
    )
    
    # Export details
    format = models.CharField(
        max_length=10,
        choices=[
            ('json', 'JSON'),
            ('csv', 'CSV'),
        ],
        default='json'
    )
    
    file_path = models.CharField(max_length=500, blank=True)
    file_size_bytes = models.BigIntegerField(default=0)
    download_url = models.URLField(blank=True)
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # 30 days
    downloaded_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'data_export_requests'
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Export for {self.user.email} - {self.status}"
```

---

## 3. COOKIE BANNER IMPLEMENTATION

### 3.1 React Cookie Banner Component

**File:** `frontend/components/CookieBanner/CookieBanner.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { getCookie, setCookie } from '../../utils/cookies';
import { api } from '../../services/api';

interface CookiePreferences {
  essential: boolean;  // Always true
  functional: boolean;
  analytics: boolean;
  performance: boolean;
}

const CookieBanner: React.FC = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [preferences, setPreferences] = useState<CookiePreferences>({
    essential: true,
    functional: false,
    analytics: false,
    performance: false,
  });

  useEffect(() => {
    // Check if user already made choice
    const consentGiven = getCookie('cookie_consent');
    const gpcSignal = navigator.globalPrivacyControl || false;

    if (!consentGiven) {
      if (gpcSignal) {
        // Honor GPC signal - reject all non-essential
        handleRejectAll(true);
      } else {
        // Show banner
        setIsVisible(true);
      }
    }
  }, []);

  const handleAcceptAll = async () => {
    const newPrefs = {
      essential: true,
      functional: true,
      analytics: true,
      performance: true,
    };

    await savePreferences(newPrefs, 'accept_all');
    setIsVisible(false);
  };

  const handleRejectAll = async (fromGPC = false) => {
    const newPrefs = {
      essential: true,
      functional: false,
      analytics: false,
      performance: false,
    };

    await savePreferences(newPrefs, fromGPC ? 'gpc' : 'reject_all');
    setIsVisible(false);
  };

  const handleCustomize = async () => {
    await savePreferences(preferences, 'customize');
    setIsVisible(false);
  };

  const savePreferences = async (prefs: CookiePreferences, method: string) => {
    try {
      // Save to backend
      await api.post('/api/consent/cookies/', {
        functional: prefs.functional,
        analytics: prefs.analytics,
        performance: prefs.performance,
        method: method,
      });

      // Save consent cookie (1 year)
      setCookie('cookie_consent', 'true', 365);
      
      // Save preference cookies
      setCookie('cookie_functional', prefs.functional.toString(), 365);
      setCookie('cookie_analytics', prefs.analytics.toString(), 365);
      setCookie('cookie_performance', prefs.performance.toString(), 365);

      // Initialize analytics if accepted
      if (prefs.analytics) {
        initializeGoogleAnalytics();
      }

    } catch (error) {
      console.error('Failed to save cookie preferences:', error);
    }
  };

  const initializeGoogleAnalytics = () => {
    // Load Google Analytics
    if (typeof window !== 'undefined' && !window.gtag) {
      const script = document.createElement('script');
      script.src = `https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID`;
      script.async = true;
      document.head.appendChild(script);

      window.dataLayer = window.dataLayer || [];
      function gtag(...args: any[]) {
        window.dataLayer.push(arguments);
      }
      gtag('js', new Date());
      gtag('config', 'GA_MEASUREMENT_ID', {
        anonymize_ip: true,
        cookie_flags: 'SameSite=None;Secure',
      });
    }
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t-2 border-gray-200 shadow-2xl">
      <div className="max-w-7xl mx-auto p-6">
        {!showDetails ? (
          // Simple view
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex-1">
              <h3 className="text-lg font-semibold mb-2">
                🍪 We Value Your Privacy
              </h3>
              <p className="text-sm text-gray-600">
                We use cookies to enhance your experience. You can customize which cookies you accept.
                {' '}
                <a href="/cookies" className="text-blue-600 hover:underline" target="_blank">
                  Learn more
                </a>
              </p>
            </div>
            
            {/* CRITICAL: Symmetric buttons (2025 standard) */}
            <div className="flex gap-3">
              <button
                onClick={handleRejectAll}
                className="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium rounded-lg transition-colors"
              >
                Reject All
              </button>
              
              <button
                onClick={() => setShowDetails(true)}
                className="px-6 py-3 bg-white hover:bg-gray-50 text-gray-800 font-medium rounded-lg border-2 border-gray-300 transition-colors"
              >
                Customize
              </button>
              
              <button
                onClick={handleAcceptAll}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
              >
                Accept All
              </button>
            </div>
          </div>
        ) : (
          // Detailed view
          <div>
            <h3 className="text-xl font-semibold mb-4">Cookie Preferences</h3>
            
            <div className="space-y-4 mb-6">
              {/* Essential - always on */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <h4 className="font-medium">Essential Cookies</h4>
                  <p className="text-sm text-gray-600">
                    Required for the site to work. Cannot be disabled.
                  </p>
                </div>
                <div className="text-green-600 font-medium">Always Active</div>
              </div>

              {/* Functional */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <h4 className="font-medium">Functional Cookies</h4>
                  <p className="text-sm text-gray-600">
                    Remember your preferences (language, units, theme).
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.functional}
                    onChange={(e) => setPreferences({...preferences, functional: e.target.checked})}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              {/* Analytics */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <h4 className="font-medium">Analytics Cookies</h4>
                  <p className="text-sm text-gray-600">
                    Help us understand how you use BishulMe (Google Analytics with IP anonymization).
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.analytics}
                    onChange={(e) => setPreferences({...preferences, analytics: e.target.checked})}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              {/* Performance */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <h4 className="font-medium">Performance Cookies</h4>
                  <p className="text-sm text-gray-600">
                    Optimize loading speed and performance.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.performance}
                    onChange={(e) => setPreferences({...preferences, performance: e.target.checked})}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDetails(false)}
                className="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium rounded-lg transition-colors"
              >
                Back
              </button>
              
              <button
                onClick={handleCustomize}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
              >
                Save Preferences
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CookieBanner;
```

**Key Points:**
- ✅ Symmetric "Accept" and "Reject" buttons (2025 standard)
- ✅ GPC (Global Privacy Control) support
- ✅ No dark patterns
- ✅ Easy customization
- ✅ Saves to backend for GDPR compliance

---

Due to length limits, I'll continue with the remaining sections in the next files. Let me create a summary document first, then continue with the implementation guide.

Let me create the remaining implementation files...
