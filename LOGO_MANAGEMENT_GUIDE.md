# Logo Management System - Complete Guide

## 🎨 Overview

The Logo Management System allows you to upload and manage different logos for different languages and positions through the Django admin panel. This includes:

- **Navbar Logo (Desktop)** - Displayed in the navigation bar on desktop
- **Navbar Logo (Mobile)** - Displayed in the navigation bar on mobile devices  
- **Login Page Logo** - Displayed on the login page
- **Favicon** - Small icon in the browser tab
- **App Icon (PWA)** - Icon for Progressive Web App

Each logo type can have different versions for English, Russian, and Hebrew, or you can use a universal logo for all languages.

---

## 📁 Files Created

### Backend Files
```
backend/branding/
├── __init__.py
├── apps.py
├── models.py          # SiteLogo and SiteSettings models
├── admin.py           # Admin interface configuration
├── serializers.py     # REST API serializers
├── views.py           # API ViewSets
├── urls.py            # URL routing
├── migrations/
│   └── __init__.py
└── templates/
    └── admin/
        └── branding/
            └── quick_setup.html  # Bulk upload interface
```

### Configuration Changes
```
backend/menumine_ai/settings.py  # Added 'branding' to INSTALLED_APPS
backend/menumine_ai/urls.py      # Added branding API endpoints
```

---

## 🚀 Setup Instructions

### Step 1: Rebuild Docker Containers

```bash
# Rebuild backend container with new branding app
docker-compose -f docker-compose.prod.yml up -d --build backend

# Or rebuild all containers
docker-compose -f docker-compose.prod.yml up -d --build
```

### Step 2: Run Migrations

```bash
docker exec menumine_backend_prod python manage.py makemigrations branding
docker exec menumine_backend_prod python manage.py migrate branding
```

### Step 3: Access Admin Panel

1. Navigate to: `http://localhost:8000/admin/`
2. Login with your admin credentials
3. You'll see two new sections:
   - **Site Logos** - Manage all logos
   - **Site Settings** - Manage site-wide settings

---

## 📸 Uploading Logos

### Method 1: Quick Setup (Recommended for First Time)

1. Go to **Site Logos** in admin
2. Click **"Quick Setup"** button at the top
3. Upload all logos at once:
   - Choose files for each logo type and language
   - Leave fields empty to skip
   - SVG format recommended
4. Click **"Upload All Logos"**

**Recommended Sizes:**
- Navbar Desktop: ~200x50 px (horizontal)
- Navbar Mobile: ~40x40 px (square)
- Login Page: ~300x100 px
- Favicon: 32x32 px (square)
- App Icon: 512x512 px (square)

### Method 2: Individual Upload

1. Go to **Site Logos** → **Add Site Logo**
2. Fill in:
   - **Logo Type**: Select position (navbar, login, etc.)
   - **Language**: Select language or "All Languages"
   - **Upload Image**: Choose file
   - **Alt Text**: Accessibility text
   - **Is Active**: Check to activate
3. Click **Save**

---

## 🔌 API Endpoints

### Get All Logos for a Language

```bash
GET /api/branding/logos/for_language/?lang=en
```

**Response:**
```json
{
  "navbar_desktop": {
    "id": "uuid",
    "logo_type": "navbar_desktop",
    "language_code": "en",
    "file_url": "http://localhost:8000/media/branding/logos/navbar_desktop_en_abc123.svg",
    "alt_text": "BishulSheli",
    "is_active": true,
    "width": 200,
    "height": 50,
    "dimensions": "200x50"
  },
  "navbar_mobile": { ... },
  "login_page": { ... },
  "favicon": { ... },
  "app_icon": { ... }
}
```

### Filter Logos

```bash
# By language
GET /api/branding/logos/?lang=ru

# By logo type
GET /api/branding/logos/?type=navbar_desktop

# Combined
GET /api/branding/logos/?lang=he&type=login_page
```

### Get PWA Manifest Icons

```bash
GET /api/branding/logos/manifest/?lang=en
```

---

## 💻 Frontend Integration

### Create Logo Service

```typescript
// frontend/src/services/logoService.ts
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface LogoData {
  id: string;
  logo_type: string;
  language_code: string;
  file_url: string;
  alt_text: string;
  is_active: boolean;
  width: number | null;
  height: number | null;
  dimensions: string;
}

export interface LogosResponse {
  navbar_desktop?: LogoData;
  navbar_mobile?: LogoData;
  login_page?: LogoData;
  favicon?: LogoData;
  app_icon?: LogoData;
}

class LogoService {
  private cache: Map<string, LogosResponse> = new Map();
  private cacheExpiry: Map<string, number> = new Map();
  private readonly CACHE_DURATION = 3600000; // 1 hour in ms

  /**
   * Get all logos for a specific language
   */
  async getLogos(lang: string = 'en'): Promise<LogosResponse> {
    const cacheKey = `logos_${lang}`;
    
    // Check cache
    if (this.cache.has(cacheKey)) {
      const expiry = this.cacheExpiry.get(cacheKey) || 0;
      if (Date.now() < expiry) {
        return this.cache.get(cacheKey)!;
      }
    }

    try {
      const response = await axios.get(`${API_URL}/api/branding/logos/for_language/`, {
        params: { lang }
      });

      // Cache the response
      this.cache.set(cacheKey, response.data);
      this.cacheExpiry.set(cacheKey, Date.now() + this.CACHE_DURATION);

      return response.data;
    } catch (error) {
      console.error('Error fetching logos:', error);
      // Return empty object as fallback
      return {};
    }
  }

  /**
   * Get a specific logo by type and language
   */
  async getLogo(logoType: string, lang: string = 'en'): Promise<LogoData | null> {
    const logos = await this.getLogos(lang);
    return logos[logoType as keyof LogosResponse] || null;
  }

  /**
   * Clear cache (useful after admin updates logos)
   */
  clearCache(): void {
    this.cache.clear();
    this.cacheExpiry.clear();
  }
}

export default new LogoService();
```

### Update Navigation Component

```typescript
// frontend/src/components/Navigation.tsx
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import logoService, { LogoData } from '../services/logoService';

const Navigation: React.FC = () => {
  const { i18n } = useTranslation();
  const [desktopLogo, setDesktopLogo] = useState<LogoData | null>(null);
  const [mobileLogo, setMobileLogo] = useState<LogoData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadLogos();
  }, [i18n.language]);

  const loadLogos = async () => {
    setIsLoading(true);
    try {
      const logos = await logoService.getLogos(i18n.language);
      setDesktopLogo(logos.navbar_desktop || null);
      setMobileLogo(logos.navbar_mobile || null);
    } catch (error) {
      console.error('Error loading logos:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Fallback to static logos if API fails
  const getLogoPath = (isMobile: boolean) => {
    if (isMobile && mobileLogo) {
      return mobileLogo.file_url;
    } else if (!isMobile && desktopLogo) {
      return desktopLogo.file_url;
    }
    
    // Fallback to static logos
    const lang = i18n.language === 'he' ? 'he' : 'en';
    return isMobile
      ? `/logo/bishulsheli-logo-mobile-${lang}.svg`
      : `/logo/bishulsheli-logo-horizontal-${lang}.svg`;
  };

  const getAltText = (isMobile: boolean) => {
    if (isMobile && mobileLogo) {
      return mobileLogo.alt_text;
    } else if (!isMobile && desktopLogo) {
      return desktopLogo.alt_text;
    }
    return 'BishulSheli';
  };

  return (
    <nav>
      {/* Desktop Logo */}
      <div className="hidden md:flex">
        <img 
          src={getLogoPath(false)} 
          alt={getAltText(false)}
          className="h-12"
        />
      </div>

      {/* Mobile Logo */}
      <div className="md:hidden">
        <img 
          src={getLogoPath(true)} 
          alt={getAltText(true)}
          className="h-10 w-10"
        />
      </div>
    </nav>
  );
};

export default Navigation;
```

### Update Login Page

```typescript
// frontend/src/pages/Login.tsx
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import logoService, { LogoData } from '../services/logoService';

const Login: React.FC = () => {
  const { i18n } = useTranslation();
  const [logo, setLogo] = useState<LogoData | null>(null);

  useEffect(() => {
    loadLogo();
  }, [i18n.language]);

  const loadLogo = async () => {
    try {
      const logos = await logoService.getLogos(i18n.language);
      setLogo(logos.login_page || null);
    } catch (error) {
      console.error('Error loading login logo:', error);
    }
  };

  const getLogoPath = () => {
    if (logo) {
      return logo.file_url;
    }
    // Fallback
    const lang = i18n.language === 'he' ? 'he' : 'en';
    return `/logo/bishulsheli-logo-compact-${lang}.svg`;
  };

  return (
    <div className="login-page">
      <img 
        src={getLogoPath()} 
        alt={logo?.alt_text || 'BishulSheli'}
        className="mb-8 h-24"
      />
      {/* Login form */}
    </div>
  );
};

export default Login;
```

### Update Favicon Dynamically

```typescript
// frontend/src/utils/updateFavicon.ts
import logoService from '../services/logoService';

export const updateFavicon = async (lang: string) => {
  try {
    const logos = await logoService.getLogos(lang);
    const favicon = logos.favicon;

    if (favicon) {
      // Update favicon link
      const link: HTMLLinkElement = document.querySelector("link[rel*='icon']") || 
                                      document.createElement('link');
      link.type = 'image/x-icon';
      link.rel = 'shortcut icon';
      link.href = favicon.file_url;
      document.getElementsByTagName('head')[0].appendChild(link);
    }
  } catch (error) {
    console.error('Error updating favicon:', error);
  }
};

// Call this in your App.tsx or main component
// updateFavicon(i18n.language);
```

---

## 🎯 Language Fallback Logic

The system uses smart fallback logic:

1. **Try language-specific logo** (e.g., `navbar_desktop` + `en`)
2. **Fallback to "All Languages"** logo (e.g., `navbar_desktop` + `all`)
3. **Fallback to static files** (if API fails or no logo uploaded)

This ensures your site always has logos even if some aren't uploaded yet.

---

## 🔄 Cache Management

### Backend Cache
- Logos are cached for 1 hour
- Cache key: `site_logos_{lang}`
- Automatically invalidated when logos are updated

### Frontend Cache
- LogoService caches responses for 1 hour
- Clear cache: `logoService.clearCache()`

---

## 🧪 Testing

### Test API Endpoints

```bash
# Test English logos
curl http://localhost:8000/api/branding/logos/for_language/?lang=en

# Test Russian logos
curl http://localhost:8000/api/branding/logos/for_language/?lang=ru

# Test Hebrew logos
curl http://localhost:8000/api/branding/logos/for_language/?lang=he

# Test PWA manifest
curl http://localhost:8000/api/branding/logos/manifest/?lang=en
```

### Test Admin Interface

1. Upload a logo through Quick Setup
2. Check it appears in Site Logos list
3. Verify the preview shows correctly
4. Test API endpoint returns the new logo
5. Check frontend displays the new logo

---

## 📝 Admin Features

### List View Shows:
- ✅ Logo preview (thumbnail)
- ✅ Logo type (navbar, login, etc.)
- ✅ Language code
- ✅ Active status
- ✅ Dimensions (width x height)
- ✅ File size
- ✅ Last updated
- ✅ Uploaded by

### Detail View Shows:
- ✅ Large logo preview
- ✅ File upload field
- ✅ All metadata
- ✅ Auto-detected dimensions
- ✅ File URL

### Filters Available:
- Logo Type
- Language
- Active Status
- Upload Date

---

## 🎨 Best Practices

1. **Use SVG format** when possible (scalable, smaller file size)
2. **Optimize images** before uploading
3. **Use consistent branding** across languages
4. **Test on mobile** after uploading mobile logos
5. **Keep file sizes small** (< 500 KB recommended)
6. **Use descriptive alt text** for accessibility
7. **Upload all logo types** for best experience

---

## 🔧 Troubleshooting

### Logo Not Showing in Frontend

**Check:**
1. Logo is marked as "Active" in admin
2. API endpoint returns the logo
3. Frontend cache cleared (`logoService.clearCache()`)
4. Browser cache cleared (Ctrl+Shift+R)
5. File path is correct and accessible

### Upload Fails

**Check:**
1. File format is supported (SVG, PNG, JPG, WEBP, ICO)
2. File size < 5MB
3. File is UTF-8 encoded (for SVG)
4. Media directory has write permissions

### Wrong Logo Showing

**Check:**
1. Language parameter matches (`i18n.language`)
2. No other active logo for same type + language
3. Fallback logic working correctly
4. Cache cleared on both backend and frontend

---

## 🚀 Next Steps

After setting up the logo system:

1. ✅ Upload all logos through Quick Setup
2. ✅ Test API endpoints
3. ✅ Update frontend components to use logoService
4. ✅ Test language switching
5. ✅ Test on mobile devices
6. ✅ Update PWA manifest
7. ✅ Deploy to production

---

## 📚 Additional Resources

- **Django ImageField**: https://docs.djangoproject.com/en/4.2/ref/models/fields/#imagefield
- **DRF ViewSets**: https://www.django-rest-framework.org/api-guide/viewsets/
- **React i18n**: https://react.i18next.com/
- **PWA Manifest**: https://web.dev/add-manifest/

---

**Your logo management system is now ready!** 🎉

