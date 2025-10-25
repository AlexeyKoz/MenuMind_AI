# EmailJS Quick Reference

## 🔐 Environment Variables (.env)

```env
# EmailJS Service
EMAILJS_SERVICE_ID=service_xxxxxxx
EMAILJS_PUBLIC_KEY=your_public_key
EMAILJS_PRIVATE_KEY=your_private_key

# Templates (one per language)
EMAILJS_TEMPLATE_VERIFY_EN=template_en_xxx
EMAILJS_TEMPLATE_VERIFY_RU=template_ru_xxx
EMAILJS_TEMPLATE_VERIFY_HE=template_he_xxx
```

## 🚀 Quick Setup (5 minutes)

1. **Create EmailJS Account**: https://www.emailjs.com/
2. **Add Email Service**: Dashboard → Email Services → Add Service
3. **Get API Keys**: Dashboard → Account → API Keys
4. **Create Templates**: Dashboard → Email Templates → Create New (x3 for EN/RU/HE)
5. **Add to .env**: Copy IDs from dashboard
6. **Restart Backend**: `python manage.py runserver`

## 📝 Template Variables

Use these in your EmailJS templates:

```
{{to_email}}       - Recipient email
{{user_name}}      - User's name
{{activate_url}}   - Verification link
{{site_name}}      - "MenuMind AI"
{{greeting}}       - "Hi {{user_name}}"
{{message}}        - Main message text
{{button_text}}    - Button label
{{footer_text}}    - Footer disclaimer
```

## 🧪 Test Commands

### Register New User
```bash
curl -X POST http://localhost:8000/api/users/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"Pass123!"}'
```

### Resend Verification
```bash
curl -X POST http://localhost:8000/api/users/auth/resend-verification/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| "Service not configured" | Check all 6 env vars present |
| 401 Unauthorized | Verify API keys in dashboard |
| 404 Not Found | Check Service ID and Template IDs |
| Email not received | Check spam folder, verify service connection |

## 📊 Backend Logs

```
✅ Success:
[EmailJS] ✅ Successfully sent verification email to user@example.com

⚠️ Fallback:
[EmailJS] ⚠️ EmailJS not configured, using Django SMTP fallback

❌ Error:
[EmailJS] ❌ Failed to send after 3 attempts
```

## 🎯 Files Modified

- `backend/apps/users/services/email_service.py` - NEW
- `backend/apps/users/services/__init__.py` - NEW
- `backend/apps/users/adapters.py` - UPDATED
- `backend/apps/users/views.py` - UPDATED (comment only)
- `backend/.env` - ADD 6 variables

## 📞 Support

- **EmailJS Docs**: https://www.emailjs.com/docs/
- **Dashboard**: https://dashboard.emailjs.com/
- **Full Guide**: See `EMAILJS_INTEGRATION_COMPLETE.md`

