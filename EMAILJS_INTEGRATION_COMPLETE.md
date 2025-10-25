# 📧 EmailJS Integration - Complete Setup Guide

## ✅ Implementation Complete!

This guide contains all the information you need to set up and use EmailJS with your MenuMind AI application.

---

## 📋 Table of Contents

1. [Environment Variables](#environment-variables)
2. [EmailJS Dashboard Setup](#emailjs-dashboard-setup)
3. [Email Template Creation](#email-template-creation)
4. [Testing Instructions](#testing-instructions)
5. [Troubleshooting](#troubleshooting)

---

## 🔐 Environment Variables

Add these variables to your `backend/.env` file:

```env
# EmailJS Configuration
EMAILJS_SERVICE_ID=service_xxxxxxx
EMAILJS_PUBLIC_KEY=your_public_key_here
EMAILJS_PRIVATE_KEY=your_private_key_here

# Email Templates (one for each language)
EMAILJS_TEMPLATE_VERIFY_EN=template_xxxxxxx_en
EMAILJS_TEMPLATE_VERIFY_RU=template_xxxxxxx_ru
EMAILJS_TEMPLATE_VERIFY_HE=template_xxxxxxx_he
```

### Variable Descriptions:

| Variable | Description | Where to Find |
|----------|-------------|---------------|
| `EMAILJS_SERVICE_ID` | Your email service identifier | EmailJS Dashboard → Email Services |
| `EMAILJS_PUBLIC_KEY` | Public API key | EmailJS Dashboard → Account → API Keys |
| `EMAILJS_PRIVATE_KEY` | Private API key (server-side) | EmailJS Dashboard → Account → API Keys |
| `EMAILJS_TEMPLATE_VERIFY_EN` | English verification template | EmailJS Dashboard → Email Templates |
| `EMAILJS_TEMPLATE_VERIFY_RU` | Russian verification template | EmailJS Dashboard → Email Templates |
| `EMAILJS_TEMPLATE_VERIFY_HE` | Hebrew verification template | EmailJS Dashboard → Email Templates |

---

## 🚀 EmailJS Dashboard Setup

### Step 1: Create Account

1. Go to [EmailJS.com](https://www.emailjs.com/)
2. Click **"Sign Up"** and create a free account
3. Verify your email address

### Step 2: Add Email Service

1. Navigate to **Email Services** in the dashboard
2. Click **"Add New Service"**
3. Choose your email provider:
   - **Gmail** (recommended for development)
   - **Outlook/Office365**
   - **SendGrid**
   - **Custom SMTP**
4. Follow the provider-specific setup:

#### For Gmail:
- Click **"Connect Account"**
- Authorize EmailJS to send emails via your Gmail
- **Important**: Enable 2FA and use App Password for production

#### For Custom SMTP:
- Enter your SMTP server details
- Host, port, username, password
- Test the connection

5. Copy the **Service ID** (e.g., `service_abc123`)
6. Save it to `.env` as `EMAILJS_SERVICE_ID`

### Step 3: Get API Keys

1. Go to **Account** → **General** → **API Keys**
2. Find your **Public Key** (e.g., `user_abc123`)
   - Save to `.env` as `EMAILJS_PUBLIC_KEY`
3. Find or generate **Private Key** (for server-side)
   - Save to `.env` as `EMAILJS_PRIVATE_KEY`
   - **⚠️ Keep this secret! Never expose in frontend code**

---

## 📝 Email Template Creation

You need to create **3 templates** (one for each language: EN, RU, HE).

### Step 4: Create Email Templates

1. Navigate to **Email Templates** in dashboard
2. Click **"Create New Template"**
3. For each language (EN, RU, HE):

#### Template Configuration:

**Template Name**: `Email Verification - English`  
**Template ID**: Will be auto-generated (e.g., `template_abc123_en`)

#### Email Content Structure:

**Subject Line:**
```
Verify your email address - MenuMind AI
```

**Email Body (HTML):**

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }
        .content {
            background: #f9f9f9;
            padding: 30px;
            border-radius: 0 0 10px 10px;
        }
        .button {
            display: inline-block;
            background: #667eea;
            color: white !important;
            padding: 15px 40px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
            font-weight: bold;
        }
        .button:hover {
            background: #5568d3;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{site_name}}</h1>
    </div>
    <div class="content">
        <h2>{{greeting}}</h2>
        <p>{{message}}</p>
        
        <div style="text-align: center;">
            <a href="{{activate_url}}" class="button">{{button_text}}</a>
        </div>
        
        <p style="color: #666; font-size: 14px; margin-top: 30px;">
            {{footer_text}}
        </p>
        
        <p style="color: #999; font-size: 12px; margin-top: 20px;">
            If the button doesn't work, copy and paste this link into your browser:<br>
            <a href="{{activate_url}}">{{activate_url}}</a>
        </p>
    </div>
    <div class="footer">
        <p>&copy; 2025 {{site_name}}. All rights reserved.</p>
    </div>
</body>
</html>
```

#### Template Variables:

EmailJS will automatically receive these variables from your backend:

| Variable | Description | Example |
|----------|-------------|---------|
| `{{to_email}}` | Recipient email | `user@example.com` |
| `{{user_name}}` | User's name | `John Doe` |
| `{{activate_url}}` | Verification URL | `http://localhost:3000/verify-email/abc123` |
| `{{site_name}}` | Site name | `MenuMind AI` |
| `{{subject}}` | Email subject | `Verify your email address` |
| `{{greeting}}` | Greeting text | `Hi John` |
| `{{message}}` | Main message | `Thank you for signing up...` |
| `{{button_text}}` | Button text | `Verify Email Address` |
| `{{footer_text}}` | Footer text | `If you did not create...` |

#### Language-Specific Templates:

**English (EN):**
- Subject: `Verify your email address - MenuMind AI`
- Button: `Verify Email Address`

**Russian (RU):**
- Subject: `Подтвердите ваш email адрес - MenuMind AI`
- Button: `Подтвердить Email`

**Hebrew (HE):**
- Subject: `אמת את כתובת האימייל שלך - MenuMind AI`
- Button: `אמת אימייל`
- **Note**: Set text direction to RTL in template settings

### Step 5: Save Template IDs

After creating each template:
1. Copy the **Template ID** from the dashboard
2. Add to `.env`:
```env
EMAILJS_TEMPLATE_VERIFY_EN=template_abc123_en
EMAILJS_TEMPLATE_VERIFY_RU=template_xyz789_ru
EMAILJS_TEMPLATE_VERIFY_HE=template_def456_he
```

### Step 6: Test Templates

1. In EmailJS dashboard, click **"Test It"** on each template
2. Fill in sample data:
```json
{
    "to_email": "your-test-email@example.com",
    "user_name": "Test User",
    "activate_url": "http://localhost:3000/verify-email/test123",
    "site_name": "MenuMind AI",
    "greeting": "Hi Test User",
    "message": "Thank you for signing up!",
    "button_text": "Verify Email",
    "footer_text": "Link expires in 24 hours"
}
```
3. Send test email
4. Verify you receive it correctly

---

## 🧪 Testing Instructions

### 1. Restart Backend

After adding environment variables:

```bash
cd backend
# Restart your Django server
python manage.py runserver
```

You should see:
```
[EmailJS] ✅ Service configured successfully
```

If misconfigured:
```
[EmailJS] ⚠️ Service not fully configured. Missing credentials.
```

### 2. Test Registration Flow

#### Create a New User:

```bash
# Using curl
curl -X POST http://localhost:8000/api/users/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

#### Check Backend Logs:

You should see:
```
📧 VERIFICATION EMAIL
============================================================
To: test@example.com
Language: en
Verification URL: http://localhost:3000/verify-email/abc123
============================================================

[EmailJS] 📧 Sending verification email to test@example.com (attempt 1/3)
[EmailJS] ✅ Successfully sent verification email to test@example.com
```

### 3. Test Resend Verification

```bash
# Login first
TOKEN=$(curl -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"SecurePass123!"}' \
  | jq -r '.access')

# Resend verification
curl -X POST http://localhost:8000/api/users/auth/resend-verification/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

Expected response:
```json
{
    "message": "Verification email sent. Please check your inbox."
}
```

### 4. Test Email Reception

1. Check your inbox for the verification email
2. Verify the email design looks correct
3. Click the verification button
4. Should redirect to `http://localhost:3000/verify-email/KEY`
5. Frontend should show success message

### 5. Test Multilingual Support

Create users with different preferred languages:

```python
# In Django shell (python manage.py shell)
from django.contrib.auth import get_user_model
User = get_user_model()

# Create Russian user
user_ru = User.objects.create_user(
    username='testuser_ru',
    email='test_ru@example.com',
    password='SecurePass123!'
)
user_ru.preferred_language = 'ru'
user_ru.save()

# Create Hebrew user
user_he = User.objects.create_user(
    username='testuser_he',
    email='test_he@example.com',
    password='SecurePass123!'
)
user_he.preferred_language = 'he'
user_he.save()
```

Trigger verification emails and verify correct language template is used.

---

## 🐛 Troubleshooting

### Issue: "EmailJS Service not configured"

**Cause**: Missing or incorrect environment variables

**Solution**:
1. Check `.env` file exists in `backend/` directory
2. Verify all 6 variables are present
3. Restart Django server
4. Check backend logs for specific missing variables

### Issue: "Failed to send email (401 Unauthorized)"

**Cause**: Incorrect API keys

**Solution**:
1. Re-check `EMAILJS_PUBLIC_KEY` and `EMAILJS_PRIVATE_KEY`
2. In EmailJS dashboard, go to Account → API Keys
3. Copy keys exactly (no extra spaces)
4. Update `.env` and restart

### Issue: "Failed to send email (404 Not Found)"

**Cause**: Incorrect Service ID or Template ID

**Solution**:
1. Verify `EMAILJS_SERVICE_ID` matches dashboard
2. Verify template IDs match exactly
3. Ensure templates are **Active** in dashboard

### Issue: Email sends but user doesn't receive

**Possible Causes**:
1. Email in spam folder (check spam)
2. Email service not properly configured
3. Recipient email blocked by provider

**Solutions**:
1. Add sender to safe senders list
2. Check EmailJS dashboard → Logs for delivery status
3. Verify email service connection in EmailJS
4. For Gmail: ensure app password is used

### Issue: Fallback to Django SMTP always triggers

**Cause**: EmailJS configuration incomplete

**Solution**:
1. Check backend logs for `[EmailJS] ⚠️` messages
2. Verify all 3 template IDs are configured
3. Test each template in EmailJS dashboard
4. Ensure templates have correct variable names

### Issue: Wrong language template used

**Cause**: User language not set or template missing

**Solution**:
1. Check `user.preferred_language` in database
2. Verify template exists for that language
3. Backend will fallback to English if language template missing

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Email Flow                             │
└─────────────────────────────────────────────────────────┘

1. User Action (Registration / Resend)
         ↓
2. Django View (views.py)
         ↓
3. Allauth sends confirmation
         ↓
4. MultilingualAccountAdapter.send_confirmation_mail()
         ↓
5. Try EmailJS Service
         ├─ Success → Email sent ✅
         └─ Failure → Fallback to Django SMTP ⚠️
```

### Fallback Strategy:

The system is **production-safe** with automatic fallback:

1. **Primary**: EmailJS (fast, reliable, no SMTP config needed)
2. **Fallback**: Django SMTP (your existing setup)

This means:
- ✅ Emails always send (even if EmailJS down)
- ✅ Zero downtime during migration
- ✅ No breaking changes to existing flow

---

## 🎯 Benefits of EmailJS

### vs Django SMTP:

| Feature | EmailJS | Django SMTP |
|---------|---------|-------------|
| **Setup Time** | 10 minutes | 30+ minutes |
| **Configuration** | Dashboard UI | Code + env vars |
| **Template Editing** | Live UI editor | Edit code, restart server |
| **Email Tracking** | Built-in dashboard | Custom implementation |
| **Deliverability** | Optimized by provider | Depends on your server |
| **Multilingual** | Template per language | Code-based rendering |
| **Cost** | Free tier: 200/month | Depends on provider |
| **Security** | API keys only | SMTP credentials |

---

## 📈 Production Considerations

### 1. Rate Limits

**EmailJS Free Tier:**
- 200 emails/month
- For production, upgrade to paid plan ($10/month = 10K emails)

### 2. Security

**✅ DO:**
- Keep `EMAILJS_PRIVATE_KEY` secret
- Use environment variables (never commit)
- Rotate keys periodically

**❌ DON'T:**
- Expose private key in frontend
- Commit `.env` to git
- Share keys in public channels

### 3. Monitoring

**Track Email Delivery:**
1. EmailJS Dashboard → Logs
2. Monitor success rate
3. Set up alerts for failures

**Backend Logging:**
```python
# Check logs for:
[EmailJS] ✅ Successfully sent  # Success
[EmailJS] ⚠️ Failed to send    # Needs attention
[EmailJS] ❌ ...               # Critical error
```

### 4. Backup Strategy

**Always maintain SMTP fallback:**
- Configure Django `EMAIL_*` settings
- Test fallback quarterly
- Document SMTP credentials

---

## ✅ Checklist

Before going to production:

- [ ] EmailJS account created
- [ ] Email service connected and tested
- [ ] All 3 language templates created
- [ ] Template IDs added to `.env`
- [ ] API keys added to `.env`
- [ ] Backend restarted with new config
- [ ] Test email sent successfully
- [ ] Multilingual templates tested
- [ ] Fallback to SMTP tested
- [ ] Production email service configured (not Gmail personal)
- [ ] Monitoring dashboard reviewed
- [ ] Error handling tested

---

## 📞 Support

### EmailJS Support:
- Documentation: https://www.emailjs.com/docs/
- Community: https://www.emailjs.com/community/

### MenuMind AI Issues:
- Check backend logs for detailed errors
- Verify all environment variables
- Test with `curl` commands above

---

## 🎉 Summary

**You now have:**
- ✅ EmailJS integration with automatic fallback
- ✅ Multilingual email templates (EN/RU/HE)
- ✅ Production-ready error handling
- ✅ Zero downtime migration strategy
- ✅ Comprehensive testing guide

**Next steps:**
1. Set up EmailJS account
2. Create email templates
3. Add environment variables
4. Test the integration
5. Deploy to production

**The system will work immediately with Django SMTP while you set up EmailJS. No rush!** 🚀

