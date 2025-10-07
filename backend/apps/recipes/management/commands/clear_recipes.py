"""
Management command to clear all recipes from the database

Usage:
    python manage.py clear_recipes
"""

from django.core.management.base import BaseCommand
from apps.recipes.models import (
    Recipe, CanonicalRecipe, RecipeLike,
    RecipeRating, RecipeReview, RecipeReviewHelpful
)


class Command(BaseCommand):
    help = 'Clear all recipes and related data from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion without prompting',
        )

    def handle(self, *args, **options):
        # Count existing data
        recipe_count = Recipe.objects.count()
        canonical_count = CanonicalRecipe.objects.count()
        like_count = RecipeLike.objects.count()
        rating_count = RecipeRating.objects.count()
        review_count = RecipeReview.objects.count()
        helpful_count = RecipeReviewHelpful.objects.count()

        self.stdout.write(self.style.WARNING('\nCurrent Database Status:'))
        self.stdout.write(f'  - Recipes (user forks): {recipe_count}')
        self.stdout.write(f'  - Canonical Recipes: {canonical_count}')
        self.stdout.write(f'  - Likes: {like_count}')
        self.stdout.write(f'  - Ratings: {rating_count}')
        self.stdout.write(f'  - Reviews: {review_count}')
        self.stdout.write(f'  - Helpful marks: {helpful_count}')
        self.stdout.write('')

        if recipe_count == 0 and canonical_count == 0:
            self.stdout.write(self.style.SUCCESS('Database is already empty!'))
            return

        # Confirm deletion
        if not options['confirm']:
            confirm = input(
                'Are you sure you want to delete ALL recipes? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING(
                    'Cancelled. No data was deleted.'))
                return

        self.stdout.write(self.style.WARNING('\nDeleting all recipe data...'))

        try:
            # Delete in correct order (respect foreign keys)

            # 1. Delete helpful marks (references reviews)
            deleted_helpful = RecipeReviewHelpful.objects.all().delete()[0]
            self.stdout.write(
                f'  [OK] Deleted {deleted_helpful} helpful marks')

            # 2. Delete reviews (references canonical recipes)
            deleted_reviews = RecipeReview.objects.all().delete()[0]
            self.stdout.write(f'  [OK] Deleted {deleted_reviews} reviews')

            # 3. Delete ratings (references canonical recipes)
            deleted_ratings = RecipeRating.objects.all().delete()[0]
            self.stdout.write(f'  [OK] Deleted {deleted_ratings} ratings')

            # 4. Delete likes (references canonical recipes)
            deleted_likes = RecipeLike.objects.all().delete()[0]
            self.stdout.write(f'  [OK] Deleted {deleted_likes} likes')

            # 5. Delete recipes (user forks, may reference canonical)
            deleted_recipes = Recipe.objects.all().delete()[0]
            self.stdout.write(f'  [OK] Deleted {deleted_recipes} user recipes')

            # 6. Delete canonical recipes
            deleted_canonical = CanonicalRecipe.objects.all().delete()[0]
            self.stdout.write(
                f'  [OK] Deleted {deleted_canonical} canonical recipes')

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(
                'All recipe data deleted successfully!'))
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(
                'Database is now clean. Ready for fresh recipes!'))

        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'Error deleting data: {e}'))
            import traceback
            traceback.print_exc()
