"""
IML Sync Service - Syncs ingredients from IML SQLite to PostgreSQL
"""
import sqlite3
import json
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import IngredientCache, IngredientTranslation


class IMLSyncService:
    """Service for syncing IML SQLite database to PostgreSQL"""

    def __init__(self):
        self.iml_db_path = getattr(
            settings, 'IML_DB_PATH', '../ingredient-master-list/data/iml.db')
        self.conn = None

    def connect(self) -> bool:
        """Connect to IML SQLite database (READ ONLY)"""
        try:
            self.conn = sqlite3.connect(
                f'file:{self.iml_db_path}?mode=ro', uri=True)
            self.conn.row_factory = sqlite3.Row  # Access columns by name

            # Set to read-only mode
            self.conn.execute("PRAGMA query_only = ON")

            print(f"[OK] Connected to IML database: {self.iml_db_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to connect to IML database: {e}")
            return False

    def disconnect(self):
        """Close IML database connection"""
        if self.conn:
            self.conn.close()
            print("[OK] Disconnected from IML database")

    def get_iml_structure(self) -> Dict:
        """Inspect IML database structure"""
        if not self.conn:
            return {}

        cursor = self.conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        structure = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [{'name': row[1], 'type': row[2]}
                       for row in cursor.fetchall()]
            structure[table] = columns

        return structure

    def sync_all(self, force: bool = False) -> Tuple[int, int, int]:
        """
        Sync all ingredients from IML to PostgreSQL

        Args:
            force: If True, sync all. If False, only sync modified since last sync

        Returns:
            (created_count, updated_count, error_count)
        """
        if not self.connect():
            return (0, 0, 1)

        try:
            print("[START] Starting IML sync...")

            # Get IML structure first
            structure = self.get_iml_structure()
            print(f"[STRUCTURE] IML Database structure:")
            for table, columns in structure.items():
                print(f"  - {table}: {len(columns)} columns")

            # Sync ingredients
            created, updated, errors = self._sync_ingredients(force)

            print(f"\n[OK] Sync complete!")
            print(f"   Created: {created}")
            print(f"   Updated: {updated}")
            print(f"   Errors: {errors}")

            return (created, updated, errors)

        except Exception as e:
            print(f"[ERROR] Sync failed: {e}")
            import traceback
            traceback.print_exc()
            return (0, 0, 1)
        finally:
            self.disconnect()

    def _sync_ingredients(self, force: bool) -> Tuple[int, int, int]:
        """Sync ingredients from IML"""
        cursor = self.conn.cursor()

        # First, inspect the actual table structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Available tables: {tables}")

        # Try to find the main ingredients table
        # Common names: ingredients, ingredient, items, food_items
        ingredient_table = None
        for possible_name in ['ingredients', 'ingredient', 'items', 'food_items', 'foods']:
            if possible_name in tables:
                ingredient_table = possible_name
                break

        if not ingredient_table:
            print(
                f"⚠️  Could not find ingredients table. Available tables: {tables}")
            print(f"⚠️  Please check IML database structure")
            return (0, 0, 1)

        print(f"[OK] Found ingredients table: {ingredient_table}")

        # Get table structure
        cursor.execute(f"PRAGMA table_info({ingredient_table})")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        print(f"[COLUMNS] Columns: {list(columns.keys())}")

        # Query ingredients
        try:
            # Try to get all rows first to see what data looks like
            cursor.execute(f"SELECT * FROM {ingredient_table} LIMIT 5")
            sample_rows = cursor.fetchall()

            if sample_rows:
                print(f"\n[SAMPLE] Sample data (first row):")
                sample = dict(sample_rows[0])
                # Show first 10 columns
                for key, value in list(sample.items())[:10]:
                    print(f"   {key}: {value}")

            # Now sync all ingredients
            if force:
                query = f"SELECT * FROM {ingredient_table}"
            else:
                # Try to filter by modified_at if column exists
                if 'modified_at' in columns or 'updated_at' in columns:
                    last_sync = self._get_last_sync_time()
                    date_column = 'modified_at' if 'modified_at' in columns else 'updated_at'
                    query = f"SELECT * FROM {ingredient_table} WHERE {date_column} > ?"
                    cursor.execute(query, (last_sync,))
                else:
                    query = f"SELECT * FROM {ingredient_table}"
                    cursor.execute(query)

            if force:
                cursor.execute(query)

            rows = cursor.fetchall()
            print(f"\n[SYNC] Syncing {len(rows)} ingredients...")

            created_count = 0
            updated_count = 0
            error_count = 0

            for row in rows:
                try:
                    result = self._sync_single_ingredient(dict(row), columns)
                    if result == 'created':
                        created_count += 1
                    elif result == 'updated':
                        updated_count += 1

                    # Progress indicator
                    if (created_count + updated_count) % 100 == 0:
                        print(
                            f"   Progress: {created_count + updated_count}/{len(rows)}")

                except Exception as e:
                    error_count += 1
                    print(f"   ❌ Error syncing ingredient: {e}")

            return (created_count, updated_count, error_count)

        except Exception as e:
            print(f"❌ Error querying ingredients: {e}")
            import traceback
            traceback.print_exc()
            return (0, 0, 1)

    def _sync_single_ingredient(self, row_data: Dict, columns: Dict) -> str:
        """
        Sync single ingredient to PostgreSQL

        Returns: 'created', 'updated', or 'error'
        """
        # Extract ingredient_key (try different possible column names)
        ingredient_key = None
        for key_field in ['ingredient_key', 'key', 'id', 'food_id', 'fdc_id']:
            if key_field in row_data and row_data[key_field]:
                ingredient_key = str(row_data[key_field])
                break

        if not ingredient_key:
            print(f"   ⚠️  Skipping row - no ingredient_key found")
            return 'error'

        # Extract other fields with fallbacks
        category = row_data.get('category', row_data.get('food_category', ''))
        source = row_data.get('source', row_data.get('data_source', 'unknown'))

        # Parse JSON fields
        def safe_json_parse(data, default=None):
            if not data:
                return default or {}
            if isinstance(data, str):
                try:
                    return json.loads(data)
                except:
                    return default or {}
            return data

        common_units = safe_json_parse(row_data.get('common_units'))
        unit_conversions = safe_json_parse(row_data.get('unit_conversions'))
        shelf_life = safe_json_parse(row_data.get('shelf_life'))
        storage_recommendations = safe_json_parse(
            row_data.get('storage_recommendations'))
        nutrition_per_100g = safe_json_parse(
            row_data.get('nutrition_per_100g'))

        # Create or update IngredientCache
        with transaction.atomic():
            ingredient, created = IngredientCache.objects.update_or_create(
                ingredient_key=ingredient_key,
                defaults={
                    'category': category,
                    'source': source,
                    'common_units': common_units,
                    'unit_conversions': unit_conversions,
                    'shelf_life': shelf_life,
                    'storage_recommendations': storage_recommendations,
                    'nutrition_per_100g': nutrition_per_100g,
                    'metadata': row_data,  # Store full row for reference
                    'last_synced': timezone.now()
                }
            )

            # Sync translations (if available in IML)
            self._sync_translations(ingredient, row_data)

            return 'created' if created else 'updated'

    def _sync_translations(self, ingredient: IngredientCache, row_data: Dict):
        """Sync translations for ingredient"""
        # Check if translations are stored as JSON in single field
        translations_json = row_data.get(
            'translations', row_data.get('names', None))

        if translations_json:
            # Parse translations JSON
            if isinstance(translations_json, str):
                try:
                    translations = json.loads(translations_json)
                except:
                    translations = {}
            else:
                translations = translations_json

            # Expected format: {"en": "tomato", "ru": "помидор", "he": "עגבנייה"}
            for lang in ['en', 'ru', 'he']:
                if lang in translations:
                    name = translations[lang]

                    # Also check for description and aliases
                    description = translations.get(f'{lang}_description', '')
                    aliases = translations.get(f'{lang}_aliases', [])
                    if isinstance(aliases, str):
                        try:
                            aliases = json.loads(aliases)
                        except:
                            aliases = []

                    IngredientTranslation.objects.update_or_create(
                        ingredient=ingredient,
                        language=lang,
                        defaults={
                            'name': name,
                            'description': description,
                            'aliases': aliases,
                            'storage_tips': ''
                        }
                    )
        else:
            # Fallback: look for separate name columns (name_en, name_ru, name_he)
            for lang in ['en', 'ru', 'he']:
                name_field = f'name_{lang}'
                if name_field in row_data and row_data[name_field]:
                    IngredientTranslation.objects.update_or_create(
                        ingredient=ingredient,
                        language=lang,
                        defaults={
                            'name': row_data[name_field],
                            'description': row_data.get(f'description_{lang}', ''),
                            'aliases': [],
                            'storage_tips': ''
                        }
                    )

    def _get_last_sync_time(self) -> str:
        """Get timestamp of last successful sync"""
        last_ingredient = IngredientCache.objects.order_by(
            '-last_synced').first()
        if last_ingredient:
            return last_ingredient.last_synced.isoformat()
        return '1970-01-01T00:00:00'

    def get_sync_stats(self) -> Dict:
        """Get statistics about current sync state"""
        return {
            'total_ingredients': IngredientCache.objects.count(),
            'total_translations': IngredientTranslation.objects.count(),
            'languages': {
                'en': IngredientTranslation.objects.filter(language='en').count(),
                'ru': IngredientTranslation.objects.filter(language='ru').count(),
                'he': IngredientTranslation.objects.filter(language='he').count(),
            },
            'sources': list(IngredientCache.objects.values_list('source', flat=True).distinct()),
            'categories': list(IngredientCache.objects.values_list('category', flat=True).distinct()),
            'last_sync': IngredientCache.objects.order_by('-last_synced').first().last_synced if IngredientCache.objects.exists() else None
        }
