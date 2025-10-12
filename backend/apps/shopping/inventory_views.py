"""
Inventory Management Views - Complete API endpoints for inventory
"""
from rest_framework import views
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal

from .models import Inventory, InventoryHistory, ShoppingList, ShoppingItem
from .serializers import (
    InventorySerializer,
    InventoryHistorySerializer,
    AICategorizationSuggestionSerializer,
    BulkInventoryCreateSerializer,
    InventoryConsumeSerializer,
    RecipeFromInventorySerializer
)
from .inventory_services import InventoryCategorizationService, InventoryRecipeGenerator


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

    @action(detail=False, methods=['post'])
    def generate_recipes(self, request):
        """
        Generate recipe suggestions from current inventory

        POST /api/inventory/generate_recipes/
        Body (optional):
        {
            "max_recipes": 5,
            "prioritize_expiring": true,
            "max_missing_ingredients": 2
        }
        """
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

        # Get user profile for nutrition goals
        user_profile = {
            'daily_calories_goal': getattr(request.user, 'daily_calories_goal', 2000),
            'daily_protein_goal': getattr(request.user, 'daily_protein_goal', 150),
            'dietary_restrictions': [],  # TODO: Add to user model
            'allergies': [],  # TODO: Add to user model
            'activity_level': 'moderate'
        }

        # Generate recipes with AI
        generator = InventoryRecipeGenerator()
        max_recipes = request.data.get('max_recipes', 5)
        prioritize_expiring = request.data.get('prioritize_expiring', True)
        max_missing = request.data.get('max_missing_ingredients', 2)

        recipes = generator.generate_recipes(
            inventory_items=items_data,
            user_profile=user_profile,
            max_recipes=max_recipes,
            prioritize_expiring=prioritize_expiring,
            max_missing_ingredients=max_missing
        )

        serializer = RecipeFromInventorySerializer(recipes, many=True)

        return Response({
            'success': True,
            'inventory_count': len(items_data),
            'recipe_count': len(recipes),
            'recipes': serializer.data
        })


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
        items = request.data.get('items', [])

        if not items:
            return Response(
                {'error': 'items list is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use AI service to categorize
        service = InventoryCategorizationService()
        suggestions = service.categorize_items(items)

        serializer = AICategorizationSuggestionSerializer(
            suggestions, many=True)

        return Response({
            'success': True,
            'suggestions': serializer.data
        })
