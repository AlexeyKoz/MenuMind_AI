# 📧 Brevo (Sendinblue) Email Integration - Complete Setup Guide

## 🎯 Overview

This guide will help you set up **Brevo** (formerly Sendinblue) as your primary transactional email service for MenuMind AI. Brevo offers:

- ✅ **300 free emails per day** (perfect for development and small production)
- ✅ **99%+ delivery rate** (better than Gmail SMTP)
- ✅ **Real-time email tracking and analytics**
- ✅ **No sender email restrictions** (use any domain you own)
- ✅ **API-based** (faster and more reliable than SMTP)
- ✅ **Official Python SDK** (easy integration)

---

## 📋 Table of Contents

1. [Account Setup](#1-account-setup)
2. [Sender Email Verification](#2-sender-email-verification)
3. [API Key Generation](#3-api-key-generation)
4. [Template Creation](#4-template-creation)
5. [Backend Configuration](#5-backend-configuration)
6. [Testing](#6-testing)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Account Setup

### 1.1 Create Brevo Account

1. Go to: **https://www.brevo.com/** (or https://www.sendinblue.com/)
2. Click **"Sign Up Free"**
3. Fill in registration form:
   - Email: `menumindaiproject@gmail.com`
   - Password: (your secure password)
   - Company Name: `MenuMind AI`
   - Country: Your country
4. Verify your email
5. Complete onboarding wizard

### 1.2 Account Verification

- Brevo may ask for phone verification
- Some accounts require manual approval (usually 1-2 hours)
- Free plan includes: **300 emails/day**

---

## 2. Sender Email Verification

⚠️ **CRITICAL:** You must verify your sender email before you can send emails.

### Option A: Use Gmail (Quick Start - Recommended)

**Good for:** Development and testing

1. In Brevo Dashboard → **Senders, Domains & Dedicated IPs**
2. Click **"Add a Sender"**
3. Enter:
   - **Email:** `menumindaiproject@gmail.com`
   - **Name:** `MenuMind AI`
4. Click **"Add"**
5. Brevo will send a verification email to `menumindaiproject@gmail.com`
6. Check Gmail inbox and click the verification link
7. **Status should change to "Verified" ✅**

### Option B: Use Custom Domain (Production - Optional)

**Good for:** Production with your own domain (e.g., `noreply@menumindai.com`)

1. Go to **Senders, Domains & Dedicated IPs**
2. Click **"Add a Domain"**
3. Enter your domain: `menumindai.com`
4. Brevo will provide DNS records to add:
   - **TXT record** (for SPF)
   - **TXT record** (for DKIM)
   - **CNAME record** (for tracking)
5. Add these records to your domain registrar (Namecheap, GoDaddy, etc.)
6. Wait 24-48 hours for DNS propagation
7. Brevo will automatically verify your domain
8. Once verified, you can use any email @menumindai.com

**For now, use Option A (Gmail) to get started quickly!**

---

## 3. API Key Generation

### 3.1 Get Your API Key

1. In Brevo Dashboard → **SMTP & API** (top right menu)
2. Click **"API Keys"** tab
3. You'll see a default key already created, OR
4. Click **"Generate a new API key"**
   - Name: `MenuMind AI Production`
   - Click **"Generate"**
5. **⚠️ COPY THE API KEY IMMEDIATELY** (you can't see it again!)
   - Format: `xkeysib-xxxxxxxxxxxxxxxxxxxxx-yyyyyyyyyyyy`

**Example API Key:**
```
xkeysib-1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t-1A2B3C4D5E6F7G8H
```

---

## 4. Template Creation

You need to create **3 transactional email templates** (one for each language).

### 4.1 Access Templates

1. In Brevo Dashboard → **Campaigns** → **Transactional** (left sidebar)
2. Click **"Templates"**
3. Click **"New Template"**

---

### 4.2 Template 1: English Verification

**Template Settings:**
- **Template Name:** `Email Verification - English`
- **Subject:** `Verify your email address - MenuMind AI`
- **Sender Name:** `MenuMind AI`
- **Sender Email:** `menumindaiproject@gmail.com` (or your verified email)

**Template Content (HTML):**

Click **"Design Template"** → Switch to **"Code"** editor → Paste this:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }
        .email-container {
            max-width: 600px;
            margin: 20px auto;
            background: #ffffff;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }
        .content {
            padding: 40px 30px;
        }
        .content h2 {
            color: #333;
            font-size: 24px;
            margin: 0 0 20px 0;
        }
        .content p {
            color: #666;
            font-size: 16px;
            margin: 0 0 20px 0;
        }
        .button-container {
            text-align: center;
            margin: 30px 0;
        }
        .button {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            padding: 16px 48px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 16px;
            transition: transform 0.2s;
        }
        .button:hover {
            transform: translateY(-2px);
        }
        .footer-note {
            color: #999;
            font-size: 14px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }
        .footer {
            background: #f9f9f9;
            padding: 20px 30px;
            text-align: center;
            color: #999;
            font-size: 14px;
        }
        .link-fallback {
            color: #667eea;
            word-break: break-all;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>{{ params.SITE_NAME }}</h1>
        </div>
        <div class="content">
            <h2>Hello {{ params.USER_NAME }}! 👋</h2>
            <p>Welcome to MenuMind AI! We're excited to have you on board.</p>
            <p>To start using your account, please verify your email address by clicking the button below:</p>
            
            <div class="button-container">
                <a href="{{ params.ACTIVATE_URL }}" class="button">Verify Email Address</a>
            </div>
            
            <div class="footer-note">
                <p><strong>Why verify?</strong></p>
                <p>Email verification helps us:</p>
                <ul style="text-align: left; color: #666;">
                    <li>Protect your account security</li>
                    <li>Ensure you receive important updates</li>
                    <li>Enable AI-powered recipe generation</li>
                </ul>
                
                <p style="margin-top: 20px;"><strong>Didn't sign up?</strong></p>
                <p>If you didn't create this account, you can safely ignore this email.</p>
                
                <p style="margin-top: 30px; font-size: 12px;">
                    <strong>Button not working?</strong> Copy and paste this link into your browser:<br>
                    <a href="{{ params.ACTIVATE_URL }}" class="link-fallback">{{ params.ACTIVATE_URL }}</a>
                </p>
            </div>
        </div>
        <div class="footer">
            <p>&copy; 2025 MenuMind AI. All rights reserved.</p>
            <p>This is an automated message. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
```

**Template Variables Used:**
- `{{ params.SITE_NAME }}` - "MenuMind AI"
- `{{ params.USER_NAME }}` - User's name
- `{{ params.ACTIVATE_URL }}` - Verification URL
- `{{ params.USER_EMAIL }}` - User's email (for tracking)

**Click "Save and Activate"**

**⭐ COPY THE TEMPLATE ID** - You'll see it in the URL or template list (e.g., `1`, `2`, `3`)

---

### 4.3 Template 2: Russian Verification

**Template Settings:**
- **Template Name:** `Email Verification - Russian`
- **Subject:** `Подтвердите ваш email адрес - MenuMind AI`
- **Sender Name:** `MenuMind AI`
- **Sender Email:** `menumindaiproject@gmail.com`

**Template Content (HTML):**

Use the same HTML structure as English, but change the text content:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- Same styles as English template -->
    <style>
        /* Copy all styles from English template */
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>{{ params.SITE_NAME }}</h1>
        </div>
        <div class="content">
            <h2>Здравствуйте, {{ params.USER_NAME }}! 👋</h2>
            <p>Добро пожаловать в MenuMind AI! Мы рады приветствовать вас.</p>
            <p>Чтобы начать использовать ваш аккаунт, пожалуйста, подтвердите ваш email адрес, нажав на кнопку ниже:</p>
            
            <div class="button-container">
                <a href="{{ params.ACTIVATE_URL }}" class="button">Подтвердить Email</a>
            </div>
            
            <div class="footer-note">
                <p><strong>Зачем подтверждать?</strong></p>
                <p>Подтверждение email помогает нам:</p>
                <ul style="text-align: left; color: #666;">
                    <li>Защитить безопасность вашего аккаунта</li>
                    <li>Убедиться, что вы получаете важные обновления</li>
                    <li>Активировать AI-генерацию рецептов</li>
                </ul>
                
                <p style="margin-top: 20px;"><strong>Не регистрировались?</strong></p>
                <p>Если вы не создавали этот аккаунт, можете спокойно проигнорировать это письмо.</p>
                
                <p style="margin-top: 30px; font-size: 12px;">
                    <strong>Кнопка не работает?</strong> Скопируйте и вставьте эту ссылку в браузер:<br>
                    <a href="{{ params.ACTIVATE_URL }}" class="link-fallback">{{ params.ACTIVATE_URL }}</a>
                </p>
            </div>
        </div>
        <div class="footer">
            <p>&copy; 2025 MenuMind AI. Все права защищены.</p>
            <p>Это автоматическое сообщение. Пожалуйста, не отвечайте на это письмо.</p>
        </div>
    </div>
</body>
</html>
```

**Click "Save and Activate"**

**⭐ COPY THE TEMPLATE ID**

---

### 4.4 Template 3: Hebrew Verification

**Template Settings:**
- **Template Name:** `Email Verification - Hebrew`
- **Subject:** `אמת את כתובת האימייל שלך - MenuMind AI`
- **Sender Name:** `MenuMind AI`
- **Sender Email:** `menumindaiproject@gmail.com`
- **⚠️ IMPORTANT:** Set text direction to **RTL (Right-to-Left)**

**Template Content (HTML):**

```html
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Arial', 'Helvetica', sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            direction: rtl;
            text-align: right;
        }
        .email-container {
            max-width: 600px;
            margin: 20px auto;
            background: #ffffff;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }
        .content {
            padding: 40px 30px;
        }
        .content h2 {
            color: #333;
            font-size: 24px;
            margin: 0 0 20px 0;
        }
        .content p {
            color: #666;
            font-size: 16px;
            margin: 0 0 20px 0;
        }
        .button-container {
            text-align: center;
            margin: 30px 0;
        }
        .button {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            padding: 16px 48px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 16px;
        }
        .footer-note {
            color: #999;
            font-size: 14px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }
        .footer {
            background: #f9f9f9;
            padding: 20px 30px;
            text-align: center;
            color: #999;
            font-size: 14px;
        }
        .link-fallback {
            color: #667eea;
            word-break: break-all;
            font-size: 13px;
            direction: ltr;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>{{ params.SITE_NAME }}</h1>
        </div>
        <div class="content">
            <h2>שלום {{ params.USER_NAME }}! 👋</h2>
            <p>ברוכים הבאים ל-MenuMind AI! אנחנו שמחים שהצטרפת אלינו.</p>
            <p>כדי להתחיל להשתמש בחשבון שלך, אנא אמת את כתובת האימייל שלך על ידי לחיצה על הכפתור למטה:</p>
            
            <div class="button-container">
                <a href="{{ params.ACTIVATE_URL }}" class="button">אמת כתובת אימייל</a>
            </div>
            
            <div class="footer-note">
                <p><strong>למה לאמת?</strong></p>
                <p>אימות אימייל עוזר לנו:</p>
                <ul style="text-align: right; color: #666;">
                    <li>להגן על אבטחת החשבון שלך</li>
                    <li>לוודא שאתה מקבל עדכונים חשובים</li>
                    <li>להפעיל יצירת מתכונים מבוססת AI</li>
                </ul>
                
                <p style="margin-top: 20px;"><strong>לא נרשמת?</strong></p>
                <p>אם לא יצרת חשבון זה, אתה יכול להתעלם מהודעה זו בבטחה.</p>
                
                <p style="margin-top: 30px; font-size: 12px;">
                    <strong>הכפתור לא עובד?</strong> העתק והדבק קישור זה בדפדפן שלך:<br>
                    <a href="{{ params.ACTIVATE_URL }}" class="link-fallback">{{ params.ACTIVATE_URL }}</a>
                </p>
            </div>
        </div>
        <div class="footer">
            <p>&copy; 2025 MenuMind AI. כל הזכויות שמורות.</p>
            <p>זוהי הודעה אוטומטית. אנא אל תענה לאימייל זה.</p>
        </div>
    </div>
</body>
</html>
```

**Click "Save and Activate"**

**⭐ COPY THE TEMPLATE ID**

---

## 5. Backend Configuration

### 5.1 Install Brevo SDK

```bash
cd backend
pip install sib-api-v3-sdk==7.6.0
```

Or add to `requirements.txt`:
```
sib-api-v3-sdk==7.6.0
```

### 5.2 Update `backend/.env`

Add these lines to your **`backend/.env`** file:

```env
# ============================================
# Brevo (Sendinblue) Email Configuration
# ============================================

# API Key from Brevo Dashboard → SMTP & API → API Keys
BREVO_API_KEY=xkeysib-YOUR_API_KEY_HERE

# Verified sender email from Brevo Dashboard → Senders
BREVO_SENDER_EMAIL=menumindaiproject@gmail.com

# Sender name that appears in emails
BREVO_SENDER_NAME=MenuMind AI

# Template IDs from Brevo Dashboard → Templates
BREVO_TEMPLATE_VERIFY_EN=1
BREVO_TEMPLATE_VERIFY_RU=2
BREVO_TEMPLATE_VERIFY_HE=3
```

**⚠️ Replace placeholder values with your actual:**
- **API Key** from Step 3
- **Sender Email** (verified email from Step 2)
- **Template IDs** from Step 4 (EN, RU, HE)

**Example with real values:**
```env
BREVO_API_KEY=xkeysib-1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t-1A2B3C4D5E6F7G8H
BREVO_SENDER_EMAIL=menumindaiproject@gmail.com
BREVO_SENDER_NAME=MenuMind AI
BREVO_TEMPLATE_VERIFY_EN=1
BREVO_TEMPLATE_VERIFY_RU=2
BREVO_TEMPLATE_VERIFY_HE=3
```

---

## 6. Testing

### 6.1 Restart Backend

```bash
cd backend
python manage.py runserver
```

**Look for this in the console:**
```
[Brevo] ✅ Service initialized successfully. Sender: MenuMind AI <menumindaiproject@gmail.com>
```

**If you see:**
```
[Brevo] ⚠️ Service not fully configured. Missing credentials or templates.
```
→ Check your `.env` file!

### 6.2 Create Test Script

Create `backend/test_brevo.py`:

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Brevo Email Configuration
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
django.setup()

from django.conf import settings
from apps.users.services.brevo_email_service import get_brevo_service

def test_brevo_config():
    """Test Brevo configuration"""
    
    print("="*60)
    print("Brevo Configuration Check")
    print("="*60)
    
    # Check environment variables
    api_key = getattr(settings, 'BREVO_API_KEY', None)
    sender_email = getattr(settings, 'BREVO_SENDER_EMAIL', None)
    sender_name = getattr(settings, 'BREVO_SENDER_NAME', None)
    template_en = getattr(settings, 'BREVO_TEMPLATE_VERIFY_EN', None)
    template_ru = getattr(settings, 'BREVO_TEMPLATE_VERIFY_RU', None)
    template_he = getattr(settings, 'BREVO_TEMPLATE_VERIFY_HE', None)
    
    print(f"\n1. Environment Variables:")
    print(f"   BREVO_API_KEY: {'SET' if api_key else 'NOT SET'} {f'({api_key[:30]}...)' if api_key and len(api_key) > 30 else ''}")
    print(f"   BREVO_SENDER_EMAIL: {sender_email or 'NOT SET'}")
    print(f"   BREVO_SENDER_NAME: {sender_name or 'NOT SET'}")
    print(f"   BREVO_TEMPLATE_VERIFY_EN: {template_en or 'NOT SET'}")
    print(f"   BREVO_TEMPLATE_VERIFY_RU: {template_ru or 'NOT SET'}")
    print(f"   BREVO_TEMPLATE_VERIFY_HE: {template_he or 'NOT SET'}")
    
    # Check service status
    print(f"\n2. Brevo Service Status:")
    brevo_service = get_brevo_service()
    print(f"   Service Enabled: {brevo_service.enabled}")
    
    if not brevo_service.enabled:
        print("\n[ERROR] Brevo is NOT configured!")
        print("\nPlease add these to your backend/.env file:")
        print("="*60)
        print("BREVO_API_KEY=your_api_key")
        print("BREVO_SENDER_EMAIL=your_verified_email")
        print("BREVO_SENDER_NAME=MenuMind AI")
        print("BREVO_TEMPLATE_VERIFY_EN=template_id")
        print("BREVO_TEMPLATE_VERIFY_RU=template_id")
        print("BREVO_TEMPLATE_VERIFY_HE=template_id")
        print("="*60)
        return False
    
    print(f"   API Key: {api_key[:30]}...")
    print(f"   Sender: {brevo_service.sender_name} <{brevo_service.sender_email}>")
    
    return True

def test_send_email():
    """Test sending an email"""
    
    print("\n" + "="*60)
    print("Test Email Sending")
    print("="*60)
    
    # Get test email from user
    test_email = input("\nEnter your email to receive test verification email: ").strip()
    
    if not test_email or '@' not in test_email:
        print("[ERROR] Invalid email address")
        return False
    
    print(f"\n[INFO] Sending test verification email to: {test_email}")
    
    brevo_service = get_brevo_service()
    
    # Send test email
    success, message = brevo_service.send_verification_email(
        to_email=test_email,
        user_name="Test User",
        activate_url="http://localhost:3000/verify-email/TEST123456",
        language='en'
    )
    
    if success:
        print("\n[SUCCESS] Email sent successfully!")
        print(f"[INFO] Message: {message}")
        print(f"[INFO] Check your inbox: {test_email}")
        print("[INFO] Check Brevo Dashboard → Logs for delivery status")
        return True
    else:
        print("\n[ERROR] Failed to send email")
        print(f"[ERROR] Message: {message}")
        return False

def main():
    """Main function"""
    
    # Test configuration
    if not test_brevo_config():
        return
    
    # Ask if user wants to send test email
    print("\n" + "="*60)
    send_test = input("\nDo you want to send a test email? (y/n): ").strip().lower()
    
    if send_test == 'y':
        test_send_email()
    
    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Test cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

### 6.3 Run Test

```bash
cd backend
python test_brevo.py
```

**Expected output:**
```
============================================================
Brevo Configuration Check
============================================================

1. Environment Variables:
   BREVO_API_KEY: SET (xkeysib-1a2b3c4d5e6f7g8h9i...)
   BREVO_SENDER_EMAIL: menumindaiproject@gmail.com
   BREVO_SENDER_NAME: MenuMind AI
   BREVO_TEMPLATE_VERIFY_EN: 1
   BREVO_TEMPLATE_VERIFY_RU: 2
   BREVO_TEMPLATE_VERIFY_HE: 3

2. Brevo Service Status:
   Service Enabled: True
   
Do you want to send a test email? (y/n): y

Enter your email to receive test verification email: your@email.com

[Brevo] 📧 Sending verification email to your@email.com using template 1
[Brevo] ✅ Successfully sent email to your@email.com
[SUCCESS] Email sent successfully!
```

### 6.4 Test from Frontend

1. **Register a new user:**
   - Go to: http://localhost:3000/register
   - Fill in registration form
   - Submit

2. **Check email:**
   - Email should arrive within **5-30 seconds**
   - Check inbox: `menumindaiproject@gmail.com`
   - Should see beautiful verification email
   - Click verification link
   - Should redirect to: http://localhost:3000/verify-email/KEY

3. **Verify in Brevo Dashboard:**
   - Go to: Brevo Dashboard → **Logs** → **Email Logs**
   - You should see your email with status: **Delivered ✅**

---

## 7. Troubleshooting

### Issue 1: "Service not configured"

**Problem:** Backend logs show `[Brevo] ⚠️ Service not fully configured`

**Solution:**
1. Check `.env` file is in `backend/` directory (not `frontend/`)
2. Verify all 6 variables are set
3. No quotes around values
4. Restart backend: `python manage.py runserver`

### Issue 2: "Invalid API key" (401 error)

**Problem:** `[Brevo] ❌ API error: 401 - Unauthorized`

**Solution:**
1. Double-check API key in `.env` matches Brevo Dashboard
2. API key should start with `xkeysib-`
3. No extra spaces or line breaks
4. Regenerate API key if needed

### Issue 3: "Email not delivered"

**Problem:** Test passes but email not received

**Solution:**
1. Check spam/junk folder
2. Check Brevo Dashboard → Logs
3. Verify sender email is verified (green checkmark)
4. Check Brevo account is activated

### Issue 4: "Template not found" (400 error)

**Problem:** `[Brevo] ❌ Template not found`

**Solution:**
1. Verify template IDs in `.env` match Brevo Dashboard
2. Templates must be **"Active"** (not draft)
3. Template IDs are numbers: `1`, `2`, `3`
4. Click "Save and Activate" after creating template

### Issue 5: "Rate limit exceeded" (429 error)

**Problem:** `[Brevo] ❌ Rate limit exceeded`

**Solution:**
1. Free plan: 300 emails/day
2. Wait 24 hours for limit reset
3. Upgrade to paid plan if needed
4. Check Brevo Dashboard → Usage

### Issue 6: Wrong language template

**Problem:** Email arrives in wrong language

**Solution:**
1. Check user's `preferred_language` field
2. Verify all 3 template IDs are correct in `.env`
3. Template selection: EN (default), RU, HE

---

## ✅ Success Checklist

- [ ] Brevo account created
- [ ] Sender email verified (green checkmark in Brevo)
- [ ] API key generated and copied
- [ ] 3 templates created (EN, RU, HE)
- [ ] All 3 template IDs copied
- [ ] All 6 variables in `backend/.env`
- [ ] `sib-api-v3-sdk` installed
- [ ] Backend restarted
- [ ] Test script shows "Service Enabled: True"
- [ ] Test email received successfully
- [ ] Registration email works from frontend

---

## 📊 Email Service Priority

Your system now has **3-tier email fallback**:

1. **🥇 Brevo (Primary)** - Fast, reliable, 300/day free
2. **🥈 EmailJS (Secondary)** - If Brevo fails
3. **🥉 Django SMTP (Final)** - Console output or Gmail SMTP

Backend logs will show which service was used:
```
[Brevo] ✅ Successfully sent verification email
[EmailJS] ⚠️ Brevo not configured, trying EmailJS
[Django SMTP] ⚠️ Using fallback SMTP
```

---

## 🎉 You're Done!

**Congratulations!** You've successfully integrated Brevo email service. Your users will now receive professional, fast, and reliable verification emails.

**Next steps:**
- Monitor email delivery in Brevo Dashboard
- Add more template types (welcome, password reset)
- Consider upgrading to paid plan for higher limits
- Set up custom domain for production

**Questions?** Check Brevo documentation: https://developers.brevo.com/

---

## 📚 Additional Resources

- **Brevo Dashboard:** https://app.brevo.com/
- **API Documentation:** https://developers.brevo.com/
- **Python SDK:** https://github.com/sendinblue/APIv3-python-library
- **Email Templates:** https://help.brevo.com/hc/en-us/articles/360000946299
- **Domain Verification:** https://help.brevo.com/hc/en-us/articles/360000991600

---

**Created for MenuMind AI - Email Verification System**  
**Version:** 0.9.0  
**Last Updated:** 2025-01-26

