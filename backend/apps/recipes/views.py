from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponse
from asgiref.sync import async_to_sync
import asyncio
import json

from .models import Recipe, UserRecipe
from .serializers import (
    RecipeSerializer, CreateRecipeSerializer,
    UserRecipeSerializer, RCIPFormatSerializer
)
from .services import RecipeAgentService, RecipeDeduplicationService
from apps.shopping.models import ShoppingList, ShoppingItem


class RecipeViewSet(viewsets.ModelViewSet):
    """Recipe management with AI agent integration"""

    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get recipes - latest versions only by default"""
        queryset = Recipe.objects.filter(is_latest_version=True)

        # Filter by search query
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(cuisine__icontains=search)
            )

        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty', None)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        # Filter by diet labels
        diet = self.request.query_params.get('diet', None)
        if diet:
            queryset = queryset.filter(diet_labels__contains=[diet])

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        """Create recipe and associate with user"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def find_recipe(self, request):
        """
        AI Agent endpoint: User describes what they want to cook
        Agent finds recipe, converts to RCIP, and optionally adds to shopping list
        """
        user_query = request.data.get('query', '')
        shopping_list_id = request.data.get('shopping_list_id', None)
        add_to_shopping_list = request.data.get('add_to_shopping_list', True)

        if not user_query:
            return Response(
                {'error': 'Please describe what you want to cook'},
                status=status.HTTP_400_BAD_REQUEST
            )

        print(f"[RECIPE REQUEST] '{user_query}' from {request.user.username}")

        # Get user preferences
        user_preferences = {
            'dietary_restrictions': request.user.dietary_restrictions,
            'allergies': request.user.allergies
        }

        # Run recipe agent
        agent = RecipeAgentService()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            success, recipe_data, message = loop.run_until_complete(
                agent.find_and_convert_recipe(user_query, user_preferences)
            )
        finally:
            loop.close()

        if not success:
            return Response(
                {'error': message},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check for duplicate recipes
        dedup_service = RecipeDeduplicationService()
        existing_recipes = dedup_service.find_duplicate_recipes(recipe_data)

        if existing_recipes:
            existing = existing_recipes.first()
            should_create_new = dedup_service.should_create_new_version(
                existing, recipe_data
            )

            if not should_create_new:
                print(
                    f"[REUSE] Using existing recipe: {existing.name} (v{existing.version})")
                recipe = existing
                created = False
            else:
                print(
                    f"[NEW VERSION] Creating new version of recipe: {existing.name}")
                recipe = self._create_recipe_from_data(
                    recipe_data, request.user)
                created = True
        else:
            print(
                f"[CREATE] Creating new recipe: {recipe_data['meta']['name']}")
            recipe = self._create_recipe_from_data(recipe_data, request.user)
            created = True

        # Add to shopping list if requested
        added_items = []
        if add_to_shopping_list and shopping_list_id:
            added_items = self._add_ingredients_to_shopping_list(
                recipe,
                shopping_list_id,
                request.user
            )

        return Response({
            'success': True,
            'message': 'Created new recipe' if created else 'Found existing recipe',
            'recipe': RecipeSerializer(recipe, context={'request': request}).data,
            'created': created,
            'version': recipe.version,
            'ingredients_added': len(added_items),
            'shopping_list_items': added_items
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def _create_recipe_from_data(self, recipe_data: dict, user) -> Recipe:
        """Create Recipe model from RCIP data"""
        meta = recipe_data.get('meta', {})

        recipe = Recipe.objects.create(
            rcip_version=recipe_data.get('rcip_version', '0.1'),
            name=meta.get('name', 'Untitled Recipe'),
            description=meta.get('description', ''),
            author=meta.get('author', ''),
            source_url=meta.get('source_url', ''),
            created_by=user,
            ingredients=recipe_data.get('ingredients', []),
            steps=recipe_data.get('steps', []),
            prep_time_minutes=meta.get('prep_time_minutes'),
            cook_time_minutes=meta.get('cook_time_minutes'),
            total_time_minutes=meta.get('total_time_minutes'),
            servings=meta.get('servings', {}).get('amount', 4),
            difficulty=meta.get('difficulty', 'intermediate'),
            cuisine=meta.get('keywords', [''])[
                0] if meta.get('keywords') else '',
            diet_labels=meta.get('diet_labels', [])
        )

        return recipe

    def _add_ingredients_to_shopping_list(
        self,
        recipe: Recipe,
        shopping_list_id: str,
        user
    ) -> list:
        """Add recipe ingredients to shopping list"""
        try:
            shopping_list = ShoppingList.objects.get(
                id=shopping_list_id,
                is_active=True
            )

            # Check if user has permission to add items
            is_creator = shopping_list.creator == user
            if is_creator:
                can_add_items = True
            else:
                try:
                    collaborator = shopping_list.collaborators.get(user=user)
                    can_add_items = collaborator.can_add_items
                except shopping_list.collaborators.model.DoesNotExist:
                    print(
                        f"[ERROR] User {user.username} is not a collaborator")
                    return []

            if not can_add_items:
                print(
                    f"[ERROR] User {user.username} cannot add items to list {shopping_list.name}")
                return []

            added_items = []
            user_color = getattr(user, 'personal_color', '#4F46E5')

            for ingredient in recipe.ingredients:
                # Parse ingredient data
                name = ingredient.get('name', '')
                if not name:
                    continue

                # Get amount and unit
                amount = ingredient.get('amount', 1)
                unit = ingredient.get('unit', 'unit')

                # Create shopping item
                item = ShoppingItem.objects.create(
                    shopping_list=shopping_list,
                    added_by=user,
                    name=name,
                    quantity=amount,
                    unit=unit,
                    category='other',  # Could be improved with categorization
                    notes=f"From recipe: {recipe.name}",
                    user_color=user_color,
                    priority=1 if is_creator else 0
                )

                added_items.append({
                    'id': str(item.id),
                    'name': item.name,
                    'quantity': float(item.quantity),
                    'unit': item.unit
                })

                print(f"   [OK] Added to shopping list: {name}")

            # Update recipe statistics
            recipe.times_added_to_lists += 1
            recipe.save()

            # Send WebSocket notification
            try:
                from channels.layers import get_channel_layer

                channel_layer = get_channel_layer()
                if channel_layer:
                    for item_data in added_items:
                        async_to_sync(channel_layer.group_send)(
                            f'shopping_list_{shopping_list_id}',
                            {
                                'type': 'item_added',
                                'item': item_data,
                                'user': {
                                    'id': str(user.id),
                                    'username': user.username,
                                    'first_name': user.first_name,
                                    'color': user_color
                                }
                            }
                        )
            except Exception as e:
                print(f"[WARNING] WebSocket notification failed: {e}")

            return added_items

        except ShoppingList.DoesNotExist:
            print(f"[ERROR] Shopping list not found: {shopping_list_id}")
            return []
        except Exception as e:
            print(f"[ERROR] Error adding ingredients to shopping list: {e}")
            return []

    @action(detail=True, methods=['get'])
    def rcip_format(self, request, pk=None):
        """Export recipe in full RCIP format"""
        recipe = self.get_object()
        rcip_data = recipe.to_rcip_format()

        return Response(rcip_data)

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Get all versions of this recipe"""
        recipe = self.get_object()

        # Get all versions (including current)
        if recipe.parent_recipe:
            versions = Recipe.objects.filter(
                Q(parent_recipe=recipe.parent_recipe) | Q(
                    id=recipe.parent_recipe.id)
            ).order_by('version')
        else:
            versions = Recipe.objects.filter(
                Q(parent_recipe=recipe) | Q(id=recipe.id)
            ).order_by('version')

        serializer = RecipeSerializer(
            versions, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def save_recipe(self, request, pk=None):
        """Save recipe to user's collection"""
        recipe = self.get_object()

        user_recipe, created = UserRecipe.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )

        if created:
            return Response({
                'message': f'Saved recipe: {recipe.name}',
                'saved': True
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'message': 'Recipe already saved',
                'saved': True
            })

    @action(detail=True, methods=['delete'])
    def unsave_recipe(self, request, pk=None):
        """Remove recipe from user's collection"""
        recipe = self.get_object()

        deleted_count, _ = UserRecipe.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()

        if deleted_count > 0:
            return Response({
                'message': f'Removed recipe: {recipe.name}',
                'saved': False
            })
        else:
            return Response({
                'message': 'Recipe was not saved',
                'saved': False
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def mark_cooked(self, request, pk=None):
        """Mark recipe as cooked"""
        recipe = self.get_object()

        try:
            user_recipe = UserRecipe.objects.get(
                user=request.user, recipe=recipe)
            user_recipe.times_cooked += 1
            user_recipe.last_cooked = timezone.now()
            user_recipe.save()

            # Update recipe statistics
            recipe.times_cooked += 1
            recipe.save()

            return Response({
                'message': 'Recipe marked as cooked',
                'times_cooked': user_recipe.times_cooked
            })
        except UserRecipe.DoesNotExist:
            return Response(
                {'error': 'Recipe not saved. Save it first before marking as cooked.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def my_recipes(self, request):
        """Get user's saved recipes"""
        user_recipes = UserRecipe.objects.filter(
            user=request.user
        ).select_related('recipe').order_by('-saved_at')

        serializer = UserRecipeSerializer(user_recipes, many=True)
        return Response({
            'recipes': serializer.data,
            'total': user_recipes.count()
        })

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular recipes by times cooked"""
        recipes = Recipe.objects.filter(
            is_latest_version=True
        ).order_by('-times_cooked', '-times_added_to_lists')[:20]

        serializer = RecipeSerializer(
            recipes, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def download_rcip(self, request, pk=None):
        """
        Download recipe as .rcip file

        GET /api/recipes/{recipe_id}/download_rcip/

        Returns: File download response with recipe in RCIP format
        """
        recipe = self.get_object()

        # Convert to full RCIP format
        rcip_data = recipe.to_rcip_format()

        # Create JSON response with proper formatting
        response = HttpResponse(
            json.dumps(rcip_data, indent=2, ensure_ascii=False),
            content_type='application/json'
        )

        # Set filename for download
        safe_name = recipe.name.replace(' ', '_').replace('/', '_')
        response['Content-Disposition'] = f'attachment; filename="{safe_name}.rcip"'

        return response

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser, JSONParser])
    def upload_rcip(self, request):
        """
        Upload and import a .rcip recipe file

        POST /api/recipes/upload_rcip/
        Content-Type: multipart/form-data

        Body:
            file: .rcip file

        Returns: Created recipe data
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES['file']

        # Check file extension
        if not uploaded_file.name.endswith('.rcip'):
            return Response(
                {'error': 'File must have .rcip extension'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Read and parse RCIP file
            file_content = uploaded_file.read().decode('utf-8')
            rcip_data = json.loads(file_content)

            # Validate required RCIP fields
            required_fields = ['rcip_version', 'meta', 'ingredients', 'steps']
            for field in required_fields:
                if field not in rcip_data:
                    return Response(
                        {'error': f'Missing required RCIP field: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Extract data from RCIP format
            meta = rcip_data['meta']

            # Check for duplicates
            dedup_service = RecipeDeduplicationService()
            existing_recipes = dedup_service.find_duplicate_recipes(rcip_data)

            if existing_recipes.exists():
                existing = existing_recipes.first()
                return Response({
                    'message': 'Recipe already exists',
                    'recipe': RecipeSerializer(existing, context={'request': request}).data,
                    'is_duplicate': True
                }, status=status.HTTP_200_OK)

            # Create recipe from RCIP data
            recipe = Recipe.objects.create(
                rcip_version=rcip_data.get('rcip_version', '0.1'),
                name=meta.get('name', 'Untitled Recipe'),
                description=meta.get('description', ''),
                author=meta.get('author', request.user.username),
                source_url=meta.get('source_url'),
                ingredients=rcip_data['ingredients'],
                steps=rcip_data['steps'],
                prep_time_minutes=meta.get('prep_time_minutes'),
                cook_time_minutes=meta.get('cook_time_minutes'),
                total_time_minutes=meta.get('total_time_minutes'),
                servings=meta.get('servings', {}).get('amount', 4) if isinstance(
                    meta.get('servings'), dict) else meta.get('servings', 4),
                difficulty=meta.get('difficulty', 'intermediate'),
                cuisine=meta.get('cuisine', ''),
                diet_labels=meta.get('diet_labels', []),
                created_by=request.user
            )

            # Calculate hash for deduplication
            if not recipe.recipe_hash:
                recipe.recipe_hash = recipe.calculate_recipe_hash()
                recipe.save()

            print(f"[UPLOAD] Recipe '{recipe.name}' imported from .rcip file")

            return Response({
                'message': 'Recipe imported successfully',
                'recipe': RecipeSerializer(recipe, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)

        except json.JSONDecodeError:
            return Response(
                {'error': 'Invalid JSON format in .rcip file'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print(f"[ERROR] RCIP upload failed: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to import recipe: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def ai_search(self, request):
        """
        AI-powered recipe search and creation

        POST /api/recipes/recipes/ai_search/
        {
            "query": "Italian pasta carbonara",
            "preferences": {
                "diet": "vegetarian",
                "allergies": ["nuts"]
            }
        }
        """
        query = request.data.get('query')
        if not query:
            return Response(
                {'error': 'Query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        preferences = request.data.get('preferences', {})

        # Run async service
        try:
            agent = RecipeAgentService()

            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success, recipe_data, message = loop.run_until_complete(
                agent.find_and_convert_recipe(query, preferences)
            )
            loop.close()

            if not success:
                return Response(
                    {'error': message},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check for duplicates
            duplicates = RecipeDeduplicationService.find_duplicate_recipes(
                recipe_data)

            if duplicates.exists():
                existing = duplicates.first()

                # Check if we should create a new version
                should_version = RecipeDeduplicationService.should_create_new_version(
                    existing,
                    recipe_data
                )

                if not should_version:
                    # Return existing recipe
                    serializer = RecipeSerializer(
                        existing, context={'request': request})
                    return Response({
                        'message': 'Recipe already exists in database',
                        'recipe': serializer.data,
                        'created': False
                    })

            # Create new recipe from RCIP data
            recipe = Recipe.objects.create(
                name=recipe_data['meta']['name'],
                description=recipe_data['meta']['description'],
                author=recipe_data['meta']['author'],
                source_url=recipe_data['meta']['source_url'],
                ingredients=recipe_data['ingredients'],
                steps=recipe_data['steps'],
                prep_time_minutes=recipe_data['meta']['prep_time_minutes'],
                cook_time_minutes=recipe_data['meta']['cook_time_minutes'],
                total_time_minutes=recipe_data['meta']['total_time_minutes'],
                servings=recipe_data['meta']['servings']['amount'],
                difficulty=recipe_data['meta']['difficulty'],
                diet_labels=recipe_data['meta']['diet_labels'],
                created_by=request.user
            )

            serializer = RecipeSerializer(recipe, context={'request': request})
            return Response({
                'message': message,
                'recipe': serializer.data,
                'created': True
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"[ERROR] AI Search Error: {e}")
            import traceback
            traceback.print_exc()

            return Response(
                {'error': f'Failed to process recipe: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserRecipeViewSet(viewsets.ModelViewSet):
    """User's saved recipes"""

    serializer_class = UserRecipeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get user's saved recipes"""
        return UserRecipe.objects.filter(
            user=self.request.user
        ).select_related('recipe')

    def perform_create(self, serializer):
        """Save recipe for user"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """Rate a saved recipe"""
        user_recipe = self.get_object()
        rating = request.data.get('rating')

        if not rating or not (1 <= int(rating) <= 5):
            return Response(
                {'error': 'Rating must be between 1 and 5'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_recipe.rating = rating
        user_recipe.save()

        return Response({
            'message': 'Recipe rated successfully',
            'rating': user_recipe.rating
        })

    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        """Add or update notes for a recipe"""
        user_recipe = self.get_object()
        notes = request.data.get('notes', '')

        user_recipe.notes = notes
        user_recipe.save()

        return Response({
            'message': 'Notes updated successfully',
            'notes': user_recipe.notes
        })
