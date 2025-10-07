from django.apps import AppConfig


class RecipesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.recipes'

    def ready(self):
        """Import signals when app is ready"""
        import apps.recipes.signals

