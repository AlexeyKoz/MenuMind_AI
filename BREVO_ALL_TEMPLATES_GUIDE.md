# 📧 Brevo Email Templates - Complete Template Guide

## 🎯 Overview

This guide provides all email templates you need for MenuMind AI. Each template comes in 3 languages (English, Russian, Hebrew) and uses Brevo's template system.

---

## 📋 Template Types

| Template Type | Priority | Purpose |
|---------------|----------|---------|
| **Verification** | 🔴 Critical | Email address verification (needed now) |
| **Welcome** | 🟡 High | Welcome message after verification |
| **Password Reset** | 🔴 Critical | Password reset link |
| **Notification** | 🟢 Medium | Generic notifications |

---

## 🔑 Template Variables Reference

All templates use Brevo's `{{ params.VARIABLE_NAME }}` syntax:

### Common Variables (All Templates)
- `{{ params.SITE_NAME }}` - "MenuMind AI"
- `{{ params.USER_NAME }}` - User's display name
- `{{ params.USER_EMAIL }}` - User's email address

### Template-Specific Variables

**Verification:**
- `{{ params.ACTIVATE_URL }}` - Email verification link

**Welcome:**
- `{{ params.DASHBOARD_URL }}` - Link to dashboard

**Password Reset:**
- `{{ params.RESET_URL }}` - Password reset link

**Notification:**
- `{{ params.SUBJECT }}` - Notification subject
- `{{ params.MESSAGE }}` - Notification message
- `{{ params.ACTION_URL }}` - Optional action button URL
- `{{ params.ACTION_TEXT }}` - Optional action button text

---

## 📝 Template 1: Email Verification (3 languages)

### 1A. English Verification

**Template Name:** `Email Verification - English`  
**Subject:** `Verify your email address - MenuMind AI`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; margin: 0; padding: 0; }
        .email-container { max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 600; }
        .content { padding: 40px 30px; }
        .content h2 { color: #333; font-size: 24px; margin: 0 0 20px 0; }
        .content p { color: #666; font-size: 16px; margin: 0 0 20px 0; }
        .button-container { text-align: center; margin: 30px 0; }
        .button { display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white !important; padding: 16px 48px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px; }
        .footer-note { color: #999; font-size: 14px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
        .footer { background: #f9f9f9; padding: 20px 30px; text-align: center; color: #999; font-size: 14px; }
        .link-fallback { color: #667eea; word-break: break-all; font-size: 13px; }
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
                <p>Email verification helps us protect your account and ensure you receive important updates.</p>
                
                <p style="margin-top: 20px;"><strong>Didn't sign up?</strong></p>
                <p>If you didn't create this account, you can safely ignore this email.</p>
                
                <p style="margin-top: 30px; font-size: 12px;">
                    <strong>Button not working?</strong> Copy and paste this link:<br>
                    <a href="{{ params.ACTIVATE_URL }}" class="link-fallback">{{ params.ACTIVATE_URL }}</a>
                </p>
            </div>
        </div>
        <div class="footer">
            <p>&copy; 2025 MenuMind AI. All rights reserved.</p>
            <p>This is an automated message. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
```

**Environment Variable:** `BREVO_TEMPLATE_VERIFY_EN=1`

---

### 1B. Russian Verification

**Template Name:** `Email Verification - Russian`  
**Subject:** `Подтвердите ваш email адрес - MenuMind AI`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        /* Same CSS as English */
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; margin: 0; padding: 0; }
        .email-container { max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 600; }
        .content { padding: 40px 30px; }
        .content h2 { color: #333; font-size: 24px; margin: 0 0 20px 0; }
        .content p { color: #666; font-size: 16px; margin: 0 0 20px 0; }
        .button-container { text-align: center; margin: 30px 0; }
        .button { display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white !important; padding: 16px 48px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px; }
        .footer-note { color: #999; font-size: 14px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
        .footer { background: #f9f9f9; padding: 20px 30px; text-align: center; color: #999; font-size: 14px; }
        .link-fallback { color: #667eea; word-break: break-all; font-size: 13px; }
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
            <p>Чтобы начать использовать ваш аккаунт, пожалуйста, подтвердите ваш email адрес:</p>
            
            <div class="button-container">
                <a href="{{ params.ACTIVATE_URL }}" class="button">Подтвердить Email</a>
            </div>
            
            <div class="footer-note">
                <p><strong>Зачем подтверждать?</strong></p>
                <p>Подтверждение email помогает защитить ваш аккаунт и гарантирует получение важных обновлений.</p>
                
                <p style="margin-top: 20px;"><strong>Не регистрировались?</strong></p>
                <p>Если вы не создавали этот аккаунт, можете проигнорировать это письмо.</p>
                
                <p style="margin-top: 30px; font-size: 12px;">
                    <strong>Кнопка не работает?</strong> Скопируйте эту ссылку:<br>
                    <a href="{{ params.ACTIVATE_URL }}" class="link-fallback">{{ params.ACTIVATE_URL }}</a>
                </p>
            </div>
        </div>
        <div class="footer">
            <p>&copy; 2025 MenuMind AI. Все права защищены.</p>
            <p>Это автоматическое сообщение. Пожалуйста, не отвечайте.</p>
        </div>
    </div>
</body>
</html>
```

**Environment Variable:** `BREVO_TEMPLATE_VERIFY_RU=2`

---

### 1C. Hebrew Verification

**Template Name:** `Email Verification - Hebrew`  
**Subject:** `אמת את כתובת האימייל שלך - MenuMind AI`  
**⚠️ IMPORTANT:** Set text direction to **RTL**

```html
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, Helvetica, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; margin: 0; padding: 0; direction: rtl; text-align: right; }
        .email-container { max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 600; }
        .content { padding: 40px 30px; }
        .content h2 { color: #333; font-size: 24px; margin: 0 0 20px 0; }
        .content p { color: #666; font-size: 16px; margin: 0 0 20px 0; }
        .button-container { text-align: center; margin: 30px 0; }
        .button { display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white !important; padding: 16px 48px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px; }
        .footer-note { color: #999; font-size: 14px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
        .footer { background: #f9f9f9; padding: 20px 30px; text-align: center; color: #999; font-size: 14px; }
        .link-fallback { color: #667eea; word-break: break-all; font-size: 13px; direction: ltr; display: inline-block; }
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
            <p>כדי להתחיל להשתמש בחשבון שלך, אנא אמת את כתובת האימייל שלך:</p>
            
            <div class="button-container">
                <a href="{{ params.ACTIVATE_URL }}" class="button">אמת כתובת אימייל</a>
            </div>
            
            <div class="footer-note">
                <p><strong>למה לאמת?</strong></p>
                <p>אימות אימייל עוזר להגן על החשבון שלך ולוודא שאתה מקבל עדכונים חשובים.</p>
                
                <p style="margin-top: 20px;"><strong>לא נרשמת?</strong></p>
                <p>אם לא יצרת חשבון זה, אתה יכול להתעלם מהודעה זו.</p>
                
                <p style="margin-top: 30px; font-size: 12px;">
                    <strong>הכפתור לא עובד?</strong> העתק קישור זה:<br>
                    <a href="{{ params.ACTIVATE_URL }}" class="link-fallback">{{ params.ACTIVATE_URL }}</a>
                </p>
            </div>
        </div>
        <div class="footer">
            <p>&copy; 2025 MenuMind AI. כל הזכויות שמורות.</p>
            <p>זוהי הודעה אוטומטית. אנא אל תענה.</p>
        </div>
    </div>
</body>
</html>
```

**Environment Variable:** `BREVO_TEMPLATE_VERIFY_HE=3`

---

## ✅ Your `.env` Configuration

After creating all templates, add their IDs to `backend/.env`:

```env
# ============================================
# BREVO EMAIL TEMPLATES
# ============================================

# Already configured
BREVO_API_KEY=14f78b35796c4f9bb947e71ae815a2...
BREVO_SENDER_EMAIL=menumindaiproject@gmail.com
BREVO_SENDER_NAME=MenuMind AI

# REQUIRED: Email Verification (add these 3)
BREVO_TEMPLATE_VERIFY_EN=1
BREVO_TEMPLATE_VERIFY_RU=2
BREVO_TEMPLATE_VERIFY_HE=3

# OPTIONAL: Welcome Email (create later)
# BREVO_TEMPLATE_WELCOME_EN=4
# BREVO_TEMPLATE_WELCOME_RU=5
# BREVO_TEMPLATE_WELCOME_HE=6

# OPTIONAL: Password Reset (create later)
# BREVO_TEMPLATE_PASSWORD_RESET_EN=7
# BREVO_TEMPLATE_PASSWORD_RESET_RU=8
# BREVO_TEMPLATE_PASSWORD_RESET_HE=9

# OPTIONAL: Notifications (create later)
# BREVO_TEMPLATE_NOTIFICATION_EN=10
# BREVO_TEMPLATE_NOTIFICATION_RU=11
# BREVO_TEMPLATE_NOTIFICATION_HE=12
```

---

## 🧪 Testing After Configuration

### 1. Test Configuration

```bash
cd backend
python test_brevo.py
```

**Expected Output:**
```
Brevo Service Status: True
BREVO_TEMPLATE_VERIFY_EN: 1
BREVO_TEMPLATE_VERIFY_RU: 2
BREVO_TEMPLATE_VERIFY_HE: 3
```

### 2. Send Test Email

When prompted:
```
Do you want to send a test email? (y/n): y
Enter your email: your@email.com
```

### 3. Test from Frontend

```
1. Register new user
2. Check email
3. Click verification link
```

---

## 📊 Template Creation Workflow

### Quick Start (15 minutes)

**1. Login to Brevo:**
- https://app.brevo.com/

**2. Create Templates:**
- Campaigns → Transactional → Templates → New Template

**3. For Each Template:**
- Name: `Email Verification - [Language]`
- Subject: (see above)
- Content: Copy HTML from this guide
- Save & Activate
- Copy Template ID

**4. Update `.env`:**
- Add 3 template IDs
- Restart backend

**5. Test:**
- Run `python test_brevo.py`
- Send test email

---

## 🎯 Priority Order

**Implement Now (Critical):**
1. ✅ Verification EN - Template ID: `BREVO_TEMPLATE_VERIFY_EN`
2. ✅ Verification RU - Template ID: `BREVO_TEMPLATE_VERIFY_RU`
3. ✅ Verification HE - Template ID: `BREVO_TEMPLATE_VERIFY_HE`

**Implement Later (Optional):**
4. ⏳ Welcome emails (3 languages)
5. ⏳ Password reset (3 languages)
6. ⏳ Notifications (3 languages)

---

## 🚀 Next Steps

1. **Create 3 verification templates** in Brevo Dashboard
2. **Add template IDs** to `backend/.env`
3. **Restart backend:** `python manage.py runserver`
4. **Test:** `python test_brevo.py`
5. **Test from frontend:** Register new user

---

**Questions?** See `BREVO_SETUP_COMPLETE_GUIDE.md` for detailed instructions.

**Template IDs:** Replace `1`, `2`, `3` with your actual template IDs from Brevo Dashboard.

