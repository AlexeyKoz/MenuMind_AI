"""
Backend tests for Logo Management System.

Tests:
- Logo model creation and validation
- Logo API endpoints
- Language fallback logic
- Admin functionality
- Image upload and processing
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from branding.models import SiteLogo, SiteSettings
import json

User = get_user_model()


class SiteLogoModelTests(TestCase):
    """Test SiteLogo model"""

    def setUp(self):
        # Create a simple SVG file for testing
        self.svg_content = b'''<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50">
            <text x="10" y="30">Test Logo</text>
        </svg>'''
        self.test_file = SimpleUploadedFile(
            "test_logo.svg",
            self.svg_content,
            content_type="image/svg+xml"
        )

    def test_create_logo(self):
        """Test creating a logo"""
        logo = SiteLogo.objects.create(
            logo_type='navbar_desktop',
            language_code='en',
            image_file=self.test_file,
            alt_text='Test Logo',
            is_active=True,
            uploaded_by='test_user'
        )
        
        self.assertEqual(logo.logo_type, 'navbar_desktop')
        self.assertEqual(logo.language_code, 'en')
        self.assertTrue(logo.is_active)
        self.assertIsNotNone(logo.image_file)

    def test_logo_string_representation(self):
        """Test logo __str__ method"""
        logo = SiteLogo.objects.create(
            logo_type='login_page',
            language_code='he',
            image_file=self.test_file,
            alt_text='Hebrew Logo',
            is_active=True
        )
        
        self.assertIn('Login Page Logo', str(logo))
        self.assertIn('Hebrew', str(logo))
        self.assertIn('✓', str(logo))

    def test_only_one_active_logo_per_type_language(self):
        """Test that only one logo can be active per type and language"""
        # Create first active logo
        logo1 = SiteLogo.objects.create(
            logo_type='navbar_desktop',
            language_code='en',
            image_file=SimpleUploadedFile("logo1.svg", self.svg_content),
            is_active=True
        )
        
        # Create second active logo with same type and language
        logo2 = SiteLogo.objects.create(
            logo_type='navbar_desktop',
            language_code='en',
            image_file=SimpleUploadedFile("logo2.svg", self.svg_content),
            is_active=True
        )
        
        # First logo should be deactivated
        logo1.refresh_from_db()
        self.assertFalse(logo1.is_active)
        self.assertTrue(logo2.is_active)

    def test_different_languages_can_coexist(self):
        """Test that different languages can have their own active logos"""
        logo_en = SiteLogo.objects.create(
            logo_type='navbar_desktop',
            language_code='en',
            image_file=SimpleUploadedFile("logo_en.svg", self.svg_content),
            is_active=True
        )
        
        logo_he = SiteLogo.objects.create(
            logo_type='navbar_desktop',
            language_code='he',
            image_file=SimpleUploadedFile("logo_he.svg", self.svg_content),
            is_active=True
        )
        
        # Both should remain active
        logo_en.refresh_from_db()
        logo_he.refresh_from_db()
        self.assertTrue(logo_en.is_active)
        self.assertTrue(logo_he.is_active)


class LogoAPITests(APITestCase):
    """Test Logo API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.svg_content = b'''<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50">
            <text x="10" y="30">Test</text>
        </svg>'''

    def create_test_logo(self, logo_type, language_code, is_active=True):
        """Helper to create test logos"""
        return SiteLogo.objects.create(
            logo_type=logo_type,
            language_code=language_code,
            image_file=SimpleUploadedFile(
                f"logo_{logo_type}_{language_code}.svg",
                self.svg_content
            ),
            alt_text=f'Test {logo_type} {language_code}',
            is_active=is_active
        )

    def test_list_all_logos(self):
        """Test listing all active logos"""
        self.create_test_logo('navbar_desktop', 'en')
        self.create_test_logo('login_page', 'he')
        
        response = self.client.get('/api/branding/logos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_by_language(self):
        """Test filtering logos by language"""
        self.create_test_logo('navbar_desktop', 'en')
        self.create_test_logo('navbar_desktop', 'he')
        self.create_test_logo('navbar_desktop', 'ru')
        
        # Test English filter
        response = self.client.get('/api/branding/logos/?lang=en')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['language_code'], 'en')

    def test_filter_by_logo_type(self):
        """Test filtering logos by type"""
        self.create_test_logo('navbar_desktop', 'en')
        self.create_test_logo('login_page', 'en')
        self.create_test_logo('favicon', 'en')
        
        response = self.client.get('/api/branding/logos/?type=navbar_desktop')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['logo_type'], 'navbar_desktop')

    def test_for_language_endpoint(self):
        """Test for_language endpoint with fallback logic"""
        # Create language-specific logo
        self.create_test_logo('navbar_desktop', 'en')
        self.create_test_logo('login_page', 'he')
        # Create universal logo as fallback
        self.create_test_logo('favicon', 'all')
        
        response = self.client.get('/api/branding/logos/for_language/?lang=en')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have navbar_desktop (EN specific) and favicon (all languages)
        self.assertIn('navbar_desktop', response.data)
        self.assertIn('favicon', response.data)
        self.assertEqual(response.data['navbar_desktop']['language_code'], 'en')
        self.assertEqual(response.data['favicon']['language_code'], 'all')

    def test_fallback_to_all_languages(self):
        """Test that API falls back to 'all' language when specific not found"""
        # Only create 'all' language logo
        self.create_test_logo('navbar_desktop', 'all')
        
        # Request for specific language
        response = self.client.get('/api/branding/logos/for_language/?lang=ru')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return the 'all' language logo as fallback
        self.assertIn('navbar_desktop', response.data)
        self.assertEqual(response.data['navbar_desktop']['language_code'], 'all')

    def test_all_logo_types_for_language(self):
        """Test getting all logo types for a specific language"""
        # Create all logo types for English
        logo_types = ['navbar_desktop', 'navbar_mobile', 'login_page', 'favicon', 'app_icon']
        for logo_type in logo_types:
            self.create_test_logo(logo_type, 'en')
        
        response = self.client.get('/api/branding/logos/for_language/?lang=en')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have all 5 logo types
        for logo_type in logo_types:
            self.assertIn(logo_type, response.data)

    def test_inactive_logos_not_returned(self):
        """Test that inactive logos are not returned by API"""
        self.create_test_logo('navbar_desktop', 'en', is_active=False)
        
        response = self.client.get('/api/branding/logos/?lang=en')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_manifest_endpoint(self):
        """Test PWA manifest endpoint"""
        self.create_test_logo('app_icon', 'en')
        self.create_test_logo('favicon', 'en')
        
        response = self.client.get('/api/branding/logos/manifest/?lang=en')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('icons', response.data)
        self.assertIsInstance(response.data['icons'], list)


class LanguageLogoTests(APITestCase):
    """Test logo behavior across all 3 languages (EN, RU, HE)"""

    def setUp(self):
        self.client = APIClient()
        self.svg_content = b'''<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50">
            <text x="10" y="30">Logo</text>
        </svg>'''
        
        # Create logos for all 3 languages
        self.languages = ['en', 'ru', 'he']
        self.logo_types = ['navbar_desktop', 'navbar_mobile', 'login_page']

    def create_logos_for_all_languages(self):
        """Create logos for all languages and types"""
        for lang in self.languages:
            for logo_type in self.logo_types:
                SiteLogo.objects.create(
                    logo_type=logo_type,
                    language_code=lang,
                    image_file=SimpleUploadedFile(
                        f"logo_{logo_type}_{lang}.svg",
                        self.svg_content
                    ),
                    alt_text=f'{logo_type} {lang}',
                    is_active=True
                )

    def test_english_logos(self):
        """Test getting all logos for English"""
        self.create_logos_for_all_languages()
        
        response = self.client.get('/api/branding/logos/for_language/?lang=en')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for logo_type in self.logo_types:
            self.assertIn(logo_type, response.data)
            self.assertEqual(response.data[logo_type]['language_code'], 'en')

    def test_russian_logos(self):
        """Test getting all logos for Russian"""
        self.create_logos_for_all_languages()
        
        response = self.client.get('/api/branding/logos/for_language/?lang=ru')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for logo_type in self.logo_types:
            self.assertIn(logo_type, response.data)
            self.assertEqual(response.data[logo_type]['language_code'], 'ru')

    def test_hebrew_logos(self):
        """Test getting all logos for Hebrew"""
        self.create_logos_for_all_languages()
        
        response = self.client.get('/api/branding/logos/for_language/?lang=he')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for logo_type in self.logo_types:
            self.assertIn(logo_type, response.data)
            self.assertEqual(response.data[logo_type]['language_code'], 'he')

    def test_all_languages_have_different_logos(self):
        """Test that each language returns its own unique logos"""
        self.create_logos_for_all_languages()
        
        responses = {}
        for lang in self.languages:
            response = self.client.get(f'/api/branding/logos/for_language/?lang={lang}')
            responses[lang] = response.data
        
        # Verify each language has navbar_desktop
        for lang in self.languages:
            self.assertIn('navbar_desktop', responses[lang])
        
        # Verify the IDs are different (unique logos per language)
        en_id = responses['en']['navbar_desktop']['id']
        ru_id = responses['ru']['navbar_desktop']['id']
        he_id = responses['he']['navbar_desktop']['id']
        
        self.assertNotEqual(en_id, ru_id)
        self.assertNotEqual(en_id, he_id)
        self.assertNotEqual(ru_id, he_id)


class SiteSettingsTests(TestCase):
    """Test SiteSettings model (singleton)"""

    def test_settings_singleton(self):
        """Test that only one settings instance can exist"""
        settings1 = SiteSettings.get_settings()
        settings2 = SiteSettings.get_settings()
        
        self.assertEqual(settings1.id, settings2.id)
        self.assertEqual(SiteSettings.objects.count(), 1)

    def test_settings_defaults(self):
        """Test default settings values"""
        settings = SiteSettings.get_settings()
        
        self.assertEqual(settings.site_name_en, 'BishulSheli')
        self.assertEqual(settings.primary_color, '#9B59B6')
        self.assertEqual(settings.secondary_color, '#8E44AD')

