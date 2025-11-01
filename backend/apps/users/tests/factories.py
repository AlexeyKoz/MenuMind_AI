"""
Test data factories for users app.
Use these to create realistic test data easily.
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from apps.users.models import User, UserPreferences

fake = Faker()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
        django_get_or_create = ('email',)
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')
    is_active = True
    
    # Profile fields
    birth_date = factory.Faker('date_of_birth', minimum_age=18, maximum_age=80)
    gender = factory.Iterator(['male', 'female', 'other'])
    height_cm = factory.Faker('random_int', min=150, max=200)
    weight_kg = factory.Faker('pydecimal', left_digits=3, right_digits=2, min_value=40, max_value=150)
    activity_level = factory.Iterator(['sedentary', 'light', 'moderate', 'very', 'extra'])
    
    # Nutrition goals
    daily_calories_goal = factory.Faker('random_int', min=1500, max=3000)
    daily_protein_goal = factory.Faker('random_int', min=50, max=200)
    daily_carbs_goal = factory.Faker('random_int', min=150, max=400)
    daily_fat_goal = factory.Faker('random_int', min=50, max=150)
    
    # Dietary restrictions
    dietary_restrictions = factory.LazyFunction(lambda: [])
    allergies = factory.LazyFunction(lambda: [])
    
    # Language preference
    preferred_language = 'en'
    
    # Unit preferences
    weight_unit = 'kg'
    volume_unit = 'liters'
    time_format = '24h'
    
    # Collaboration
    personal_color = '#4F46E5'
    shopping_role = 'both'
    
    @factory.post_generation
    def verified(self, create, extracted, **kwargs):
        """Set email verified if requested."""
        if extracted:
            try:
                from allauth.account.models import EmailAddress
                EmailAddress.objects.get_or_create(
                    user=self,
                    email=self.email,
                    defaults={'verified': True, 'primary': True}
                )
            except ImportError:
                pass


class VerifiedUserFactory(UserFactory):
    """Factory for creating verified users."""
    verified = True


class AdminUserFactory(UserFactory):
    """Factory for creating admin users."""
    is_staff = True
    is_superuser = True
    verified = True


class UserPreferencesFactory(DjangoModelFactory):
    """Factory for creating UserPreferences instances."""
    
    class Meta:
        model = UserPreferences
    
    user = factory.SubFactory(UserFactory)
    language = 'en'
    unit_system = 'metric'
    weight_unit = 'kg'
    volume_unit = 'L'
    temperature_unit = 'C'


class UserWithPreferencesFactory(UserFactory):
    """Factory for creating user with preferences."""
    
    preferences = factory.RelatedFactory(
        UserPreferencesFactory,
        factory_related_name='user'
    )





