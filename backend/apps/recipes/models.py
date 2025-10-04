from django.db import models
from django.db.models import Q
from apps.users.models import User
import uuid
import hashlib
import json


class Recipe(models.Model):
    """Recipe stored in RCIP format with versioning support"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # RCIP metadata
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

    # Deduplication & Versioning
    recipe_hash = models.CharField(max_length=64, db_index=True)
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
        ]
        unique_together = [['recipe_hash', 'version']]

    def __str__(self):
        return f"{self.name} (v{self.version})"

    def save(self, *args, **kwargs):
        # Calculate recipe hash for deduplication
        if not self.recipe_hash:
            self.recipe_hash = self.calculate_recipe_hash()

        # Handle versioning
        if not self.pk:  # New recipe
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

    def to_rcip_format(self):
        """Export recipe in full RCIP format"""
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



