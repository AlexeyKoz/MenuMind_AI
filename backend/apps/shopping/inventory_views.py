"""
Inventory Management Views - Complete API endpoints for inventory
"""
from .inventory_services import InventoryCategorizationService, InventoryRecipeGenerator
from .serializers import (
    InventorySerializer,
    InventoryHistorySerializer,
    AICategorizationSuggestionSerializer,
    BulkInventoryCreateSerializer,
    InventoryConsumeSerializer,
    RecipeFromInventorySerializer
)
from .models import Inventory, InventoryHistory, ShoppingList, ShoppingItem
import logging
from rest_framework import views
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class InventoryViewSet(viewsets.ModelViewSet):
    """
    Complete Inventory Management API

    Endpoints:
    - GET /api/inventory/ - List all user's inventory
    - POST /api/inventory/ - Create single item
    - GET /api/inventory/{id}/ - Get detail
    - PATCH /api/inventory/{id}/ - Update item
    - DELETE /api/inventory/{id}/ - Delete item
    - GET /api/inventory/expiring_soon/ - Items expiring within 7 days
    - GET /api/inventory/low_stock/ - Items below threshold
    - GET /api/inventory/by_location/ - Filter by location
    - PATCH /api/inventory/{id}/move/ - Move item to different location
    - GET /api/inventory/{id}/history/ - Get item history
    - POST /api/inventory/bulk_create/ - Create multiple items
    - POST /api/inventory/consume/ - Consume items (cooking)
    - POST /api/inventory/generate_recipes/ - AI recipe generation
    """

    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get user's inventory items + items from collaborative shopping lists
        """
        user = self.request.user

        # Get user's own items
        queryset = Inventory.objects.filter(user=user)

        # Add items from collaborative shopping lists
        # (items where shopping_list is linked and user is collaborator)
        collaborative_lists = ShoppingList.objects.filter(
            collaborators__user=user
        ).distinct()

        collaborative_items = Inventory.objects.filter(
            shopping_list__in=collaborative_lists
        )

        # Combine
        queryset = (queryset | collaborative_items).distinct()

        # Order by location and name only (avoid issues with null expiration_date)
        return queryset.select_related('shopping_list').order_by('location', 'name')

    def perform_create(self, serializer):
        """Create inventory item"""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Update inventory item and create history entry"""
        instance = self.get_object()
        old_quantity = instance.quantity
        old_location = instance.location

        # Save the update
        updated_instance = serializer.save()

        # Create history entry if quantity or location changed
        if updated_instance.quantity != old_quantity:
            InventoryHistory.objects.create(
                inventory_item=updated_instance,
                action='adjusted',
                quantity_change=updated_instance.quantity - old_quantity,
                previous_quantity=old_quantity,
                new_quantity=updated_instance.quantity,
                notes=f"Manual adjustment by {self.request.user.username}"
            )

        if updated_instance.location != old_location:
            InventoryHistory.objects.create(
                inventory_item=updated_instance,
                action='moved',
                quantity_change=Decimal('0'),
                previous_quantity=updated_instance.quantity,
                new_quantity=updated_instance.quantity,
                notes=f"Moved from {old_location} to {updated_instance.location}"
            )

    def perform_destroy(self, instance):
        """Delete inventory item with history"""
        InventoryHistory.objects.create(
            inventory_item=instance,
            action='deleted',
            quantity_change=-instance.quantity,
            previous_quantity=instance.quantity,
            new_quantity=Decimal('0'),
            notes=f"Deleted by {self.request.user.username}"
        )
        instance.delete()

    # ===== Custom Query Endpoints =====

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """
        Get items expiring within 7 days

        GET /api/inventory/expiring_soon/
        Query params:
        - days: Number of days (default: 7)
        """
        days = int(request.query_params.get('days', 7))
        today = timezone.now().date()
        expiry_date = today + timedelta(days=days)

        items = self.get_queryset().filter(
            expiration_date__lte=expiry_date,
            expiration_date__gte=today
        ).order_by('expiration_date')

        serializer = self.get_serializer(items, many=True)
        return Response({
            'count': items.count(),
            'items': serializer.data
        })

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """
        Get items below low stock threshold

        GET /api/inventory/low_stock/
        """
        items = [item for item in self.get_queryset() if item.is_low_stock]
        serializer = self.get_serializer(items, many=True)

        return Response({
            'count': len(items),
            'items': serializer.data
        })

    @action(detail=False, methods=['get'])
    def by_location(self, request):
        """
        Get items by location with counts

        GET /api/inventory/by_location/?location=fridge
        """
        location = request.query_params.get('location')

        if not location:
            # Return summary by location
            queryset = self.get_queryset()
            print(
                f"[INVENTORY] by_location called for user: {request.user}, queryset count: {queryset.count()}")
            summary = {}

            for loc, _ in Inventory._meta.get_field('location').choices:
                items = queryset.filter(location=loc)
                expiring_count = sum(
                    1 for item in items if item.is_expiring_soon)

                print(
                    f"[INVENTORY] Location {loc}: {items.count()} items, {expiring_count} expiring")

                summary[loc] = {
                    'count': items.count(),
                    'expiring_count': expiring_count,
                    'items': InventorySerializer(items, many=True).data
                }

            return Response(summary)

        # Filter by specific location
        items = self.get_queryset().filter(location=location)
        serializer = self.get_serializer(items, many=True)

        return Response({
            'location': location,
            'count': items.count(),
            'items': serializer.data
        })

    # ===== Item-specific actions =====

    @action(detail=True, methods=['patch'])
    def move(self, request, pk=None):
        """
        Move item to different location

        PATCH /api/inventory/{id}/move/
        Body: {"new_location": "freezer"}
        """
        item = self.get_object()
        new_location = request.data.get('new_location')

        if not new_location:
            return Response(
                {'error': 'new_location is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        valid_locations = [choice[0]
                           for choice in Inventory._meta.get_field('location').choices]
        if new_location not in valid_locations:
            return Response(
                {'error': f'Invalid location. Must be one of: {", ".join(valid_locations)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_location = item.location
        item.location = new_location
        item.save()

        # Create history entry
        InventoryHistory.objects.create(
            inventory_item=item,
            action='moved',
            quantity_change=Decimal('0'),
            previous_quantity=item.quantity,
            new_quantity=item.quantity,
            notes=f"Moved from {old_location} to {new_location}"
        )

        serializer = self.get_serializer(item)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        Get history for specific item

        GET /api/inventory/{id}/history/
        """
        item = self.get_object()
        history = item.history.all()[:20]  # Last 20 entries

        serializer = InventoryHistorySerializer(history, many=True)
        return Response({
            'item': InventorySerializer(item).data,
            'history': serializer.data
        })

    # ===== Bulk operations =====

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Create multiple inventory items at once

        POST /api/inventory/bulk_create/
        Body:
        {
            "items": [
                {
                    "name": "Milk",
                    "quantity": 1,
                    "unit": "L",
                    "location": "fridge",
                    "category": "dairy",
                    "expiration_date": "2025-10-18",
                    "shopping_list_id": "uuid" (optional)
                },
                ...
            ]
        }
        """
        bulk_serializer = BulkInventoryCreateSerializer(data=request.data)
        bulk_serializer.is_valid(raise_exception=True)

        items_data = bulk_serializer.validated_data['items']
        created_items = []
        merged_items = []
        errors = []

        for item_data in items_data:
            try:
                # Handle shopping_list_id
                shopping_list_id = item_data.pop('shopping_list_id', None)
                shopping_list = None

                if shopping_list_id:
                    try:
                        shopping_list = ShoppingList.objects.get(
                            id=shopping_list_id
                        )
                        if not shopping_list.can_access(request.user):
                            errors.append({
                                'item': item_data.get('name'),
                                'error': 'No access to shopping list'
                            })
                            continue
                    except ShoppingList.DoesNotExist:
                        pass

                # Clean up expiration_date: convert empty string to None or parse date string
                if 'expiration_date' in item_data:
                    if item_data['expiration_date'] == '' or item_data['expiration_date'] is None:
                        item_data['expiration_date'] = None
                    elif isinstance(item_data['expiration_date'], str):
                        # Parse date string to date object
                        try:
                            item_data['expiration_date'] = datetime.strptime(
                                item_data['expiration_date'], '%Y-%m-%d'
                            ).date()
                        except ValueError:
                            item_data['expiration_date'] = None

                # Clean up purchase_date: convert empty string to None or parse date string
                if 'purchase_date' in item_data:
                    if item_data['purchase_date'] == '' or item_data['purchase_date'] is None:
                        item_data['purchase_date'] = None
                    elif isinstance(item_data['purchase_date'], str):
                        # Parse date string to date object
                        try:
                            item_data['purchase_date'] = datetime.strptime(
                                item_data['purchase_date'], '%Y-%m-%d'
                            ).date()
                        except ValueError:
                            item_data['purchase_date'] = None

                # Check if item already exists (same name + location)
                existing_item = Inventory.objects.filter(
                    user=request.user,
                    name__iexact=item_data['name'],  # Case-insensitive match
                    location=item_data['location']
                ).first()

                if existing_item:
                    # Item exists - update quantity and expiration date
                    previous_qty = existing_item.quantity
                    new_quantity = item_data['quantity']
                    existing_item.quantity += new_quantity

                    # Update expiration date if new date is sooner (items expiring sooner should be prioritized)
                    if item_data.get('expiration_date'):
                        if not existing_item.expiration_date or item_data['expiration_date'] < existing_item.expiration_date:
                            existing_item.expiration_date = item_data['expiration_date']

                    existing_item.save()

                    # Create history entry for addition to existing item
                    InventoryHistory.objects.create(
                        inventory_item=existing_item,
                        action='adjusted',
                        quantity_change=new_quantity,
                        previous_quantity=previous_qty,
                        new_quantity=existing_item.quantity,
                        notes=f"Added {new_quantity}{existing_item.unit} from shopping list (merged with existing)"
                    )

                    merged_items.append(existing_item)
                else:
                    # Create new item
                    item = Inventory.objects.create(
                        user=request.user,
                        shopping_list=shopping_list,
                        **item_data
                    )

                    # Create history entry for new item
                    InventoryHistory.objects.create(
                        inventory_item=item,
                        action='added',
                        quantity_change=item.quantity,
                        previous_quantity=Decimal('0'),
                        new_quantity=item.quantity,
                        notes=f"Added from shopping list" if shopping_list else "Manually added"
                    )

                    created_items.append(item)

            except Exception as e:
                errors.append({
                    'item': item_data.get('name'),
                    'error': str(e)
                })

        # Combine all items for serialization (both new and merged)
        all_items = created_items + merged_items
        print(
            f"[INVENTORY] bulk_create completed: {len(created_items)} new, {len(merged_items)} merged, {len(errors)} errors")
        print(
            f"[INVENTORY] Created item IDs: {[item.id for item in created_items]}")
        print(
            f"[INVENTORY] Merged item IDs: {[item.id for item in merged_items]}")

        serializer = self.get_serializer(all_items, many=True)

        return Response({
            'success': True,
            'created_count': len(created_items),
            'merged_count': len(merged_items),
            'total_count': len(all_items),
            'error_count': len(errors),
            'items': serializer.data,
            'errors': errors,
            'message': f"Successfully processed {len(all_items)} items ({len(created_items)} new, {len(merged_items)} merged with existing)"
        }, status=status.HTTP_201_CREATED if all_items else status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def consume(self, request):
        """
        Consume inventory items (e.g., when cooking)

        POST /api/inventory/consume/
        Body:
        {
            "items": [
                {"inventory_id": "uuid", "quantity_used": 300, "unit": "g"},
                ...
            ],
            "recipe_id": "uuid" (optional),
            "notes": "Cooked Chicken Curry"
        }
        """
        consume_serializer = InventoryConsumeSerializer(data=request.data)
        consume_serializer.is_valid(raise_exception=True)

        items_data = consume_serializer.validated_data['items']
        recipe_id = consume_serializer.validated_data.get('recipe_id')
        notes = consume_serializer.validated_data.get('notes', '')

        recipe = None
        if recipe_id:
            from apps.recipes.models import Recipe
            try:
                recipe = Recipe.objects.get(id=recipe_id)
            except Recipe.DoesNotExist:
                pass

        consumed_items = []
        errors = []

        for item_data in items_data:
            try:
                inventory_id = item_data['inventory_id']
                quantity_used = Decimal(str(item_data['quantity_used']))

                item = Inventory.objects.get(id=inventory_id)

                # Check permission
                if not item.can_access(request.user):
                    errors.append({
                        'item': str(inventory_id),
                        'error': 'No permission to access this item'
                    })
                    continue

                # Check sufficient quantity
                if item.quantity < quantity_used:
                    errors.append({
                        'item': item.name,
                        'error': f'Insufficient quantity (has: {item.quantity}, needs: {quantity_used})'
                    })
                    continue

                # Update quantity
                old_quantity = item.quantity
                item.quantity -= quantity_used
                item.save()

                # Create history entry
                InventoryHistory.objects.create(
                    inventory_item=item,
                    action='consumed',
                    quantity_change=-quantity_used,
                    previous_quantity=old_quantity,
                    new_quantity=item.quantity,
                    recipe=recipe,
                    notes=notes or f"Used in cooking"
                )

                consumed_items.append(item)

            except Inventory.DoesNotExist:
                errors.append({
                    'item': item_data.get('inventory_id'),
                    'error': 'Item not found'
                })
            except Exception as e:
                errors.append({
                    'item': item_data.get('inventory_id'),
                    'error': str(e)
                })

        serializer = self.get_serializer(consumed_items, many=True)

        return Response({
            'success': True,
            'consumed_count': len(consumed_items),
            'error_count': len(errors),
            'items': serializer.data,
            'errors': errors
        })

    @action(detail=False, methods=['post'], url_path='recipe-briefs')
    def recipe_briefs(self, request):
        """
        Generate recipe briefs from inventory (NEW AGENT)

        This is the entry point for the new inventory recipe agent.
        It generates short recipe briefs (5 at a time) and caches them for 24h.

        POST /api/inventory/recipe-briefs/
        Query params:
            - offset: Number of recipes to skip (default: 0)
            - count: Number of recipes to return (default: 5)

        Response:
        {
            "success": true,
            "briefs": [...],
            "total_generated": 10,
            "can_generate_more": true,
            "cached": false,
            "cache_expires_at": "2025-10-24T12:00:00"
        }
        """
        from apps.inventory.inventory_recipe_agent import get_inventory_recipe_agent

        # Get inventory items
        inventory_items = self.get_queryset()
        items_data = []
        for item in inventory_items:
            items_data.append({
                'name': item.name,
                'quantity': float(item.quantity),
                'unit': item.unit,
                'category': item.category,
                'location': item.location,
                'expiration_date': item.expiration_date.isoformat() if item.expiration_date else None
            })

        # Get parameters
        offset = int(request.query_params.get('offset', 0))
        count = int(request.query_params.get('count', 5))

        # Generate briefs
        agent = get_inventory_recipe_agent()
        result = agent.generate_recipe_briefs(
            user_id=str(request.user.id),
            inventory_items=items_data,
            count=count,
            offset=offset
        )

        return Response({
            'success': True,
            **result
        })

    @action(detail=False, methods=['post'], url_path='generate-full-recipe')
    def generate_full_recipe(self, request):
        """
        Generate full recipe from a brief (NEW AGENT)

        This endpoint:
        1. Takes a recipe brief
        2. Generates full recipe with detailed steps
        3. Checks for duplicates using deduplication service
        4. Returns full recipe (or duplicate if found)

        POST /api/inventory/generate-full-recipe/
        Body:
        {
            "brief": {
                "name": "Recipe Name",
                "description": "...",
                "main_ingredients": [...],
                "cook_time_minutes": 30,
                "difficulty": "intermediate",
                "cuisine": "Italian"
            }
        }

        Response:
        {
            "success": true,
            "is_duplicate": false,
            "recipe": {...},
            "duplicate_id": null  # or UUID if duplicate
        }
        """
        from apps.inventory.inventory_recipe_agent import get_inventory_recipe_agent
        from apps.core.deduplication_service import get_deduplication_service
        from apps.recipes.models import CanonicalRecipe

        # Get brief from request
        brief = request.data.get('brief')
        if not brief:
            return Response({
                'success': False,
                'error': 'Recipe brief is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get user's language
        target_language = self._get_user_language(request)

        # Get inventory items
        inventory_items = self.get_queryset()
        items_data = []
        for item in inventory_items:
            items_data.append({
                'name': item.name,
                'quantity': float(item.quantity),
                'unit': item.unit,
                'category': item.category
            })

        # Generate full recipe
        agent = get_inventory_recipe_agent()
        full_recipe = agent.generate_full_recipe(
            brief=brief,
            inventory_items=items_data,
            target_language=target_language
        )

        if not full_recipe:
            return Response({
                'success': False,
                'error': 'Failed to generate recipe'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Check for duplicates
        dedup_service = get_deduplication_service()
        duplicate = dedup_service.check_duplicate(
            recipe_name=full_recipe['name'],
            ingredients=[ing['name']
                         for ing in full_recipe.get('ingredients', [])]
        )

        if duplicate:
            return Response({
                'success': True,
                'is_duplicate': True,
                'duplicate_id': str(duplicate.id),
                'duplicate_name': duplicate.name,
                'message': f'Similar recipe already exists: {duplicate.name}'
            })

        # Save as canonical recipe
        try:
            # Convert to RCIP format
            rcip_data = {
                'rcip_version': '2.0',
                'metadata': {
                    'title': full_recipe['name'],
                    'description': full_recipe.get('description', ''),
                    'cuisine': full_recipe.get('cuisine', ''),
                    'difficulty': full_recipe.get('difficulty', 'intermediate'),
                    'prep_time_minutes': full_recipe.get('prep_time_minutes', 15),
                    'cook_time_minutes': full_recipe.get('cook_time_minutes', 30),
                    'servings': full_recipe.get('servings', 4),
                    'tags': full_recipe.get('tags', [])
                },
                'structure': {
                    'ingredients': full_recipe.get('ingredients', []),
                    'steps': [{'instruction': step} for step in full_recipe.get('instructions', [])]
                }
            }

            canonical_recipe = CanonicalRecipe.objects.create(
                canonical_data=rcip_data,
                author=request.user,
                source='inventory_agent',
                recipe_status='validated'
            )

            return Response({
                'success': True,
                'is_duplicate': False,
                'recipe_id': str(canonical_recipe.id),
                'recipe': full_recipe,
                'message': 'Recipe created successfully'
            })

        except Exception as e:
            logger.error(f"[INV AGENT] Failed to save recipe: {e}")
            return Response({
                'success': False,
                'error': f'Failed to save recipe: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def generate_recipes(self, request):
        """
        Generate recipe suggestions from current inventory (OLD AGENT - DEPRECATED)

        SPRINT 7 INTEGRATION:
        - Phase 1: Validates recipes before returning
        - Phase 2: Generates in user's language only (lazy approach)
        - Phase 3: Two-tier caching (Redis + PostgreSQL)

        POST /api/inventory/generate_recipes/
        Headers:
            X-User-Language: 'en' | 'he' | 'ru' (optional)

        Body (optional):
        {
            "max_recipes": 5,
            "prioritize_expiring": true,
            "max_missing_ingredients": 2,
            "force_regenerate": false  # Set true to bypass cache
        }

        Response:
        {
            "success": true,
            "language": "he",
            "cached": true,              # Phase 3: Cache status
            "cache_source": "redis",     # Phase 3: redis|postgresql|none
            "validated": true,
            "inventory_count": 15,
            "recipe_count": 5,
            "recipes": [...],
            "generation_info": {
                "ai_model": "gemini-2.5-flash-lite",
                "generation_time_ms": 2400,
                "validated": true,
                "language": "he"
            }
        }
        """
        import time
        from apps.shopping.inventory_cache_service import get_inventory_cache_service
        from apps.ai_agents.rate_limiter import AIRateLimiter
        from allauth.account.models import EmailAddress

        start_time = time.time()

        # ⭐ CHECK EMAIL VERIFICATION FIRST
        try:
            email_address = EmailAddress.objects.get(
                user=request.user,
                email=request.user.email
            )

            if not email_address.verified:
                return Response({
                    'success': False,
                    'error': 'Email verification required',
                    'message': (
                        'Please verify your email address before generating recipes. '
                        'Check your inbox for the verification link we sent you. '
                        'If you didn\'t receive it, you can request a new one from your profile.'
                    ),
                    'verification_required': True,
                    'email': request.user.email,
                    'recipes': []
                }, status=status.HTTP_403_FORBIDDEN)

        except EmailAddress.DoesNotExist:
            # Email not registered in allauth (shouldn't happen, but handle gracefully)
            return Response({
                'success': False,
                'error': 'Email verification required',
                'message': (
                    'Your email address needs to be verified. '
                    'Please contact support if you continue to see this message.'
                ),
                'verification_required': True,
                'recipes': []
            }, status=status.HTTP_403_FORBIDDEN)

        # Get generation parameters first to check rate limit
        max_recipes = request.data.get('max_recipes', 5)
        force_regenerate = request.data.get('force_regenerate', False)

        # ⭐ CHECK RATE LIMIT (only if not using cache or forcing regeneration)
        # Cached recipes don't count against the limit
        if force_regenerate:
            allowed, message, limit_type = AIRateLimiter.check_rate_limit(
                request.user, max_recipes)

            if not allowed:
                return Response({
                    'success': False,
                    'error': message,
                    'limit_type': limit_type,
                    'rate_limited': True
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Phase 2: Detect user's language
        user_language = self._get_user_language(request)

        # Get user's inventory
        inventory_items = self.get_queryset()

        # Format for AI
        items_data = []
        for item in inventory_items:
            items_data.append({
                'name': item.name,
                'quantity': float(item.quantity),
                'unit': item.unit,
                'expiration_date': item.expiration_date.isoformat() if item.expiration_date else None,
                'location': item.location,
                'category': item.category
            })

        # Get generation parameters
        generation_params = {
            'max_recipes': max_recipes,
            'prioritize_expiring': request.data.get('prioritize_expiring', True),
            'max_missing_ingredients': request.data.get('max_missing_ingredients', 2)
        }

        # Phase 3: Check cache (unless force_regenerate)
        cache_service = get_inventory_cache_service()
        cached_recipes = None
        cache_source = 'none'

        if not force_regenerate:
            cached_recipes = cache_service.get_cached_recipes(
                user=request.user,
                inventory_items=items_data,
                language=user_language,
                generation_params=generation_params
            )

            if cached_recipes:
                # Cache hit - return immediately (no rate limit applied)
                cache_time_ms = int((time.time() - start_time) * 1000)

                # Determine cache source from log message (Redis vs PostgreSQL)
                cache_source = 'redis'  # Default, actual source detected in service logs

                return Response({
                    'success': True,
                    'language': user_language,
                    'cached': True,
                    'cache_source': cache_source,
                    'validated': True,
                    'inventory_count': len(items_data),
                    'recipe_count': len(cached_recipes),
                    'recipes': cached_recipes,
                    'generation_info': {
                        'ai_model': 'cached',
                        'generation_time_ms': cache_time_ms,
                        'validated': True,
                        'language': user_language,
                        'cache_hit': True
                    }
                })

        # ⭐ CHECK RATE LIMIT before generating (for non-forced requests)
        if not force_regenerate:
            allowed, message, limit_type = AIRateLimiter.check_rate_limit(
                request.user, max_recipes)

            if not allowed:
                return Response({
                    'success': False,
                    'error': message,
                    'limit_type': limit_type,
                    'rate_limited': True
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Cache miss - generate with AI (Phase 1 & 2)
        user_profile = {
            'daily_calories_goal': getattr(request.user, 'daily_calories_goal', 2000),
            'daily_protein_goal': getattr(request.user, 'daily_protein_goal', 150),
            'dietary_restrictions': [],
            'allergies': [],
            'activity_level': 'moderate'
        }

        generator = InventoryRecipeGenerator()
        recipes = generator.generate_recipes(
            inventory_items=items_data,
            user_profile=user_profile,
            max_recipes=generation_params['max_recipes'],
            prioritize_expiring=generation_params['prioritize_expiring'],
            max_missing_ingredients=generation_params['max_missing_ingredients'],
            target_language=user_language
        )

        # Calculate generation time
        generation_time_ms = int((time.time() - start_time) * 1000)

        # Phase 3: Save to cache
        ai_model = 'gemini-2.5-flash-lite'
        if recipes and recipes[0].get('validation', {}).get('ai_provider') == 'groq':
            ai_model = 'groq-llama-3.3-70b'

        cache_service.save_recipes(
            user=request.user,
            inventory_items=items_data,
            recipes=recipes,
            language=user_language,
            generation_params=generation_params,
            ai_model=ai_model,
            generation_time_ms=generation_time_ms
        )

        # ⭐ LOG SUCCESSFUL REQUEST
        AIRateLimiter.log_request(request.user, len(recipes))

        # Get updated stats
        stats = AIRateLimiter.get_user_stats(request.user)

        # Get rate limit headers
        headers = AIRateLimiter.get_rate_limit_headers(request.user)

        response = Response({
            'success': True,
            'language': user_language,
            'cached': False,
            'cache_source': 'none',
            'validated': True,
            'inventory_count': len(items_data),
            'recipe_count': len(recipes),
            'recipes': recipes,
            'generation_info': {
                'ai_model': ai_model,
                'generation_time_ms': generation_time_ms,
                'validated': True,
                'language': user_language,
                'cache_hit': False
            },
            'rate_limit_stats': stats
        })

        # Add rate limit headers to response
        for header_name, header_value in headers.items():
            response[header_name] = header_value

        return response

    def perform_create(self, serializer):
        """Override to invalidate cache when inventory item is created"""
        instance = serializer.save()
        self._invalidate_recipe_cache()
        return instance

    def perform_update(self, serializer):
        """Override to invalidate cache when inventory item is updated"""
        instance = serializer.save()
        self._invalidate_recipe_cache()
        return instance

    def perform_destroy(self, instance):
        """Override to invalidate cache when inventory item is deleted"""
        instance.delete()
        self._invalidate_recipe_cache()

    def _invalidate_recipe_cache(self):
        """Invalidate cached recipes for current user (Phase 3)"""
        from apps.shopping.inventory_cache_service import get_inventory_cache_service
        cache_service = get_inventory_cache_service()
        cache_service.invalidate_cache(self.request.user)

    @action(detail=False, methods=['post'], url_path='create-recipe-from-brief')
    def create_recipe_from_brief(self, request):
        """
        Create a full recipe from an inventory brief (Phase 4)

        This endpoint:
        1. Checks if similar recipe exists (Recipe Matcher)
        2. If no match, generates full recipe with detailed steps
        3. Validates the recipe
        4. Submits to Universal Agent API for translation
        5. Tracks inventory consumption

        POST /api/inventory/create-recipe-from-brief/
        Body:
        {
            "brief": {
                "name": "Chicken Rice Bowl",
                "ingredients_from_inventory": [...],
                "missing_ingredients": [...],
                "cooking_time": "30 min",
                "difficulty": "easy",
                "nutrition": {...}
            },
            "language": "en"  # optional
        }

        Response:
        {
            "success": true,
            "match_found": false,
            "recipe_id": "uuid",
            "recipe_url": "/recipes/uuid",
            "message": "Recipe created successfully"
        }
        """
        import time
        from apps.shopping.recipe_matcher_service import get_recipe_matcher_service
        from apps.shopping.full_recipe_generator import get_full_recipe_generator
        from apps.core.services import get_universal_validator
        from apps.recipes.models import CanonicalRecipe, RecipeTranslation
        from django.utils import timezone

        start_time = time.time()

        # Get brief from request
        brief = request.data.get('brief')
        if not brief:
            return Response({
                'success': False,
                'error': 'Recipe brief is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        language = request.data.get(
            'language') or self._get_user_language(request)

        print(
            f"\n[CREATE RECIPE] Starting for '{brief.get('name')}' in {language}")

        # Phase 4.0: Check if similar recipe exists
        matcher = get_recipe_matcher_service()

        # Extract ingredient names for matching
        ingredient_names = [
            ing['name'] for ing in brief.get('ingredients_from_inventory', [])
        ] + brief.get('missing_ingredients', [])

        match = matcher.find_matching_recipe(
            recipe_name=brief['name'],
            ingredients=ingredient_names,
            language=language
        )

        if match:
            # Match found - return existing recipe
            print(
                f"[CREATE RECIPE] ✅ Match found: {match['title']} (score: {match['match_score']:.2f})")

            return Response({
                'success': True,
                'match_found': True,
                'recipe_id': match['recipe_id'],
                'recipe_url': f"/recipes/{match['recipe_id']}",
                'match_info': {
                    'existing_title': match['title'],
                    'match_score': match['match_score'],
                    'name_similarity': match.get('name_similarity', 0),
                    'ingredient_overlap': match.get('ingredient_overlap', 0)
                },
                'message': f"Similar recipe already exists: {match['title']}"
            })

        # No match - generate full recipe
        print(f"[CREATE RECIPE] No match found, generating full recipe...")

        full_recipe_generator = get_full_recipe_generator()
        rcip_recipe = full_recipe_generator.generate_full_recipe(
            brief, language)

        if not rcip_recipe:
            return Response({
                'success': False,
                'error': 'Failed to generate full recipe'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        ai_provider = rcip_recipe.pop('ai_provider', 'unknown')

        # Validate the recipe
        validator = get_universal_validator()
        validation_result = validator.validate_recipe(rcip_recipe)

        print(
            f"[CREATE RECIPE] Validation score: {validation_result.overall_score}/100")

        if not validation_result.is_valid:
            print(f"[CREATE RECIPE] ⚠️ Low validation score, but proceeding...")

        # Create CanonicalRecipe
        try:
            canonical_recipe = CanonicalRecipe.objects.create(
                canonical_data=rcip_recipe,
                author=request.user,
                source='inventory_agent',
                recipe_status='validated' if validation_result.is_valid else 'pending',
                validation_score=validation_result.overall_score
            )

            print(f"[CREATE RECIPE] ✅ Recipe created: {canonical_recipe.id}")

            # Create initial translation in source language
            RecipeTranslation.objects.create(
                recipe=canonical_recipe,
                language=language,
                content={
                    'title': rcip_recipe['metadata']['title'],
                    'description': rcip_recipe['metadata'].get('description', ''),
                    'ingredients_text': {},  # Will be filled by translation service
                    'steps_text': [step['instruction'] for step in rcip_recipe['structure']['steps']],
                    'tags': rcip_recipe['metadata'].get('tags', [])
                },
                translation_status='complete',
                confidence=100,
                translated_at=timezone.now()
            )

            print(
                f"[CREATE RECIPE] ✅ Initial translation created for {language}")

            # TODO: Track inventory consumption (Phase 4.5)

            generation_time_ms = int((time.time() - start_time) * 1000)

            return Response({
                'success': True,
                'match_found': False,
                'recipe_id': str(canonical_recipe.id),
                'recipe_url': f"/recipes/{canonical_recipe.id}",
                'validation': {
                    'score': validation_result.overall_score,
                    'is_valid': validation_result.is_valid,
                    'issues_count': len(validation_result.issues)
                },
                'generation_info': {
                    'ai_provider': ai_provider,
                    'generation_time_ms': generation_time_ms,
                    'language': language
                },
                'message': 'Recipe created successfully'
            })

        except Exception as e:
            print(f"[CREATE RECIPE] ❌ Error creating recipe: {e}")
            import traceback
            traceback.print_exc()

            return Response({
                'success': False,
                'error': f'Failed to save recipe: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_user_language(self, request) -> str:
        """
        Get user's current language (Phase 2)

        Priority:
        1. User profile (preferred_language)
        2. Frontend header (X-User-Language)
        3. Accept-Language header
        4. Default: 'en'
        """
        # Check user profile
        if hasattr(request.user, 'preferred_language') and request.user.preferred_language:
            lang = request.user.preferred_language
            if lang in ['en', 'he', 'ru']:
                return lang

        # Check custom header from frontend
        frontend_lang = request.META.get('HTTP_X_USER_LANGUAGE')
        if frontend_lang and frontend_lang in ['en', 'he', 'ru']:
            return frontend_lang

        # Check Accept-Language
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', 'en')
        lang_code = accept_language.split(',')[0].split('-')[0][:2]

        return lang_code if lang_code in ['en', 'he', 'ru'] else 'en'


# Additional viewset for AI categorization (used by shopping list)


class AICategorizationView(views.APIView):
    """
    AI-powered categorization for shopping items

    POST /api/inventory/categorize/
    Body:
    {
        "items": [
            {"id": "uuid", "name": "Milk 1L"},
            {"id": "uuid", "name": "Chicken breast 500g"},
            ...
        ]
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.core.security import AIInputValidator
        
        items = request.data.get('items', [])

        if not items:
            return Response(
                {'error': 'items list is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 🔒 SECURITY: Validate item count and names
        if len(items) > 100:
            return Response(
                {'error': 'Too many items. Maximum 100 items per request'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sanitized_items = []
        for item in items:
            if not isinstance(item, dict) or 'name' not in item:
                continue
            
            # Validate item name
            is_valid, error_msg, sanitized_name = AIInputValidator.validate_search_input(
                item['name'], field_name="item name"
            )
            
            if is_valid:
                sanitized_items.append({
                    'id': item.get('id', ''),
                    'name': sanitized_name
                })
        
        if not sanitized_items:
            return Response(
                {'error': 'No valid items provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use AI service to categorize
        service = InventoryCategorizationService()
        suggestions = service.categorize_items(sanitized_items)

        serializer = AICategorizationSuggestionSerializer(
            suggestions, many=True)

        return Response({
            'success': True,
            'suggestions': serializer.data
        })
