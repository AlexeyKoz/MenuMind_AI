from django.db import models
from django.db.models import Q, Avg, Count
from apps.users.models import User
import uuid
import hashlib
import json


class CanonicalRecipe(models.Model):
    """
    Global master recipe - one per unique dish.
    Represents the canonical/official version that serves as source of truth.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)

    # Source tracking
    SOURCE_TYPE_CHOICES = [
        ('ai_generated', 'AI Generated'),
        ('user_created', 'User Created'),
        ('community_curated', 'Community Curated')
    ]
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE_CHOICES,
        default='ai_generated'
    )
    ai_source_url = models.URLField(blank=True, null=True)
    original_creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='canonical_recipes_created'
    )

    # Recipe content (RCIP format)
    base_ingredients = models.JSONField(default=list)
    base_steps = models.JSONField(default=list)

    # Metadata
    cuisine = models.CharField(max_length=100, blank=True)
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        default='intermediate'
    )
    diet_labels = models.JSONField(default=list)
    prep_time_minutes = models.IntegerField(null=True, blank=True)
    cook_time_minutes = models.IntegerField(null=True, blank=True)
    total_time_minutes = models.IntegerField(null=True, blank=True)
    servings = models.IntegerField(default=4)

    # Deduplication
    recipe_hash = models.CharField(max_length=64, db_index=True, unique=True)

    # Aggregated statistics (denormalized for performance)
    total_saves = models.IntegerField(default=0)
    total_cooked = models.IntegerField(default=0)
    total_views = models.IntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0)
    total_ratings = models.IntegerField(default=0)
    total_reviews = models.IntegerField(default=0)

    # Publication settings
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



    # ... existing fields ...
    
    # ============================================================================
    # MULTILINGUAL SUPPORT (NEW - v2.0)
    # ============================================================================
    
    title_translations = models.JSONField(
        default=dict,
        blank=True,
        help_text='Translations: {en: "Ukrainian Borscht", ru: "Украинский борщ", he: "בורשט אוקראיני"}'
    )
    
    description_translations = models.JSONField(
        default=dict,
        blank=True,
        help_text='Description translations for each language'
    )
    
    steps_translations = models.JSONField(
        default=dict,
        blank=True,
        help_text='Steps translations: {en: [{step_number: 1, instruction: "..."}], ru: [...], he: [...]}'
    )
    
    nutrition_per_serving = models.JSONField(
        default=dict,
        blank=True,
        help_text='Nutrition calculated from IML: {calories: 380, protein: 26, fat: 15, carbs: 32, fiber: 4}'
    )
    
    original_language = models.CharField(
        max_length=2,
        choices=[('en', 'English'), ('ru', 'Russian'), ('he', 'Hebrew')],
        default='en',
        help_text='Language in which recipe was originally created'
    )
    
    # ... existing Meta, methods ...



    class Meta:
        db_table = 'canonical_recipes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name', 'recipe_hash']),
            models.Index(fields=['source_type']),
            models.Index(fields=['-average_rating', '-total_saves']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"

    def update_statistics(self):
        """Update denormalized statistics from related objects"""
        # Update ratings
        rating_stats = self.ratings.aggregate(
            avg=Avg('rating'),
            count=Count('id')
        )
        self.average_rating = rating_stats['avg'] or 0
        self.total_ratings = rating_stats['count']

        # Update reviews count
        self.total_reviews = self.reviews.filter(is_approved=True).count()

        # Update saves (forks count)
        self.total_saves = self.user_forks.count()

        self.save(update_fields=['average_rating',
                  'total_ratings', 'total_reviews', 'total_saves'])

    def to_rcip_format(self):
        """Export canonical recipe in RCIP format"""
        return {
            "rcip_version": "0.1",
            "id": f"canonical-{self.id}",
            "meta": {
                "name": self.name,
                "description": self.description,
                "source_type": self.source_type,
                "source_url": self.ai_source_url,
                "difficulty": self.difficulty,
                "servings": {
                    "amount": self.servings,
                    "unit": "portions",
                    "adjustable": True
                },
                "prep_time_minutes": self.prep_time_minutes,
                "cook_time_minutes": self.cook_time_minutes,
                "total_time_minutes": self.total_time_minutes,
                "keywords": [self.cuisine] if self.cuisine else [],
                "diet_labels": self.diet_labels
            },
            "ingredients": self.base_ingredients,
            "steps": self.base_steps,
            "extensions": {
                "canonical_id": str(self.id),
                "total_saves": self.total_saves,
                "total_cooked": self.total_cooked,
                "average_rating": float(self.average_rating)
            }
        }


class Recipe(models.Model):
    """
    User's personal recipe copy (fork) with modifications.
    Can also be standalone recipe (when canonical_recipe is None).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to canonical recipe (NEW - for fork system)
    canonical_recipe = models.ForeignKey(
        CanonicalRecipe,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='user_forks'
    )
    is_fork = models.BooleanField(default=False)

    # User modifications (delta storage for forks)
    user_modifications = models.JSONField(default=dict, blank=True)
    # Example structure:
    # {
    #   "ingredients_changed": [{"name": "bacon", "original_amount": 200, "new_amount": 400}],
    #   "steps_changed": {2: "Modified step text"},
    #   "notes": "My personal twist - extra garlic!",
    #   "servings": 6  // override
    # }
   
    # ... existing fields ...
    
    # ============================================================================
    # MULTILINGUAL SUPPORT (NEW - v2.0)
    # ============================================================================
    
    title_translations = models.JSONField(
        default=dict,
        blank=True,
        help_text='Title translations if user renames fork: {en: "...", ru: "...", he: "..."}'
    )
    
    # ... existing Meta, methods ...
    # RCIP metadata (kept for standalone recipes)
    rcip_version = models.CharField(max_length=10, default="0.1")
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)

    # Recipe content (stored as JSON in RCIP format)
    ingredients = models.JSONField(default=list)
    steps = models.JSONField(default=list)

    # Source & Attribution
    author = models.CharField(max_length=200, blank=True)
    source_url = models.URLField(blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_recipes'
    )

    # Recipe metadata
    prep_time_minutes = models.IntegerField(null=True, blank=True)
    cook_time_minutes = models.IntegerField(null=True, blank=True)
    total_time_minutes = models.IntegerField(null=True, blank=True)
    servings = models.IntegerField(default=4)
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        default='intermediate'
    )
    cuisine = models.CharField(max_length=100, blank=True)
    diet_labels = models.JSONField(default=list)

    # Deduplication & Versioning (kept for legacy support)
    recipe_hash = models.CharField(
        max_length=64, db_index=True, null=True, blank=True)
    version = models.IntegerField(default=1)
    parent_recipe = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='versions'
    )
    is_latest_version = models.BooleanField(default=True)

    # Statistics
    times_added_to_lists = models.IntegerField(default=0)
    times_cooked = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recipes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name', 'recipe_hash']),
            models.Index(fields=['created_by', '-created_at']),
            models.Index(fields=['is_latest_version']),
            models.Index(fields=['canonical_recipe', 'is_fork']),
        ]
        unique_together = [['recipe_hash', 'version']]

    def __str__(self):
        if self.is_fork and self.canonical_recipe:
            return f"{self.name} (fork of {self.canonical_recipe.name})"
        return f"{self.name} (v{self.version})"

    def save(self, *args, **kwargs):
        # Calculate recipe hash for deduplication (for non-forks)
        if not self.recipe_hash and not self.is_fork:
            self.recipe_hash = self.calculate_recipe_hash()

        # Handle versioning (for non-forks)
        if not self.pk and not self.is_fork:  # New recipe
            existing = Recipe.objects.filter(
                recipe_hash=self.recipe_hash
            ).order_by('-version').first()

            if existing:
                # This is a duplicate - create new version
                self.parent_recipe = existing.parent_recipe or existing
                self.version = existing.version + 1

                # Mark old versions as not latest
                Recipe.objects.filter(
                    recipe_hash=self.recipe_hash
                ).update(is_latest_version=False)

        super().save(*args, **kwargs)

    def calculate_recipe_hash(self):
        """Calculate hash based on recipe content for deduplication"""
        # Normalize recipe name (lowercase, remove extra spaces)
        normalized_name = ' '.join(self.name.lower().split())

        # Sort ingredients by name for consistent hashing
        sorted_ingredients = sorted(
            [ing.get('name', '').lower() for ing in self.ingredients]
        )

        # Create hash string
        hash_string = f"{normalized_name}:{','.join(sorted_ingredients)}"

        return hashlib.sha256(hash_string.encode()).hexdigest()

    def get_effective_recipe(self):
        """
        Merge canonical recipe with user modifications.
        Returns the final recipe data that should be displayed to user.
        """
        if not self.is_fork or not self.canonical_recipe:
            # Standalone recipe - return own data
            return {
                'name': self.name,
                'description': self.description,
                'ingredients': self.ingredients,
                'steps': self.steps,
                'servings': self.servings,
                'prep_time_minutes': self.prep_time_minutes,
                'cook_time_minutes': self.cook_time_minutes,
                'total_time_minutes': self.total_time_minutes,
                'difficulty': self.difficulty,
                'cuisine': self.cuisine,
                'diet_labels': self.diet_labels,
            }

        # Fork - merge canonical with modifications
        canonical = self.canonical_recipe
        mods = self.user_modifications

        # Start with canonical data
        result = {
            'name': canonical.name,
            'description': canonical.description,
            'ingredients': list(canonical.base_ingredients),  # Copy
            'steps': list(canonical.base_steps),  # Copy
            'servings': canonical.servings,
            'prep_time_minutes': canonical.prep_time_minutes,
            'cook_time_minutes': canonical.cook_time_minutes,
            'total_time_minutes': canonical.total_time_minutes,
            'difficulty': canonical.difficulty,
            'cuisine': canonical.cuisine,
            'diet_labels': list(canonical.diet_labels),
        }

        # Apply user modifications
        if 'ingredients_changed' in mods:
            for change in mods['ingredients_changed']:
                # Find ingredient and update
                for ing in result['ingredients']:
                    if ing.get('name') == change.get('name'):
                        ing.update(change.get('new_data', {}))

        if 'steps_changed' in mods:
            for step_idx, new_text in mods['steps_changed'].items():
                idx = int(step_idx)
                if 0 <= idx < len(result['steps']):
                    result['steps'][idx]['instruction'] = new_text

        # Override fields if present in modifications
        for field in ['servings', 'prep_time_minutes', 'cook_time_minutes', 'total_time_minutes']:
            if field in mods:
                result[field] = mods[field]

        # Add user notes
        if 'notes' in mods:
            result['user_notes'] = mods['notes']

        return result

    def to_rcip_format(self):
        """Export recipe in full RCIP format"""
        if self.is_fork and self.canonical_recipe:
            # Export effective recipe (merged)
            effective = self.get_effective_recipe()
            return {
                "rcip_version": self.rcip_version,
                "id": f"fork-{self.id}",
                "meta": {
                    "name": effective['name'],
                    "description": effective['description'],
                    "author": self.canonical_recipe.original_creator.username if self.canonical_recipe.original_creator else '',
                    "created_date": self.created_at.isoformat(),
                    "source_url": self.canonical_recipe.ai_source_url,
                    "difficulty": effective['difficulty'],
                    "servings": {
                        "amount": effective['servings'],
                        "unit": "portions",
                        "adjustable": True
                    },
                    "prep_time_minutes": effective['prep_time_minutes'],
                    "cook_time_minutes": effective['cook_time_minutes'],
                    "total_time_minutes": effective['total_time_minutes'],
                    "keywords": [effective['cuisine']] if effective['cuisine'] else [],
                    "diet_labels": effective['diet_labels']
                },
                "ingredients": effective['ingredients'],
                "steps": effective['steps'],
                "extensions": {
                    "is_fork": True,
                    "canonical_id": str(self.canonical_recipe.id),
                    "user_modifications": self.user_modifications,
                    "times_cooked": self.times_cooked,
                }
            }

        # Standalone recipe
        return {
            "rcip_version": self.rcip_version,
            "id": f"rcip-{self.id}",
            "meta": {
                "name": self.name,
                "description": self.description,
                "author": self.author,
                "created_date": self.created_at.isoformat(),
                "source_url": self.source_url,
                "difficulty": self.difficulty,
                "servings": {
                    "amount": self.servings,
                    "unit": "portions",
                    "adjustable": True
                },
                "prep_time_minutes": self.prep_time_minutes,
                "cook_time_minutes": self.cook_time_minutes,
                "total_time_minutes": self.total_time_minutes,
                "keywords": [self.cuisine] if self.cuisine else [],
                "diet_labels": self.diet_labels
            },
            "ingredients": self.ingredients,
            "steps": self.steps,
            "extensions": {
                "version": self.version,
                "times_cooked": self.times_cooked,
                "parent_recipe_id": str(self.parent_recipe.id) if self.parent_recipe else None
            }
        }


class UserRecipe(models.Model):
    """Track which recipes users have saved/cooked"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='saved_recipes')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='saved_by_users')

    # User customizations
    notes = models.TextField(blank=True)
    rating = models.IntegerField(null=True, blank=True, choices=[
                                (i, i) for i in range(1, 6)])
    times_cooked = models.IntegerField(default=0)
    last_cooked = models.DateTimeField(null=True, blank=True)

    # Archive functionality
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_recipes'
        unique_together = [['user', 'recipe']]
        indexes = [
            models.Index(fields=['user', '-saved_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


# ============================================================================
# SOCIAL FEATURES MODELS
# ============================================================================

class RecipeLike(models.Model):
    """Simple like/heart system for canonical recipes"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipe_likes')
    canonical_recipe = models.ForeignKey(
        CanonicalRecipe,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recipe_likes'
        unique_together = [['user', 'canonical_recipe']]
        indexes = [
            models.Index(fields=['canonical_recipe', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} likes {self.canonical_recipe.name}"


class RecipeRating(models.Model):
    """5-star rating system for canonical recipes"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipe_ratings')
    canonical_recipe = models.ForeignKey(
        CanonicalRecipe,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recipe_ratings'
        unique_together = [['user', 'canonical_recipe']]
        indexes = [
            models.Index(fields=['canonical_recipe', '-rating']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} rated {self.canonical_recipe.name}: {self.rating}/5"


class RecipeReview(models.Model):
    """Detailed reviews with text content for canonical recipes"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipe_reviews')
    canonical_recipe = models.ForeignKey(
        CanonicalRecipe,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])

    # Social engagement
    helpful_count = models.IntegerField(default=0)

    # Moderation
    is_reported = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recipe_reviews'
        unique_together = [['user', 'canonical_recipe']]
        indexes = [
            models.Index(fields=['canonical_recipe', '-helpful_count']),
            models.Index(fields=['canonical_recipe', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username}'s review of {self.canonical_recipe.name}"


class RecipeReviewHelpful(models.Model):
    """Track who marked reviews as helpful"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='helpful_reviews')
    review = models.ForeignKey(
        RecipeReview, on_delete=models.CASCADE, related_name='marked_helpful_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recipe_review_helpful'
        unique_together = [['user', 'review']]
        indexes = [
            models.Index(fields=['review', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} found review helpful"
