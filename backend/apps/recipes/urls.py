from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet, UserRecipeViewSet

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'user-recipes', UserRecipeViewSet, basename='user-recipe')

urlpatterns = [
    path('', include(router.urls)),
]



