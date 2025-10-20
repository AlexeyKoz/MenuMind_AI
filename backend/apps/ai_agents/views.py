from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import async_to_sync

from apps.recipes.services import RecipeAgentService


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_recipes_from_inventory(request):
    """
    Generate recipe suggestions based on user's preferences.

    This endpoint is for the Recipes page AI Generator tab.
    It generates random/popular recipes based on user preferences,
    NOT from inventory.

    For inventory-based recipe generation, use the shopping app endpoint:
    /api/shopping/inventory/generate_recipes/

    Request body (optional):
        - max_recipes: int (default: 3)
        - cuisine: string (optional)
        - difficulty: string (optional)

    Returns:
        - recipes: list of canonical recipes
        - message: success message
    """
    # Get options from request
    max_recipes = request.data.get('max_recipes', 3)
    cuisine = request.data.get('cuisine', '')
    difficulty = request.data.get('difficulty', '')

    # Build query based on user preferences
    queries = [
        "easy pasta recipe",
        "quick chicken dinner",
        "healthy vegetarian meal",
        "simple dessert",
        "30 minute dinner"
    ]

    # Customize based on user dietary restrictions
    user_restrictions = request.user.dietary_restrictions
    if user_restrictions:
        if 'vegetarian' in user_restrictions.lower():
            queries = ["vegetarian pasta",
                       "veggie stir fry", "vegetarian curry"]
        elif 'vegan' in user_restrictions.lower():
            queries = ["vegan pasta", "vegan curry", "vegan bowl"]

    # Limit to requested number
    queries = queries[:max_recipes]

    print(
        f"[AI RECIPES] Generating {len(queries)} recipes for {request.user.username}")

    # Get user preferences
    user_preferences = {
        'dietary_restrictions': request.user.dietary_restrictions,
        'allergies': request.user.allergies,
        'language': getattr(request.user, 'preferred_language', 'en'),
        'unit_system': 'metric' if getattr(request.user, 'weight_unit', 'kg') == 'kg' else 'imperial'
    }

    # Generate multiple recipes
    agent = RecipeAgentService()
    generated_recipes = []

    try:
        # Generate recipes based on different queries
        for i, query in enumerate(queries):
            success, result, message = async_to_sync(agent.process_recipe_query)(
                query,
                request.user,
                user_preferences
            )

            if success:
                generated_recipes.append(result['canonical_recipe'])
                print(
                    f"[AI RECIPES] Generated recipe {i+1}/{len(queries)}: {result['canonical_recipe']['name']}")
            else:
                print(
                    f"[AI RECIPES] Failed to generate recipe {i+1}: {message}")
                # Don't fail the entire request if one recipe fails
                continue

        if not generated_recipes:
            return Response({
                'error': 'Failed to generate recipes. Please try again later.',
                'recipes': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'success': True,
            'recipes': generated_recipes,
            'message': f'Generated {len(generated_recipes)} recipe(s)'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"[AI RECIPES ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'An error occurred while generating recipes: {str(e)}',
            'recipes': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_assistant(request):
    """
    General AI assistant endpoint for various tasks.
    To be implemented.
    """
    return Response({
        'message': 'AI Assistant endpoint - Coming soon!'
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_coaching(request):
    """
    AI nutrition coaching endpoint.
    To be implemented.
    """
    return Response({
        'message': 'AI Coaching endpoint - Coming soon!'
    }, status=status.HTTP_501_NOT_IMPLEMENTED)
