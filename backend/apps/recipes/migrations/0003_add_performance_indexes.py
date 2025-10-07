"""
Performance optimization migration - Add database indexes

Indexes added:
- CanonicalRecipe: source_type, cuisine, difficulty, is_published, created_at
- CanonicalRecipe: Composite indexes for common queries
- RecipeReview: canonical_recipe + created_at (for sorting)
- RecipeLike, RecipeRating: user + canonical_recipe (for user lookups)
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_add_canonical_recipes_and_social_features'),
    ]

    operations = [
        # CanonicalRecipe indexes for filtering and sorting
        migrations.AddIndex(
            model_name='canonicalrecipe',
            index=models.Index(fields=['source_type'],
                               name='recipes_can_source_idx'),
        ),
        migrations.AddIndex(
            model_name='canonicalrecipe',
            index=models.Index(fields=['cuisine'],
                               name='recipes_can_cuisine_idx'),
        ),
        migrations.AddIndex(
            model_name='canonicalrecipe',
            index=models.Index(fields=['difficulty'],
                               name='recipes_can_diff_idx'),
        ),
        migrations.AddIndex(
            model_name='canonicalrecipe',
            index=models.Index(fields=['is_published'],
                               name='recipes_can_pub_idx'),
        ),
        migrations.AddIndex(
            model_name='canonicalrecipe',
            index=models.Index(fields=['-created_at'],
                               name='recipes_can_created_idx'),
        ),

        # Composite indexes for common query patterns
        migrations.AddIndex(
            model_name='canonicalrecipe',
            index=models.Index(
                fields=['is_published', '-average_rating'],
                name='recipes_can_pub_rating_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='canonicalrecipe',
            index=models.Index(
                fields=['is_published', '-total_saves'],
                name='recipes_can_pub_saves_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='canonicalrecipe',
            index=models.Index(
                fields=['is_published', '-total_cooked'],
                name='recipes_can_pub_cooked_idx'
            ),
        ),

        # Review indexes for sorting and filtering
        migrations.AddIndex(
            model_name='recipereview',
            index=models.Index(
                fields=['canonical_recipe', '-created_at'],
                name='recipes_rev_recipe_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='recipereview',
            index=models.Index(
                fields=['canonical_recipe', '-helpful_count'],
                name='recipes_rev_recipe_help_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='recipereview',
            index=models.Index(
                fields=['canonical_recipe', '-rating'],
                name='recipes_rev_recipe_rating_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='recipereview',
            index=models.Index(
                fields=['is_approved'],
                name='recipes_rev_approved_idx'
            ),
        ),

        # User lookup indexes for social features
        migrations.AddIndex(
            model_name='recipelike',
            index=models.Index(
                fields=['user', 'canonical_recipe'],
                name='recipes_like_user_recipe_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='reciperating',
            index=models.Index(
                fields=['user', 'canonical_recipe'],
                name='recipes_rate_user_recipe_idx'
            ),
        ),

        # Recipe fork indexes
        migrations.AddIndex(
            model_name='recipe',
            index=models.Index(
                fields=['created_by', 'is_fork'],
                name='recipes_rec_user_fork_idx'
            ),
        ),
    ]

