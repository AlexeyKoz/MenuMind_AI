# Legal Documents Setup Guide

## ✅ What's Been Done

### 1. **Updated Management Command**
   - Fixed `backend/legal/management/commands/load_bishulsheli_docs.py`
   - Now matches your new file structure in `legal_documents/EN`, `legal_documents/RU`, `legal_documents/HE`
   - Loads all 15 documents (5 types × 3 languages)

### 2. **Enhanced Django Admin** with File Upload Feature
   - **Added `backend/legal/forms.py`**:
     - `LegalDocumentUploadForm`: Bulk upload form
     - `LegalDocumentAdminForm`: Single document form with optional file upload
   - **Updated `backend/legal/admin.py`**:
     - Added `language_code` to list display
     - Added file upload field to edit form
     - Created custom upload view at `/admin/legal/legaldocument/upload/`
   - **Created Upload Template**: `backend/legal/templates/admin/legal/upload_document.html`

### 3. **Google Button Centering Fix**
   - Fixed `frontend/src/components/GoogleSignInButton.tsx`
   - Button now stays centered regardless of size

---

## 🚀 Next Steps - Load Documents to Database

### Step 1: Start Your Services

You need PostgreSQL running to load the documents. Run:

```bash
start_fullstack_complete.bat
```

OR manually start PostgreSQL:

```bash
# Start PostgreSQL service
net start postgresql-x64-13

# OR if using a different version
pg_ctl -D "C:\Program Files\PostgreSQL\13\data" start
```

### Step 2: Load Documents

Once PostgreSQL is running, execute:

```bash
cd C:\Users\al7ko\Desktop\after-deploy\MenuMind_AI
python backend\manage.py load_bishulsheli_docs --path "legal_documents" --force
```

**Expected Output:**
```
======================================================================
Loading BishulSheli Legal Documents (EN, RU, HE)
======================================================================
Created: Terms of Service (EN) v2.0 - 5234 chars, 891 words
Created: Privacy Policy (EN) v2.0 - 6782 chars, 1124 words
Created: Cookie Policy (EN) v2.0 - 4567 chars, 743 words
...
======================================================================
Loaded: 15 | Skipped: 0 | Errors: 0
======================================================================

Total legal documents in database: 15
  - English: 5
  - Russian: 5
  - Hebrew: 5

✅ All BishulSheli documents loaded successfully!
```

---

## 📝 File Upload Feature - How to Use

### Option 1: Upload from Admin Panel (Future Use)

1. Navigate to: `http://localhost:8000/admin/legal/legaldocument/`
2. Click **"Upload Document"** button (top right)
3. Fill in the form:
   - **Document Type**: Select (Terms, Privacy, Cookies, etc.)
   - **Language**: Select (EN, RU, HE)
   - **Version**: e.g., `2.0`, `2.1`
   - **Effective Date**: Select date
   - **Markdown File**: Upload `.md` file
   - **Set as Active**: Check to make it the active version
4. Click **"Upload Document"**

### Option 2: Edit Existing Document

1. Go to: `http://localhost:8000/admin/legal/legaldocument/`
2. Click on any document to edit
3. **Two ways to update content:**
   - **Upload File**: Use "Upload Markdown File (Optional)" field
   - **Edit Directly**: Scroll down and edit the "Content" textarea
4. Save changes

---

## 📂 Current File Structure

```
legal_documents/
├── EN/
│   ├── Terms-of-service-v2_en.md
│   ├── Privacy-policy_v2_en.md
│   ├── Cookie-policy_v2_en.md
│   ├── Copyright_en.md
│   └── rcip-license_en.md
├── RU/
│   ├── Terms-of-service-v2_ru.md
│   ├── Privacy-policy_v2_ru.md
│   ├── Cookie-policy_v2_ru.md
│   ├── Copyright_ru.md
│   └── rcip-license-ru.md
└── HE/
    ├── Terms-of-service-v2_he.md
    ├── Privacy-policy_v2_he.md
    ├── Cookie-policy_v2_he.md
    ├── Copyright_he.md
    └── rcip-license-he.md
```

---

## 🔗 Frontend Integration

The frontend automatically fetches documents based on the user's language:

```typescript
// Example API call from frontend
const response = await fetch(`${apiUrl}/api/legal/terms/?lang=en`);
```

**Supported URLs:**
- `/api/legal/terms/` - Terms of Service
- `/api/legal/privacy/` - Privacy Policy
- `/api/legal/cookies/` - Cookie Policy
- `/api/legal/copyright/` - Copyright Notice
- `/api/legal/rcip/` - RCIP License

Each endpoint accepts a `lang` parameter (`en`, `ru`, or `he`).

---

## ✨ Key Features

✅ **Multi-language Support**: EN, RU, HE  
✅ **Version Control**: Track document versions  
✅ **Active Version Management**: Only one active version per type/language  
✅ **File Upload**: Upload .md files directly from admin  
✅ **Audit Trail**: Tracks who updated documents and when  
✅ **Word Count**: Automatic word count display  
✅ **Language-specific Rendering**: Frontend shows correct language automatically

---

## 🛠️ Troubleshooting

### Problem: "File not found" errors
**Solution**: Make sure you're running the command from the project root and the path is correct.

### Problem: Database connection error
**Solution**: Start PostgreSQL before running the load command.

### Problem: Documents not showing on frontend
**Solution**: 
1. Check database has documents: `SELECT * FROM legal_documents;`
2. Verify `is_active = true`
3. Check frontend API URL in `.env`

### Problem: Wrong language showing
**Solution**: 
1. Check `i18n.language` in browser console
2. Verify API is receiving correct `lang` parameter
3. Ensure document exists for that language

---

## 📊 Admin Panel Features

**List View Shows:**
- Document Type (Terms, Privacy, etc.)
- Language Code (EN, RU, HE)
- Version
- Effective Date
- Active Status
- Word Count
- Last Updated
- Updated By (username)

**Filters:**
- Document Type
- Language Code
- Active Status
- Effective Date

**Search:**
- Document Type
- Version
- Content (full-text search)

---

## 🎯 Summary

All code changes are complete! You now have:

1. ✅ **Updated load command** matching your new file structure
2. ✅ **Enhanced admin panel** with file upload capability
3. ✅ **Professional upload interface** for future document updates
4. ✅ **Centered Google button** that stays aligned

**Next Action:** Start PostgreSQL and run the load command to populate the database!

