# 📧 Mailjet Email Templates - Complete Setup Guide

## 🎯 Current Status

✅ Mailjet integration code is ready
✅ Mailjet library installed
✅ API Key configured: `5c73c3615ed646d7e974407de9a57247`
⏳ SECRET KEY needed (click eye icon in dashboard to reveal)
⏳ Email templates need to be created

---

## 🔑 Step 1: Get Your Secret Key (CRITICAL)

1. **Go to:** https://app.mailjet.com/account/api_keys
2. **Find:** Primary API Key row (`5c73c3615ed646d7e974407de9a57247`)
3. **Click:** The **eye icon (👁️)** in the "Secret Key" column
4. **Copy:** The full secret key (will be long string of letters/numbers)

5. **Update `.env` file:**
   ```env
   MAILJET_SECRET_KEY=paste_your_secret_key_here
   ```

---

## 📝 Step 2: Verify Sender Email

Before sending emails, you must verify your sender email:

1. **Go to:** https://app.mailjet.com/account/sender
2. **Add sender:** `menumindaiproject@gmail.com`
3. **Verify:** Check Gmail inbox and click verification link
4. **Status should show:** ✅ Verified

---

## 🎨 Step 3: Create Email Templates

### Navigate to Templates

1. Go to: https://app.mailjet.com/
2. Click **"Transactional"** (left sidebar)
3. Click **"Passport"** or **"Templates"**
4. Click **"Create a new template"**

---

### Template 1: English Verification

**Template Name:** `Email Verification - English`

**Template Variables to Add:**
- `user_name`
- `activate_url`
- `site_name`

**Subject Line:**
```
Verify your email address - {{var:site_name:""}}
```

**HTML Content:**
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
            <h1>{{var:site_name:"MenuMind AI"}}</h1>
        </div>
        <div class="content">
            <h2>Hello {{var:user_name:"there"}}! 👋</h2>
            <p>Welcome to MenuMind AI! We're excited to have you on board.</p>
            <p>To start using your account, please verify your email address by clicking the button below:</p>
            
            <div class="button-container">
                <a href="{{var:activate_url:"#"}}" class="button">Verify Email Address</a>
            </div>
            
            <div class="footer-note">
                <p><strong>Why verify?</strong></p>
                <p>Email verification helps us protect your account and ensure you receive important updates.</p>
                
                <p style="margin-top: 20px;"><strong>Didn't sign up?</strong></p>
                <p>If you didn't create this account, you can safely ignore this email.</p>
                
                <p style="margin-top: 30px; font-size: 12px;">
                    <strong>Button not working?</strong> Copy and paste this link:<br>
                    <a href="{{var:activate_url:"#"}}" class="link-fallback">{{var:activate_url:""}}</a>
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

**Save Template and Copy the Template ID**

---

### Template 2: Russian Verification

**Template Name:** `Email Verification - Russian`

**Subject Line:**
```
Подтвердите ваш email адрес - {{var:site_name:""}}
```

**HTML Content:** (Same structure, Russian text)
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- Same styles as English -->
    <style>
        /* Copy all styles from English template */
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
            <h1>{{var:site_name:"MenuMind AI"}}</h1>
        </div>
        <div class="content">
            <h2>Здравствуйте, {{var:user_name:"там"}}! 👋</h2>
            <p>Добро пожаловать в MenuMind AI! Мы рады приветствовать вас.</p>
            <p>Чтобы начать использовать ваш аккаунт, пожалуйста, подтвердите ваш email адрес:</p>
            
            <div class="button-container">
                <a href="{{var:activate_url:"#"}}" class="button">Подтвердить Email</a>
            </div>
            
            <div class="footer-note">
                <p><strong>Зачем подтверждать?</strong></p>
                <p>Подтверждение email помогает защитить ваш аккаунт и гарантирует получение важных обновлений.</p>
                
                <p style="margin-top: 20px;"><strong>Не регистрировались?</strong></p>
                <p>Если вы не создавали этот аккаунт, можете проигнорировать это письмо.</p>
                
                <p style="margin-top: 30px; font-size: 12px;">
                    <strong>Кнопка не работает?</strong> Скопируйте эту ссылку:<br>
                    <a href="{{var:activate_url:"#"}}" class="link-fallback">{{var:activate_url:""}}</a>
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

**Save and Copy Template ID**

---

### Template 3: Hebrew Verification

**Template Name:** `Email Verification - Hebrew`

**Subject Line:**
```
אמת את כתובת האימייל שלך - {{var:site_name:""}}
```

**HTML Content:** (RTL support)
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
            <h1>{{var:site_name:"MenuMind AI"}}</h1>
        </div>
        <div class="content">
            <h2>שלום {{var:user_name:"שם"}}! 👋</h2>
            <p>ברוכים הבאים ל-MenuMind AI! אנחנו שמחים שהצטרפת אלינו.</p>
            <p>כדי להתחיל להשתמש בחשבון שלך, אנא אמת את כתובת האימייל שלך:</p>
            
            <div class="button-container">
                <a href="{{var:activate_url:"#"}}" class="button">אמת כתובת אימייל</a>
            </div>
            
            <div class="footer-note">
                <p><strong>למה לאמת?</strong></p>
                <p>אימות אימייל עוזר להגן על החשבון שלך ולוודא שאתה מקבל עדכונים חשובים.</p>
                
                <p style="margin-top: 20px;"><strong>לא נרשמת?</strong></p>
                <p>אם לא יצרת חשבון זה, אתה יכול להתעלם מהודעה זו.</p>
                
                <p style="margin-top: 30px; font-size: 12px;">
                    <strong>הכפתור לא עובד?</strong> העתק קישור זה:<br>
                    <a href="{{var:activate_url:"#"}}" class="link-fallback">{{var:activate_url:""}}</a>
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

**Save and Copy Template ID**

---

## ✅ Step 4: Update `.env` File

After creating all 3 templates, update `backend/.env`:

```env
# Mailjet Template IDs
MAILJET_TEMPLATE_VERIFY_EN=your_english_template_id
MAILJET_TEMPLATE_VERIFY_RU=your_russian_template_id
MAILJET_TEMPLATE_VERIFY_HE=your_hebrew_template_id
```

**Note:** Template IDs in Mailjet are numbers (like `123456` or `7891234`)

---

## 🧪 Step 5: Test

Once everything is configured:

```bash
cd backend
python test_mailjet.py
```

---

## 📊 Configuration Checklist

- [ ] Get Secret Key from Mailjet dashboard
- [ ] Update `MAILJET_SECRET_KEY` in `.env`
- [ ] Verify sender email (`menumindaiproject@gmail.com`)
- [ ] Create English template
- [ ] Create Russian template
- [ ] Create Hebrew template
- [ ] Copy all 3 template IDs
- [ ] Add template IDs to `.env`
- [ ] Test with `python test_mailjet.py`

---

## 🔗 Quick Links

- **API Keys:** https://app.mailjet.com/account/api_keys
- **Sender Verification:** https://app.mailjet.com/account/sender
- **Templates:** https://app.mailjet.com/templates/transactional
- **Documentation:** https://dev.mailjet.com/

---

## 📝 Template Variable Reference

All Mailjet templates use these variables:

```
{{var:user_name:"Default Name"}}
{{var:activate_url:"#"}}
{{var:site_name:"MenuMind AI"}}
```

The `:""` or `:"text"` part is the default value if variable is not provided.

---

**Ready to test!** After completing all steps, your email verification will work via Mailjet! 📧✨

