# 📧 Brevo Integration - Quick Reference

## ⚡ Quick Start (5 Steps)

### 1. Install SDK
```bash
cd backend
pip install sib-api-v3-sdk==7.6.0
```

### 2. Get Brevo Credentials
- Sign up: https://www.brevo.com/
- Verify sender email: `menumindaiproject@gmail.com`
- Get API key: Dashboard → SMTP & API → API Keys
- Create 3 templates (EN/RU/HE)
- Copy template IDs

### 3. Update backend/.env
```env
BREVO_API_KEY=xkeysib-YOUR_KEY_HERE
BREVO_SENDER_EMAIL=menumindaiproject@gmail.com
BREVO_SENDER_NAME=MenuMind AI
BREVO_TEMPLATE_VERIFY_EN=1
BREVO_TEMPLATE_VERIFY_RU=2
BREVO_TEMPLATE_VERIFY_HE=3
```

### 4. Restart Backend
```bash
python manage.py runserver
```

### 5. Test
```bash
python test_brevo.py
```

---

## 📋 Files Modified

✅ Created:
- `backend/apps/users/services/brevo_email_service.py`
- `backend/test_brevo.py`
- `BREVO_SETUP_COMPLETE_GUIDE.md`

✅ Updated:
- `backend/apps/users/services/__init__.py`
- `backend/apps/users/adapters.py` (Brevo integration)
- `backend/apps/users/views.py` (comments)
- `backend/menumine_ai/settings.py` (Brevo config)
- `backend/requirements.txt` (added sib-api-v3-sdk)

---

## 🎯 Email Service Priority

1. **Brevo** (Primary - Production ready)
2. **EmailJS** (Secondary backup)
3. **Django SMTP** (Final fallback)

---

## 🔧 Template Variables

All templates use these variables:

```python
{
    'USER_NAME': 'John Doe',
    'ACTIVATE_URL': 'http://localhost:3000/verify-email/KEY',
    'SITE_NAME': 'MenuMind AI',
    'USER_EMAIL': 'user@example.com'
}
```

---

## ✅ Testing Checklist

- [ ] `pip install sib-api-v3-sdk`
- [ ] Brevo account created
- [ ] Sender email verified
- [ ] API key in backend/.env
- [ ] 3 templates created and active
- [ ] Template IDs in backend/.env
- [ ] Backend restarted
- [ ] `python test_brevo.py` passes
- [ ] Registration email works

---

## 🐛 Quick Debug

**Service not enabled?**
```bash
python test_brevo.py
# Check which variable is missing
```

**Email not received?**
1. Check Brevo Dashboard → Logs
2. Check spam folder
3. Verify sender email has green checkmark

**Wrong template?**
```python
# Check template IDs match Brevo
BREVO_TEMPLATE_VERIFY_EN=1  # English
BREVO_TEMPLATE_VERIFY_RU=2  # Russian
BREVO_TEMPLATE_VERIFY_HE=3  # Hebrew
```

---

## 📊 Brevo Dashboard Links

- **Dashboard:** https://app.brevo.com/
- **Senders:** https://app.brevo.com/senders
- **Templates:** https://app.brevo.com/templates
- **API Keys:** https://app.brevo.com/settings/keys/api
- **Logs:** https://app.brevo.com/logs/email

---

## 🚀 Free Tier Limits

- **300 emails/day** (free forever)
- **Unlimited contacts**
- **Real-time analytics**
- **API access**

Upgrade: https://www.brevo.com/pricing/

---

## 📞 Support

**Full Guide:** See `BREVO_SETUP_COMPLETE_GUIDE.md`

**Brevo Docs:** https://developers.brevo.com/

**Python SDK:** https://github.com/sendinblue/APIv3-python-library

