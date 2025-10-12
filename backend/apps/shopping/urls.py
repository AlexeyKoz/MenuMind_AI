from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse
from . import views
from .inventory_views import InventoryViewSet, AICategorizationView


def shopping_root(request):
    return JsonResponse({
        'message': 'Shopping API',
        'endpoints': {
            'lists': '/api/shopping/lists/',
            'items': '/api/shopping/items/',
            'inventory': '/api/shopping/inventory/',
        }
    })


# Create router for viewsets
router = DefaultRouter()
router.register(r'lists', views.ShoppingListViewSet, basename='shoppinglist')
router.register(r'items', views.ShoppingItemViewSet, basename='shoppingitem')
router.register(r'inventory', InventoryViewSet, basename='inventory')

urlpatterns = [
    path('', shopping_root, name='shopping_root'),
    path('inventory/categorize/', AICategorizationView.as_view(),
         name='inventory-categorize'),
    path('', include(router.urls)),
]
