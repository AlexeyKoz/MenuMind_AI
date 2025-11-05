# AI Agent Implementation Prompt - BishulMe Legal Framework (Part 2)

**Continued from Part 1...**

---

## 4. LEGAL PAGES

### 4.1 Django Views for Legal Pages

**File:** `legal/views.py`

```python
from django.views.generic import TemplateView
from django.shortcuts import render
import markdown

class LegalPageView(TemplateView):
    """Base view for legal pages."""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_name'] = 'BishulMe'
        context['site_url'] = 'https://bishul.me'
        context['support_email'] = 'bishulme@gmail.com'
        return context

class TermsOfServiceView(LegalPageView):
    template_name = 'legal/terms.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Load markdown file
        with open('legal_docs/FINAL-terms-of-service-v3-EN.md', 'r', encoding='utf-8') as f:
            md_content = f.read()
            context['content'] = markdown.markdown(md_content)
        return context

class PrivacyPolicyView(LegalPageView):
    template_name = 'legal/privacy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        with open('legal_docs/FINAL-privacy-policy-v3-EN.md', 'r', encoding='utf-8') as f:
            md_content = f.read()
            context['content'] = markdown.markdown(md_content)
        return context

class CookiePolicyView(LegalPageView):
    template_name = 'legal/cookies.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        with open('legal_docs/FINAL-cookie-policy-v3-EN.md', 'r', encoding='utf-8') as f:
            md_content = f.read()
            context['content'] = markdown.markdown(md_content)
        return context
```

**File:** `legal/urls.py`

```python
from django.urls import path
from . import views

app_name = 'legal'

urlpatterns = [
    path('terms/', views.TermsOfServiceView.as_view(), name='terms'),
    path('privacy/', views.PrivacyPolicyView.as_view(), name='privacy'),
    path('cookies/', views.CookiePolicyView.as_view(), name='cookies'),
]
```

---

## 5. USER REGISTRATION

### 5.1 Registration Form with Legal Checkbox

**React Component:** `frontend/pages/Register.tsx`

```typescript
import React, { useState } from 'react';
import { api } from '../services/api';
import { useNavigate } from 'react-router-dom';

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    birthdate: '',
    legalAccepted: false,
  });
  const [errors, setErrors] = useState<any>({});
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const validateForm = () => {
    const newErrors: any = {};

    // Email validation
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    // Age validation (18+)
    if (!formData.birthdate) {
      newErrors.birthdate = 'Birthdate is required';
    } else {
      const age = calculateAge(formData.birthdate);
      if (age < 18) {
        newErrors.birthdate = 'You must be at least 18 years old to use BishulMe';
      }
    }

    // Legal acceptance - CRITICAL
    if (!formData.legalAccepted) {
      newErrors.legalAccepted = 'You must accept the Terms, Privacy Policy, and Cookie Policy';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const calculateAge = (birthdate: string): number => {
    const today = new Date();
    const birth = new Date(birthdate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    
    return age;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const response = await api.post('/api/auth/register/', {
        email: formData.email,
        password: formData.password,
        name: formData.name,
        birthdate: formData.birthdate,
        legal_accepted: formData.legalAccepted,
      });

      // Registration successful
      alert('Registration successful! Please check your email to verify your account.');
      navigate('/login');
      
    } catch (error: any) {
      if (error.response?.data) {
        setErrors(error.response.data);
      } else {
        setErrors({ general: 'Registration failed. Please try again.' });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create Your BishulMe Account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Join thousands of home cooks discovering new recipes
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {errors.general && (
            <div className="rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-800">{errors.general}</p>
            </div>
          )}

          <div className="rounded-md shadow-sm space-y-4">
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email Address *
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleChange}
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                  errors.email ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                placeholder="you@example.com"
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">{errors.email}</p>
              )}
            </div>

            {/* Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                Name (Optional)
              </label>
              <input
                id="name"
                name="name"
                type="text"
                value={formData.name}
                onChange={handleChange}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="John Doe"
              />
            </div>

            {/* Birthdate - CRITICAL for 18+ verification */}
            <div>
              <label htmlFor="birthdate" className="block text-sm font-medium text-gray-700">
                Date of Birth * (You must be 18+)
              </label>
              <input
                id="birthdate"
                name="birthdate"
                type="date"
                required
                value={formData.birthdate}
                onChange={handleChange}
                max={new Date(new Date().setFullYear(new Date().getFullYear() - 18)).toISOString().split('T')[0]}
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                  errors.birthdate ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
              />
              {errors.birthdate && (
                <p className="mt-1 text-sm text-red-600">{errors.birthdate}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password *
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                  errors.password ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                placeholder="Minimum 8 characters"
              />
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password}</p>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                Confirm Password *
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                required
                value={formData.confirmPassword}
                onChange={handleChange}
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                  errors.confirmPassword ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
              />
              {errors.confirmPassword && (
                <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>
              )}
            </div>
          </div>

          {/* Legal Checkbox - CRITICAL */}
          <div className="flex items-start">
            <div className="flex items-center h-5">
              <input
                id="legalAccepted"
                name="legalAccepted"
                type="checkbox"
                required
                checked={formData.legalAccepted}
                onChange={handleChange}
                className={`h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded ${
                  errors.legalAccepted ? 'border-red-300' : ''
                }`}
              />
            </div>
            <div className="ml-3 text-sm">
              <label htmlFor="legalAccepted" className="font-medium text-gray-700">
                I agree to the{' '}
                <a href="/terms" target="_blank" className="text-blue-600 hover:underline">
                  Terms of Service
                </a>
                ,{' '}
                <a href="/privacy" target="_blank" className="text-blue-600 hover:underline">
                  Privacy Policy
                </a>
                , and{' '}
                <a href="/cookies" target="_blank" className="text-blue-600 hover:underline">
                  Cookie Policy
                </a>
                . *
              </label>
              {errors.legalAccepted && (
                <p className="mt-1 text-sm text-red-600">{errors.legalAccepted}</p>
              )}
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className={`group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white ${
                loading ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'
              } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <a href="/login" className="font-medium text-blue-600 hover:underline">
                Log in
              </a>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RegisterPage;
```

---

## 6. PRIVACY SETTINGS

### 6.1 Privacy Settings Page

**React Component:** `frontend/pages/PrivacySettings.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

const PrivacySettingsPage: React.FC = () => {
  const [settings, setSettings] = useState({
    functional_cookies: false,
    analytics_cookies: false,
    performance_cookies: false,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await api.get('/api/privacy/settings/');
      setSettings(response.data);
    } catch (error) {
      console.error('Failed to load privacy settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put('/api/privacy/settings/', settings);
      alert('Privacy settings saved successfully!');
    } catch (error) {
      alert('Failed to save settings. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleExportData = async () => {
    if (!confirm('Export all your data? This may take a few minutes.')) {
      return;
    }

    setExportLoading(true);
    try {
      const response = await api.post('/api/privacy/export/');
      alert(
        'Data export requested! You will receive an email with download link within 24 hours.'
      );
    } catch (error) {
      alert('Failed to request data export. Please try again.');
    } finally {
      setExportLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    const confirmDelete = confirm(
      'Are you sure you want to delete your account? This action CANNOT be undone. All your data will be permanently deleted within 30 days.'
    );

    if (!confirmDelete) {
      return;
    }

    const confirmAgain = prompt(
      'Type "DELETE" in capital letters to confirm account deletion:'
    );

    if (confirmAgain !== 'DELETE') {
      alert('Account deletion cancelled.');
      return;
    }

    setDeleteLoading(true);
    try {
      await api.delete('/api/privacy/delete-account/');
      alert(
        'Your account has been scheduled for deletion. You will be logged out. All data will be deleted within 30 days.'
      );
      // Logout and redirect
      window.location.href = '/logout';
    } catch (error) {
      alert('Failed to delete account. Please contact support.');
    } finally {
      setDeleteLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading privacy settings...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold mb-8">Privacy Settings</h1>

      {/* Cookie Preferences */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Cookie Preferences</h2>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between py-3 border-b">
            <div>
              <h3 className="font-medium">Essential Cookies</h3>
              <p className="text-sm text-gray-600">Required for the site to work</p>
            </div>
            <div className="text-green-600 font-medium">Always Active</div>
          </div>

          <div className="flex items-center justify-between py-3 border-b">
            <div>
              <h3 className="font-medium">Functional Cookies</h3>
              <p className="text-sm text-gray-600">Remember your preferences</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.functional_cookies}
                onChange={(e) =>
                  setSettings({ ...settings, functional_cookies: e.target.checked })
                }
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between py-3 border-b">
            <div>
              <h3 className="font-medium">Analytics Cookies</h3>
              <p className="text-sm text-gray-600">Help us improve (Google Analytics)</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.analytics_cookies}
                onChange={(e) =>
                  setSettings({ ...settings, analytics_cookies: e.target.checked })
                }
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between py-3">
            <div>
              <h3 className="font-medium">Performance Cookies</h3>
              <p className="text-sm text-gray-600">Optimize loading speed</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.performance_cookies}
                onChange={(e) =>
                  setSettings({ ...settings, performance_cookies: e.target.checked })
                }
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="mt-6 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg disabled:bg-blue-400"
        >
          {saving ? 'Saving...' : 'Save Cookie Preferences'}
        </button>
      </div>

      {/* Data Rights - GDPR */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Your Data Rights</h2>

        <div className="space-y-4">
          <div>
            <h3 className="font-medium mb-2">Export Your Data (GDPR Article 20)</h3>
            <p className="text-sm text-gray-600 mb-3">
              Download all your data in JSON format. You'll receive an email with a download link.
            </p>
            <button
              onClick={handleExportData}
              disabled={exportLoading}
              className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg disabled:bg-green-400"
            >
              {exportLoading ? 'Requesting...' : 'Export My Data'}
            </button>
          </div>

          <div className="pt-4 border-t">
            <h3 className="font-medium mb-2 text-red-600">Delete Your Account (GDPR Article 17)</h3>
            <p className="text-sm text-gray-600 mb-3">
              Permanently delete your account and all associated data. This action CANNOT be undone.
              All data will be deleted within 30 days.
            </p>
            <button
              onClick={handleDeleteAccount}
              disabled={deleteLoading}
              className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg disabled:bg-red-400"
            >
              {deleteLoading ? 'Deleting...' : 'Delete My Account'}
            </button>
          </div>
        </div>
      </div>

      {/* Additional Links */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="font-medium mb-3">Learn More</h3>
        <ul className="space-y-2 text-sm">
          <li>
            <a href="/privacy" className="text-blue-600 hover:underline" target="_blank">
              Read our Privacy Policy
            </a>
          </li>
          <li>
            <a href="/cookies" className="text-blue-600 hover:underline" target="_blank">
              Read our Cookie Policy
            </a>
          </li>
          <li>
            <a href="/terms" className="text-blue-600 hover:underline" target="_blank">
              Read our Terms of Service
            </a>
          </li>
          <li>
            <a href="mailto:bishulme@gmail.com" className="text-blue-600 hover:underline">
              Contact us about privacy
            </a>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default PrivacySettingsPage;
```

---

## 7. RATE LIMITING

### 7.1 Django Rate Limiting Middleware

**File:** `utils/rate_limiting.py`

```python
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from api.models import AIUsageLog
import time

class RateLimitMiddleware:
    """
    Rate limiting middleware for AI requests.
    Enforces: 10/day free, 100/day premium
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only check AI endpoints
        if request.path.startswith('/api/ai/'):
            if request.user.is_authenticated:
                # Check rate limit
                if not self.check_rate_limit(request.user):
                    return JsonResponse({
                        'error': 'Rate limit exceeded',
                        'message': 'You have exceeded your daily AI request limit.',
                        'limit': 100 if request.user.is_premium else 10,
                        'reset_at': self.get_reset_time(),
                    }, status=429)
        
        response = self.get_response(request)
        return response
    
    def check_rate_limit(self, user):
        """Check if user is within rate limit."""
        today = timezone.now().date()
        daily_count = AIUsageLog.get_daily_count(user, today)
        
        limit = 100 if user.is_premium else 10
        
        return daily_count < limit
    
    def get_reset_time(self):
        """Get timestamp when rate limit resets (midnight Israel time)."""
        from datetime import datetime, time as dt_time
        from pytz import timezone as pytz_timezone
        
        israel_tz = pytz_timezone('Asia/Jerusalem')
        now = datetime.now(israel_tz)
        midnight = datetime.combine(now.date() + timedelta(days=1), dt_time.min)
        midnight = israel_tz.localize(midnight)
        
        return midnight.isoformat()
```

### 7.2 Cooldown Enforcement

**File:** `api/views.py`

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.utils import timezone
from api.models import AIUsageLog
import time

class AIRequestView(APIView):
    """Base view for AI requests with cooldown."""
    permission_classes = [IsAuthenticated]
    
    def check_cooldown(self, user):
        """
        Check 30-second cooldown between requests (free users only).
        Premium users have no cooldown.
        """
        if user.is_premium:
            return True, 0
        
        cache_key = f'ai_cooldown_{user.id}'
        last_request = cache.get(cache_key)
        
        if last_request:
            elapsed = time.time() - last_request
            if elapsed < 30:
                return False, int(30 - elapsed)
        
        return True, 0
    
    def set_cooldown(self, user):
        """Set cooldown timestamp."""
        if not user.is_premium:
            cache_key = f'ai_cooldown_{user.id}'
            cache.set(cache_key, time.time(), timeout=30)
    
    def post(self, request):
        # Check cooldown
        can_proceed, wait_seconds = self.check_cooldown(request.user)
        
        if not can_proceed:
            return Response({
                'error': 'Please wait before making another request',
                'wait_seconds': wait_seconds,
                'message': f'Please wait {wait_seconds} seconds before your next request.',
            }, status=429)
        
        # Process AI request
        # ... (your AI logic here)
        
        # Log usage
        AIUsageLog.objects.create(
            user=request.user,
            request_type='recipe_gen',  # or whatever type
            prompt=request.data.get('prompt'),
            ai_provider='gemini',
            within_limit=True,
            user_plan='premium' if request.user.is_premium else 'free',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        # Set cooldown
        self.set_cooldown(request.user)
        
        return Response({'result': 'AI response here'})
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

---

## 8. DATA EXPORT/DELETE

### 8.1 Data Export API

**Django View:** `accounts/views.py`

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import DataExportRequest
from celery import shared_task
import json
from django.core.serializers import serialize

@shared_task
def generate_data_export(export_request_id):
    """
    Celery task to generate data export (runs in background).
    """
    from accounts.models import DataExportRequest
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        export_request = DataExportRequest.objects.get(id=export_request_id)
        export_request.status = 'processing'
        export_request.save()
        
        user = export_request.user
        
        # Collect all user data
        data = {
            'user_info': {
                'email': user.email,
                'name': user.name,
                'created_at': user.created_at.isoformat(),
            },
            'health_data': {
                'weight': user.profile.weight,
                'height': user.profile.height,
                'birthday': user.profile.birthday.isoformat() if user.profile.birthday else None,
                # ... more health data
            },
            'recipes': list(user.recipes.values()),
            'meal_logs': list(user.meal_logs.values()),
            'ai_interactions': list(user.ai_usage.values()),
            # ... more data
        }
        
        # Save to file
        file_path = f'exports/user_{user.id}_{timezone.now().timestamp()}.json'
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        # Update export request
        export_request.status = 'completed'
        export_request.completed_at = timezone.now()
        export_request.expires_at = timezone.now() + timedelta(days=30)
        export_request.file_path = file_path
        export_request.download_url = f'https://bishul.me/downloads/{export_request.id}'
        export_request.save()
        
        # Send email with download link
        send_export_email(user, export_request)
        
    except Exception as e:
        export_request.status = 'failed'
        export_request.error_message = str(e)
        export_request.save()

class DataExportView(APIView):
    """GDPR Article 20: Right to data portability."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Create export request
        export_request = DataExportRequest.objects.create(
            user=request.user,
            format='json',
            status='pending',
        )
        
        # Queue background task
        generate_data_export.delay(export_request.id)
        
        return Response({
            'message': 'Data export requested. You will receive an email with download link within 24 hours.',
            'request_id': str(export_request.id),
        })
```

---

## 9. EMAIL TEMPLATES

### 9.1 Verification Email

**File:** `templates/emails/verification.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Verify Your BishulMe Account</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2563eb;">BishulMe</h1>
        <p style="color: #6b7280;">בישול שלי</p>
    </div>
    
    <h2>Welcome to BishulMe!</h2>
    
    <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{ verification_url }}" 
           style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
            Verify Email Address
        </a>
    </div>
    
    <p style="color: #6b7280; font-size: 14px;">
        If the button doesn't work, copy and paste this link into your browser:<br>
        <a href="{{ verification_url }}">{{ verification_url }}</a>
    </p>
    
    <p style="color: #6b7280; font-size: 14px;">
        This link will expire in 24 hours.
    </p>
    
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
    
    <p style="color: #6b7280; font-size: 12px;">
        If you didn't create this account, you can safely ignore this email.
    </p>
    
    <p style="color: #6b7280; font-size: 12px;">
        © 2025 BishulMe. All rights reserved.<br>
        <a href="https://bishul.me/privacy">Privacy Policy</a> | 
        <a href="https://bishul.me/terms">Terms of Service</a>
    </p>
</body>
</html>
```

---

## 10. TESTING

### 10.1 Legal Framework Tests

**File:** `tests/test_legal_compliance.py`

```python
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from legal.models import UserConsent

User = get_user_model()

class LegalComplianceTests(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_cookie_banner_shows_on_first_visit(self):
        """Cookie banner should show for new visitors."""
        response = self.client.get('/')
        self.assertContains(response, 'cookie-banner')
    
    def test_registration_requires_legal_checkbox(self):
        """Registration must require legal acceptance."""
        response = self.client.post('/api/auth/register/', {
            'email': 'newuser@example.com',
            'password': 'password123',
            'birthdate': '2000-01-01',
            'legal_accepted': False,  # Not accepted
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('legal_accepted', response.json())
    
    def test_registration_enforces_18_plus(self):
        """Registration must reject users under 18."""
        from datetime import date, timedelta
        
        # 17 years old
        birthdate = (date.today() - timedelta(days=365*17)).isoformat()
        
        response = self.client.post('/api/auth/register/', {
            'email': 'minor@example.com',
            'password': 'password123',
            'birthdate': birthdate,
            'legal_accepted': True,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('age', response.json()['error'].lower())
    
    def test_ai_rate_limiting_free_user(self):
        """Free users should be limited to 10 AI requests/day."""
        self.client.force_login(self.user)
        
        # Make 10 requests (should succeed)
        for i in range(10):
            response = self.client.post('/api/ai/generate/', {
                'prompt': f'Test prompt {i}'
            })
            self.assertEqual(response.status_code, 200)
        
        # 11th request should be rate limited
        response = self.client.post('/api/ai/generate/', {
            'prompt': 'Test prompt 11'
        })
        self.assertEqual(response.status_code, 429)
    
    def test_data_export_creates_request(self):
        """Data export should create request and queue task."""
        self.client.force_login(self.user)
        
        response = self.client.post('/api/privacy/export/')
        self.assertEqual(response.status_code, 200)
        
        # Check request was created
        from accounts.models import DataExportRequest
        export_request = DataExportRequest.objects.filter(user=self.user).first()
        self.assertIsNotNone(export_request)
        self.assertEqual(export_request.status, 'pending')
    
    def test_account_deletion(self):
        """Account deletion should schedule deletion."""
        self.client.force_login(self.user)
        
        response = self.client.delete('/api/privacy/delete-account/')
        self.assertEqual(response.status_code, 200)
        
        # User should be marked for deletion
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_deleted)
    
    def test_gpc_signal_honored(self):
        """GPC signal should automatically reject cookies."""
        response = self.client.get('/', HTTP_SEC_GPC='1')
        
        # Check that cookies were rejected
        consent = response.client.cookies.get('cookie_analytics')
        self.assertEqual(consent.value, 'false')
```

---

## ✅ IMPLEMENTATION CHECKLIST

Use this checklist to track your progress:

### Phase 1: Backend Setup (2-3 hours)
- [ ] Create database models (UserConsent, AIUsageLog, DataExportRequest)
- [ ] Run migrations
- [ ] Create legal views (Terms, Privacy, Cookies)
- [ ] Set up URL routing

### Phase 2: Cookie Banner (2-3 hours)
- [ ] Create CookieBanner React component
- [ ] Implement symmetric accept/reject buttons
- [ ] Add GPC support
- [ ] Test cookie consent flow

### Phase 3: Legal Pages (1 hour)
- [ ] Upload legal markdown files
- [ ] Create legal page templates
- [ ] Add footer links to all pages

### Phase 4: Registration (1-2 hours)
- [ ] Create registration form with legal checkbox
- [ ] Add 18+ age verification
- [ ] Implement email verification
- [ ] Test registration flow

### Phase 5: Privacy Settings (2-3 hours)
- [ ] Create privacy settings page
- [ ] Implement cookie preference toggles
- [ ] Add data export button
- [ ] Add account deletion button

### Phase 6: Rate Limiting (1-2 hours)
- [ ] Implement rate limiting middleware
- [ ] Add cooldown enforcement
- [ ] Create AI usage logging
- [ ] Test rate limits

### Phase 7: Testing (1-2 hours)
- [ ] Write unit tests
- [ ] Test all user flows
- [ ] Verify GDPR compliance
- [ ] Check mobile responsiveness

---

**Total Estimated Time: 10-16 hours**

Good luck with implementation! 🚀
