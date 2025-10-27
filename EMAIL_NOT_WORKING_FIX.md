# 📧 Email Verification Not Working - DIAGNOSIS & FIX

## 🔍 Problem Identified

You're not receiving verification emails because:

### **1. EmailJS is NOT Configured**
```
EMAILJS_SERVICE_ID: NOT SET
EMAILJS_PUBLIC_KEY: NOT SET
EMAILJS_PRIVATE_KEY: NOT SET
All templates: NOT SET
```

**Result:** EmailJS is disabled, falls back to Django SMTP

### **2. Django is in DEBUG Mode**
```python
# In settings.py
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**Result:** Emails are printed to **backend console logs**, not sent to real addresses!

---

## ✅ Solutions (Choose One)

### **Option 1: Quick Test - Enable Console Emails (Recommended for Testing)**

**Check your backend terminal logs** - the email content should be printed there!

Look for output like:
```
============================================================
📧 VERIFICATION EMAIL
============================================================
To: your-email@example.com
Subject: Verify your email address
Verification URL: http://localhost:3000/verify-email/abc123
============================================================

Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: Verify your email address
From: noreply@example.com
To: your-email@example.com

Hi there,

Please verify your email address by clicking the link below:
http://localhost:3000/verify-email/abc123
```

**To verify email manually:**
1. Copy the verification URL from backend logs
2. Paste it in your browser
3. Email will be verified! ✅

---

### **Option 2: Setup EmailJS (For Real Emails)**

**Follow these steps to configure EmailJS:**

#### **Step 1: Create EmailJS Account**
1. Go to https://www.emailjs.com/
2. Sign up for free account
3. Verify your email

#### **Step 2: Add Email Service**
1. Dashboard → Email Services
2. Click "Add New Service"
3. Choose your provider (Gmail recommended)
4. Connect your email account
5. Copy the **Service ID** (e.g., `service_abc123`)

#### **Step 3: Get API Keys**
1. Dashboard → Account → API Keys
2. Copy **Public Key** (e.g., `user_abc123`)
3. Copy or generate **Private Key** (for server-side)

#### **Step 4: Create Email Templates**

Create 3 templates (one for each language):

**Template: Email Verification - English**
- Go to Dashboard → Email Templates
- Click "Create New Template"
- Use this HTML:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
        .button { 
            display: inline-block; 
            background: #667eea; 
            color: white !important; 
            padding: 15px 40px; 
            text-decoration: none; 
            border-radius: 5px; 
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <h1>{{site_name}}</h1>
    <h2>{{greeting}}</h2>
    <p>{{message}}</p>
    
    <div style="text-align: center;">
        <a href="{{activate_url}}" class="button">{{button_text}}</a>
    </div>
    
    <p style="color: #666; font-size: 14px; margin-top: 30px;">
        {{footer_text}}
    </p>
    
    <p style="color: #999; font-size: 12px;">
        If the button doesn't work, copy and paste this link:<br>
        <a href="{{activate_url}}">{{activate_url}}</a>
    </p>
</body>
</html>
```

- Save and copy the **Template ID**
- Repeat for Russian and Hebrew (translate texts)

#### **Step 5: Add to .env File**

Edit `backend/.env` and add:

```env
# EmailJS Configuration
EMAILJS_SERVICE_ID=service_YOUR_ID_HERE
EMAILJS_PUBLIC_KEY=user_YOUR_PUBLIC_KEY
EMAILJS_PRIVATE_KEY=YOUR_PRIVATE_KEY_HERE
EMAILJS_TEMPLATE_VERIFY_EN=template_ENGLISH_ID
EMAILJS_TEMPLATE_VERIFY_RU=template_RUSSIAN_ID
EMAILJS_TEMPLATE_VERIFY_HE=template_HEBREW_ID
```

#### **Step 6: Restart Backend**

```bash
# Stop backend (Ctrl+C)
# Restart:
cd backend
python manage.py runserver
```

You should see:
```
[EmailJS] ✅ Service configured successfully
```

#### **Step 7: Test**

Run the test script:
```bash
cd backend
python test_emailjs.py
```

Enter your email when prompted to receive a test verification email!

---

### **Option 3: Use Gmail SMTP (Alternative to EmailJS)**

If you prefer traditional SMTP over EmailJS:

#### **Step 1: Setup Gmail App Password**
1. Go to https://myaccount.google.com/security
2. Enable 2-Factor Authentication
3. Go to "App passwords"
4. Create new app password for "Mail"
5. Copy the generated password

#### **Step 2: Add to .env**

```env
# Gmail SMTP Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password-here
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

#### **Step 3: Modify settings.py (temporary for testing)**

Find this section and comment out DEBUG check:
```python
# Email Configuration
# if DEBUG:
#     EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# else:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@menumine.com')
```

#### **Step 4: Restart Backend**
```bash
python manage.py runserver
```

---

## 🧪 Testing

### **Test with Backend Logs (Console Backend)**

1. Keep backend running
2. Try to resend verification email from frontend
3. Check backend terminal - you'll see the email content printed
4. Copy the verification URL
5. Paste in browser to verify

### **Test with Real Emails (EmailJS/SMTP)**

1. Configure EmailJS or Gmail SMTP (see above)
2. Restart backend
3. Register new user or resend verification
4. Check your inbox (and spam folder!)
5. Click verification link

---

## 📊 Quick Diagnosis Tool

Run this anytime to check your configuration:

```bash
cd backend
python test_emailjs.py
```

It will tell you:
- ✅ What's configured
- ❌ What's missing
- 🧪 Option to send test email

---

## 🎯 Recommended Approach

**For Development/Testing:**
1. ✅ Use console backend (current setup)
2. ✅ Check backend logs for verification URLs
3. ✅ Manually copy/paste URLs to verify

**For Production:**
1. ✅ Setup EmailJS (easier, no SMTP config)
2. ✅ Or setup Gmail SMTP
3. ✅ Users get real emails

---

## 📝 Current Status

**Email Backend:** Console (logs only)  
**EmailJS:** Not configured  
**SMTP:** Not configured  

**Result:** Emails are printed to backend console

---

## 🔍 Where to Find Verification URL

**In backend terminal, look for:**
```
============================================================
📧 VERIFICATION EMAIL
============================================================
To: user@example.com
...
Verification URL: http://localhost:3000/verify-email/ABC123XYZ
============================================================
```

**Copy this URL and paste in browser to verify the email!**

---

## 📚 Documentation

- **EmailJS Full Guide:** `EMAILJS_INTEGRATION_COMPLETE.md`
- **EmailJS Quick Ref:** `EMAILJS_QUICK_REFERENCE.md`
- **Test Tool:** `backend/test_emailjs.py`

---

## 🎉 Summary

**Problem:** Not receiving emails  
**Cause 1:** EmailJS not configured (falls back to console)  
**Cause 2:** DEBUG=True uses console backend  

**Quick Fix:** Check backend logs for verification URL  
**Proper Fix:** Configure EmailJS or Gmail SMTP  

**Status:** ✅ System working correctly (console mode)

🚀 **Choose your preferred email method and follow the steps above!**

