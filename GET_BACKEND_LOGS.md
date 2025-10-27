# 🔍 DEBUGGING GUIDE - Get Backend Console Output

## 🎯 What I Need From You

I need to see the **FULL backend console output** to diagnose the issue.

---

## 📋 **Step-by-Step Instructions:**

### **Step 1: Restart Backend**

1. In your backend terminal, press `CTRL+C` to stop the server
2. Restart it:
   ```bash
   python manage.py runserver
   ```
3. Keep this terminal **visible and in focus**

---

### **Step 2: Test Registration**

**Option A: Via Frontend** (Recommended)
1. Open browser: http://localhost:3000/register
2. Register a new user:
   - Username: `debuguser001`
   - Email: `menumindaiproject@gmail.com`
   - Password: `TestPass123!`
3. Click "Register"

**Option B: Via Test Script**
```bash
# In a NEW terminal
cd backend
python test_registration.py
```

---

### **Step 3: Copy Backend Console Output**

After registration, you should see in backend console:
```
📧 Attempting to send verification email to menumindaiproject@gmail.com
✅ Verification email sent successfully to menumindaiproject@gmail.com

OR

❌ Failed to send verification email: [error details]
[Full traceback here]
```

**→ SELECT ALL THIS TEXT and COPY IT**

---

### **Step 4: Test Resend Button**

1. After registration, click **"Resend verification email"** button on frontend
2. Backend console should show:
```
============================================================
🔄 RESEND VERIFICATION EMAIL REQUEST
============================================================
User: debuguser001
User email: menumindaiproject@gmail.com
User authenticated: True
============================================================
```

**→ SELECT ALL THIS TEXT and COPY IT**

---

### **Step 5: Send Me EVERYTHING**

Paste here:
1. ✅ Output from registration attempt
2. ✅ Output from resend button click
3. ✅ Any error tracebacks
4. ✅ All Mailjet-related logs

---

## 📝 Example of What I'm Looking For:

```
📧 Attempting to send verification email to test@example.com
============================================================
📧 VERIFICATION EMAIL
============================================================
To: test@example.com
Language: en
Verification URL: http://localhost:3000/verify-email/abc123
============================================================

[Mailjet] 📧 Sending verification email to test@example.com using template 7431399 (language: en)
[Mailjet] ✅ Successfully sent email to test@example.com
[Mailjet] ✅ Successfully sent verification email to test@example.com
[Mailjet] Message: Email sent successfully via Mailjet
✅ Verification email sent successfully to test@example.com
```

---

## 🚨 **IMPORTANT**

- Don't edit or summarize the output
- Copy the ENTIRE output including all `===` lines
- Include any errors or warnings
- Include both registration AND resend attempts

---

**Once I see the backend logs, I can immediately tell you what's wrong!** 🔍

