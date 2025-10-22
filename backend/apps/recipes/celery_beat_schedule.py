"""
Celery Beat Schedule Configuration - Sprint 5 Background Agents

This file configures periodic tasks for the MenuMineAI system.

Background Agents:
1. Hourly Translation Scan - Check for missing translations
2. Hourly Discovery Cache Refresh - Keep cache fresh
3. Daily Translation Cleanup - Remove stale/failed translations
4. Weekly Cache Cleanup - Remove old cache entries

To enable Celery Beat:
    celery -A menumine_ai beat --loglevel=info

To run worker + beat together:
    celery -A menumine_ai worker --beat --loglevel=info
"""
from celery.schedules import crontab

# Sprint 5: Background Agents Schedule
CELERY_BEAT_SCHEDULE = {
    # ===================================================================
    # HOURLY TASKS
    # ===================================================================

    'hourly-translation-scan': {
        'task': 'apps.recipes.tasks.hourly_translation_scan',
        'schedule': crontab(minute=0),  # Every hour at :00
        'options': {
            'expires': 3300,  # Task expires after 55 minutes
        }
    },

    'hourly-discovery-cache-refresh': {
        'task': 'apps.recipes.tasks.refresh_discovery_cache',
        'schedule': crontab(minute=30),  # Every hour at :30
        'options': {
            'expires': 3300,
        }
    },

    # ===================================================================
    # DAILY TASKS
    # ===================================================================

    'daily-translation-cleanup': {
        'task': 'apps.recipes.tasks.cleanup_stale_translations',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3:00 AM
        'options': {
            'expires': 86400,  # Task expires after 24 hours
        }
    },

    # Sprint 7 - Phase 3: Inventory cache cleanup
    'daily-inventory-cache-cleanup': {
        'task': 'shopping.cleanup_expired_recipe_cache',
        'schedule': crontab(hour=3, minute=30),  # Daily at 3:30 AM
        'options': {
            'expires': 86400,
        }
    },

    # ===================================================================
    # WEEKLY TASKS
    # ===================================================================

    'weekly-cache-cleanup': {
        'task': 'apps.recipes.tasks.cleanup_stale_discovery_cache',
        # Sunday at 4:00 AM
        'schedule': crontab(day_of_week=0, hour=4, minute=0),
        'options': {
            'expires': 604800,  # Task expires after 1 week
        }
    },
}

# Alternative schedules for development/testing
CELERY_BEAT_SCHEDULE_DEV = {
    # Run tasks more frequently for testing

    'every-5min-translation-scan': {
        'task': 'apps.recipes.tasks.hourly_translation_scan',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },

    'every-10min-cache-refresh': {
        'task': 'apps.recipes.tasks.refresh_discovery_cache',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },

    'hourly-translation-cleanup': {
        'task': 'apps.recipes.tasks.cleanup_stale_translations',
        'schedule': crontab(minute=0),  # Every hour
    },

    'daily-cache-cleanup': {
        'task': 'apps.recipes.tasks.cleanup_stale_discovery_cache',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
}

# Task routing (optional - for task prioritization)
CELERY_TASK_ROUTES = {
    # High priority: User-facing translation tasks
    'apps.recipes.tasks.translate_recipe_immediate': {'queue': 'high_priority'},
    'apps.recipes.tasks.translate_recipe_on_demand': {'queue': 'high_priority'},

    # Normal priority: Background translations
    'apps.recipes.tasks.translate_recipe_background': {'queue': 'default'},

    # Low priority: Maintenance tasks
    'apps.recipes.tasks.hourly_translation_scan': {'queue': 'low_priority'},
    'apps.recipes.tasks.refresh_discovery_cache': {'queue': 'low_priority'},
    'apps.recipes.tasks.cleanup_stale_translations': {'queue': 'low_priority'},
    'apps.recipes.tasks.cleanup_stale_discovery_cache': {'queue': 'low_priority'},
    # Sprint 7
    'shopping.cleanup_expired_recipe_cache': {'queue': 'low_priority'},
}

# Task time limits (prevent hung tasks)
CELERY_TASK_TIME_LIMITS = {
    'apps.recipes.tasks.translate_recipe_immediate': 30,  # 30 seconds
    'apps.recipes.tasks.translate_recipe_background': 60,  # 1 minute
    'apps.recipes.tasks.translate_recipe_on_demand': 30,
    'apps.recipes.tasks.hourly_translation_scan': 600,  # 10 minutes
    'apps.recipes.tasks.refresh_discovery_cache': 600,
    'apps.recipes.tasks.cleanup_stale_translations': 300,  # 5 minutes
    'apps.recipes.tasks.cleanup_stale_discovery_cache': 300,
    'shopping.cleanup_expired_recipe_cache': 300,  # Sprint 7 - 5 minutes
}

# Celery Beat configuration for Django settings.py
"""
To use in settings.py:

from apps.recipes.celery_beat_schedule import CELERY_BEAT_SCHEDULE

# Add to your settings:
CELERY_BEAT_SCHEDULE = CELERY_BEAT_SCHEDULE

# Optional: Add task routing and time limits
CELERY_TASK_ROUTES = CELERY_TASK_ROUTES
CELERY_TASK_TIME_LIMITS = CELERY_TASK_TIME_LIMITS
"""
