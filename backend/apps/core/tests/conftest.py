"""
Pytest configuration and fixtures for core app tests
"""
import pytest
from apps.users.tests.conftest import api_client, authenticated_client, user  # noqa
from .factories import (  # noqa
    IngredientCacheFactory,
    IngredientTranslationFactory,
    CookingTermCacheFactory,
    CookingTermTranslationFactory,
    ImportHistoryFactory,
    TomatoIngredientFactory,
    ChoppingTermFactory,
    SuccessfulImportHistoryFactory,
    FailedImportHistoryFactory
)


@pytest.fixture
def ingredient():
    """Create a basic ingredient"""
    return IngredientCacheFactory()


@pytest.fixture
def ingredient_with_translations():
    """Create an ingredient with translations in all languages"""
    ingredient = TomatoIngredientFactory()
    IngredientTranslationFactory(
        ingredient=ingredient,
        language='en',
        name='Red Tomatoes',
        aliases=['tomato', 'red tomato', 'tomatoes']
    )
    IngredientTranslationFactory(
        ingredient=ingredient,
        language='ru',
        name='Помидоры красные',
        aliases=['помидор', 'томат']
    )
    IngredientTranslationFactory(
        ingredient=ingredient,
        language='he',
        name='עגבניות אדומות',
        aliases=['עגבנייה']
    )
    return ingredient


@pytest.fixture
def cooking_term():
    """Create a basic cooking term"""
    return CookingTermCacheFactory()


@pytest.fixture
def cooking_term_with_translations():
    """Create a cooking term with translations in all languages"""
    term = ChoppingTermFactory()
    CookingTermTranslationFactory(
        term=term,
        language_code='en',
        translation='chop',
        verification_status='human_verified'
    )
    CookingTermTranslationFactory(
        term=term,
        language_code='ru',
        translation='нарезать',
        verification_status='human_verified'
    )
    CookingTermTranslationFactory(
        term=term,
        language_code='he',
        translation='לחתוך',
        verification_status='human_verified'
    )
    return term





