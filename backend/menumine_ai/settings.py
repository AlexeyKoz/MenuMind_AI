import os
import sys
from pathlib import Path
from datetime import timedelta
import environ

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env()
# Read .env file from BASE_DIR (backend/)
env_file = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_file):
    environ.Env.read_env(env_file)
    print(f"[INFO] Loaded environment from: {env_file}")
else:
    print(f"[WARNING] .env file not found at: {env_file}")

# Note: We use full path 'apps.app_name' in INSTALLED_APPS
# Do NOT modify sys.path as it breaks Django's app loading

# Security
SECRET_KEY = env(
    'SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = env.bool('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[
                         'localhost', '127.0.0.1', '0.0.0.0'])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'rest_framework.authtoken',
    'django.contrib.sites',  # Required for allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'corsheaders',
    'channels',
    'django_extensions',

    # Local apps
    'apps.users',
    'apps.shopping',
    'apps.recipes',
    'apps.ai_agents',
    'apps.nutrition',
    'apps.analytics',
    'apps.core.apps.CoreConfig',  # Use CoreConfig for service initialization
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'menumine_ai.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ASGI
ASGI_APPLICATION = 'menumine_ai.asgi.application'

# Database
# Database - Use SQLite for development, PostgreSQL for production
if env.bool('USE_POSTGRES', default=False):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DB_NAME', default='menumine_ai'),
            'USER': env('DB_USER', default='postgres'),
            'PASSWORD': env('DB_PASSWORD', default='password'),
            'HOST': env('DB_HOST', default='localhost'),
            'PORT': env('DB_PORT', default='5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

    # IML Integration
IML_DB_PATH = os.getenv(
    'IML_DB_PATH', r'C:\Users\al7ko\Desktop\ingredients-master-list-new\ingredient-master-list\data\iml.db')

# CookLingo Database Path
COOKLINGO_DB_PATH = os.getenv(
    'COOKLINGO_DB_PATH', os.path.join(BASE_DIR, 'cooklingo.db'))

# Multilingual
LANGUAGES = [
    ('en', 'English'),
    ('ru', 'Русский'),
    ('he', 'עברית')
]
LANGUAGE_CODE = 'en'
USE_I18N = True

# Redis & Channels
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')

# Django Caching - with fallback to LocMemCache if Redis is unavailable
try:
    import redis
    # Test Redis connection
    r = redis.from_url(REDIS_URL, socket_connect_timeout=1)
    r.ping()
    # If Redis is available, use it
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
                'RETRY_ON_TIMEOUT': True,
                'MAX_CONNECTIONS': 50,
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                },
            }
        }
    }
    print("[INFO] Using Redis for caching")
except (ImportError, redis.exceptions.ConnectionError, Exception) as e:
    # Fallback to in-memory cache for development
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
    print(
        f"[WARNING] Redis not available ({type(e).__name__}), using in-memory cache for development")

# Django Channels - WebSocket Layer (Redis-backed for production performance)
try:
    # Test Redis connection for channels
    r_test = redis.from_url(REDIS_URL, socket_connect_timeout=1)
    r_test.ping()

    # Redis is available - use it for channels (RECOMMENDED for production)
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [REDIS_URL],
                "capacity": 1500,  # Maximum number of messages to store
                "expiry": 10,  # Message expiry time in seconds
                "group_expiry": 86400,  # Group expiry time (24 hours)
                "symmetric_encryption_keys": [env('SECRET_KEY', default='change-me-in-production')],
            },
        },
    }
    print("[INFO] Using Redis for Django Channels (WebSocket layer)")
except (ImportError, redis.exceptions.ConnectionError, Exception) as e:
    # Fallback to in-memory channel layer for development without Redis
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
    print(
        f"[WARNING] Redis not available ({type(e).__name__}), using in-memory channel layer for development")
    print("[WARNING] In-memory channels don't support multiple workers - only for local development!")

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# CORS Settings
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:8001',
    'http://127.0.0.1:8001',
])

# Allow all origins in development (remove in production)
CORS_ALLOW_ALL_ORIGINS = env.bool('CORS_ALLOW_ALL_ORIGINS', default=True)

# Allow credentials for CORS
CORS_ALLOW_CREDENTIALS = True

# Allowed headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-user-language',  # NEW: For multilingual dashboard (Sprint 9)
]

# Allowed methods
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Celery
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# AI Configuration
GROQ_API_KEY = env('GROQ_API_KEY', default='')
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
GEMINI_API_KEY = env('GEMINI_API_KEY', default='')  # Gemini Flash 2.5
GOOGLE_CLOUD_API_KEY = env('GOOGLE_CLOUD_API_KEY',
                           default='')  # Google Translate API

# ============================================
# SITE CONFIGURATION
# ============================================
SITE_ID = 1

# ============================================
# AUTHENTICATION BACKENDS
# ============================================
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# ============================================
# REST AUTH & JWT CONFIGURATION
# ============================================
REST_USE_JWT = True
JWT_AUTH_COOKIE = None  # We're using Bearer tokens
JWT_AUTH_REFRESH_COOKIE = None

# ============================================
# ALLAUTH ACCOUNT SETTINGS
# ============================================
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = False
ACCOUNT_ADAPTER = 'apps.users.adapters.MultilingualAccountAdapter'

# Social auth settings
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'mandatory'

# ============================================
# SOCIAL AUTH PROVIDERS
# ============================================
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': env('GOOGLE_CLIENT_ID', default=''),
            'secret': env('GOOGLE_CLIENT_SECRET', default=''),
            'key': ''
        }
    }
}

# ============================================
# EMAIL CONFIGURATION
# ============================================
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
    EMAIL_PORT = env.int('EMAIL_PORT', default=587)
    EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
    EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@menumindai.com')
EMAIL_SUBJECT_PREFIX = '[MenuMindAI] '

# Frontend URL for email links
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:3000')

# Search & Scraping APIs
BRAVE_SEARCH_API_KEY = env('BRAVE_SEARCH_API_KEY', default='')
FIRECRAWL_API_KEY = env('FIRECRAWL_API_KEY', default='')

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Jerusalem'
USE_I18N = True
USE_TZ = True
