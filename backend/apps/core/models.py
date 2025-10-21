"""
Core models for ingredient management and IML integration
"""
from django.db import models


class IngredientCache(models.Model):
    """Cached ingredients from IML SQLite"""

    ingredient_key = models.CharField(
        max_length=200,
        unique=True,
        db_index=True,
        help_text='Unique ingredient key from IML (e.g., tomatoes-red-ripe)'
    )
    category = models.CharField(max_length=50, blank=True)
    source = models.CharField(
        max_length=50,
        help_text='Data source: usda, openfoodfacts, brave'
    )

    # IML data
    common_units = models.JSONField(
        default=dict,
        help_text='Common units by type: {weight: [g, kg], volume: [ml, L], count: [pcs]}'
    )

    unit_conversions = models.JSONField(
        default=dict,
        help_text='Unit conversions: {1_pcs: 150g, 1_cup: 180g}'
    )

    shelf_life = models.JSONField(
        default=dict,
        help_text='Shelf life in days: {room_temperature: 2, refrigerator: 7, freezer: 180}'
    )

    storage_recommendations = models.JSONField(
        default=dict,
        help_text='Storage recommendations: {recommended: refrigerator, temperature_range: 4-10°C}'
    )

    nutrition_per_100g = models.JSONField(
        default=dict,
        help_text='Nutrition per 100g: {calories: 18, protein: 0.9, fat: 0.2, carbs: 3.9, ...}'
    )

    metadata = models.JSONField(
        default=dict,
        help_text='Full IML data for reference'
    )

    last_synced = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ingredients_cache'
        verbose_name = 'Ingredient Cache'
        verbose_name_plural = 'Ingredient Cache'
        indexes = [
            models.Index(fields=['ingredient_key']),
            models.Index(fields=['category']),
            models.Index(fields=['source']),
        ]

    def __str__(self):
        return f"{self.ingredient_key} ({self.source})"


class IngredientTranslation(models.Model):
    """Translations for ingredients from IML"""

    ingredient = models.ForeignKey(
        IngredientCache,
        on_delete=models.CASCADE,
        related_name='translations'
    )

    language = models.CharField(
        max_length=2,
        choices=[('en', 'English'), ('ru', 'Russian'), ('he', 'Hebrew')]
    )

    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)
    aliases = models.JSONField(
        default=list,
        help_text='Alternative names: [tomato, red tomato]'
    )

    storage_tips = models.TextField(blank=True)

    class Meta:
        db_table = 'ingredient_translations'
        verbose_name = 'Ingredient Translation'
        verbose_name_plural = 'Ingredient Translations'
        unique_together = [['ingredient', 'language']]
        indexes = [
            models.Index(fields=['language', 'name']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.ingredient.ingredient_key} - {self.language}: {self.name}"


class CookingTermCache(models.Model):
    """Cached cooking terms from CookLingo SQLite"""

    term_english = models.CharField(
        max_length=200,
        unique=True,
        db_index=True,
        help_text='English cooking term'
    )
    term_english_normalized = models.CharField(
        max_length=200,
        db_index=True,
        help_text='Normalized English term for matching'
    )
    term_type = models.CharField(
        max_length=50,
        blank=True,
        help_text='Type of term: technique, tool, ingredient, method, etc.'
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text='Category: heat_method, cutting_method, mixing_method, etc.'
    )
    definition = models.TextField(
        blank=True,
        help_text='Definition of the cooking term'
    )
    usage_frequency = models.CharField(
        max_length=20,
        blank=True,
        help_text='How common: very_common, common, uncommon, rare'
    )
    difficulty_level = models.CharField(
        max_length=20,
        blank=True,
        help_text='Skill level: beginner, intermediate, advanced'
    )
    confidence_score = models.IntegerField(
        default=0,
        help_text='Translation confidence (0-100)'
    )
    verified = models.BooleanField(
        default=False,
        help_text='Whether translation has been verified'
    )

    last_synced = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cooking_terms_cache'
        verbose_name = 'Cooking Term'
        verbose_name_plural = 'Cooking Terms'
        indexes = [
            models.Index(fields=['term_english']),
            models.Index(fields=['term_english_normalized']),
            models.Index(fields=['category']),
            models.Index(fields=['term_type']),
        ]

    def __str__(self):
        return f"{self.term_english} ({self.category})"


class CookingTermTranslation(models.Model):
    """Translations for cooking terms from CookLingo"""

    term = models.ForeignKey(
        CookingTermCache,
        on_delete=models.CASCADE,
        related_name='translations'
    )

    language_code = models.CharField(
        max_length=2,
        choices=[('en', 'English'), ('ru', 'Russian'), ('he', 'Hebrew')]
    )

    translation = models.CharField(
        max_length=200,
        db_index=True,
        help_text='Translated term'
    )

    verification_status = models.CharField(
        max_length=20,
        default='unverified',
        help_text='Verification status: unverified, ai_verified, web_verified, human_verified'
    )

    alternative_translations = models.JSONField(
        default=list,
        help_text='Alternative translations: [alt1, alt2]'
    )

    cultural_notes = models.TextField(
        blank=True,
        help_text='Cultural or usage notes for this translation'
    )

    source = models.CharField(
        max_length=50,
        blank=True,
        help_text='Translation source: gemini, groq, web, manual'
    )

    confidence_score = models.IntegerField(
        default=0,
        help_text='Translation confidence (0-100)'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cooking_term_translations'
        verbose_name = 'Cooking Term Translation'
        verbose_name_plural = 'Cooking Term Translations'
        unique_together = [['term', 'language_code']]
        indexes = [
            models.Index(fields=['language_code', 'translation']),
            models.Index(fields=['translation']),
        ]

    def __str__(self):
        return f"{self.term.term_english} -> {self.language_code}: {self.translation}"
