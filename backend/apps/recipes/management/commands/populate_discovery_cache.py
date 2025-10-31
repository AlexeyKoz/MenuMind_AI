"""
Management command to populate discovery cache for existing recipes
"""
from django.core.management.base import BaseCommand
from apps.recipes.models import CanonicalRecipe, DiscoveryCache


class Command(BaseCommand):
    help = 'Populate discovery cache for all published canonical recipes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate cache entries even if they exist',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        self.stdout.write('[INFO] Starting discovery cache population...')
        
        # Get all published recipes
        recipes = CanonicalRecipe.objects.filter(is_published=True)
        total_recipes = recipes.count()
        
        self.stdout.write(f'[INFO] Found {total_recipes} published recipes')
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for idx, recipe in enumerate(recipes, 1):
            self.stdout.write(f'[{idx}/{total_recipes}] Processing: {recipe.name}')
            
            # Create cache entry for each supported language
            for lang in ['en', 'he', 'ru']:
                if force:
                    # Delete and recreate
                    DiscoveryCache.objects.filter(
                        canonical_recipe=recipe,
                        language=lang
                    ).delete()
                
                cache_entry, created = DiscoveryCache.objects.get_or_create(
                    canonical_recipe=recipe,
                    language=lang,
                    defaults={
                        'title': recipe.name,
                        'brief': (recipe.description[:200] if recipe.description else ''),
                        'image_url': recipe.ai_source_url or '',
                        'tags': recipe.diet_labels or []
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'  [OK] Created cache entry for {lang}')
                elif force:
                    updated_count += 1
                    self.stdout.write(f'  [UPDATE] Updated cache entry for {lang}')
                else:
                    skipped_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'\n[SUCCESS] Discovery cache population complete!\n'
            f'   Created: {created_count}\n'
            f'   Updated: {updated_count}\n'
            f'   Skipped: {skipped_count}\n'
            f'   Total recipes processed: {total_recipes}'
        ))

