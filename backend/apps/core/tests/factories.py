"""
Test data factories for core app models
"""
import factory
from factory.django import DjangoModelFactory
from apps.core.models import (
    IngredientCache,
    IngredientTranslation,
    CookingTermCache,
    CookingTermTranslation,
    ImportHistory
)


class IngredientCacheFactory(DjangoModelFactory):
    """Factory for IngredientCache model"""
    
    class Meta:
        model = IngredientCache
    
    ingredient_key = factory.Faker('slug')
    category = factory.Faker('random_element', elements=['vegetables', 'fruits', 'meat', 'dairy', 'grains'])
    source = factory.Faker('random_element', elements=['usda', 'openfoodfacts', 'brave'])
    common_units = factory.LazyFunction(lambda: {
        'weight': ['g', 'kg'],
        'volume': ['ml', 'L'],
        'count': ['pcs']
    })
    unit_conversions = factory.LazyFunction(lambda: {
        '1_pcs': '150g',
        '1_cup': '180g'
    })
    shelf_life = factory.LazyFunction(lambda: {
        'room_temperature': 2,
        'refrigerator': 7,
        'freezer': 180
    })
    storage_recommendations = factory.LazyFunction(lambda: {
        'recommended': 'refrigerator',
        'temperature_range': '4-10°C'
    })
    nutrition_per_100g = factory.LazyFunction(lambda: {
        'calories': 18,
        'protein': 0.9,
        'fat': 0.2,
        'carbs': 3.9
    })
    metadata = factory.LazyFunction(dict)
    typical_amount_min = factory.Faker('pyint', min_value=10, max_value=50)
    typical_amount_max = factory.Faker('pyint', min_value=200, max_value=500)
    typical_amount_avg = factory.Faker('pyint', min_value=100, max_value=200)
    max_per_serving = factory.Faker('pyint', min_value=300, max_value=1000)
    warning_threshold = factory.Faker('pyint', min_value=500, max_value=2000)


class IngredientTranslationFactory(DjangoModelFactory):
    """Factory for IngredientTranslation model"""
    
    class Meta:
        model = IngredientTranslation
    
    ingredient = factory.SubFactory(IngredientCacheFactory)
    language = factory.Faker('random_element', elements=['en', 'ru', 'he'])
    name = factory.Faker('word')
    description = factory.Faker('sentence')
    aliases = factory.LazyFunction(lambda: ['alias1', 'alias2'])
    storage_tips = factory.Faker('text', max_nb_chars=200)


class CookingTermCacheFactory(DjangoModelFactory):
    """Factory for CookingTermCache model"""
    
    class Meta:
        model = CookingTermCache
    
    term_english = factory.Faker('word')
    term_english_normalized = factory.LazyAttribute(lambda obj: obj.term_english.lower())
    term_type = factory.Faker('random_element', elements=['technique', 'tool', 'ingredient', 'method'])
    category = factory.Faker('random_element', elements=['heat_method', 'cutting_method', 'mixing_method'])
    definition = factory.Faker('text', max_nb_chars=200)
    usage_frequency = factory.Faker('random_element', elements=['very_common', 'common', 'uncommon', 'rare'])
    difficulty_level = factory.Faker('random_element', elements=['beginner', 'intermediate', 'advanced'])
    confidence_score = factory.Faker('pyint', min_value=50, max_value=100)
    verified = factory.Faker('boolean', chance_of_getting_true=80)


class CookingTermTranslationFactory(DjangoModelFactory):
    """Factory for CookingTermTranslation model"""
    
    class Meta:
        model = CookingTermTranslation
    
    term = factory.SubFactory(CookingTermCacheFactory)
    language_code = factory.Faker('random_element', elements=['en', 'ru', 'he'])
    translation = factory.Faker('word')
    verification_status = factory.Faker('random_element', elements=['unverified', 'ai_verified', 'web_verified', 'human_verified'])
    alternative_translations = factory.LazyFunction(lambda: ['alt1'])
    cultural_notes = factory.Faker('text', max_nb_chars=100)
    source = factory.Faker('random_element', elements=['gemini', 'groq', 'web', 'manual'])
    confidence_score = factory.Faker('pyint', min_value=60, max_value=100)


class ImportHistoryFactory(DjangoModelFactory):
    """Factory for ImportHistory model"""
    
    class Meta:
        model = ImportHistory
    
    import_type = factory.Faker('random_element', elements=['iml', 'cooklingo', 'iml_delete', 'cooklingo_delete'])
    source_file = factory.Faker('file_name', extension='db')
    records_imported = factory.Faker('pyint', min_value=0, max_value=1000)
    records_updated = factory.Faker('pyint', min_value=0, max_value=500)
    records_failed = factory.Faker('pyint', min_value=0, max_value=50)
    imported_by = factory.Faker('user_name')
    status = factory.Faker('random_element', elements=['success', 'partial', 'failed'])
    error_log = factory.Faker('text', max_nb_chars=500)
    summary = factory.LazyFunction(dict)


# Trait factories for specific scenarios
class TomatoIngredientFactory(IngredientCacheFactory):
    """Pre-configured tomato ingredient"""
    ingredient_key = 'tomatoes-red-ripe'
    category = 'vegetables'
    source = 'usda'
    nutrition_per_100g = factory.LazyFunction(lambda: {
        'calories': 18,
        'protein': 0.9,
        'fat': 0.2,
        'carbs': 3.9
    })


class ChoppingTermFactory(CookingTermCacheFactory):
    """Pre-configured chopping cooking term"""
    term_english = 'chop'
    term_english_normalized = 'chop'
    term_type = 'technique'
    category = 'cutting_method'
    definition = 'Cut food into small pieces'
    usage_frequency = 'very_common'
    difficulty_level = 'beginner'
    verified = True


class SuccessfulImportHistoryFactory(ImportHistoryFactory):
    """Pre-configured successful import"""
    status = 'success'
    records_failed = 0
    error_log = ''


class FailedImportHistoryFactory(ImportHistoryFactory):
    """Pre-configured failed import"""
    status = 'failed'
    records_imported = 0
    records_updated = 0
    records_failed = factory.Faker('pyint', min_value=50, max_value=1000)
    error_log = factory.Faker('text', max_nb_chars=1000)

