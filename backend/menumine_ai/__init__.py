"""
MenuMine AI - Food Intelligence Platform
"""

# Version Information
from .celery import app as celery_app
__version__ = "0.9.0"
__author__ = "Alexey Kozlov"
__license__ = "MIT"

# Make version easily importable
VERSION = __version__

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.

__all__ = ('celery_app', 'VERSION', '__version__')
