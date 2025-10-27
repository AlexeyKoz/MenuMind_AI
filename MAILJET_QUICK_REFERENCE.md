# 📧 Mailjet Integration - Quick Reference

## 🎯 What You Need

### 1. API Credentials
From: https://app.mailjet.com/account/api_keys
- **API Key:** `5c73c3615ed646d7e974407de9a57247` ✅
- **Secret Key:** Click eye icon (👁️) to reveal ⏳

### 2. Verify Sender
From: https://app.mailjet.com/account/sender
- **Email:** `menumindaiproject@gmail.com`
- Check Gmail inbox → Click verification link

### 3. Create Templates
From: https://app.mailjet.com/templates/transactional

Create 3 templates:
1. **English Verification** → Copy Template ID
2. **Russian Verification** → Copy Template ID
3. **Hebrew Verification** → Copy Template ID

---

## 🔧 Configuration

Add to `backend/.env`:

```env
# Mailjet Configuration
MAILJET_API_KEY=5c73c3615ed646d7e974407de9a57247
MAILJET_SECRET_KEY=YOUR_SECRET_KEY_HERE
MAILJET_SENDER_EMAIL=menumindaiproject@gmail.com
MAILJET_SENDER_NAME=MenuMind AI

# Template IDs (after creating templates)
MAILJET_TEMPLATE_VERIFY_EN=123456
MAILJET_TEMPLATE_VERIFY_RU=789012
MAILJET_TEMPLATE_VERIFY_HE=345678
```

---

## 🧪 Testing

```bash
cd backend
python test_mailjet.py
```

---

## 📝 Template Variables

All templates must include:
- `{{var:user_name:""}}`
- `{{var:activate_url:""}}`
- `{{var:site_name:"MenuMind AI"}}`

---

## 🔗 Dashboard Links

- **API Keys:** https://app.mailjet.com/account/api_keys
- **Sender Verification:** https://app.mailjet.com/account/sender
- **Templates:** https://app.mailjet.com/templates/transactional
- **Statistics:** https://app.mailjet.com/stats
- **Documentation:** https://dev.mailjet.com/

---

## ✅ Checklist

1. [ ] Reveal and copy Secret Key
2. [ ] Update `MAILJET_SECRET_KEY` in `.env`
3. [ ] Verify sender email
4. [ ] Create 3 templates (EN/RU/HE)
5. [ ] Add template IDs to `.env`
6. [ ] Run `python test_mailjet.py`
7. [ ] Test registration on frontend

---

## 🎨 Email Priority Order

The system tries services in this order:

1. **Mailjet** (PRIMARY) ✅
2. **Brevo** (SECONDARY)
3. **EmailJS** (TERTIARY)
4. **Django SMTP** (FALLBACK)

---

## 📧 Free Tier Limits

- **Mailjet Free:** 200 emails/day, 6,000 emails/month
- **Brevo Free:** 300 emails/day
- **EmailJS Free:** 200 emails/month

---

**Your current setup uses Mailjet as primary!** 🚀

