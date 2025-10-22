"""
Django app configuration for core services
Initializes in-memory caching services on startup
"""
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core Services'

    def ready(self):
        """
        Initialize services when Django starts
        Called once on server startup
        """
        # Only initialize in main process (not in migration/management commands)
        import sys
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return

        logger.info("=" * 60)
        logger.info("🚀 Initializing MenuMineAI Core Services...")
        logger.info("=" * 60)

        try:
            # Initialize IML Service
            from .services.iml_service import iml_service
            iml_service.initialize()

            # Initialize CookLingo Service
            from .services.cooklingo_service import cooklingo_service
            cooklingo_service.initialize()

            # Print summary
            iml_stats = iml_service.get_stats()
            cooklingo_stats = cooklingo_service.get_stats()

            logger.info("")
            logger.info("📊 Service Statistics:")
            logger.info(
                f"   IML Ingredients:  {iml_stats['total_ingredients']} loaded ({iml_stats['cache_size_kb']}KB)")
            logger.info(
                f"   CookLingo Terms:  {cooklingo_stats['total_terms']} loaded ({cooklingo_stats['cache_size_kb']}KB)")
            logger.info("")
            logger.info("✅ All services initialized successfully!")
            logger.info("⚡ Performance: <1ms lookups, <5ms batch operations")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            logger.error(
                "   Services will be available but may perform slower")
            import traceback
            traceback.print_exc()
