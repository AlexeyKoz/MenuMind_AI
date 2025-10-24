"""
Management command to warm IML translation cache
Pre-translates all ingredients to all supported languages
"""

from django.core.management.base import BaseCommand
from apps.core.models import IngredientCache, IngredientTranslation
from apps.core.google_translate_service import get_google_translate_service
import time


class Command(BaseCommand):
    help = 'Warm IML cache by translating all ingredients to all languages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of ingredients to process (for testing)'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip ingredients that already have all translations'
        )

    def handle(self, *args, **options):
        translator = get_google_translate_service()
        supported_languages = ['en', 'ru', 'he']

        # Get ingredients to process
        queryset = IngredientCache.objects.all()

        if options['limit']:
            queryset = queryset[:options['limit']]

        total = queryset.count()
        self.stdout.write(
            self.style.SUCCESS(f"🚀 Starting IML translation warm-up"))
        self.stdout.write(f"📊 Processing {total} ingredients...")

        processed = 0
        translated = 0
        skipped = 0
        failed = 0

        start_time = time.time()

        for idx, ingredient in enumerate(queryset, 1):
            # Check existing translations
            existing_langs = set(
                ingredient.translations.values_list('language', flat=True)
            )

            missing_langs = set(supported_languages) - existing_langs

            if not missing_langs:
                if options['skip_existing']:
                    skipped += 1
                    if idx % 100 == 0:
                        self.stdout.write(
                            f"[{idx}/{total}] Skipped: {ingredient.ingredient_key}")
                    continue

            # Get English name (base for translation)
            en_trans = ingredient.translations.filter(language='en').first()
            if not en_trans:
                self.stdout.write(
                    self.style.WARNING(
                        f"[{idx}/{total}] ⚠️ No English translation for: {ingredient.ingredient_key}")
                )
                failed += 1
                continue

            en_name = en_trans.name

            # Translate missing languages
            for lang in missing_langs:
                try:
                    translated_name = translator.translate_text(
                        en_name,
                        target_language=lang,
                        source_language='en'
                    )

                    if translated_name:
                        # Create or update translation
                        IngredientTranslation.objects.update_or_create(
                            ingredient=ingredient,
                            language=lang,
                            defaults={'name': translated_name}
                        )

                        translated += 1

                        # Show progress every 10 items
                        if idx % 10 == 0:
                            self.stdout.write(
                                f"[{idx}/{total}] {en_name} → [{lang}] {translated_name}"
                            )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"[{idx}/{total}] ⚠️ Translation failed for: {en_name} → {lang}")
                        )
                        failed += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"[{idx}/{total}] ❌ Error translating {en_name} → {lang}: {e}")
                    )
                    failed += 1

            processed += 1

            # Progress indicator every 50 items
            if idx % 50 == 0:
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                eta = (total - idx) / rate if rate > 0 else 0
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n📈 Progress: {idx}/{total} ({idx/total*100:.1f}%) | "
                        f"Rate: {rate:.1f} items/sec | ETA: {eta/60:.1f} min\n"
                    )
                )

        elapsed = time.time() - start_time

        # Final summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(
            "✅ IML Translation Warm-Up Complete!"))
        self.stdout.write("="*60)
        self.stdout.write(f"📊 Total Ingredients: {total}")
        self.stdout.write(f"✅ Processed: {processed}")
        self.stdout.write(f"🌍 Translations Created: {translated}")
        self.stdout.write(f"⏭️ Skipped (already complete): {skipped}")
        self.stdout.write(f"❌ Failed: {failed}")
        self.stdout.write(f"⏱️ Time Elapsed: {elapsed/60:.2f} minutes")
        self.stdout.write(
            f"⚡ Average Speed: {processed/elapsed:.2f} items/second")
        self.stdout.write("="*60 + "\n")

        # Recommendation
        if total > 0:
            iml_coverage = (processed / total) * 100
            self.stdout.write(
                self.style.SUCCESS(
                    f"🎯 IML Coverage: {iml_coverage:.1f}% of ingredients now support multilang!"
                )
            )
            self.stdout.write(
                "\n💡 Next time a recipe uses these ingredients, translations will be INSTANT! ⚡"
            )
