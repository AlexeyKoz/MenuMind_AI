"""
Management command to import CookLingo terms from JSON export file
Usage: python manage.py import_cooklingo_json
"""
from django.core.management.base import BaseCommand
from apps.core.models import CookingTermCache, CookingTermTranslation
import json
import os


class Command(BaseCommand):
    help = 'Import cooking terms from CookLingo JSON export file'

    def handle(self, *args, **options):
        # Try multiple possible paths
        possible_paths = [
            'backend/data/cooklingo_export.json',
            'data/cooklingo_export.json',
            '/app/backend/data/cooklingo_export.json',
            '/app/data/cooklingo_export.json',
        ]
        
        json_file = None
        for path in possible_paths:
            if os.path.exists(path):
                json_file = path
                break
        
        if not json_file:
            self.stdout.write(self.style.ERROR(f'File not found. Tried: {possible_paths}'))
            return

        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('COOKLINGO JSON IMPORT'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

        # Load JSON data
        self.stdout.write('Loading JSON file...')
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cooking_terms = data.get('cooking_terms', [])
        translations = data.get('cooking_term_translations', [])  # Fixed key name
        
        total_terms = len(cooking_terms)
        total_translations = len(translations)
        
        self.stdout.write(f'Found {total_terms} cooking terms in JSON file')
        self.stdout.write(f'Found {total_translations} translations in JSON file\n')
        self.stdout.write('[START] Importing cooking terms...\n')

        created_count = 0
        updated_count = 0
        error_count = 0

        # Import cooking terms
        for idx, term_data in enumerate(cooking_terms, 1):
            if idx % 100 == 0:
                self.stdout.write(f'Progress: {idx}/{total_terms} ({(idx/total_terms)*100:.1f}%)')

            try:
                term_english = term_data.get('term_english', '')
                if not term_english:
                    error_count += 1
                    continue

                # Create or update CookingTermCache
                term, created = CookingTermCache.objects.update_or_create(
                    term_english=term_english,
                    defaults={
                        'term_english_normalized': term_data.get('term_english_normalized', term_english.lower()),
                        'term_type': term_data.get('term_type', 'other'),
                        'category': term_data.get('category', 'other'),
                        'definition': term_data.get('definition', ''),
                        'usage_frequency': term_data.get('usage_frequency', 'low'),
                        'difficulty_level': term_data.get('difficulty_level', 'basic'),
                        'confidence_score': term_data.get('confidence_score', 50),
                        'verified': term_data.get('verified', False),
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                error_count += 1
                if error_count <= 10:  # Only show first 10 errors
                    self.stdout.write(self.style.ERROR(f'Error on term {idx}: {str(e)}'))

        self.stdout.write(f'\n[OK] Terms imported: {created_count} created, {updated_count} updated, {error_count} errors')

        # Build a mapping of JSON IDs to database objects for translations
        self.stdout.write('\n[BUILD] Creating term ID mapping...')
        term_id_map = {}
        for term_data in cooking_terms:
            term_id = term_data.get('id')
            term_english = term_data.get('term_english', '')
            if term_id and term_english:
                try:
                    term = CookingTermCache.objects.get(term_english=term_english)
                    term_id_map[term_id] = term
                except CookingTermCache.DoesNotExist:
                    pass
        self.stdout.write(f'Mapped {len(term_id_map)} term IDs')

        # Import translations
        self.stdout.write('\n[START] Importing translations...\n')
        
        trans_created = 0
        trans_updated = 0
        trans_errors = 0

        for idx, trans_data in enumerate(translations, 1):
            if idx % 100 == 0:
                self.stdout.write(f'Progress: {idx}/{total_translations} ({(idx/total_translations)*100:.1f}%)')

            try:
                term_id = trans_data.get('term_id')  # Changed from term_english to term_id
                language = trans_data.get('language_code', '')  # Changed from 'language'
                translation = trans_data.get('translation', '')

                if not term_id or not language or not translation:
                    trans_errors += 1
                    continue

                # Find the cooking term from our mapping
                term = term_id_map.get(term_id)
                if not term:
                    trans_errors += 1
                    continue

                # Create or update translation
                trans_obj, created = CookingTermTranslation.objects.update_or_create(
                    term=term,  # Fixed: use 'term' not 'cooking_term'
                    language_code=language,
                    defaults={
                        'translation': translation,
                        'confidence_score': trans_data.get('confidence_score', 50),
                    }
                )

                if created:
                    trans_created += 1
                else:
                    trans_updated += 1

            except Exception as e:
                trans_errors += 1
                if trans_errors <= 10:  # Only show first 10 errors
                    self.stdout.write(self.style.ERROR(f'Error on translation {idx}: {str(e)}'))

        # Final summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('[COMPLETE] Import finished!\n'))
        self.stdout.write('Terms:')
        self.stdout.write(f'   Total processed: {total_terms}')
        self.stdout.write(f'   Created: {created_count}')
        self.stdout.write(f'   Updated: {updated_count}')
        self.stdout.write(f'   Errors: {error_count}')
        self.stdout.write('\nTranslations:')
        self.stdout.write(f'   Total processed: {total_translations}')
        self.stdout.write(f'   Created: {trans_created}')
        self.stdout.write(f'   Updated: {trans_updated}')
        self.stdout.write(f'   Errors: {trans_errors}\n')

        # Show final stats
        total_terms_db = CookingTermCache.objects.count()
        total_trans_db = CookingTermTranslation.objects.count()
        trans_en = CookingTermTranslation.objects.filter(language_code='en').count()
        trans_ru = CookingTermTranslation.objects.filter(language_code='ru').count()
        trans_he = CookingTermTranslation.objects.filter(language_code='he').count()

        self.stdout.write('[STATS] Current database state:')
        self.stdout.write(f'   Total cooking terms: {total_terms_db}')
        self.stdout.write(f'   Total translations: {total_trans_db}')
        self.stdout.write(f'     - EN: {trans_en}')
        self.stdout.write(f'     - RU: {trans_ru}')
        self.stdout.write(f'     - HE: {trans_he}\n')
        
        self.stdout.write(self.style.SUCCESS('='*60))

