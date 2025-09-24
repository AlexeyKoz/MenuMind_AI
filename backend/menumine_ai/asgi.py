"""
ASGI config for menumine_ai project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# ⚠️ CRITICAL: Import consumers AFTER Django is initialized above!
# ⚠️ DO NOT move these imports to the top of the file!
from apps.shopping.consumers import ShoppingListConsumer
from apps.shopping.user_consumer import UserNotificationConsumer

websocket_urlpatterns = [
    path('ws/shopping/<uuid:list_id>/', ShoppingListConsumer.as_asgi()),
    path('ws/user/notifications/', UserNotificationConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})

