# 📧 Email Verification Testing Guide - bishul.me

## Overview
This guide will help you test that users receive verification emails after the Mailjet configuration update.

---

## ✅ What Was Updated

### Mailjet Template IDs:
- **English (EN)**: `7459709`
- **Russian (RU)**: `7459713`
- **Hebrew (HE)**: `7459704`

### Sender Configuration:
- **From**: `BishulSheli <support@bishul.me>`
- **Site Name**: `bishul.me`
- **Brand Color**: `#9B59B6` (Purple gradient)

---

## 🧪 Testing Methods

### Method 1: Using the Test Command (Recommended)

The easiest way to test all three language templates:

```bash
cd backend
python manage.py test_verification_email your_email@example.com --all-languages
```

**Test specific language:**
```bash
# English only
python manage.py test_verification_email your_email@example.com --language en

# Russian only
python manage.py test_verification_email your_email@example.com --language ru

# Hebrew only
python manage.py test_verification_email your_email@example.com --language he
```

**Test with Mailjet templates (not simple HTML):**
```bash
python manage.py test_verification_email your_email@example.com --all-languages --use-templates
```

---

### Method 2: Create a Test User (Real Flow)

Test the actual registration flow:

#### Step 1: Start your local server
```bash
# If not running already
start_fullstack_complete.bat
```

#### Step 2: Open the app
```
http://localhost:3000
```

#### Step 3: Register a new user
1. Click **"Sign Up"**
2. Fill in the form:
   - Email: Use a real email you can access
   - Username: testuser
   - Password: Test1234!
   - **Select Language**: Choose EN, RU, or HE
3. Click **"Create Account"**

#### Step 4: Check your email
Within 1-2 minutes, you should receive a verification email from:
```
BishulSheli <support@bishul.me>
```

#### Step 5: Verify the email content
Check that the email:
- ✅ Has "bishul.me" in the header (not MenuMind AI or BishulSheli)
- ✅ Uses purple color scheme (#9B59B6)
- ✅ Has correct language text
- ✅ Contains a working verification link
- ✅ Shows "© 2025 bishul.me"

#### Step 6: Click the verification link
The link should redirect you to:
```
http://localhost:3000/verify-email/{key}
```

And your email should be verified!

---

### Method 3: Check Django Logs

If emails aren't arriving, check the backend logs:

```bash
# In the terminal running Django/Daphne
# Look for lines like:
[Mailjet] 📧 Sending verification email to test@example.com using template 7459709 (language: en)
[Mailjet] ✅ Successfully sent email to test@example.com
```

Or errors like:
```
[Mailjet] ❌ Failed to send email: Invalid API credentials
[Mailjet] ❌ No template configured for verification/en
```

---

## 🔍 Troubleshooting

### Email Not Received

**1. Check Spam/Junk Folder**
   - Emails from new senders often go to spam first
   - Look for emails from `support@bishul.me`

**2. Verify Mailjet Configuration**
```bash
cd backend
python manage.py shell
```

Then in the Python shell:
```python
from apps.users.services.mailjet_email_service import get_mailjet_service

service = get_mailjet_service()
print(f"Service enabled: {service.enabled}")
print(f"API Key: {service.api_key[:10]}...")
print(f"Sender: {service.sender_name} <{service.sender_email}>")
print(f"Templates: {service.templates['verification']}")
```

Expected output:
```
Service enabled: True
API Key: 7fddcffd9...
Sender: BishulSheli <support@bishul.me>
Templates: {'en': 7459709, 'ru': 7459713, 'he': 7459704}
```

**3. Check Mailjet Secret Key**

The Mailjet secret key must be configured in `backend/.env`:
```env
MAILJET_SECRET_KEY=your_actual_secret_key_here
```

Without this, emails won't send!

**4. Test with Simple Command**
```bash
python manage.py test_verification_email your@email.com --language en
```

This will show you exactly what's failing.

---

## 📋 Verification Checklist

Use this checklist when testing:

### English Email (EN)
- [ ] Subject: "Verify your email address - bishul.me"
- [ ] Header shows: "bishul.me" and "My Cooking Platform"
- [ ] Purple gradient header (#9B59B6)
- [ ] Button says: "Verify Email Address"
- [ ] Footer: "© 2025 bishul.me. All rights reserved."
- [ ] Link works and redirects correctly

### Russian Email (RU)
- [ ] Subject: "Подтвердите ваш email - bishul.me"
- [ ] Header shows: "bishul.me" and "Бишул Шели | Мои Рецепты"
- [ ] Purple gradient header (#9B59B6)
- [ ] Button says: "Подтвердить Email"
- [ ] Footer: "© 2025 bishul.me. Все права защищены."
- [ ] Link works and redirects correctly

### Hebrew Email (HE)
- [ ] Subject: "אמת את כתובת האימייל שלך - bishul.me"
- [ ] Header shows: "bishul.me" and "בישול שלי | המטבח שלי"
- [ ] Purple gradient header (#9B59B6)
- [ ] Button says: "אמת כתובת אימייל"
- [ ] RTL (right-to-left) layout
- [ ] Footer: "© 2025 bishul.me. כל הזכויות שמורות."
- [ ] Link works and redirects correctly

---

## 🎯 Quick Test Script

Run all tests at once:

```bash
cd backend

# Test all three languages
echo "Testing English..."
python manage.py test_verification_email your@email.com --language en

echo "Testing Russian..."
python manage.py test_verification_email your@email.com --language ru

echo "Testing Hebrew..."
python manage.py test_verification_email your@email.com --language he

echo "✅ All tests sent! Check your inbox."
```

---

## 📞 Support

If emails still aren't working:

1. **Check Mailjet Dashboard**: https://app.mailjet.com/
   - Verify `support@bishul.me` is a verified sender
   - Check sending statistics
   - Look for bounced/blocked emails

2. **Verify DNS Records**: Ensure `bishul.me` has proper SPF/DKIM records

3. **Check Rate Limits**: Mailjet has sending limits on free/starter plans

---

## ✨ Success Criteria

Email verification is working correctly when:
- ✅ Test command shows "SUCCESS" for all languages
- ✅ Emails arrive within 1-2 minutes
- ✅ Email content matches branding (bishul.me, purple colors)
- ✅ Verification links work correctly
- ✅ New user registrations receive emails automatically

---

**Happy Testing! 🚀**

