"""
Global pytest fixtures available to all tests.
"""
import pytest
from django.conf import settings
from rest_framework.test import APIClient
from faker import Faker
from unittest.mock import MagicMock, patch

fake = Faker()

# ============================================================================
# DATABASE & TRANSACTIONAL FIXTURES
# ============================================================================

@pytest.fixture(scope='session')
def django_db_setup():
    """Setup test database."""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


@pytest.fixture
def db_access(db):
    """Provide database access to tests."""
    return db


# ============================================================================
# API CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def api_client():
    """Unauthenticated API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Authenticated API client with JWT token."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def user(db):
    """Create a test user."""
    from apps.users.models import User
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='TestPass123!'
    )
    return user


@pytest.fixture
def verified_user(db):
    """Create a verified test user."""
    from apps.users.models import User
    user = User.objects.create_user(
        username='verified',
        email='verified@example.com',
        password='TestPass123!'
    )
    # Mark email as verified
    try:
        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(
            user=user,
            email=user.email,
            verified=True,
            primary=True
        )
    except ImportError:
        pass
    return user


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis cache."""
    redis_mock = MagicMock()
    with patch('django.core.cache.cache', redis_mock):
        yield redis_mock


@pytest.fixture
def mock_celery():
    """Mock Celery tasks."""
    with patch('celery.app.task.Task.apply_async') as mock:
        yield mock


@pytest.fixture
def mock_groq_client():
    """Mock Groq AI client."""
    with patch('groq.Client') as mock:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='{"recipe": "data"}'))]
        )
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_gemini_client():
    """Mock Google Gemini client."""
    with patch('google.generativeai.GenerativeModel') as mock:
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = MagicMock(
            text='{"translated": "content"}'
        )
        mock.return_value = mock_instance
        yield mock_instance


# ============================================================================
# TIME MOCKING
# ============================================================================

@pytest.fixture
def freeze_time_fixture():
    """Freeze time for testing time-dependent logic."""
    from freezegun import freeze_time
    with freeze_time("2025-01-15 12:00:00"):
        yield


# ============================================================================
# EMAIL MOCKING
# ============================================================================

@pytest.fixture
def mailoutbox():
    """Capture sent emails."""
    from django.core import mail
    return mail.outbox


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def create_user():
    """Factory function to create users."""
    def _create_user(**kwargs):
        from apps.users.models import User
        defaults = {
            'username': f'user_{fake.uuid4()[:8]}',
            'email': fake.email(),
            'password': 'TestPass123!'
        }
        defaults.update(kwargs)
        password = defaults.pop('password')
        user = User.objects.create_user(**defaults)
        user.set_password(password)
        user.save()
        return user
    return _create_user


@pytest.fixture
def sample_recipe_data():
    """Sample recipe data for testing."""
    return {
        'name': 'Test Recipe',
        'source': 'test',
        'content': {
            'version': '2.0',
            'metadata': {
                'name': 'Test Recipe',
                'servings': 4,
                'prep_time': 15,
                'cook_time': 30
            },
            'ingredients': [
                {'name': 'flour', 'quantity': 2, 'unit': 'cups'},
                {'name': 'eggs', 'quantity': 3, 'unit': 'pieces'}
            ],
            'instructions': [
                {'step': 1, 'description': 'Mix ingredients'},
                {'step': 2, 'description': 'Cook'}
            ]
        }
    }





