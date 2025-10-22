"""
Admin Import Service for IML and CookLingo data
Handles importing from SQLite files and managing database operations
"""
import sqlite3
import logging
from typing import Dict, Optional
from django.db import transaction
from apps.core.models import (
    IngredientCache,
    IngredientTranslation,
    CookingTermCache,
    CookingTermTranslation,
    ImportHistory
)
import json

logger = logging.getLogger(__name__)


class AdminImportService:
    """
    Service for importing IML and CookLingo data from SQLite files

    Features:
    - Import from SQLite to PostgreSQL
    - Update existing records or insert new ones
    - Track import history with detailed statistics
    - Handle errors gracefully with logging
    """

    def import_iml_from_sqlite(
        self,
        sqlite_path: str,
        imported_by: str = "admin"
    ) -> Dict:
        """
        Import IML ingredients from SQLite file

        Expected SQLite schema:
        - Table: ingredients
        - Columns: ingredient_key, category, en_name, he_name, ru_name, 
                   aliases (JSON), typical_amount_min, typical_amount_max, etc.

        Args:
            sqlite_path: Path to SQLite .db file
            imported_by: Username of person performing import

        Returns:
            Dict with statistics: {imported, updated, failed, errors}
        """
        stats = {
            'imported': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }

        try:
            # Connect to SQLite
            conn = sqlite3.connect(sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Verify table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='ingredients'"
            )
            if not cursor.fetchone():
                raise ValueError(
                    "SQLite file does not contain 'ingredients' table")

            # Read all ingredients
            cursor.execute("SELECT * FROM ingredients")
            rows = cursor.fetchall()

            if not rows:
                raise ValueError("No ingredients found in SQLite file")

            logger.info(
                f"[IML IMPORT] Found {len(rows)} ingredients in SQLite file")

            # Process each ingredient
            with transaction.atomic():
                for row in rows:
                    try:
                        ingredient_key = row['ingredient_key']

                        # Parse aliases JSON if it's a string
                        aliases = row.get('aliases', '[]')
                        if isinstance(aliases, str):
                            try:
                                aliases = json.loads(aliases)
                            except:
                                aliases = []

                        # Get or create ingredient cache
                        ingredient, created = IngredientCache.objects.get_or_create(
                            ingredient_key=ingredient_key,
                            defaults={
                                'category': row.get('category', ''),
                                'source': 'iml_import',
                                'common_units': row.get('common_units', {}),
                                'unit_conversions': row.get('unit_conversions', {}),
                                'shelf_life': row.get('shelf_life', {}),
                                'storage_recommendations': row.get('storage_recommendations', {}),
                                'nutrition_per_100g': row.get('nutrition_per_100g', {}),
                                'typical_amount_min': row.get('typical_amount_min'),
                                'typical_amount_max': row.get('typical_amount_max'),
                                'typical_amount_avg': row.get('typical_amount_avg'),
                                'max_per_serving': row.get('max_per_serving'),
                                'warning_threshold': row.get('warning_threshold'),
                            }
                        )

                        if created:
                            stats['imported'] += 1
                            logger.debug(f"  [NEW] {ingredient_key}")
                        else:
                            # Update existing
                            ingredient.category = row.get(
                                'category', ingredient.category)
                            ingredient.typical_amount_min = row.get(
                                'typical_amount_min')
                            ingredient.typical_amount_max = row.get(
                                'typical_amount_max')
                            ingredient.typical_amount_avg = row.get(
                                'typical_amount_avg')
                            ingredient.max_per_serving = row.get(
                                'max_per_serving')
                            ingredient.warning_threshold = row.get(
                                'warning_threshold')
                            ingredient.save()
                            stats['updated'] += 1
                            logger.debug(f"  [UPDATE] {ingredient_key}")

                        # Import translations
                        for lang in ['en', 'he', 'ru']:
                            name_field = f'{lang}_name'
                            if name_field in row.keys() and row[name_field]:
                                IngredientTranslation.objects.update_or_create(
                                    ingredient=ingredient,
                                    language=lang,
                                    defaults={
                                        'name': row[name_field],
                                        'aliases': aliases if lang == 'en' else []
                                    }
                                )

                    except Exception as e:
                        stats['failed'] += 1
                        error_msg = f"{ingredient_key}: {str(e)}"
                        stats['errors'].append(error_msg)
                        logger.error(f"  [FAILED] {error_msg}")

            conn.close()

            # Log to import history
            self._log_import_history(
                import_type='iml',
                source_file=sqlite_path.split('/')[-1],
                stats=stats,
                imported_by=imported_by
            )

            logger.info(f"[IML IMPORT] Complete: {stats['imported']} imported, "
                        f"{stats['updated']} updated, {stats['failed']} failed")

            # Reload IML service memory cache
            try:
                from .iml_service import iml_service
                iml_service.reload()
                logger.info("[IML IMPORT] ✅ Memory cache reloaded")
            except Exception as e:
                logger.warning(
                    f"[IML IMPORT] ⚠️  Failed to reload memory cache: {e}")

            return stats

        except Exception as e:
            error_msg = f"Critical error: {str(e)}"
            stats['errors'].append(error_msg)
            logger.error(f"[IML IMPORT] {error_msg}")

            # Log failed import
            self._log_import_history(
                import_type='iml',
                source_file=sqlite_path.split(
                    '/')[-1] if sqlite_path else 'unknown',
                stats=stats,
                imported_by=imported_by,
                status='failed'
            )

            return stats

    def import_cooklingo_from_sqlite(
        self,
        sqlite_path: str,
        imported_by: str = "admin"
    ) -> Dict:
        """
        Import CookLingo terms from SQLite file

        Expected SQLite schema:
        - Table: cooking_terms
        - Columns: term_english, term_type, category, en_term, he_term, ru_term

        Args:
            sqlite_path: Path to SQLite .db file
            imported_by: Username of person performing import

        Returns:
            Dict with statistics
        """
        stats = {
            'imported': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }

        try:
            conn = sqlite3.connect(sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Verify table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='cooking_terms'"
            )
            if not cursor.fetchone():
                raise ValueError(
                    "SQLite file does not contain 'cooking_terms' table")

            cursor.execute("SELECT * FROM cooking_terms")
            rows = cursor.fetchall()

            if not rows:
                raise ValueError("No cooking terms found in SQLite file")

            logger.info(
                f"[COOKLINGO IMPORT] Found {len(rows)} terms in SQLite file")

            with transaction.atomic():
                for row in rows:
                    try:
                        term_english = row['term_english']

                        # Get or create cooking term
                        term, created = CookingTermCache.objects.get_or_create(
                            term_english=term_english,
                            defaults={
                                'term_english_normalized': term_english.lower().strip(),
                                'term_type': row.get('term_type', ''),
                                'category': row.get('category', ''),
                                'definition': row.get('definition', ''),
                                'usage_frequency': row.get('usage_frequency', ''),
                                'difficulty_level': row.get('difficulty_level', ''),
                            }
                        )

                        if created:
                            stats['imported'] += 1
                            logger.debug(f"  [NEW] {term_english}")
                        else:
                            # Update existing
                            term.category = row.get('category', term.category)
                            term.term_type = row.get(
                                'term_type', term.term_type)
                            term.save()
                            stats['updated'] += 1
                            logger.debug(f"  [UPDATE] {term_english}")

                        # Import translations
                        for lang in ['en', 'he', 'ru']:
                            term_field = f'{lang}_term'
                            if term_field in row.keys() and row[term_field]:
                                CookingTermTranslation.objects.update_or_create(
                                    term=term,
                                    language_code=lang,
                                    defaults={
                                        'translation': row[term_field],
                                        'source': 'cooklingo_import',
                                        'confidence_score': 100,
                                        'verification_status': 'human_verified'
                                    }
                                )

                    except Exception as e:
                        stats['failed'] += 1
                        error_msg = f"{term_english}: {str(e)}"
                        stats['errors'].append(error_msg)
                        logger.error(f"  [FAILED] {error_msg}")

            conn.close()

            self._log_import_history(
                import_type='cooklingo',
                source_file=sqlite_path.split('/')[-1],
                stats=stats,
                imported_by=imported_by
            )

            logger.info(f"[COOKLINGO IMPORT] Complete: {stats['imported']} imported, "
                        f"{stats['updated']} updated, {stats['failed']} failed")

            # Reload CookLingo service memory cache
            try:
                from .cooklingo_service import cooklingo_service
                cooklingo_service.reload()
                logger.info("[COOKLINGO IMPORT] ✅ Memory cache reloaded")
            except Exception as e:
                logger.warning(
                    f"[COOKLINGO IMPORT] ⚠️  Failed to reload memory cache: {e}")

            return stats

        except Exception as e:
            error_msg = f"Critical error: {str(e)}"
            stats['errors'].append(error_msg)
            logger.error(f"[COOKLINGO IMPORT] {error_msg}")

            self._log_import_history(
                import_type='cooklingo',
                source_file=sqlite_path.split(
                    '/')[-1] if sqlite_path else 'unknown',
                stats=stats,
                imported_by=imported_by,
                status='failed'
            )

            return stats

    def delete_all_iml(self, imported_by: str = "admin") -> Dict:
        """
        Delete ALL IML ingredients
        ⚠️ DESTRUCTIVE OPERATION - Use with caution!
        """
        try:
            count = IngredientCache.objects.count()
            IngredientCache.objects.all().delete()

            self._log_import_history(
                import_type='iml_delete',
                source_file='N/A',
                stats={'deleted': count},
                imported_by=imported_by
            )

            logger.warning(f"[IML DELETE] Deleted {count} ingredients")
            return {'deleted': count}

        except Exception as e:
            logger.error(f"[IML DELETE] Failed: {e}")
            raise

    def delete_all_cooklingo(self, imported_by: str = "admin") -> Dict:
        """
        Delete ALL CookLingo terms
        ⚠️ DESTRUCTIVE OPERATION - Use with caution!
        """
        try:
            count = CookingTermCache.objects.count()
            CookingTermCache.objects.all().delete()

            self._log_import_history(
                import_type='cooklingo_delete',
                source_file='N/A',
                stats={'deleted': count},
                imported_by=imported_by
            )

            logger.warning(f"[COOKLINGO DELETE] Deleted {count} terms")
            return {'deleted': count}

        except Exception as e:
            logger.error(f"[COOKLINGO DELETE] Failed: {e}")
            raise

    def get_database_stats(self) -> Dict:
        """Get current database statistics"""
        return {
            'iml_ingredients': IngredientCache.objects.count(),
            'iml_translations': IngredientTranslation.objects.count(),
            'cooklingo_terms': CookingTermCache.objects.count(),
            'cooklingo_translations': CookingTermTranslation.objects.count(),
            'import_history_count': ImportHistory.objects.count(),
        }

    def _log_import_history(
        self,
        import_type: str,
        source_file: str,
        stats: Dict,
        imported_by: str,
        status: str = None
    ):
        """Log import operation to history"""

        # Determine status if not provided
        if status is None:
            if stats.get('failed', 0) == 0:
                status = 'success'
            elif stats.get('imported', 0) + stats.get('updated', 0) > 0:
                status = 'partial'
            else:
                status = 'failed'

        ImportHistory.objects.create(
            import_type=import_type,
            source_file=source_file,
            records_imported=stats.get('imported', 0),
            records_updated=stats.get('updated', 0),
            records_failed=stats.get('failed', 0),
            imported_by=imported_by,
            status=status,
            error_log=json.dumps(stats.get('errors', [])),
            summary={'total_records': stats.get(
                'imported', 0) + stats.get('updated', 0) + stats.get('failed', 0)}
        )


# Global service instance
admin_import_service = AdminImportService()
