from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponse
from asgiref.sync import async_to_sync
import json

from .models import (
    Recipe, UserRecipe, CanonicalRecipe,
    RecipeLike, RecipeRating, RecipeReview, RecipeReviewHelpful
)
from .serializers import (
    RecipeSerializer, CreateRecipeSerializer,
    UserRecipeSerializer, RCIPFormatSerializer,
    CanonicalRecipeSerializer, CanonicalRecipeListSerializer,
    RecipeLikeSerializer, RecipeRatingSerializer,
    RecipeReviewSerializer, CreateReviewSerializer
)
from .services import RecipeAgentService, RecipeDeduplicationService
from .builder import RecipeBuilderService
from .cache import RecipeCache
from .throttles import (
    ReviewRateThrottle, ReviewDailyThrottle,
    LikeRateThrottle, RatingRateThrottle,
    RecipeBuilderThrottle, RecipeBuilderDailyThrottle,
    RecipeSearchThrottle, RecipeSearchDailyThrottle,
    MarkHelpfulThrottle
)
from .tasks import update_canonical_recipe_statistics
from apps.shopping.models import ShoppingList, ShoppingItem
from django.shortcuts import get_object_or_404


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

    @action(detail=False, methods=['post'], throttle_classes=[RecipeSearchThrottle, RecipeSearchDailyThrottle])
    def find_recipe(self, request):
        """
        AI Agent endpoint: User describes what they want to cook
        Agent finds recipe, converts to RCIP, and optionally adds to shopping list

        Throttle: 20/hour, 100/day
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
            'allergies': request.user.allergies,
            'language': getattr(request.user, 'preferred_language', 'en'),
            'unit_system': 'metric' if getattr(request.user, 'weight_unit', 'kg') == 'kg' else 'imperial'
        }

        # Run recipe agent WITH DEDUPLICATION
        agent = RecipeAgentService()

        # Use async_to_sync to properly handle async function
        success, result, message = async_to_sync(agent.process_recipe_query)(
            user_query, request.user, user_preferences
        )

        if not success:
            return Response(
                {'error': message},
                status=status.HTTP_404_NOT_FOUND
            )

        # Result contains: canonical_recipe, user_recipe, is_new
        canonical_recipe = result['canonical_recipe']
        user_recipe = result['user_recipe']
        created = result['is_new']

        print(
            f"[RESULT] {'Created new' if created else 'Found existing'} canonical recipe: {canonical_recipe['name']}")
        print(f"[RESULT] User fork created/retrieved: {user_recipe['id']}")

        # Add to shopping list if requested (use canonical ingredients)
        added_items = []
        if add_to_shopping_list and shopping_list_id:
            # Create temp object to pass to shopping list method
            from .models import Recipe
            temp_recipe = type('obj', (object,), {
                'name': canonical_recipe['name'],
                'ingredients': canonical_recipe['base_ingredients']
            })()
            added_items = self._add_ingredients_to_shopping_list(
                temp_recipe,
                shopping_list_id,
                request.user
            )

        return Response({
            'success': True,
            'message': message,
            'canonical_recipe': canonical_recipe,
            'user_recipe': user_recipe,
            'created': created,
            'is_new_canonical': created,
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
        """Archive recipe (soft delete) from user's collection"""
        from django.utils import timezone
        recipe = self.get_object()

        try:
            user_recipe = UserRecipe.objects.get(
                user=request.user,
                recipe=recipe
            )
            user_recipe.is_archived = True
            user_recipe.archived_at = timezone.now()
            user_recipe.save(update_fields=['is_archived', 'archived_at'])

            return Response({
                'message': f'Recipe "{recipe.name}" moved to archive',
                'saved': False,
                'archived': True
            })
        except UserRecipe.DoesNotExist:
            return Response({
                'message': 'Recipe was not saved',
                'saved': False
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def restore_recipe(self, request, pk=None):
        """Restore archived recipe to user's collection"""
        recipe = self.get_object()

        try:
            user_recipe = UserRecipe.objects.get(
                user=request.user,
                recipe=recipe,
                is_archived=True
            )
            user_recipe.is_archived = False
            user_recipe.archived_at = None
            user_recipe.save(update_fields=['is_archived', 'archived_at'])

            return Response({
                'message': f'Recipe "{recipe.name}" restored to My Recipes',
                'saved': True,
                'archived': False
            })
        except UserRecipe.DoesNotExist:
            return Response({
                'message': 'Recipe is not archived',
                'error': True
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['delete'])
    def permanently_delete_recipe(self, request, pk=None):
        """Permanently delete recipe from user's collection (from archive only)"""
        recipe = self.get_object()

        deleted_count, _ = UserRecipe.objects.filter(
            user=request.user,
            recipe=recipe,
            is_archived=True
        ).delete()

        if deleted_count > 0:
            return Response({
                'message': f'Recipe "{recipe.name}" permanently deleted',
                'deleted': True
            })
        else:
            return Response({
                'message': 'Recipe is not archived or does not exist',
                'error': True
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def mark_cooked(self, request, pk=None):
        """
        Toggle recipe cooked status (like the Like button)
        - First click: Mark as cooked (increment global counter)
        - Second click: Unmark (decrement global counter)
        Global counter shows total times cooked by ALL users
        """
        recipe = self.get_object()

        try:
            user_recipe = UserRecipe.objects.get(
                user=request.user, recipe=recipe)

            # Check if already marked as cooked (using last_cooked as indicator)
            if user_recipe.last_cooked is not None:
                # Unmark as cooked
                user_recipe.last_cooked = None
                user_recipe.times_cooked = max(0, user_recipe.times_cooked - 1)
                user_recipe.save()

                # Decrement global counter
                recipe.times_cooked = max(0, recipe.times_cooked - 1)
                recipe.save()

                cooked = False
                message = 'Recipe unmarked as cooked'
                print(
                    f"[COOKED] User {request.user.username} unmarked {recipe.name} as cooked")
            else:
                # Mark as cooked
                user_recipe.times_cooked += 1
                user_recipe.last_cooked = timezone.now()
                user_recipe.save()

                # Increment global counter
                recipe.times_cooked += 1
                recipe.save()

                cooked = True
                message = 'Recipe marked as cooked'
                print(
                    f"[COOKED] User {request.user.username} marked {recipe.name} as cooked")

            return Response({
                'message': message,
                'cooked': cooked,
                'user_times_cooked': user_recipe.times_cooked,
                'global_times_cooked': recipe.times_cooked
            })
        except UserRecipe.DoesNotExist:
            return Response(
                {'error': 'Recipe not saved. Save it first before marking as cooked.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def my_recipes(self, request):
        """Get user's saved recipes (excluding archived)"""
        user_recipes = UserRecipe.objects.filter(
            user=request.user,
            is_archived=False
        ).select_related('recipe').order_by('-saved_at')

        # Flatten the structure: merge UserRecipe and Recipe data
        recipes_data = []
        for user_recipe in user_recipes:
            recipe = user_recipe.recipe
            recipe_data = RecipeSerializer(
                recipe, context={'request': request}).data
            recipe_data['is_saved'] = True  # All my_recipes are saved
            recipe_data['saved_at'] = user_recipe.saved_at
            recipe_data['times_cooked'] = user_recipe.times_cooked
            recipe_data['last_cooked'] = user_recipe.last_cooked
            recipe_data['user_notes'] = user_recipe.notes
            recipe_data['user_rating'] = user_recipe.rating
            recipes_data.append(recipe_data)

        return Response({
            'recipes': recipes_data,
            'total': user_recipes.count()
        })

    @action(detail=False, methods=['get'])
    def archived_recipes(self, request):
        """Get user's archived recipes"""
        archived_recipes = UserRecipe.objects.filter(
            user=request.user,
            is_archived=True
        ).select_related('recipe').order_by('-archived_at')

        # Flatten the structure: merge UserRecipe and Recipe data
        recipes_data = []
        for user_recipe in archived_recipes:
            recipe = user_recipe.recipe
            recipe_data = RecipeSerializer(
                recipe, context={'request': request}).data
            # Archived recipes are not actively "saved"
            recipe_data['is_saved'] = False
            recipe_data['archived_at'] = user_recipe.archived_at
            recipe_data['times_cooked'] = user_recipe.times_cooked
            recipe_data['last_cooked'] = user_recipe.last_cooked
            recipe_data['user_notes'] = user_recipe.notes
            recipe_data['user_rating'] = user_recipe.rating
            recipes_data.append(recipe_data)

        return Response({
            'recipes': recipes_data,
            'total': archived_recipes.count()
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
        AI-powered recipe search and creation WITH DEDUPLICATION

        POST /api/recipes/recipes/ai_search/
        {
            "query": "Italian pasta carbonara",
            "preferences": {
                "diet": "vegetarian",
                "allergies": ["nuts"]
            }
        }

        Returns:
        {
            "success": true,
            "canonical_recipe": {...},  // Master recipe
            "user_recipe": {...},       // User's fork
            "is_new": false,            // Whether canonical was just created
            "message": "Found existing recipe: Italian Pasta Carbonara"
        }
        """
        query = request.data.get('query')
        if not query:
            return Response(
                {'error': 'Query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        preferences = request.data.get('preferences', {})

        # Run async service WITH DEDUPLICATION
        try:
            agent = RecipeAgentService()

            # Use async_to_sync to properly handle async function
            success, result, message = async_to_sync(agent.process_recipe_query)(
                query, request.user, preferences
            )

            if not success:
                return Response(
                    {'error': message},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Result contains: canonical_recipe, user_recipe, is_new
            return Response({
                'success': True,
                'canonical_recipe': result['canonical_recipe'],
                'user_recipe': result['user_recipe'],
                'is_new': result['is_new'],
                'message': message
            }, status=status.HTTP_201_CREATED if result['is_new'] else status.HTTP_200_OK)

        except Exception as e:
            print(f"[ERROR] AI Search Error: {e}")
            import traceback
            traceback.print_exc()

            return Response(
                {'error': f'Failed to process recipe: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], throttle_classes=[RecipeBuilderThrottle, RecipeBuilderDailyThrottle])
    def start_builder(self, request):
        """
        Start recipe builder session

        POST /api/recipes/recipes/start_builder/

        Returns:
        {
            "session_id": "uuid",
            "current_step": "basic_info",
            "message": "Builder session started"
        }

        Throttle: 10/hour, 30/day
        """
        builder = RecipeBuilderService()

        # Use async_to_sync to properly handle async function
        session_id = async_to_sync(
            builder.create_builder_session)(request.user)

        return Response({
            'session_id': session_id,
            'current_step': 'basic_info',
            'message': 'Builder session started. Please provide basic recipe information.',
            'steps': ['basic_info', 'ingredients', 'steps', 'finalize']
        })

    @action(detail=False, methods=['post'])
    def builder_step(self, request):
        """
        Process builder step with AI assistance

        POST /api/recipes/recipes/builder_step/
        {
            "session_id": "uuid",
            "step": "basic_info|ingredients|steps|review|finalize",
            "data": {
                // Step-specific data
            }
        }

        STEP 1 - Basic Info:
        {
            "session_id": "...",
            "step": "basic_info",
            "data": {
                "name": "Summer Greek Salad",
                "cuisine": "Greek",
                "servings": 4,
                "difficulty": "beginner",
                "description": "Fresh and healthy salad"
            }
        }

        STEP 2 - Ingredients:
        {
            "session_id": "...",
            "step": "ingredients",
            "data": {
                "ingredients": [
                    "4 tomatoes",
                    "2 cucumbers",
                    "200g feta cheese",
                    "3 tbsp olive oil"
                ]
            }
        }

        STEP 3 - Steps:
        {
            "session_id": "...",
            "step": "steps",
            "data": {
                "steps_description": "Chop vegetables, mix in bowl, add dressing"
                // OR
                "steps": ["Step 1 text", "Step 2 text", ...]
            }
        }

        STEP 4 - Review & Edit (First Call - Get compiled recipe):
        {
            "session_id": "...",
            "step": "review",
            "data": {}
        }
        Returns compiled recipe data for user to review/edit

        STEP 4 - Review & Edit (Second Call - Save edits):
        {
            "session_id": "...",
            "step": "review",
            "data": {
                "save_edits": true,
                "edited_data": {
                    "basic_info": {...},
                    "ingredients": [{...}],
                    "steps": [{...}],
                    "estimated_times": {...}
                }
            }
        }

        STEP 5 - Finalize:
        {
            "session_id": "...",
            "step": "finalize",
            "data": {
                "is_public": true,
                "description": "Additional notes",
                "tags": ["healthy", "quick"]
            }
        }
        """
        session_id = request.data.get('session_id')
        step = request.data.get('step')
        data = request.data.get('data', {})

        if not session_id or not step:
            return Response(
                {'error': 'session_id and step are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        builder = RecipeBuilderService()

        try:
            # Use async_to_sync to properly handle async function
            result = async_to_sync(builder.process_step)(
                session_id, step, data)

            if not result.get('success'):
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

            # If finalize step, return 201 Created
            if step == 'finalize':
                return Response(result, status=status.HTTP_201_CREATED)

            return Response(result)

        except ValueError as e:
            return Response(
                {'error': str(e), 'current_step': step},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print(f"[ERROR] Builder step error: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to process step: {str(e)}'},
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


# ============================================================================
# CANONICAL RECIPES VIEWSET (Social Features)
# ============================================================================

class CanonicalRecipeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for canonical recipes with social features

    Endpoints:
    - GET /canonical/ - List canonical recipes
    - GET /canonical/{id}/ - Get canonical recipe details
    - POST /canonical/{id}/like/ - Toggle like
    - POST /canonical/{id}/rate/ - Rate recipe (1-5 stars)
    - POST /canonical/{id}/add_review/ - Add review
    - GET /canonical/{id}/reviews/ - Get reviews (sortable)
    - PATCH /canonical/{id}/reviews/{review_id}/ - Update review
    - DELETE /canonical/{id}/reviews/{review_id}/ - Delete review
    - POST /canonical/{id}/reviews/{review_id}/helpful/ - Mark review helpful
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get published canonical recipes"""
        queryset = CanonicalRecipe.objects.filter(is_published=True)

        # Filter by search query
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(cuisine__icontains=search)
            )

        # Filter by cuisine
        cuisine = self.request.query_params.get('cuisine', None)
        if cuisine:
            queryset = queryset.filter(cuisine__iexact=cuisine)

        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty', None)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        # Filter by diet labels
        diet = self.request.query_params.get('diet', None)
        if diet:
            queryset = queryset.filter(diet_labels__contains=[diet])

        # Filter by source type
        source_type = self.request.query_params.get('source_type', None)
        if source_type:
            queryset = queryset.filter(source_type=source_type)

        # Sorting
        sort = self.request.query_params.get('sort', 'recent')
        if sort == 'popular':
            queryset = queryset.order_by('-total_saves', '-average_rating')
        elif sort == 'top_rated':
            queryset = queryset.order_by('-average_rating', '-total_ratings')
        elif sort == 'most_cooked':
            queryset = queryset.order_by('-total_cooked')
        else:  # recent
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_serializer_class(self):
        """Use lighter serializer for list view"""
        if self.action == 'list':
            return CanonicalRecipeListSerializer
        return CanonicalRecipeSerializer

    @action(detail=True, methods=['post'], throttle_classes=[LikeRateThrottle])
    def like(self, request, pk=None):
        """
        Toggle like on canonical recipe
        When liked, automatically saves recipe to user's collection (My Recipes)

        POST /api/recipes/canonical/{id}/like/

        Returns:
        {
            "liked": true/false,
            "total_likes": 123,
            "saved_to_my_recipes": true/false
        }
        """
        canonical = self.get_object()

        like, created = RecipeLike.objects.get_or_create(
            user=request.user,
            canonical_recipe=canonical
        )

        saved_to_my_recipes = False

        if not created:
            # Unlike
            like.delete()
            liked = False
            print(
                f"[LIKE] User {request.user.username} unliked {canonical.name}")
        else:
            liked = True
            print(
                f"[LIKE] User {request.user.username} liked {canonical.name}")

            # When user likes a recipe, automatically save it to their collection
            # Create or get user's fork of this canonical recipe
            from .services import RecipeAgentService
            from asgiref.sync import async_to_sync

            try:
                agent = RecipeAgentService()
                # This will create a fork + UserRecipe entry if needed
                user_fork = async_to_sync(agent._create_or_get_user_fork)(
                    request.user, canonical
                )
                saved_to_my_recipes = True
                print(f"[LIKE] Recipe saved to My Recipes: {user_fork.id}")
            except Exception as e:
                print(f"[ERROR] Failed to save recipe to My Recipes: {e}")

        # Get updated like count
        total_likes = canonical.likes.count()

        # Invalidate caches (gracefully handle if Redis not running)
        try:
            RecipeCache.invalidate_user_likes(str(request.user.id))
            RecipeCache.invalidate_all_for_recipe(str(canonical.id))
        except Exception as e:
            print(
                f"[WARNING] Could not invalidate cache (Redis may not be running): {e}")

        # Queue background task to update statistics (optional - gracefully handle if Redis/Celery not running)
        try:
            update_canonical_recipe_statistics.delay(str(canonical.id))
        except Exception as e:
            print(
                f"[WARNING] Could not queue background task (Redis/Celery may not be running): {e}")
            # Continue anyway - statistics will be eventually consistent

        return Response({
            'liked': liked,
            'total_likes': total_likes,
            'user_liked': liked,
            'saved_to_my_recipes': saved_to_my_recipes
        })

    @action(detail=True, methods=['get'])
    def likes_status(self, request, pk=None):
        """
        Get like status for current user

        GET /api/recipes/canonical/{id}/likes_status/

        Returns:
        {
            "user_liked": true,
            "total_likes": 123
        }
        """
        canonical = self.get_object()

        user_liked = RecipeLike.objects.filter(
            user=request.user,
            canonical_recipe=canonical
        ).exists()

        total_likes = canonical.likes.count()

        return Response({
            'user_liked': user_liked,
            'total_likes': total_likes
        })

    @action(detail=True, methods=['post'], throttle_classes=[RatingRateThrottle])
    def rate(self, request, pk=None):
        """
        Rate canonical recipe (1-5 stars)

        POST /api/recipes/canonical/{id}/rate/
        Body: {"rating": 5}

        Returns:
        {
            "success": true,
            "your_rating": 5,
            "average_rating": 4.5,
            "total_ratings": 42
        }
        """
        canonical = self.get_object()
        rating_value = request.data.get('rating')

        if not rating_value or not (1 <= int(rating_value) <= 5):
            return Response(
                {'error': 'Rating must be between 1 and 5'},
                status=status.HTTP_400_BAD_REQUEST
            )

        rating, created = RecipeRating.objects.update_or_create(
            user=request.user,
            canonical_recipe=canonical,
            defaults={'rating': int(rating_value)}
        )

        # Update canonical's average rating (denormalized)
        self._update_average_rating(canonical)

        # Invalidate caches (gracefully handle if Redis not running)
        try:
            RecipeCache.invalidate_user_ratings(str(request.user.id))
            RecipeCache.invalidate_all_for_recipe(str(canonical.id))
        except Exception as e:
            print(
                f"[WARNING] Could not invalidate cache (Redis may not be running): {e}")

        action_text = 'rated' if created else 'updated rating for'
        print(
            f"[RATING] User {request.user.username} {action_text} {canonical.name}: {rating_value}/5")

        return Response({
            'success': True,
            'your_rating': rating.rating,
            'average_rating': float(canonical.average_rating),
            'total_ratings': canonical.total_ratings,
            'message': f'Recipe rated {rating.rating}/5'
        })

    def _update_average_rating(self, canonical: CanonicalRecipe):
        """Update denormalized rating fields"""
        from django.db.models import Avg, Count

        stats = canonical.ratings.aggregate(
            avg=Avg('rating'),
            count=Count('id')
        )

        canonical.average_rating = stats['avg'] or 0
        canonical.total_ratings = stats['count']
        canonical.save(update_fields=['average_rating', 'total_ratings'])

    @action(detail=True, methods=['post'], throttle_classes=[ReviewRateThrottle, ReviewDailyThrottle])
    def add_review(self, request, pk=None):
        """
        Add review to canonical recipe

        POST /api/recipes/canonical/{id}/add_review/
        Body: {
            "title": "Amazing recipe!",
            "content": "I made this and it was delicious...",
            "rating": 5
        }

        Returns review data
        """
        canonical = self.get_object()

        # Check if user already reviewed
        if RecipeReview.objects.filter(user=request.user, canonical_recipe=canonical).exists():
            return Response(
                {'error': 'You already reviewed this recipe. Edit your existing review instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CreateReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = RecipeReview.objects.create(
            user=request.user,
            canonical_recipe=canonical,
            title=serializer.validated_data.get('title', ''),
            content=serializer.validated_data['content'],
            rating=serializer.validated_data['rating']
        )

        # Update canonical statistics
        canonical.total_reviews += 1
        canonical.save(update_fields=['total_reviews'])

        # Also create/update rating
        RecipeRating.objects.update_or_create(
            user=request.user,
            canonical_recipe=canonical,
            defaults={'rating': review.rating}
        )
        self._update_average_rating(canonical)

        # Invalidate caches
        RecipeCache.invalidate_review_list(str(canonical.id))
        RecipeCache.invalidate_all_for_recipe(str(canonical.id))

        print(
            f"[REVIEW] User {request.user.username} reviewed {canonical.name}: {review.rating}/5")

        return Response(
            RecipeReviewSerializer(review, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """
        Get reviews for canonical recipe

        GET /api/recipes/canonical/{id}/reviews/?sort=helpful|recent|rating

        Returns paginated reviews
        """
        canonical = self.get_object()
        sort_by = request.query_params.get('sort', 'helpful')

        reviews_qs = canonical.reviews.filter(is_approved=True)

        if sort_by == 'helpful':
            reviews_qs = reviews_qs.order_by('-helpful_count', '-created_at')
        elif sort_by == 'recent':
            reviews_qs = reviews_qs.order_by('-created_at')
        elif sort_by == 'rating':
            reviews_qs = reviews_qs.order_by('-rating', '-helpful_count')
        else:
            reviews_qs = reviews_qs.order_by('-created_at')

        # Pagination
        page = self.paginate_queryset(reviews_qs)
        if page is not None:
            serializer = RecipeReviewSerializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = RecipeReviewSerializer(
            reviews_qs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['patch', 'delete'], url_path='reviews/(?P<review_id>[^/.]+)')
    def manage_review(self, request, pk=None, review_id=None):
        """
        Update or delete user's review

        PATCH /api/recipes/canonical/{id}/reviews/{review_id}/
        Body: {
            "title": "Updated title",
            "content": "Updated content",
            "rating": 4
        }

        DELETE /api/recipes/canonical/{id}/reviews/{review_id}/
        """
        canonical = self.get_object()
        review = get_object_or_404(
            RecipeReview,
            id=review_id,
            canonical_recipe=canonical,
            user=request.user  # Only owner can update/delete
        )

        if request.method == 'PATCH':
            # Update review
            serializer = CreateReviewSerializer(
                data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            for field, value in serializer.validated_data.items():
                setattr(review, field, value)
            review.save()

            # Update rating if changed
            if 'rating' in serializer.validated_data:
                RecipeRating.objects.update_or_create(
                    user=request.user,
                    canonical_recipe=canonical,
                    defaults={'rating': review.rating}
                )
                self._update_average_rating(canonical)

            print(
                f"[REVIEW] User {request.user.username} updated review for {canonical.name}")

            return Response(
                RecipeReviewSerializer(
                    review, context={'request': request}).data
            )

        elif request.method == 'DELETE':
            # Delete review
            review.delete()

            # Update canonical statistics
            canonical.total_reviews = max(0, canonical.total_reviews - 1)
            canonical.save(update_fields=['total_reviews'])

            print(
                f"[REVIEW] User {request.user.username} deleted review for {canonical.name}")

            return Response(
                {'message': 'Review deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(detail=True, methods=['post'], url_path='reviews/(?P<review_id>[^/.]+)/helpful')
    def mark_review_helpful(self, request, pk=None, review_id=None):
        """
        Mark review as helpful (toggle)

        POST /api/recipes/canonical/{id}/reviews/{review_id}/helpful/

        Returns:
        {
            "marked_helpful": true/false,
            "helpful_count": 5
        }

        Throttle: MarkHelpfulThrottle (50/hour)
        """
        canonical = self.get_object()
        review = get_object_or_404(
            RecipeReview,
            id=review_id,
            canonical_recipe=canonical
        )

        helpful, created = RecipeReviewHelpful.objects.get_or_create(
            user=request.user,
            review=review
        )

        if not created:
            # Toggle off
            helpful.delete()
            review.helpful_count = max(0, review.helpful_count - 1)
            marked_helpful = False
            action_text = 'unmarked'
        else:
            review.helpful_count += 1
            marked_helpful = True
            action_text = 'marked'

        review.save(update_fields=['helpful_count'])

        # Invalidate review list cache
        RecipeCache.invalidate_review_list(str(canonical.id))

        print(
            f"[HELPFUL] User {request.user.username} {action_text} review as helpful")

        return Response({
            'marked_helpful': marked_helpful,
            'helpful_count': review.helpful_count
        })
