"""
Test data factories for recipes app.

Uses factory_boy to generate realistic test data.
"""
import factory
from factory.django import DjangoModelFactory
from factory import fuzzy
from apps.recipes.models import (
    CanonicalRecipe,
    Recipe,
    UserRecipe,
    RecipeLike,
    RecipeRating,
    RecipeReview,
    RecipeReviewHelpful,
    RecipeTranslation,
    DiscoveryCache
)
from apps.users.tests.factories import UserFactory


# ============================================================================
# CANONICAL RECIPE FACTORIES
# ============================================================================

class CanonicalRecipeFactory(DjangoModelFactory):
    """Factory for creating CanonicalRecipe instances."""
    
    class Meta:
        model = CanonicalRecipe
    
    name = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('paragraph', nb_sentences=3)
    source_type = 'ai_generated'
    
    base_ingredients = factory.LazyFunction(lambda: [
        {
            "name": "Chicken breast",
            "amount": 500,
            "unit": "g",
            "preparation": "diced"
        },
        {
            "name": "Olive oil",
            "amount": 2,
            "unit": "tbsp"
        },
        {
            "name": "Garlic",
            "amount": 3,
            "unit": "cloves",
            "preparation": "minced"
        }
    ])
    
    base_steps = factory.LazyFunction(lambda: [
        {
            "step_number": 1,
            "instruction": "Prepare all ingredients",
            "time_minutes": 10
        },
        {
            "step_number": 2,
            "instruction": "Cook the chicken in olive oil",
            "time_minutes": 15
        },
        {
            "step_number": 3,
            "instruction": "Add garlic and serve",
            "time_minutes": 5
        }
    ])
    
    cuisine = factory.Faker('random_element', elements=['Italian', 'Mexican', 'Chinese', 'Japanese', 'French'])
    difficulty = factory.Faker('random_element', elements=['beginner', 'intermediate', 'advanced'])
    diet_labels = factory.LazyFunction(lambda: ['high-protein', 'low-carb'])
    allergens = factory.LazyFunction(lambda: [])
    
    prep_time_minutes = 10
    cook_time_minutes = 20
    total_time_minutes = 30
    servings = 4
    
    recipe_hash = factory.Faker('sha256')
    
    total_saves = 0
    total_cooked = 0
    total_views = 0
    average_rating = 0
    total_ratings = 0
    total_reviews = 0
    
    is_published = True
    is_featured = False
    
    original_language = 'en'


class UserCreatedCanonicalRecipeFactory(CanonicalRecipeFactory):
    """Factory for user-created canonical recipes."""
    
    source_type = 'user_created'
    original_creator = factory.SubFactory(UserFactory)


class FeaturedCanonicalRecipeFactory(CanonicalRecipeFactory):
    """Factory for featured canonical recipes."""
    
    is_featured = True
    average_rating = factory.Faker('pydecimal', left_digits=1, right_digits=2, positive=True, min_value=4, max_value=5)
    total_ratings = factory.Faker('random_int', min=10, max=100)
    total_saves = factory.Faker('random_int', min=50, max=500)


# ============================================================================
# RECIPE (USER FORK) FACTORIES
# ============================================================================

class RecipeFactory(DjangoModelFactory):
    """Factory for creating standalone Recipe instances."""
    
    class Meta:
        model = Recipe
    
    name = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('paragraph', nb_sentences=2)
    
    ingredients = factory.LazyFunction(lambda: [
        {
            "name": "Tomatoes",
            "amount": 4,
            "unit": "pieces"
        },
        {
            "name": "Salt",
            "amount": 1,
            "unit": "tsp"
        }
    ])
    
    steps = factory.LazyFunction(lambda: [
        {
            "step_number": 1,
            "instruction": "Chop the tomatoes"
        },
        {
            "step_number": 2,
            "instruction": "Season with salt"
        }
    ])
    
    author = factory.Faker('name')
    created_by = factory.SubFactory(UserFactory)
    
    prep_time_minutes = 15
    cook_time_minutes = 25
    total_time_minutes = 40
    servings = 4
    difficulty = 'intermediate'
    cuisine = factory.Faker('random_element', elements=['Italian', 'Mexican', 'Chinese'])
    diet_labels = factory.LazyFunction(lambda: ['vegetarian'])
    allergens = factory.LazyFunction(lambda: [])
    
    is_fork = False
    version = 1
    is_latest_version = True
    
    times_added_to_lists = 0
    times_cooked = 0


class RecipeForkFactory(RecipeFactory):
    """Factory for creating forked Recipe instances."""
    
    canonical_recipe = factory.SubFactory(CanonicalRecipeFactory)
    is_fork = True
    
    user_modifications = factory.LazyFunction(lambda: {
        "servings": 6,
        "notes": "My personal version with extra spices"
    })


# ============================================================================
# USER RECIPE FACTORIES
# ============================================================================

class UserRecipeFactory(DjangoModelFactory):
    """Factory for UserRecipe (saved recipes) instances."""
    
    class Meta:
        model = UserRecipe
    
    user = factory.SubFactory(UserFactory)
    recipe = factory.SubFactory(RecipeFactory)
    
    notes = factory.Faker('sentence')
    rating = factory.Faker('random_int', min=1, max=5)
    times_cooked = factory.Faker('random_int', min=0, max=10)
    
    is_archived = False


class ArchivedUserRecipeFactory(UserRecipeFactory):
    """Factory for archived user recipes."""
    
    is_archived = True
    archived_at = factory.Faker('date_time_this_year')


# ============================================================================
# SOCIAL FEATURES FACTORIES
# ============================================================================

class RecipeLikeFactory(DjangoModelFactory):
    """Factory for RecipeLike instances."""
    
    class Meta:
        model = RecipeLike
    
    user = factory.SubFactory(UserFactory)
    canonical_recipe = factory.SubFactory(CanonicalRecipeFactory)


class RecipeRatingFactory(DjangoModelFactory):
    """Factory for RecipeRating instances."""
    
    class Meta:
        model = RecipeRating
    
    user = factory.SubFactory(UserFactory)
    canonical_recipe = factory.SubFactory(CanonicalRecipeFactory)
    rating = factory.Faker('random_int', min=1, max=5)


class RecipeReviewFactory(DjangoModelFactory):
    """Factory for RecipeReview instances."""
    
    class Meta:
        model = RecipeReview
    
    user = factory.SubFactory(UserFactory)
    canonical_recipe = factory.SubFactory(CanonicalRecipeFactory)
    
    title = factory.Faker('sentence', nb_words=5)
    content = factory.Faker('paragraph', nb_sentences=5)
    rating = factory.Faker('random_int', min=1, max=5)
    
    helpful_count = 0
    is_reported = False
    is_approved = True


class RecipeReviewHelpfulFactory(DjangoModelFactory):
    """Factory for RecipeReviewHelpful instances."""
    
    class Meta:
        model = RecipeReviewHelpful
    
    user = factory.SubFactory(UserFactory)
    review = factory.SubFactory(RecipeReviewFactory)


# ============================================================================
# TRANSLATION FACTORIES
# ============================================================================

class RecipeTranslationFactory(DjangoModelFactory):
    """Factory for RecipeTranslation instances."""
    
    class Meta:
        model = RecipeTranslation
    
    canonical_recipe = factory.SubFactory(CanonicalRecipeFactory)
    language = factory.Faker('random_element', elements=['en', 'ru', 'he'])
    
    name = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('paragraph', nb_sentences=2)
    
    base_ingredients = factory.LazyFunction(lambda: [
        {
            "name": "Translated ingredient",
            "amount": 100,
            "unit": "g"
        }
    ])
    
    base_steps = factory.LazyFunction(lambda: [
        {
            "step_number": 1,
            "instruction": "Translated step"
        }
    ])
    
    status = 'completed'


class PendingRecipeTranslationFactory(RecipeTranslationFactory):
    """Factory for pending translations."""
    
    status = 'pending'


class FailedRecipeTranslationFactory(RecipeTranslationFactory):
    """Factory for failed translations."""
    
    status = 'failed'
    error_message = factory.Faker('sentence')


# ============================================================================
# DISCOVERY CACHE FACTORIES
# ============================================================================

class DiscoveryCacheFactory(DjangoModelFactory):
    """Factory for DiscoveryCache instances."""
    
    class Meta:
        model = DiscoveryCache
    
    canonical_recipe = factory.SubFactory(CanonicalRecipeFactory)
    language = factory.Faker('random_element', elements=['en', 'ru', 'he'])
    
    title = factory.Faker('sentence', nb_words=4)
    brief = factory.Faker('text', max_nb_chars=200)
    image_url = factory.Faker('image_url')
    tags = factory.LazyFunction(lambda: ['italian', 'pasta', 'dinner'])





