# 📧 EmailJS Setup Guide for menumindaiproject@gmail.com

## ✅ Step-by-Step Setup

### **IMPORTANT:** EmailJS configuration must be in **BACKEND** `.env` file, NOT frontend!

---

## 🔧 Step 1: Setup EmailJS Account

### **1.1 Create EmailJS Account**
1. Go to https://www.emailjs.com/
2. Click "Sign Up"
3. Register with your email: `menumindaiproject@gmail.com`
4. Verify your email

### **1.2 Add Gmail Service**
1. After login, go to **Email Services** (left sidebar)
2. Click **"Add New Service"**
3. Select **Gmail**
4. Click **"Connect Account"**
5. Choose/login with: `menumindaiproject@gmail.com`
6. Grant permissions to EmailJS
7. **Copy the Service ID** (looks like `service_abc123`)

---

## 🔑 Step 2: Get API Keys

1. Go to **Account** → **General** (left sidebar)
2. Scroll to **API Keys** section
3. Find your **Public Key** (looks like `user_abc123xyz`)
4. Find or click **"Create Private Key"** for **Private Key** (for server-side)
5. **Copy both keys** - you'll need them!

---

## 📝 Step 3: Create Email Templates

You need to create **3 templates** (one for each language).

### **Template 1: English**

1. Go to **Email Templates** (left sidebar)
2. Click **"Create New Template"**
3. Template Name: `Email Verification - English`

**Subject:**
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
        <p>&copy; 2025 MenuMind AI. All rights reserved.</p>
    </div>
</body>
</html>
```

4. Click **"Save"**
5. **Copy the Template ID** (looks like `template_abc123`)

### **Template 2: Russian**

Repeat the same process but use Russian text:

**Template Name:** `Email Verification - Russian`

**Subject:**
```
Подтвердите ваш email адрес - MenuMind AI
```

Use the same HTML structure but the variables will be in Russian (handled by backend).

**Copy the Template ID**

### **Template 3: Hebrew**

**Template Name:** `Email Verification - Hebrew`

**Subject:**
```
אמת את כתובת האימייל שלך - MenuMind AI
```

**IMPORTANT:** In EmailJS template settings, set **Text Direction to RTL** (Right-to-Left)

Use the same HTML structure.

**Copy the Template ID**

---

## 📄 Step 4: Update Backend .env File

Now add these to your **`backend/.env`** file (NOT frontend!):

```env
# ============================================
# EmailJS Configuration
# ============================================
EMAILJS_SERVICE_ID=service_YOUR_SERVICE_ID_HERE
EMAILJS_PUBLIC_KEY=user_YOUR_PUBLIC_KEY_HERE
EMAILJS_PRIVATE_KEY=YOUR_PRIVATE_KEY_HERE
EMAILJS_TEMPLATE_VERIFY_EN=template_ENGLISH_ID_HERE
EMAILJS_TEMPLATE_VERIFY_RU=template_RUSSIAN_ID_HERE
EMAILJS_TEMPLATE_VERIFY_HE=template_HEBREW_ID_HERE
```

**Example with real IDs:**
```env
# EmailJS Configuration
EMAILJS_SERVICE_ID=service_abc123
EMAILJS_PUBLIC_KEY=user_xyz789
EMAILJS_PRIVATE_KEY=1234567890abcdef
EMAILJS_TEMPLATE_VERIFY_EN=template_en_123
EMAILJS_TEMPLATE_VERIFY_RU=template_ru_456
EMAILJS_TEMPLATE_VERIFY_HE=template_he_789
```

### **Variable Names (IMPORTANT):**
- ✅ Correct: `EMAILJS_TEMPLATE_VERIFY_EN`
- ❌ Wrong: `EMAILJS_TEMPLATE_VERIFICATION_EN` (you had this)
- ❌ Wrong: `MAILJS_TEMPLATE_VERIFICATION_RU` (missing E)

---

## 🔄 Step 5: Restart Backend

```bash
# Stop your backend (Ctrl+C in terminal)

# Start again
cd backend
python manage.py runserver
```

**Look for this message:**
```
[EmailJS] ✅ Service configured successfully
```

If you see:
```
[EmailJS] ⚠️ Service not fully configured
```

Something is wrong with your .env file.

---

## 🧪 Step 6: Test Configuration

```bash
cd backend
python test_emailjs.py
```

**Expected output:**
```
============================================================
EmailJS Configuration Check
============================================================

1. Environment Variables:
   EMAILJS_SERVICE_ID: SET (service_abc...)
   EMAILJS_PUBLIC_KEY: SET (user_xyz...)
   EMAILJS_PRIVATE_KEY: SET (16 chars)
   EMAILJS_TEMPLATE_VERIFY_EN: SET (template_en_123)
   EMAILJS_TEMPLATE_VERIFY_RU: SET (template_ru_456)
   EMAILJS_TEMPLATE_VERIFY_HE: SET (template_he_789)

2. EmailJS Service Status:
   Service Enabled: True
   
Do you want to send a test email? (y/n):
```

Type `y` and enter your email to test!

---

## ✅ Step 7: Test Real Email

### **Option A: From Test Script**
```bash
cd backend
python test_emailjs.py
# Type 'y' when asked
# Enter your email: menumindaiproject@gmail.com
# Check inbox!
```

### **Option B: From Frontend**
1. Register a new user
2. Check `menumindaiproject@gmail.com` inbox
3. You should receive verification email!
4. Click the link to verify

---

## 📋 Checklist

Before testing, make sure:

- [ ] EmailJS account created
- [ ] Gmail service connected (`menumindaiproject@gmail.com`)
- [ ] Service ID copied
- [ ] Public Key copied
- [ ] Private Key copied  
- [ ] 3 templates created (EN, RU, HE)
- [ ] All 3 template IDs copied
- [ ] All 6 variables added to **`backend/.env`** (NOT frontend!)
- [ ] Variable names are correct (`VERIFY` not `VERIFICATION`)
- [ ] Backend restarted
- [ ] Test script shows "Service Enabled: True"

---

## 🐛 Common Issues

### **Issue 1: Variables in wrong .env file**
**Problem:** You put them in `frontend/.env`  
**Solution:** Move to `backend/.env`

### **Issue 2: Wrong variable names**
**Problem:** `EMAILJS_TEMPLATE_VERIFICATION_EN`  
**Solution:** Should be `EMAILJS_TEMPLATE_VERIFY_EN`

### **Issue 3: Service still disabled**
**Problem:** `Service Enabled: False`  
**Solution:** 
1. Check all 6 variables are in `backend/.env`
2. No quotes around values
3. No extra spaces
4. Restart backend

### **Issue 4: Email not received**
**Problem:** Test passes but no email  
**Solution:**
1. Check spam folder
2. Check EmailJS dashboard → Logs
3. Look for error messages in backend console
4. Verify Gmail service is connected in EmailJS

### **Issue 5: 401 Unauthorized**
**Problem:** Wrong API keys  
**Solution:** 
1. Re-copy keys from EmailJS dashboard
2. Make sure Private Key is for server-side
3. No extra characters or spaces

---

## 📊 File Locations

**Configuration:**
- ✅ `backend/.env` - EmailJS variables go HERE
- ❌ `frontend/.env` - NOT here!

**Code:**
- `backend/menumine_ai/settings.py` - Reads .env variables (already updated ✅)
- `backend/apps/users/services/email_service.py` - EmailJS service (already created ✅)
- `backend/apps/users/adapters.py` - Uses EmailJS (already integrated ✅)

---

## 🎯 Your Backend .env Template

Copy this and fill in your actual IDs:

```env
# ============================================
# EmailJS Configuration for menumindaiproject@gmail.com
# ============================================

# Service ID from EmailJS Dashboard → Email Services
EMAILJS_SERVICE_ID=service_

# Public Key from EmailJS Dashboard → Account → API Keys
EMAILJS_PUBLIC_KEY=user_

# Private Key from EmailJS Dashboard → Account → API Keys
EMAILJS_PRIVATE_KEY=

# Template IDs from EmailJS Dashboard → Email Templates
EMAILJS_TEMPLATE_VERIFY_EN=template_
EMAILJS_TEMPLATE_VERIFY_RU=template_
EMAILJS_TEMPLATE_VERIFY_HE=template_

# Note: NO quotes around values, NO spaces before/after =
```

---

## 🚀 Quick Start Commands

```bash
# 1. Edit backend .env file
# Add all 6 EmailJS variables

# 2. Restart backend
cd backend
python manage.py runserver

# 3. Test configuration
cd backend
python test_emailjs.py

# 4. Test from frontend
# Register new user and check email!
```

---

## ✅ Success Indicators

**Backend console shows:**
```
[EmailJS] ✅ Service configured successfully
[EmailJS] 📧 Sending verification email to user@example.com
[EmailJS] ✅ Successfully sent verification email to user@example.com
```

**Test script shows:**
```
Service Enabled: True
[SUCCESS] Email sent successfully!
```

**Inbox shows:**
- New email from `menumindaiproject@gmail.com`
- Subject: "Verify your email address - MenuMind AI"
- Beautiful HTML template
- Working verification link

---

## 🎉 Summary

**What you need to do:**

1. ✅ Create EmailJS account
2. ✅ Connect Gmail (`menumindaiproject@gmail.com`)
3. ✅ Get Service ID + API Keys
4. ✅ Create 3 templates (EN/RU/HE)
5. ✅ Add 6 variables to **`backend/.env`**
6. ✅ Restart backend
7. ✅ Test!

**Everything is ready in the code - you just need to configure EmailJS and update backend/.env!**

🚀 **Follow the steps above and you'll have real email verification working in 10-15 minutes!**

