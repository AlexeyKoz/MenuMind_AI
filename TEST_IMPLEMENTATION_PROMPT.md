# Backend Test Implementation Prompt for External AI Agent

## Context & Objective

You are a testing specialist tasked with implementing a comprehensive test suite for **MenuMindAI** - a multi-tenant food intelligence platform with Django backend and React/TypeScript frontend. 

A complete testing strategy has been designed with **~450+ test specifications**. Your task is to **implement all these tests** following the provided strategy, naming conventions, and best practices.

---

## 📚 Reference Documents

You have access to these strategy documents:
1. **BACKEND_TESTING_STRATEGY_v1.0.md** - Overall testing approach, tools, structure
2. **BACKEND_TEST_NAMES_CHECKLIST.md** - Complete list of ~450+ test names to implement
3. **README.md** - Project overview and architecture

**Read these documents first** to understand:
- Test organization and structure
- Naming conventions
- Testing tools and frameworks
- Coverage requirements
- Test pyramid approach

---

## 🎯 Your Mission

Implement **all ~450+ tests** across:
- ✅ 7 Django apps (users, recipes, shopping, nutrition, core, ai_agents, legal)
- ✅ Integration tests (cross-app workflows)
- ✅ E2E tests (complete user journeys)
- ✅ Performance tests (response times, cache)
- ✅ Security tests (auth, SQL injection, XSS)
- ✅ Celery tests (background tasks)

---

## 🛠️ Testing Stack & Tools

### Primary Framework
```python
# pytest - Modern Python testing framework
import pytest
from pytest_django.fixtures import db
from django.test import TestCase
from rest_framework.test import APIClient, APITestCase
```

### Key Dependencies
```python
# Test data factories
import factory
from factory.django import DjangoModelFactory
from faker import Faker

# Time mocking
from freezegun import freeze_time

# HTTP mocking
import responses
from unittest.mock import Mock, patch, MagicMock

# Async testing
import pytest_asyncio
from channels.testing import WebsocketCommunicator

# Celery testing
from celery.contrib.testing.worker import start_worker
```

---

## 📁 File Organization

Create tests following this structure:

```
backend/
├── apps/
│   ├── users/
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── conftest.py              # App-specific fixtures
│   │       ├── factories.py              # User/Profile factories
│   │       ├── test_models.py
│   │       ├── test_serializers.py
│   │       ├── test_views.py
│   │       ├── test_permissions.py
│   │       ├── test_auth_flows.py
│   │       ├── test_google_oauth.py
│   │       └── test_email_verification.py
│   ├── recipes/
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── conftest.py
│   │       ├── factories.py
│   │       ├── test_models.py
│   │       ├── test_serializers.py
│   │       ├── test_views.py
│   │       ├── test_translation_pipeline.py
│   │       ├── test_rcip_import_export.py
│   │       ├── test_ai_generation.py
│   │       └── test_discovery_cache.py
│   └── [other apps...]
├── tests/
│   ├── conftest.py                       # Global fixtures
│   ├── integration/
│   ├── e2e/
│   ├── performance/
│   ├── security/
│   └── celery/
├── pytest.ini                             # Pytest configuration
└── .coveragerc                            # Coverage configuration
```

---

## 🏗️ Implementation Phase Strategy

### Phase 1: Setup Infrastructure (Do This First!)

#### 1.1 Create `pytest.ini`
```ini
[pytest]
DJANGO_SETTINGS_MODULE = menumine_ai.settings
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --strict-markers
    --tb=short
    --reuse-db
    --nomigrations
    --cov=apps
    --cov-report=html
    --cov-report=term-missing
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
    unit: marks tests as unit tests
testpaths = 
    apps
    tests
```

#### 1.2 Create `.coveragerc`
```ini
[run]
source = apps
omit = 
    */migrations/*
    */tests/*
    */test_*.py
    */__init__.py
    */admin.py
    */apps.py
    */manage.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstract
```

#### 1.3 Create Global `tests/conftest.py`
```python
"""
Global pytest fixtures available to all tests.
"""
import pytest
from django.conf import settings
from rest_framework.test import APIClient
from faker import Faker

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


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis cache."""
    from unittest.mock import MagicMock
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
    with patch('apps.ai_agents.clients.groq.GroqClient') as mock:
        mock_instance = MagicMock()
        mock_instance.generate.return_value = {"recipe": "data"}
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_gemini_client():
    """Mock Google Gemini client."""
    with patch('apps.ai_agents.clients.gemini.GeminiClient') as mock:
        mock_instance = MagicMock()
        mock_instance.translate.return_value = {"translated": "content"}
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
```

---

### Phase 2: Create Factories (Test Data Generators)

For **each app**, create `factories.py` with realistic test data.

#### Example: `apps/users/tests/factories.py`
```python
"""
Test data factories for users app.
Use these to create realistic test data easily.
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from apps.users.models import User, UserProfile

fake = Faker()

class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
        django_get_or_create = ('email',)
    
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    is_active = True
    email_verified = False
    
    @factory.post_generation
    def verified(self, create, extracted, **kwargs):
        """Set email_verified if requested."""
        if extracted:
            self.email_verified = True
            if create:
                self.save()


class VerifiedUserFactory(UserFactory):
    """Factory for creating verified users."""
    email_verified = True


class AdminUserFactory(UserFactory):
    """Factory for creating admin users."""
    is_staff = True
    is_superuser = True
    email_verified = True


class UserProfileFactory(DjangoModelFactory):
    """Factory for creating UserProfile instances."""
    
    class Meta:
        model = UserProfile
    
    user = factory.SubFactory(UserFactory)
    preferred_language = 'en'
    preferences = factory.LazyFunction(lambda: {
        'theme': 'light',
        'notifications': True
    })
```

#### Example: `apps/recipes/tests/factories.py`
```python
"""
Test data factories for recipes app.
"""
import factory
from factory.django import DjangoModelFactory
from apps.recipes.models import CanonicalRecipe, UserRecipe, RecipeTranslation
from apps.users.tests.factories import UserFactory

class CanonicalRecipeFactory(DjangoModelFactory):
    """Factory for creating CanonicalRecipe instances."""
    
    class Meta:
        model = CanonicalRecipe
    
    name = factory.Faker('sentence', nb_words=3)
    source = 'test'
    content = factory.LazyFunction(lambda: {
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
    })
    archived = False


class UserRecipeFactory(DjangoModelFactory):
    """Factory for creating UserRecipe instances."""
    
    class Meta:
        model = UserRecipe
    
    user = factory.SubFactory(UserFactory)
    canonical_recipe = factory.SubFactory(CanonicalRecipeFactory)
    custom_modifications = factory.Dict({})
    favorite = False


class RecipeTranslationFactory(DjangoModelFactory):
    """Factory for creating RecipeTranslation instances."""
    
    class Meta:
        model = RecipeTranslation
    
    canonical_recipe = factory.SubFactory(CanonicalRecipeFactory)
    language = 'en'
    status = 'completed'
    content = factory.Dict({
        'translated_name': 'Test Recipe',
        'ingredients': [],
        'instructions': []
    })
```

---

### Phase 3: Implement Tests App by App

For **each test file**, follow this pattern:

#### Test Structure Template
```python
"""
Tests for [Feature/Model/View/etc].

Test Coverage:
- [List main areas covered]
- [Another area]
"""
import pytest
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

# Import models, serializers, views being tested
from apps.users.models import User, UserProfile
from apps.users.tests.factories import UserFactory, VerifiedUserFactory


# ============================================================================
# UNIT TESTS - Models
# ============================================================================

@pytest.mark.django_db
class TestUserModel:
    """Test User model behavior."""
    
    def test_create_user_with_email_and_password_succeeds(self):
        """
        GIVEN: Valid email and password
        WHEN: Creating a new user
        THEN: User is created successfully with hashed password
        """
        user = User.objects.create_user(
            email='test@example.com',
            password='securepass123'
        )
        
        assert user.email == 'test@example.com'
        assert user.check_password('securepass123')
        assert user.is_active is True
        assert user.email_verified is False
    
    def test_create_user_without_email_fails(self):
        """
        GIVEN: No email provided
        WHEN: Creating a new user
        THEN: ValueError is raised
        """
        with pytest.raises(ValueError, match='Email is required'):
            User.objects.create_user(email='', password='pass123')
    
    def test_create_user_with_duplicate_email_fails(self):
        """
        GIVEN: Email already exists in database
        WHEN: Creating user with duplicate email
        THEN: IntegrityError is raised
        """
        UserFactory(email='duplicate@example.com')
        
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            UserFactory(email='duplicate@example.com')


# ============================================================================
# UNIT TESTS - Serializers
# ============================================================================

@pytest.mark.django_db
class TestUserRegistrationSerializer:
    """Test UserRegistrationSerializer."""
    
    def test_valid_registration_data_serializes_correctly(self):
        """
        GIVEN: Valid registration data
        WHEN: Serializing the data
        THEN: Serializer is valid and data is correct
        """
        from apps.users.serializers import UserRegistrationSerializer
        
        data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['email'] == 'newuser@example.com'
    
    def test_registration_with_short_password_fails_validation(self):
        """
        GIVEN: Password shorter than minimum length
        WHEN: Validating registration data
        THEN: Validation fails with appropriate error
        """
        from apps.users.serializers import UserRegistrationSerializer
        
        data = {
            'email': 'user@example.com',
            'password': 'short',
            'password2': 'short'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors


# ============================================================================
# INTEGRATION TESTS - API Views
# ============================================================================

@pytest.mark.django_db
class TestUserRegistrationView:
    """Test user registration API endpoint."""
    
    def test_registration_post_with_valid_data_returns_201(self, api_client):
        """
        GIVEN: Valid registration data
        WHEN: POST to registration endpoint
        THEN: Returns 201 and creates user
        """
        data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!'
        }
        
        response = api_client.post('/api/users/register/', data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert User.objects.filter(email='newuser@example.com').exists()
    
    def test_registration_sends_verification_email(
        self, api_client, mailoutbox
    ):
        """
        GIVEN: Valid registration data
        WHEN: User registers
        THEN: Verification email is sent
        """
        data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!'
        }
        
        response = api_client.post('/api/users/register/', data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == ['newuser@example.com']
        assert 'verify' in mailoutbox[0].subject.lower()


# ============================================================================
# INTEGRATION TESTS - Complete Flows
# ============================================================================

@pytest.mark.integration
@pytest.mark.django_db
class TestCompleteRegistrationFlow:
    """Test complete registration to verification flow."""
    
    def test_registration_to_email_verification_to_login_complete_flow(
        self, api_client, mailoutbox
    ):
        """
        GIVEN: New user wants to register
        WHEN: User registers, verifies email, and logs in
        THEN: Complete flow succeeds
        """
        # Step 1: Register
        register_data = {
            'email': 'flow@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!'
        }
        register_response = api_client.post(
            '/api/users/register/', 
            register_data
        )
        assert register_response.status_code == status.HTTP_201_CREATED
        
        # Step 2: Extract verification token from email
        assert len(mailoutbox) == 1
        email_body = mailoutbox[0].body
        # Extract token from email (implementation specific)
        token = extract_token_from_email(email_body)
        
        # Step 3: Verify email
        verify_response = api_client.post(
            f'/api/users/verify-email/',
            {'token': token}
        )
        assert verify_response.status_code == status.HTTP_200_OK
        
        # Step 4: Login
        login_data = {
            'email': 'flow@example.com',
            'password': 'SecurePass123!'
        }
        login_response = api_client.post('/api/users/login/', login_data)
        assert login_response.status_code == status.HTTP_200_OK
        assert 'access' in login_response.data
        
        # Verify user is now verified
        user = User.objects.get(email='flow@example.com')
        assert user.email_verified is True
```

---

## 🎨 Code Quality Standards

### 1. Test Documentation
Every test should have:
```python
def test_something_happens_as_expected(self):
    """
    GIVEN: Initial conditions/context
    WHEN: Action being performed
    THEN: Expected outcome
    """
    # Arrange - Setup
    user = UserFactory()
    
    # Act - Execute
    result = user.do_something()
    
    # Assert - Verify
    assert result == expected_value
```

### 2. Use Factories for Test Data
```python
# ✅ GOOD - Use factories
user = UserFactory(email_verified=True)
recipe = CanonicalRecipeFactory(name='Test Recipe')

# ❌ BAD - Manual object creation
user = User.objects.create(
    email='test@example.com',
    password='pass',
    email_verified=True
)
```

### 3. Mock External Dependencies
```python
# ✅ GOOD - Mock AI providers
@patch('apps.ai_agents.clients.groq.GroqClient.generate')
def test_ai_generation(mock_generate):
    mock_generate.return_value = {'recipe': 'data'}
    result = generate_recipe(['flour', 'eggs'])
    assert result is not None

# ❌ BAD - Real API calls in tests
def test_ai_generation():
    result = groq_client.generate(['flour', 'eggs'])  # Real API call!
```

### 4. Test Isolation
```python
# ✅ GOOD - Each test is independent
@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = UserFactory()
        assert user.email

    def test_update_user(self):
        user = UserFactory()  # Fresh user for this test
        user.email_verified = True
        user.save()

# ❌ BAD - Tests depend on each other
class TestUserModel:
    def test_create_user(self):
        self.user = UserFactory()  # Bad: shared state
    
    def test_update_user(self):
        self.user.email_verified = True  # Depends on previous test
```

### 5. Clear Assertions
```python
# ✅ GOOD - Specific assertions
assert response.status_code == status.HTTP_201_CREATED
assert 'email' in response.data
assert response.data['email'] == 'test@example.com'

# ❌ BAD - Vague assertions
assert response.status_code == 201
assert response.data  # What are we checking?
```

---

## 🔍 Testing Patterns by Test Type

### Pattern 1: Model Tests
```python
@pytest.mark.django_db
class TestModelName:
    """Test ModelName model."""
    
    def test_model_creation_with_required_fields_succeeds(self):
        """Test creating model with minimum required fields."""
        instance = ModelNameFactory()
        assert instance.pk is not None
        assert instance.field_name is not None
    
    def test_model_string_representation(self):
        """Test __str__ method returns expected format."""
        instance = ModelNameFactory(name='Test Name')
        assert str(instance) == 'Expected String'
    
    def test_model_relationship_cascade_delete(self):
        """Test cascade delete behavior."""
        parent = ParentFactory()
        child = ChildFactory(parent=parent)
        parent.delete()
        assert not ChildModel.objects.filter(pk=child.pk).exists()
```

### Pattern 2: Serializer Tests
```python
@pytest.mark.django_db
class TestSerializerName:
    """Test SerializerName."""
    
    def test_valid_data_serializes_correctly(self):
        """Test serialization of valid data."""
        instance = ModelFactory()
        serializer = SerializerName(instance)
        assert 'field_name' in serializer.data
        assert serializer.data['field_name'] == instance.field_name
    
    def test_deserialization_creates_instance(self):
        """Test deserializing data creates model instance."""
        data = {'field1': 'value1', 'field2': 'value2'}
        serializer = SerializerName(data=data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.field1 == 'value1'
    
    def test_validation_rejects_invalid_data(self):
        """Test validation catches invalid data."""
        data = {'field1': 'invalid_value'}
        serializer = SerializerName(data=data)
        assert not serializer.is_valid()
        assert 'field1' in serializer.errors
```

### Pattern 3: API View Tests
```python
@pytest.mark.django_db
class TestAPIViewName:
    """Test API endpoint."""
    
    def test_list_endpoint_requires_authentication(self, api_client):
        """Test unauthenticated request returns 401."""
        response = api_client.get('/api/endpoint/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_endpoint_returns_paginated_results(
        self, authenticated_client
    ):
        """Test authenticated list request returns paginated data."""
        # Create test data
        ModelFactory.create_batch(15)
        
        response = authenticated_client.get('/api/endpoint/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 10  # Default page size
    
    def test_create_endpoint_with_valid_data_returns_201(
        self, authenticated_client
    ):
        """Test creating resource with valid data."""
        data = {'field1': 'value1', 'field2': 'value2'}
        response = authenticated_client.post('/api/endpoint/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Model.objects.filter(field1='value1').exists()
```

### Pattern 4: Permission Tests
```python
@pytest.mark.django_db
class TestPermissionName:
    """Test custom permission class."""
    
    def test_owner_has_permission(self, authenticated_client):
        """Test object owner has permission."""
        user = UserFactory()
        obj = ModelFactory(owner=user)
        
        # Simulate request
        request = Mock(user=user)
        permission = PermissionClass()
        assert permission.has_object_permission(request, None, obj) is True
    
    def test_non_owner_denied_permission(self, authenticated_client):
        """Test non-owner is denied permission."""
        owner = UserFactory()
        other_user = UserFactory()
        obj = ModelFactory(owner=owner)
        
        request = Mock(user=other_user)
        permission = PermissionClass()
        assert permission.has_object_permission(request, None, obj) is False
```

### Pattern 5: WebSocket Tests
```python
@pytest.mark.django_db
@pytest.mark.asyncio
class TestWebSocketConsumer:
    """Test WebSocket consumer."""
    
    async def test_websocket_connect_authenticated_succeeds(self):
        """Test authenticated connection succeeds."""
        from channels.testing import WebsocketCommunicator
        from apps.shopping.consumers import ShoppingListConsumer
        
        user = UserFactory()
        communicator = WebsocketCommunicator(
            ShoppingListConsumer.as_asgi(),
            '/ws/shopping/1/',
            headers=[(b'authorization', f'Bearer {token}'.encode())]
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        await communicator.disconnect()
```

### Pattern 6: Celery Task Tests
```python
@pytest.mark.django_db
class TestCeleryTask:
    """Test Celery background task."""
    
    @patch('apps.recipes.tasks.translate_recipe.apply_async')
    def test_task_queued_on_recipe_creation(self, mock_task):
        """Test task is queued when recipe is created."""
        recipe = CanonicalRecipeFactory()
        trigger_translation(recipe.id)
        
        mock_task.assert_called_once()
        assert mock_task.call_args[0][0] == (recipe.id,)
    
    def test_task_execution_updates_translation_status(self):
        """Test task execution updates database."""
        recipe = CanonicalRecipeFactory()
        translation = RecipeTranslationFactory(
            canonical_recipe=recipe,
            status='pending'
        )
        
        # Execute task synchronously
        from apps.recipes.tasks import translate_recipe
        translate_recipe.apply(args=[recipe.id, 'ru']).get()
        
        translation.refresh_from_db()
        assert translation.status == 'completed'
```

---

## 📋 Implementation Checklist

Work through tests in this order:

### Week 1: Foundation
- [ ] **Setup infrastructure** (pytest.ini, conftest.py, .coveragerc)
- [ ] **Users App** (~70 tests)
  - [ ] Create factories.py
  - [ ] test_models.py
  - [ ] test_serializers.py
  - [ ] test_views.py
  - [ ] test_permissions.py
  - [ ] test_auth_flows.py
  - [ ] test_google_oauth.py
  - [ ] test_email_verification.py
- [ ] **Core App** (~55 tests)
  - [ ] Create factories.py
  - [ ] test_iml_service.py
  - [ ] test_cooklingo_service.py
  - [ ] test_translation_service.py
  - [ ] test_ingredient_mapper.py
  - [ ] test_unit_converter.py
  - [ ] test_rcip_validators.py

### Week 2: Features
- [ ] **Recipes App** (~110 tests)
  - [ ] Create factories.py
  - [ ] test_models.py
  - [ ] test_serializers.py
  - [ ] test_views.py
  - [ ] test_translation_pipeline.py
  - [ ] test_rcip_import_export.py
  - [ ] test_ai_generation.py
  - [ ] test_discovery_cache.py
- [ ] **Shopping App** (~75 tests)
  - [ ] Create factories.py
  - [ ] test_models.py
  - [ ] test_serializers.py
  - [ ] test_views.py
  - [ ] test_websocket_consumers.py
  - [ ] test_collaboration.py
  - [ ] test_permissions.py
  - [ ] test_archive_workflows.py
- [ ] **Nutrition App** (~35 tests)
  - [ ] Create factories.py
  - [ ] test_models.py
  - [ ] test_serializers.py
  - [ ] test_views.py
  - [ ] test_ai_logging.py
  - [ ] test_analytics.py

### Week 3: Advanced
- [ ] **AI Agents App** (~45 tests)
- [ ] **Legal App** (~25 tests)
- [ ] **Integration Tests** (~15 tests)
- [ ] **E2E Tests** (~15 tests)
- [ ] **Performance Tests** (~15 tests)
- [ ] **Security Tests** (~25 tests)
- [ ] **Celery Tests** (~15 tests)

---

## 🎯 Quality Gates

Before considering a test file complete, verify:

### ✅ Code Quality
- [ ] All tests have descriptive docstrings
- [ ] Test names follow convention: `test_<what>_<condition>_<outcome>`
- [ ] Proper use of fixtures and factories
- [ ] External dependencies are mocked
- [ ] No real API calls or email sending in tests

### ✅ Coverage
- [ ] All model methods tested
- [ ] All API endpoints tested
- [ ] All business logic tested
- [ ] Edge cases covered
- [ ] Error conditions tested

### ✅ Best Practices
- [ ] Tests are independent (can run in any order)
- [ ] Tests are fast (unit tests < 100ms each)
- [ ] Clear arrange-act-assert structure
- [ ] Meaningful assertion messages
- [ ] No test interdependencies

### ✅ Documentation
- [ ] Module-level docstring explains what's tested
- [ ] Each test has GIVEN-WHEN-THEN docstring
- [ ] Complex setup is commented
- [ ] Non-obvious assertions explained

---

## 🚀 Execution Instructions

### For Each App:

1. **Read the codebase** for that app
   - Understand models, serializers, views
   - Identify business logic
   - Note external dependencies

2. **Create factories.py** first
   - One factory per model
   - Use Faker for realistic data
   - Handle relationships properly

3. **Implement tests file by file**
   - Start with models (easiest)
   - Then serializers
   - Then views
   - Then complex workflows

4. **Run tests frequently**
   ```bash
   # Run single test file
   pytest apps/users/tests/test_models.py -v
   
   # Run single test
   pytest apps/users/tests/test_models.py::TestUserModel::test_create_user -v
   
   # Run with coverage
   pytest apps/users/tests/ --cov=apps.users --cov-report=html
   ```

5. **Iterate until green**
   - Fix failing tests
   - Add missing fixtures
   - Mock external dependencies
   - Ensure tests are isolated

---

## 🔧 Common Issues & Solutions

### Issue: "Database not found"
**Solution:** Add `@pytest.mark.django_db` decorator
```python
@pytest.mark.django_db
class TestModel:
    def test_something(self):
        # Now has database access
```

### Issue: "Factory creates duplicate objects"
**Solution:** Use `django_get_or_create` in factory
```python
class MyFactory(DjangoModelFactory):
    class Meta:
        model = MyModel
        django_get_or_create = ('unique_field',)
```

### Issue: "Tests fail randomly"
**Solution:** Tests aren't isolated, check for shared state
```python
# ❌ BAD - Shared class variable
class TestSomething:
    user = UserFactory()  # Created once, used in all tests
    
# ✅ GOOD - Create fresh for each test
class TestSomething:
    def test_something(self):
        user = UserFactory()  # Fresh user
```

### Issue: "Slow tests"
**Solution:** Mock expensive operations
```python
# ❌ BAD - Real AI API call
def test_translation():
    result = translate_via_ai("text")  # Slow!

# ✅ GOOD - Mock AI call
@patch('apps.core.services.translate_via_ai')
def test_translation(mock_translate):
    mock_translate.return_value = "translated"
    result = translate_via_ai("text")  # Fast!
```

### Issue: "Can't test email sending"
**Solution:** Use mailoutbox fixture
```python
def test_sends_email(mailoutbox):
    send_verification_email(user)
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [user.email]
```

---

## 📊 Progress Tracking

As you implement tests, update this checklist:

```markdown
## Implementation Progress

### Users App (70 tests)
- [x] factories.py created
- [x] test_models.py (13/13) ✅
- [x] test_serializers.py (20/20) ✅
- [ ] test_views.py (25/25) 🔄 In Progress
- [ ] test_permissions.py (0/8)
- [ ] test_auth_flows.py (0/10)
- [ ] test_google_oauth.py (0/12)
- [ ] test_email_verification.py (0/15)

**Completion: 33/70 (47%)**
```

---

## 🎓 Final Notes

### Remember:
1. **Read reference documents first** - Understanding the strategy is crucial
2. **Follow the checklist** - All ~450 test names are specified
3. **Use patterns provided** - Don't reinvent the wheel
4. **Mock external services** - No real API calls
5. **Keep tests fast** - Unit tests should be < 100ms
6. **Test behavior, not implementation** - Tests should survive refactoring
7. **Document complex tests** - Future you will thank you

### Success Criteria:
- ✅ All ~450 tests implemented
- ✅ All tests passing
- ✅ >90% code coverage
- ✅ Tests run in < 5 minutes
- ✅ No flaky tests
- ✅ No real external API calls
- ✅ Clear documentation

---

## 🚀 Ready to Start!

You now have everything needed to implement a comprehensive test suite:
1. ✅ Complete test strategy
2. ✅ All test names (~450+)
3. ✅ Code patterns and examples
4. ✅ Quality standards
5. ✅ Implementation roadmap

**Begin with Phase 1 (Infrastructure Setup), then proceed app by app following the checklist.**

Good luck! 🎯
