from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from asgiref.sync import async_to_sync
from decimal import Decimal
from datetime import datetime
import uuid
import sys

# Fix for Windows console Unicode/emoji encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from channels.layers import get_channel_layer
except ImportError:
    # Fallback for when channels is not properly configured
    def get_channel_layer():
        return None

from .models import ShoppingList, ShoppingItem, Inventory, ShoppingEvent, ShoppingListCollaborator
from .serializers import (
    ShoppingListSerializer, ShoppingItemSerializer,
    InventorySerializer, ShoppingEventSerializer,
    CreateShoppingListSerializer, AddCollaboratorSerializer,
    UpdateCollaboratorPermissionsSerializer
)
from apps.ai_agents.services import AIOrchestrator


def serialize_for_channels(data):
    """Convert UUID, Decimal, and datetime objects to serializable types for channels"""
    if isinstance(data, dict):
        return {key: serialize_for_channels(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialize_for_channels(item) for item in data]
    elif isinstance(data, uuid.UUID):
        return str(data)
    elif isinstance(data, Decimal):
        return float(data)
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data


class ShoppingListViewSet(viewsets.ModelViewSet):
    """Shopping list management with real-time sync"""
    serializer_class = ShoppingListSerializer
    permission_classes = [IsAuthenticated]

    # Allow DELETE but override destroy method to prevent permanent deletion
    http_method_names = ['get', 'post', 'put',
                         'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        """Get user's created lists and collaborative lists (only active ones)"""
        return ShoppingList.objects.filter(
            Q(creator=self.request.user) |
            Q(participants=self.request.user),
            is_active=True,
            deleted_at__isnull=True
        ).distinct().prefetch_related('collaborators__user', 'items')

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return CreateShoppingListSerializer
        return ShoppingListSerializer

    def perform_create(self, serializer):
        """Create new collaborative list"""
        shopping_list = serializer.save(creator=self.request.user)

        # Auto-add creator as collaborator with full permissions
        ShoppingListCollaborator.objects.create(
            user=self.request.user,
            shopping_list=shopping_list,
            can_edit=True,
            can_add_items=True,
            can_invite_others=True
        )

        # Auto-add partner if connected
        if self.request.user.partner:
            ShoppingListCollaborator.objects.create(
                user=self.request.user.partner,
                shopping_list=shopping_list,
                can_edit=True,
                can_add_items=True,
                can_invite_others=False
            )

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add item to shopping list"""
        try:
            shopping_list = self.get_object()
            print(
                f"🛒 Adding item to shopping list: {shopping_list.name} by user: {request.user.username}")

            # Check permissions properly
            is_creator = shopping_list.creator == request.user

            if is_creator:
                # Creator has all permissions
                can_add_items = True
            else:
                # Check collaborator permissions
                try:
                    collaborator = shopping_list.collaborators.get(
                        user=request.user)
                    can_add_items = collaborator.can_add_items
                    print(
                        f"🔒 Collaborator {request.user.username} can_add_items: {can_add_items}")
                except shopping_list.collaborators.model.DoesNotExist:
                    print(
                        f"❌ User {request.user.username} is not a collaborator")
                    return Response(
                        {'error': 'You do not have permission to add items to this list'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            if not can_add_items:
                print(
                    f"❌ Permission denied: {request.user.username} cannot add items")
                return Response(
                    {'error': 'You do not have permission to add items to this list'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Create item with safe defaults
            item_data = request.data.copy()
            print(f"📝 Item data received: {item_data}")

            # Use safe defaults for missing attributes
            user_color = getattr(request.user, 'personal_color', '#4F46E5')
            priority = 1 if is_creator else 0

            # Create the item directly (bypass serializer for now)
            item = ShoppingItem.objects.create(
                shopping_list=shopping_list,
                added_by=request.user,
                name=item_data.get('name', ''),
                quantity=item_data.get('quantity', 1),
                unit=item_data.get('unit', 'unit'),
                category=item_data.get('category', 'other'),
                notes=item_data.get('notes', ''),
                user_color=user_color,
                priority=priority
            )

            print(f"✅ Item created successfully: {item.name}")

            # Increment items_added_count for the user (if they are a collaborator)
            if not is_creator:
                try:
                    collaborator = shopping_list.collaborators.get(
                        user=request.user)
                    collaborator.items_added_count += 1
                    collaborator.save()
                    print(
                        f"📊 Incremented items_added_count for {request.user.username}: {collaborator.items_added_count}")
                except shopping_list.collaborators.model.DoesNotExist:
                    pass  # Shouldn't happen since we checked permissions above

            # Send WebSocket notification
            try:
                channel_layer = get_channel_layer()
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f'shopping_list_{shopping_list.id}',
                        {
                            'type': 'item_added',
                            'item': ShoppingItemSerializer(item).data,
                            'user': {
                                'id': str(request.user.id),
                                'username': request.user.username,
                                'first_name': request.user.first_name,
                                'color': user_color
                            }
                        }
                    )
                    print(
                        f"📡 WebSocket notification sent for item: {item.name}")
            except Exception as ws_error:
                print(f"⚠️ WebSocket notification failed: {ws_error}")
                # Don't fail the request if WebSocket fails

            # Return success response
            return Response(ShoppingItemSerializer(item).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"❌ Error adding item: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to add item: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _convert_to_grams(self, quantity, unit):
        """Convert weight units to grams for storage"""
        unit_lower = unit.lower()

        # Already in grams
        if unit_lower in ['g', 'gram', 'grams']:
            return quantity

        # Kilograms to grams
        if unit_lower in ['kg', 'kilogram', 'kilograms']:
            return quantity * 1000

        # Ounces to grams
        if unit_lower in ['oz', 'ounce', 'ounces']:
            return quantity * 28.35

        # Pounds to grams
        if unit_lower in ['lb', 'lbs', 'pound', 'pounds']:
            return quantity * 453.592

        # Default
        return quantity

    def _convert_to_ml(self, quantity, unit):
        """Convert liquid units to milliliters for storage"""
        unit_lower = unit.lower()

        # Already in ml
        if unit_lower in ['ml', 'milliliter', 'milliliters']:
            return quantity

        # Liters to ml
        if unit_lower in ['l', 'liter', 'liters', 'litre', 'litres']:
            return quantity * 1000

        # Fluid ounces to ml
        if unit_lower in ['fl oz', 'fluid ounce', 'fluid ounces']:
            return quantity * 29.574

        # Cups to ml
        if unit_lower in ['cup', 'cups']:
            return quantity * 236.588

        # Tablespoons to ml
        if unit_lower in ['tbsp', 'tablespoon', 'tablespoons']:
            return quantity * 14.787

        # Teaspoons to ml
        if unit_lower in ['tsp', 'teaspoon', 'teaspoons']:
            return quantity * 4.929

        # Pints to ml
        if unit_lower in ['pint', 'pints']:
            return quantity * 473.176

        # Quarts to ml
        if unit_lower in ['quart', 'quarts']:
            return quantity * 946.353

        # Gallons to ml
        if unit_lower in ['gallon', 'gallons']:
            return quantity * 3785.41

        # Default
        return quantity

    def _validate_and_fix_ingredient(self, ingredient: dict, ingredient_name: str) -> tuple:
        """
        Validate ingredient measurement and apply intelligent fallbacks if needed.
        Returns: (quantity, unit, counter_type)
        """
        quantity = ingredient.get('amount', 1.0)
        unit = ingredient.get('unit', 'unit')

        # Convert to float to avoid Decimal issues
        try:
            quantity = float(quantity) if quantity else 1.0
        except (ValueError, TypeError):
            print(
                f"⚠️ [VALIDATION] Invalid quantity '{quantity}' for {ingredient_name}, defaulting to 1.0")
            quantity = 1.0

        # Ensure unit is a string
        if not unit or not isinstance(unit, str):
            unit = 'unit'

        unit_lower = unit.lower().strip()
        name_lower = ingredient_name.lower()

        # Define unit categories (more comprehensive)
        weight_units = [
            'g', 'gram', 'grams', 'gr',
            'kg', 'kilogram', 'kilograms', 'kilo',
            'oz', 'ounce', 'ounces',
            'lb', 'lbs', 'pound', 'pounds'
        ]
        liquid_units = [
            'ml', 'milliliter', 'milliliters', 'millilitre', 'millilitres',
            'l', 'liter', 'liters', 'litre', 'litres',
            'fl oz', 'fluid ounce', 'fluid ounces', 'floz',
            'cup', 'cups',
            'tbsp', 'tablespoon', 'tablespoons',
            'tsp', 'teaspoon', 'teaspoons',
            'pint', 'pints', 'quart', 'quarts',
            'gallon', 'gallons'
        ]
        count_units = [
            'piece', 'pieces', 'unit', 'units', 'item', 'items',
            'whole', 'clove', 'cloves', 'leaf', 'leaves'
        ]

        # Check if unit is recognized
        if unit_lower in weight_units:
            counter_type = 'weight'
            print(
                f"✅ [VALIDATION] {ingredient_name}: {quantity} {unit} -> WEIGHT counter")
        elif unit_lower in liquid_units:
            counter_type = 'liquid'
            print(
                f"✅ [VALIDATION] {ingredient_name}: {quantity} {unit} -> LIQUID counter")
        elif unit_lower in count_units:
            counter_type = 'quantity'  # Use 'quantity' to match existing code
            print(
                f"✅ [VALIDATION] {ingredient_name}: {quantity} {unit} -> QUANTITY counter")
        else:
            # Unit not recognized - apply intelligent fallback
            print(
                f"⚠️ [VALIDATION] Unknown unit '{unit}' for {ingredient_name}, inferring from ingredient type...")

            # Countable items (eggs, fruits, vegetables by piece)
            countable_keywords = ['egg', 'apple', 'tomato', 'onion', 'banana', 'potato',
                                  'lemon', 'lime', 'orange', 'clove', 'bay leaf', 'leaf',
                                  'avocado', 'garlic head', 'head', 'can', 'jar', 'pack',
                                  'bunch', 'stalk', 'sprig']
            if any(keyword in name_lower for keyword in countable_keywords):
                unit = 'pieces'
                counter_type = 'quantity'  # Use 'quantity' to match existing code
                print(
                    f"🔧 [INFERRED] {ingredient_name} -> QUANTITY COUNTER (pieces)")

            # Liquids (should use liquid counter with ml)
            elif any(keyword in name_lower for keyword in [
                'water', 'milk', 'oil', 'broth', 'stock', 'juice', 'wine',
                'cream', 'sauce', 'vinegar', 'soy sauce', 'liquid', 'extract',
                'coconut milk', 'olive oil', 'vegetable oil'
            ]):
                # If quantity is very small (<50), likely teaspoons/tablespoons, convert to ml
                if quantity < 50:
                    original_qty = quantity
                    quantity = quantity * 15  # Approximate tbsp to ml
                    print(
                        f"🔧 [ESTIMATED] {ingredient_name}: {original_qty} (assumed tbsp) -> {quantity}ml")
                unit = 'ml'
                counter_type = 'liquid'
                print(f"🔧 [INFERRED] {ingredient_name} -> LIQUID COUNTER (ml)")

            # Spices and herbs (small weights - use weight counter with grams)
            elif any(keyword in name_lower for keyword in [
                'salt', 'pepper', 'cinnamon', 'cumin', 'paprika', 'oregano',
                'basil', 'thyme', 'parsley', 'vanilla', 'spice', 'herb',
                'garlic powder', 'onion powder', 'ginger', 'nutmeg'
            ]):
                # If quantity is very small (<5), likely teaspoons, convert to grams
                if quantity < 5:
                    original_qty = quantity
                    quantity = quantity * 5  # Approximate tsp to grams
                    print(
                        f"🔧 [ESTIMATED] {ingredient_name}: {original_qty} (assumed tsp) -> {quantity}g")
                unit = 'g'
                counter_type = 'weight'
                print(f"🔧 [INFERRED] {ingredient_name} -> WEIGHT COUNTER (g)")

            # Solid ingredients (default to weight counter with grams)
            else:
                unit = 'g'
                counter_type = 'weight'
                print(
                    f"🔧 [INFERRED] {ingredient_name} -> WEIGHT COUNTER (g) [default for solids]")

        return quantity, unit, counter_type

    def _convert_to_user_preference(self, quantity, unit, weight_pref, liquid_pref):
        """Convert recipe units to user's preferred measurement system"""
        unit_lower = unit.lower()

        # Weight conversions
        weight_metric_units = ['g', 'gram',
                               'grams', 'kg', 'kilogram', 'kilograms']
        weight_imperial_units = ['oz', 'ounce', 'ounces', 'lb', 'lbs',
                                 'pound', 'pounds']

        # Liquid conversions
        liquid_metric_units = ['ml', 'milliliter', 'milliliters',
                               'l', 'liter', 'liters', 'litre', 'litres']
        liquid_imperial_units = ['fl oz', 'fluid ounce', 'fluid ounces',
                                 'cup', 'cups', 'pint', 'pints', 'quart', 'quarts', 'gallon', 'gallons']

        # Check if it's a weight unit
        if unit_lower in weight_metric_units:
            if weight_pref == 'imperial':
                # Convert metric to imperial
                if unit_lower in ['g', 'gram', 'grams']:
                    # Convert grams to ounces
                    quantity = quantity / 28.35
                    unit = 'oz'
                elif unit_lower in ['kg', 'kilogram', 'kilograms']:
                    # Convert kg to pounds
                    quantity = quantity * 2.205
                    unit = 'lb'
                print(
                    f"[WEIGHT CONV] Metric -> Imperial: {quantity:.2f} {unit}")
            # If metric preference, keep as is
            return (round(quantity, 2), unit)

        elif unit_lower in weight_imperial_units:
            if weight_pref == 'metric':
                # Convert imperial to metric
                if unit_lower in ['oz', 'ounce', 'ounces']:
                    # Convert ounces to grams
                    quantity = quantity * 28.35
                    unit = 'g'
                elif unit_lower in ['lb', 'lbs', 'pound', 'pounds']:
                    # Convert pounds to kg
                    quantity = quantity / 2.205
                    unit = 'kg'
                print(
                    f"[WEIGHT CONV] Imperial -> Metric: {quantity:.2f} {unit}")
            # If imperial preference, keep as is
            return (round(quantity, 2), unit)

        # Check if it's a liquid unit
        elif unit_lower in liquid_metric_units:
            if liquid_pref == 'imperial':
                # Convert metric to imperial
                if unit_lower in ['ml', 'milliliter', 'milliliters']:
                    # Convert ml to fl oz
                    quantity = quantity / 29.574
                    unit = 'fl oz'
                elif unit_lower in ['l', 'liter', 'liters', 'litre', 'litres']:
                    # Convert liters to gallons
                    if quantity >= 1:
                        quantity = quantity / 3.785
                        unit = 'gallon'
                    else:
                        # Small amounts to fl oz
                        quantity = (quantity * 1000) / 29.574
                        unit = 'fl oz'
                print(
                    f"[LIQUID CONV] Metric -> Imperial: {quantity:.2f} {unit}")
            # If metric preference, keep as is
            return (round(quantity, 2), unit)

        elif unit_lower in liquid_imperial_units:
            if liquid_pref == 'metric':
                # Convert imperial to metric
                if unit_lower in ['fl oz', 'fluid ounce', 'fluid ounces']:
                    # Convert fl oz to ml
                    quantity = quantity * 29.574
                    unit = 'ml'
                elif unit_lower in ['cup', 'cups']:
                    # Convert cups to ml
                    quantity = quantity * 236.588
                    unit = 'ml'
                elif unit_lower in ['pint', 'pints']:
                    # Convert pints to ml
                    quantity = quantity * 473.176
                    unit = 'ml'
                elif unit_lower in ['quart', 'quarts']:
                    # Convert quarts to liters
                    quantity = quantity * 0.946
                    unit = 'l'
                elif unit_lower in ['gallon', 'gallons']:
                    # Convert gallons to liters
                    quantity = quantity * 3.785
                    unit = 'l'
                print(
                    f"[LIQUID CONV] Imperial -> Metric: {quantity:.2f} {unit}")
            # If imperial preference, keep as is
            return (round(quantity, 2), unit)

        # Not a weight or liquid unit, return as is
        return (round(quantity, 2), unit)

    @action(detail=True, methods=['post'])
    def ai_add_items(self, request, pk=None):
        """
        AI-powered recipe finder: User types dish name (e.g., "pasta carbonara")
        Agent searches recipe, converts to RCIP, saves it, and adds ingredients to shopping list
        """
        shopping_list = self.get_object()
        query = request.data.get('text', '')

        if not query:
            return Response({
                'success': False,
                'message': 'Please describe what you want to cook'
            }, status=status.HTTP_400_BAD_REQUEST)

        print(f"[AI RECIPE REQUEST] User query: '{query}'")

        # Import recipe agent service
        try:
            from apps.recipes.services import RecipeAgentService, RecipeDeduplicationService
            from apps.recipes.models import Recipe
        except ImportError as e:
            print(f"[ERROR] Recipe app not available: {e}")
            return Response({
                'success': False,
                'message': 'Recipe service is not available'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Get user preferences
        user_preferences = {
            'dietary_restrictions': getattr(request.user, 'dietary_restrictions', ''),
            'allergies': getattr(request.user, 'allergies', '')
        }

        # Run recipe agent to find recipe
        agent = RecipeAgentService()

        try:
            print(f"[RECIPE AGENT] Searching for: {query}")
            success, recipe_data, message = async_to_sync(agent.find_and_convert_recipe)(
                query, request.user, user_preferences
            )

            if not success:
                print(f"[ERROR] Recipe agent failed: {message}")
                return Response({
                    'success': False,
                    'message': message or 'Could not find recipe'
                }, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Extract recipe objects from the returned data
            # The service returns: {'canonical_recipe': {...}, 'user_recipe': {...}, 'is_new': bool}
            user_recipe_data = recipe_data.get('user_recipe', {})
            canonical_recipe_data = recipe_data.get('canonical_recipe', {})

            # Get the actual model objects by ID
            from apps.recipes.models import Recipe, CanonicalRecipe

            recipe = Recipe.objects.get(id=user_recipe_data['id'])
            canonical_recipe = recipe.canonical_recipe

            print(f"[SUCCESS] Using recipe: {canonical_recipe.name}")
            print(f"[OK] User fork ID: {recipe.id}")

            # Add ingredients to shopping list with duplicate detection and unit conversion
            items_created = []
            items_updated = []
            items_counter_types = {}  # Track which counter type each item uses
            user_color = getattr(request.user, 'personal_color', '#4F46E5')

            # Get user preferences for unit conversion
            user_weight_preference = getattr(
                request.user, 'weight_unit_preference', 'metric')  # 'metric' or 'imperial'
            user_liquid_preference = getattr(
                request.user, 'liquid_unit_preference', 'metric')  # 'metric' or 'imperial'

            print(
                f"[USER PREFS] Weight: {user_weight_preference}, Liquid: {user_liquid_preference}")

            # Track AI messages (these are NOT shopping items)
            ai_messages = []

            # Use canonical recipe's base ingredients
            for ingredient in canonical_recipe.base_ingredients:
                ingredient_name = ingredient.get('name', '')
                if not ingredient_name:
                    continue

                # FILTER OUT AI MESSAGES (text that's not an actual ingredient)
                # Detect long text that's clearly a message, not an ingredient
                if len(ingredient_name) > 100 or any(phrase in ingredient_name.lower() for phrase in [
                    'there are no', 'however,', 'i can provide', 'the text appears',
                    'wikipedia', 'article about', 'i cannot', 'unfortunately',
                    'please note', 'here are the', 'standard recipe'
                ]):
                    print(
                        f"📝 [AI MESSAGE] Detected AI message, not adding as item: {ingredient_name[:100]}...")
                    ai_messages.append({
                        'text': ingredient_name,
                        'type': 'info',
                        'timestamp': timezone.now().isoformat()
                    })
                    continue  # Skip this "ingredient" - it's actually a message

                # STEP 1: Validate and fix ingredient measurements (intelligent fallbacks)
                # This ensures EVERY ingredient gets proper weight/liquid/count classification
                quantity, unit, counter_type = self._validate_and_fix_ingredient(
                    ingredient, ingredient_name
                )

                print(
                    f"✅ [VALIDATED] {ingredient_name}: {quantity} {unit} ({counter_type})")

                # STEP 2: Convert units based on user preferences
                # This preserves the counter type while converting to user's preferred units
                quantity, unit = self._convert_to_user_preference(
                    quantity, unit, user_weight_preference, user_liquid_preference
                )

                print(
                    f"[USER PREF] {ingredient_name}: {quantity} {unit} (will store in base units for {counter_type})")

                # Normalize ingredient name for comparison
                normalized_name = ingredient_name.lower().strip()

                # Check for existing item with same name
                existing_item = ShoppingItem.objects.filter(
                    shopping_list=shopping_list,
                    name__iexact=ingredient_name,
                    is_completed=False
                ).first()

                from decimal import Decimal

                if existing_item:
                    # Update the appropriate counter
                    if counter_type == 'weight':
                        old_weight = existing_item.weight_quantity
                        # Convert to grams and add
                        weight_in_grams = self._convert_to_grams(
                            quantity, unit)
                        existing_item.weight_quantity = Decimal(
                            str(existing_item.weight_quantity)) + Decimal(str(weight_in_grams))
                        print(
                            f"[MERGED WEIGHT] {ingredient_name}: {old_weight}g + {weight_in_grams}g = {existing_item.weight_quantity}g")
                    elif counter_type == 'liquid':
                        old_liquid = existing_item.liquid_quantity
                        # Convert to ml and add
                        liquid_in_ml = self._convert_to_ml(quantity, unit)
                        existing_item.liquid_quantity = Decimal(
                            str(existing_item.liquid_quantity)) + Decimal(str(liquid_in_ml))
                        print(
                            f"[MERGED LIQUID] {ingredient_name}: {old_liquid}ml + {liquid_in_ml}ml = {existing_item.liquid_quantity}ml")
                    else:
                        old_quantity = existing_item.quantity
                        existing_item.quantity = Decimal(
                            str(existing_item.quantity)) + Decimal(str(quantity))
                        existing_item.unit = unit  # Update unit for count items
                        print(
                            f"[MERGED QUANTITY] {ingredient_name}: {old_quantity} + {quantity} = {existing_item.quantity} {unit}")

                    existing_item.notes = (
                        f"{existing_item.notes}\n+ {quantity} {unit} from recipe: {recipe.name}"
                        if existing_item.notes
                        else f"From recipe: {recipe.name} ({quantity} {unit})"
                    )
                    existing_item.save()
                    items_updated.append(existing_item)
                else:
                    # Create new shopping item with proper counter
                    item_data = {
                        'shopping_list': shopping_list,
                        'name': ingredient_name,
                        'quantity': 1,  # Default quantity
                        'unit': 'unit',  # Default unit
                        'weight_quantity': 0,
                        'liquid_quantity': 0,
                        'category': 'other',
                        'notes': f"From recipe: {recipe.name}",
                        'added_by': request.user,
                        'user_color': user_color,
                        'ai_suggested': True
                    }

                    # Set the appropriate counter
                    if counter_type == 'weight':
                        # Convert to grams for weight_quantity storage
                        weight_in_grams = self._convert_to_grams(
                            quantity, unit)
                        item_data['weight_quantity'] = weight_in_grams
                        print(
                            f"[WEIGHT COUNTER] {ingredient_name}: {quantity} {unit} = {weight_in_grams}g")
                    elif counter_type == 'liquid':
                        # Convert to ml for liquid_quantity storage
                        liquid_in_ml = self._convert_to_ml(quantity, unit)
                        item_data['liquid_quantity'] = liquid_in_ml
                        print(
                            f"[LIQUID COUNTER] {ingredient_name}: {quantity} {unit} = {liquid_in_ml}ml")
                    else:
                        # Use quantity field for count items
                        item_data['quantity'] = quantity
                        item_data['unit'] = unit
                        print(
                            f"[QUANTITY COUNTER] {ingredient_name}: {quantity} {unit}")

                    item = ShoppingItem(**item_data)
                    item.save()
                    items_created.append(item)
                    # Track counter type for this item
                    items_counter_types[str(item.id)] = counter_type
                    print(
                        f"[NEW] Added ingredient: {ingredient_name} (counter: {counter_type})")

            # Update recipe stats
            recipe.times_added_to_lists += 1
            recipe.save()

            # Send WebSocket notifications
            channel_layer = get_channel_layer()
            if channel_layer:
                # Notify about new items
                if items_created:
                    items_data = [ShoppingItemSerializer(
                        i).data for i in items_created]
                    serialized_items = serialize_for_channels(items_data)

                    # Add counter type info to each item
                    for item_data in serialized_items:
                        item_id = str(item_data['id'])
                        if item_id in items_counter_types:
                            item_data['auto_enable_counter'] = items_counter_types[item_id]
                            print(
                                f"[AUTO-ENABLE] {item_data['name']}: {items_counter_types[item_id]} counter")

                    async_to_sync(channel_layer.group_send)(
                        f'shopping_list_{shopping_list.id}',
                        {
                            'type': 'items_batch_added',
                            'items': serialized_items,
                            'user': request.user.username
                        }
                    )
                    print(
                        f"[WEBSOCKET] Sent notification for {len(items_created)} new items with counter info")

                # Notify about updated items
                if items_updated:
                    for item in items_updated:
                        item_data = serialize_for_channels(
                            ShoppingItemSerializer(item).data)
                        async_to_sync(channel_layer.group_send)(
                            f'shopping_list_{shopping_list.id}',
                            {
                                'type': 'item_updated',
                                'item': item_data,
                                'user': request.user.username
                            }
                        )
                    print(
                        f"[WEBSOCKET] Sent notification for {len(items_updated)} updated items")

            # Prepare response message
            total_items = len(items_created) + len(items_updated)
            if items_created and items_updated:
                message = f"Added {len(items_created)} new ingredients and updated {len(items_updated)} existing items from {recipe.name}"
            elif items_created:
                message = f"Added {len(items_created)} ingredients from {recipe.name}"
            else:
                message = f"Updated {len(items_updated)} existing ingredients from {recipe.name}"

            return Response({
                'success': True,
                'recipe': {
                    'id': str(recipe.id),
                    'name': recipe.name,
                    'description': recipe.description,
                    'source_url': canonical_recipe.ai_source_url or '',
                    'servings': canonical_recipe.servings,
                    'created': recipe_data.get('is_new', False),
                    'canonical_id': str(canonical_recipe.id),
                    'canonical_name': canonical_recipe.name,
                    'user_query': query  # The original search query
                },
                'items_added': len(items_created),
                'items_updated': len(items_updated),
                'total_items': total_items,
                'new_items': [ShoppingItemSerializer(i).data for i in items_created],
                'updated_items': [ShoppingItemSerializer(i).data for i in items_updated],
                'ai_messages': ai_messages,  # AI messages separated from shopping items
                'message': message
            })

        except Exception as e:
            print(f"[ERROR] Exception in ai_add_items: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'Error processing recipe: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def mock_store_order(self, request):
        """Simulate store order"""
        store_type = request.data.get('store_type', 'wolt')
        items = request.data.get('items', [])

        from config.external_services import MockStoreServices
        services = MockStoreServices()

        if store_type == 'wolt':
            result = async_to_sync(services.wolt_order_simulation)(items)
        elif store_type == 'shufersal':
            item_names = [item['name'] for item in items]
            result = async_to_sync(services.shufersal_price_check)(item_names)
        else:
            return Response(
                {'error': 'Invalid store type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create shopping event
        if result.get('success'):
            ShoppingEvent.objects.create(
                user=request.user,
                store_name=result.get('store', store_type),
                store_type=store_type,
                total_amount=result.get('total_price_nis', 0),
                items_data=result
            )

        return Response(result)

    @action(detail=True, methods=['post'])
    def add_collaborator(self, request, pk=None):
        """Add collaborator to shopping list"""
        shopping_list = self.get_object()

        # Check permissions
        permissions = shopping_list.get_user_permission(request.user)
        if not permissions or not permissions.get('can_invite_others'):
            return Response(
                {'error': 'You do not have permission to invite collaborators'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AddCollaboratorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        collaboration_key = serializer.validated_data['collaboration_key']

        try:
            from apps.users.models import User
            collaborator_user = User.objects.get(
                collaboration_key=collaboration_key)

            # Check if user is already a collaborator
            if shopping_list.participants.filter(id=collaborator_user.id).exists():
                return Response(
                    {'error': 'User is already a collaborator on this list'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Add collaborator
            collaborator, created = shopping_list.add_collaborator(
                user=collaborator_user,
                can_edit=serializer.validated_data.get('can_edit', True),
                can_add_items=serializer.validated_data.get(
                    'can_add_items', True),
                can_invite_others=serializer.validated_data.get(
                    'can_invite_others', False)
            )

            print(
                f"🔍 add_collaborator result: collaborator={collaborator_user.username}, created={created}")

            # ALWAYS regenerate key for the PARTICIPANT (not creator) when adding collaborator
            print(
                f"🔄 Always regenerating key for PARTICIPANT for security when adding collaborator")

            # Auto-regenerate the PARTICIPANT'S collaboration key for security
            print(
                f"🔄 Starting key regeneration for PARTICIPANT {collaborator_user.username}")
            old_key = collaborator_user.collaboration_key
            print(f"🔍 Old key: {old_key}")
            new_key = collaborator_user.generate_collaboration_key()  # This now saves the model
            print(f"🔍 New key: {new_key}")
            print(
                f"🔑 Auto-regenerated collaboration key for PARTICIPANT {collaborator_user.username}: {old_key} → {new_key}")

            # Send WebSocket notifications and handle response
            if created:
                print(f"✅ New collaborator added - sending notifications")
                # Send WebSocket notification to existing participants in the list
                channel_layer = get_channel_layer()
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f'shopping_list_{shopping_list.id}',
                        {
                            'type': 'collaborator_added',
                            'collaborator': {
                                'id': str(collaborator_user.id),
                                'username': collaborator_user.username,
                                'first_name': collaborator_user.first_name,
                                'color': collaborator_user.personal_color,
                                'can_edit': collaborator.can_edit,
                                'can_add_items': collaborator.can_add_items,
                                'can_invite_others': collaborator.can_invite_others
                            },
                            'invited_by': {
                                'username': request.user.username
                            }
                        }
                    )

                    # Send a separate notification to the newly added participant
                    # about gaining access to a new list
                    async_to_sync(channel_layer.group_send)(
                        f'user_{collaborator_user.id}',
                        {
                            'type': 'list_access_granted',
                            'list': {
                                'id': str(shopping_list.id),
                                'name': shopping_list.name,
                                'is_collaborative': shopping_list.is_collaborative,
                                'creator': {
                                    'username': shopping_list.creator.username,
                                    'first_name': shopping_list.creator.first_name
                                }
                            },
                            'invited_by': {
                                'username': request.user.username,
                                'first_name': request.user.first_name
                            },
                            'message': f'You have been added to "{shopping_list.name}" by {request.user.username}'
                        }
                    )

                    # Also send individual notifications to existing participants to refresh their collaborators list
                    for existing_collaborator in shopping_list.collaborators.exclude(user=collaborator_user):
                        if existing_collaborator.user != request.user:  # Don't notify the person who added the collaborator
                            async_to_sync(channel_layer.group_send)(
                                f'user_{existing_collaborator.user.id}',
                                {
                                    'type': 'collaborator_joined',
                                    'list': {
                                        'id': str(shopping_list.id),
                                        'name': shopping_list.name,
                                    },
                                    'collaborator': {
                                        'username': collaborator_user.username,
                                        'first_name': collaborator_user.first_name,
                                    },
                                    'invited_by': {
                                        'username': request.user.username,
                                        'first_name': request.user.first_name,
                                    },
                                    'message': f'{collaborator_user.username} was added to "{shopping_list.name}" by {request.user.username}'
                                }
                            )

                    print(
                        f"📡 WebSocket notifications sent for new collaborator: {collaborator_user.username} to list: {shopping_list.name}")

                # Send notification to participant about their key change
                if channel_layer:
                    print(
                        f"📡 Sending key regeneration notification to user_{collaborator_user.id}")
                    async_to_sync(channel_layer.group_send)(
                        f'user_{collaborator_user.id}',
                        {
                            'type': 'collaboration_key_regenerated',
                            'new_collaboration_key': new_key,
                            'message': f'Your collaboration key has been automatically updated for security after being added to "{shopping_list.name}"'
                        }
                    )
                    print(f"📡 Key regeneration notification sent successfully")

                return Response({
                    'success': True,
                    'message': f'Successfully added {collaborator_user.username} as collaborator. Their collaboration key has been updated for security.',
                    'collaborator': {
                        'id': str(collaborator_user.id),
                        'username': collaborator_user.username,
                        'first_name': collaborator_user.first_name,
                        'color': collaborator_user.personal_color
                    },
                    'participant_new_key': new_key,
                    'key_regenerated_for': 'participant'
                })
            else:
                print(
                    f"✅ Collaborator {collaborator_user.username} already exists - but key WAS regenerated")

                # Send notification to participant about their key change (existing collaborator)
                channel_layer = get_channel_layer()
                if channel_layer:
                    print(
                        f"📡 Sending key regeneration notification to existing collaborator user_{collaborator_user.id}")
                    async_to_sync(channel_layer.group_send)(
                        f'user_{collaborator_user.id}',
                        {
                            'type': 'collaboration_key_regenerated',
                            'new_collaboration_key': new_key,
                            'message': f'Your collaboration key has been automatically updated for security (re-added to "{shopping_list.name}")'
                        }
                    )
                    print(
                        f"📡 Key regeneration notification sent successfully to existing collaborator")

                return Response({
                    'success': True,
                    'message': f'{collaborator_user.username} was already a collaborator, but their key has been refreshed for security',
                    'collaborator': {
                        'id': str(collaborator_user.id),
                        'username': collaborator_user.username,
                        'first_name': collaborator_user.first_name,
                        'color': collaborator_user.personal_color
                    },
                    'participant_new_key': new_key,
                    'key_regenerated_for': 'participant'
                })

        except User.DoesNotExist:
            return Response(
                {
                    'error': 'User not found',
                    'message': 'No user found with this collaboration key. Please check the key and try again.',
                    'error_type': 'user_not_found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    'error': 'One of parameters is wrong - please try again',
                    'message': 'There was an issue with the provided information. Please verify all details and try again.',
                    'error_type': 'invalid_parameters'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def update_collaborator_permissions(self, request, pk=None):
        """Update collaborator permissions"""
        shopping_list = self.get_object()

        # Only creator can update permissions
        if shopping_list.creator != request.user:
            return Response(
                {'error': 'Only the list creator can update permissions'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UpdateCollaboratorPermissionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']

        try:
            collaborator = shopping_list.collaborators.get(user_id=user_id)

            # Update permissions
            if 'can_edit' in serializer.validated_data:
                collaborator.can_edit = serializer.validated_data['can_edit']
            if 'can_add_items' in serializer.validated_data:
                collaborator.can_add_items = serializer.validated_data['can_add_items']
            if 'can_invite_others' in serializer.validated_data:
                collaborator.can_invite_others = serializer.validated_data['can_invite_others']

            collaborator.save()

            # Send WebSocket notification
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f'shopping_list_{shopping_list.id}',
                    {
                        'type': 'permissions_updated',
                        'user_id': str(user_id),
                        'permissions': {
                            'can_edit': collaborator.can_edit,
                            'can_add_items': collaborator.can_add_items,
                            'can_invite_others': collaborator.can_invite_others
                        },
                        'updated_by': request.user.username
                    }
                )

            return Response({
                'success': True,
                'message': 'Permissions updated successfully'
            })

        except ShoppingListCollaborator.DoesNotExist:
            return Response(
                {'error': 'Collaborator not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def collaborators(self, request, pk=None):
        """Get list of collaborators"""
        shopping_list = self.get_object()
        collaborators_data = []

        # Add creator
        collaborators_data.append({
            'id': str(shopping_list.creator.id),
            'username': shopping_list.creator.username,
            'first_name': shopping_list.creator.first_name,
            'color': shopping_list.creator.personal_color,
            'can_edit': True,
            'can_add_items': True,
            'can_invite_others': True,
            'is_creator': True,
            'joined_at': shopping_list.created_at
        })

        # Add other collaborators
        for collab in shopping_list.collaborators.exclude(user=shopping_list.creator):
            collaborators_data.append({
                'id': str(collab.user.id),
                'username': collab.user.username,
                'first_name': collab.user.first_name,
                'color': collab.user.personal_color,
                'can_edit': collab.can_edit,
                'can_add_items': collab.can_add_items,
                'can_invite_others': collab.can_invite_others,
                'is_creator': False,
                'joined_at': collab.joined_at
            })

        return Response({
            'collaborators': collaborators_data,
            'total': len(collaborators_data)
        })

    @action(detail=True, methods=['post'])
    def leave_list(self, request, pk=None):
        """Allow a participant to leave/remove themselves from a list"""
        shopping_list = self.get_object()

        # Check if user is a participant (not creator)
        if shopping_list.creator == request.user:
            return Response(
                {'error': 'Creator cannot leave their own list. Use delete instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user is actually a participant
        if not shopping_list.participants.filter(id=request.user.id).exists():
            return Response(
                {'error': 'You are not a participant of this list'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Remove user from participants
        shopping_list.participants.remove(request.user)

        # Get user info for notifications
        user_color = getattr(request.user, 'personal_color', '#4F46E5')
        user_info = {
            'id': str(request.user.id),
            'username': request.user.username,
            'first_name': request.user.first_name,
            'color': user_color
        }

        # Send WebSocket notification to remaining participants and creator
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f'shopping_list_{pk}',
                    {
                        'type': 'participant_left',
                        'list_id': str(shopping_list.id),
                        'list_name': shopping_list.name,
                        'participant': user_info,
                        'message': f'{request.user.username} has left the list'
                    }
                )
                print(
                    f"📡 WebSocket notification sent: {request.user.username} left list {shopping_list.name}")
        except Exception as ws_error:
            print(
                f"⚠️ WebSocket notification failed for participant leaving: {ws_error}")

        return Response({
            'message': f'You have successfully left "{shopping_list.name}"',
            'list_name': shopping_list.name
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Step 1: Creator deletes from active lists → Move to archive (soft delete only)"""
        shopping_list = self.get_object()

        print(
            f"🗑️ STEP 1 DELETE: Moving list to archive: {shopping_list.name} (ID: {shopping_list.id})")
        print(
            f"🗑️ Current state - deleted_at: {shopping_list.deleted_at}, permanently_deleted_at: {getattr(shopping_list, 'permanently_deleted_at', None)}")
        print(
            f"🗑️ Participants: {[p.username for p in shopping_list.participants.all()]}")

        # Check if user has permission to delete
        if shopping_list.creator != request.user:
            return Response(
                {'error': 'Only the creator can delete this list'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get list name before deletion for notification
        list_name = shopping_list.name
        list_id = str(shopping_list.id)

        # Perform soft delete
        print(f"🗑️ Calling soft_delete for list: {list_name}")
        shopping_list.soft_delete(request.user)
        print(f"🗑️ After soft_delete - deleted_at: {shopping_list.deleted_at}")
        print(
            f"🗑️ After soft_delete - deleted_by: {shopping_list.deleted_by.username if shopping_list.deleted_by else 'None'}")

        # Verify the list still exists in DB after soft delete
        try:
            still_exists = ShoppingList.objects.get(id=shopping_list.id)
            print(
                f"🗑️ ✅ List still exists in DB after soft delete: {still_exists.name}")
            print(
                f"🗑️ ✅ Participants still exist: {[p.username for p in still_exists.participants.all()]}")
        except ShoppingList.DoesNotExist:
            print(
                f"🗑️ ❌ ERROR: List was actually deleted from DB instead of soft deleted!")
            return Response(
                {'error': 'List was permanently deleted instead of archived'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Send WebSocket notification to all participants
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                user_color = getattr(request.user, 'personal_color', '#4F46E5')
                async_to_sync(channel_layer.group_send)(
                    f'shopping_list_{list_id}',
                    {
                        'type': 'list_deleted',
                        'list_id': list_id,
                        'list_name': list_name,
                        'deleted_by': {
                            'id': str(request.user.id),
                            'username': request.user.username,
                            'first_name': request.user.first_name,
                            'color': user_color
                        },
                        'message': f'List "{list_name}" has been moved to archive by {request.user.username}'
                    }
                )
                print(
                    f"📡 WebSocket notification sent for deleted list: {list_name}")
        except Exception as ws_error:
            print(
                f"⚠️ WebSocket notification failed for list deletion: {ws_error}")

        # CRITICAL: Do NOT call super().destroy() - this would permanently delete the object
        return Response({
            'message': f'List "{list_name}" moved to archive',
            'deleted_at': shopping_list.deleted_at
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'], url_path='soft-delete')
    def soft_delete_list(self, request, pk=None):
        """Soft delete the shopping list (move to archive) - NEW METHOD"""
        shopping_list = self.get_object()

        print(
            f"🗑️ SOFT DELETE ACTION called for list: {shopping_list.name} (ID: {shopping_list.id})")
        print(f"🗑️ Before delete - deleted_at: {shopping_list.deleted_at}")
        print(
            f"🗑️ Participants before delete: {[p.username for p in shopping_list.participants.all()]}")

        # Check if user has permission to delete
        if shopping_list.creator != request.user:
            return Response(
                {'error': 'Only the creator can delete this list'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get list name before deletion for notification
        list_name = shopping_list.name
        list_id = str(shopping_list.id)

        # Perform soft delete
        print(f"🗑️ Calling soft_delete for list: {list_name}")
        shopping_list.soft_delete(request.user)
        print(f"🗑️ After soft_delete - deleted_at: {shopping_list.deleted_at}")
        print(
            f"🗑️ After soft_delete - deleted_by: {shopping_list.deleted_by.username if shopping_list.deleted_by else 'None'}")

        # Verify the list still exists in DB after soft delete
        try:
            still_exists = ShoppingList.objects.get(id=shopping_list.id)
            print(
                f"🗑️ ✅ List still exists in DB after soft delete: {still_exists.name}")
            print(
                f"🗑️ ✅ Participants still exist: {[p.username for p in still_exists.participants.all()]}")
        except ShoppingList.DoesNotExist:
            print(
                f"🗑️ ❌ ERROR: List was actually deleted from DB instead of soft deleted!")
            return Response(
                {'error': 'List was permanently deleted instead of archived'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Send WebSocket notification to all participants
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                user_color = getattr(request.user, 'personal_color', '#4F46E5')
                async_to_sync(channel_layer.group_send)(
                    f'shopping_list_{list_id}',
                    {
                        'type': 'list_deleted',
                        'list_id': list_id,
                        'list_name': list_name,
                        'deleted_by': {
                            'id': str(request.user.id),
                            'username': request.user.username,
                            'first_name': request.user.first_name,
                            'color': user_color
                        },
                        'message': f'{request.user.username} moved "{list_name}" to archive'
                    }
                )
                print(
                    f"📡 WebSocket notification sent for deleted list: {list_name}")
        except Exception as ws_error:
            print(
                f"⚠️ WebSocket notification failed for list deletion: {ws_error}")

        return Response({
            'message': f'List "{list_name}" moved to archive',
            'deleted_at': shopping_list.deleted_at
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def archived(self, request):
        """Get archived (deleted) lists for the user"""
        print(f"🗃️ User {request.user.username} requesting archived lists")

        # Get archived lists: user is creator OR participant, but exclude permanently deleted lists where user is creator but not participant
        archived_lists = ShoppingList.objects.filter(
            Q(creator=request.user) | Q(participants=request.user),
            deleted_at__isnull=False
        ).exclude(
            # Exclude lists that are permanently deleted by this user where they're no longer a participant
            Q(permanently_deleted_by=request.user) & ~Q(
                participants=request.user)
        ).distinct().prefetch_related('collaborators__user', 'items')

        print(
            f"🗃️ Found {archived_lists.count()} archived lists for user {request.user.username}")
        for archived_list in archived_lists:
            print(f"   - {archived_list.name} (ID: {archived_list.id}) - Creator: {archived_list.creator.username}, Deleted by: {archived_list.deleted_by.username if archived_list.deleted_by else 'Unknown'}")
            participants = archived_list.participants.all()
            print(f"     Participants: {[p.username for p in participants]}")

        archived_data = []
        for shopping_list in archived_lists:
            archived_data.append({
                'id': str(shopping_list.id),
                'name': shopping_list.name,
                'deleted_at': shopping_list.deleted_at,
                'permanently_deleted_at': getattr(shopping_list, 'permanently_deleted_at', None),
                'items_count': shopping_list.items.count(),
                'creator': {
                    'username': shopping_list.creator.username,
                    'first_name': shopping_list.creator.first_name,
                },
                'can_restore': shopping_list.can_user_restore(request.user),
                'is_permanently_deleted': shopping_list.is_permanently_deleted(),
                'days_until_auto_delete': shopping_list.days_until_auto_delete
            })

        return Response({
            'results': archived_data,
            'total': len(archived_data)
        })

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore a list from archive"""
        try:
            # Get archived list (need to bypass normal queryset)
            shopping_list = ShoppingList.objects.get(
                id=pk,
                deleted_at__isnull=False
            )

            # Check if user can restore
            if not shopping_list.can_user_restore(request.user):
                return Response(
                    {'error': 'You do not have permission to restore this list'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Restore the list
            shopping_list.restore()

            return Response({
                'message': f'List "{shopping_list.name}" restored successfully'
            })

        except ShoppingList.DoesNotExist:
            return Response(
                {'error': 'Archived list not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['delete'], url_path='permanent-delete')
    def permanent_delete(self, request, pk=None):
        """Step 2: Creator permanently deletes from archive (but keeps in DB for claims)"""
        print(
            f"🗑️ permanent_delete called with pk={pk}, user={request.user.username}")
        try:
            # Get the specific archived list
            shopping_list = ShoppingList.objects.get(
                id=pk,
                deleted_at__isnull=False
            )
            print(f"🗑️ Found archived list: {shopping_list.name}")

            # Check if user has permission to delete this list
            user_is_creator = shopping_list.creator == request.user
            user_is_participant = shopping_list.participants.filter(
                id=request.user.id).exists()
            user_permanently_deleted = shopping_list.permanently_deleted_by == request.user

            if not (user_is_creator or user_is_participant or user_permanently_deleted):
                return Response(
                    {'error': 'You do not have permission to delete this list'},
                    status=status.HTTP_403_FORBIDDEN
                )

            list_name = shopping_list.name
            print(
                f"🗑️ STEP 2 DELETE: Permanent delete requested for: {list_name}")
            print(
                f"🗑️ Current state - permanently_deleted_at: {getattr(shopping_list, 'permanently_deleted_at', None)}")

            # If user is the creator
            if shopping_list.creator == request.user:
                if shopping_list.is_permanently_deleted():
                    # Creator already permanently deleted, now they want to remove from their view
                    # Check if creator is still in participants (shouldn't be, but handle gracefully)
                    if shopping_list.participants.filter(id=request.user.id).exists():
                        shopping_list.participants.remove(request.user)
                        print(
                            f"🗑️ ✅ Creator removed themselves from participants after permanent deletion")
                    else:
                        print(
                            f"🗑️ ✅ Creator was already removed from participants, marking as removed from view")

                    return Response({
                        'message': f'List "{list_name}" removed from your archive',
                        'action': 'removed_from_view'
                    })
                else:
                    # First time permanent delete by creator - try automatic transfer
                    print(
                        f"🔄 Attempting automatic ownership transfer for list: {list_name}")

                    # Check if there are participants to transfer to
                    participants_count = shopping_list.participants.exclude(
                        id=request.user.id).count()
                    print(
                        f"🔍 Found {participants_count} participants for potential transfer")

                    if participants_count > 0:
                        # Automatic ownership transfer
                        success, new_owner, transfer_message = shopping_list.transfer_ownership_to_next_participant(
                            'creator_deleted')

                        if success:
                            print(f"🏆 {transfer_message}")

                            # Send WebSocket notification to the new owner
                            try:
                                channel_layer = get_channel_layer()
                                if channel_layer:
                                    user_color = getattr(
                                        request.user, 'personal_color', '#4F46E5')

                                    # Notify the new owner
                                    async_to_sync(channel_layer.group_send)(
                                        f'user_{new_owner.id}',
                                        {
                                            'type': 'ownership_transferred',
                                            'list': {
                                                'id': str(shopping_list.id),
                                                'name': shopping_list.name,
                                                'is_collaborative': shopping_list.is_collaborative,
                                            },
                                            'new_owner': {
                                                'id': str(new_owner.id),
                                                'username': new_owner.username,
                                                'first_name': new_owner.first_name,
                                            },
                                            'previous_owner': {
                                                'id': str(request.user.id),
                                                'username': request.user.username,
                                                'first_name': request.user.first_name,
                                                'color': user_color
                                            },
                                            'message': f'You became owner of list "{list_name}" after deletion by previous owner. The list is in your archive - restore it to make it active again.'
                                        }
                                    )

                                    # Notify other remaining participants
                                    for participant in shopping_list.participants.all():
                                        if participant.user != new_owner:
                                            async_to_sync(channel_layer.group_send)(
                                                f'user_{participant.user.id}',
                                                {
                                                    'type': 'ownership_transferred',
                                                    'list': {
                                                        'id': str(shopping_list.id),
                                                        'name': shopping_list.name,
                                                    },
                                                    'new_owner': {
                                                        'username': new_owner.username,
                                                        'first_name': new_owner.first_name,
                                                    },
                                                    'previous_owner': {
                                                        'username': request.user.username,
                                                        'first_name': request.user.first_name,
                                                    },
                                                    'message': f'{new_owner.username} is now the owner of "{list_name}"'
                                                }
                                            )

                                    print(
                                        f"📡 WebSocket notifications sent for ownership transfer: {list_name}")
                            except Exception as ws_error:
                                print(
                                    f"⚠️ WebSocket notification failed for ownership transfer: {ws_error}")

                            return Response({
                                'message': f'List "{list_name}" ownership transferred to {new_owner.username}. The list remains in their archive until they choose to restore it.',
                                'action': 'ownership_transferred',
                                'new_owner': {
                                    'username': new_owner.username,
                                    'first_name': new_owner.first_name
                                }
                            })
                        else:
                            print(f"❌ Transfer failed: {transfer_message}")

                    # No participants or transfer failed - permanently delete the list
                    print(
                        f"🗑️ No participants available, permanently deleting list: {list_name}")
                    shopping_list.delete()

                    return Response({
                        'message': f'List "{list_name}" permanently deleted (no participants)',
                        'action': 'permanent_delete'
                    })

            # If user is a participant, remove them from the list
            elif shopping_list.participants.filter(id=request.user.id).exists():
                shopping_list.participants.remove(request.user)
                return Response({
                    'message': f'List "{list_name}" removed from your archive',
                    'action': 'removed_from_view'
                })

            # If user has no relation to this list
            else:
                return Response(
                    {'error': 'You do not have permission to delete this list'},
                    status=status.HTTP_403_FORBIDDEN
                )

        except ShoppingList.DoesNotExist:
            print(
                f"❌ ShoppingList.DoesNotExist: No archived list found with id={pk}")
            # Try to find any list with this ID to debug
            try:
                any_list = ShoppingList.objects.get(id=pk)
                print(
                    f"🔍 List exists but not archived: {any_list.name}, deleted_at={any_list.deleted_at}, is_active={any_list.is_active}")
            except ShoppingList.DoesNotExist:
                print(f"🔍 No list found with id={pk} at all")

            return Response(
                {'error': 'Archived list not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ShoppingItemViewSet(viewsets.ModelViewSet):
    """Shopping item management"""
    serializer_class = ShoppingItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get items from user's lists"""
        user_lists = ShoppingList.objects.filter(
            Q(creator=self.request.user) |
            Q(participants=self.request.user)
        )
        return ShoppingItem.objects.filter(shopping_list__in=user_lists)

    def destroy(self, request, *args, **kwargs):
        """Delete shopping item with proper permission checking"""
        try:
            item = self.get_object()
            shopping_list = item.shopping_list

            print(
                f"🗑️ Deleting item: {item.name} by user: {request.user.username}")

            # Check permissions properly
            is_creator = shopping_list.creator == request.user

            if is_creator:
                # Creator has all permissions
                can_edit = True
            else:
                # Check collaborator permissions
                try:
                    collaborator = shopping_list.collaborators.get(
                        user=request.user)
                    can_edit = collaborator.can_edit
                    print(
                        f"🔒 Collaborator {request.user.username} can_edit: {can_edit}")
                except shopping_list.collaborators.model.DoesNotExist:
                    print(
                        f"❌ User {request.user.username} is not a collaborator")
                    return Response(
                        {'error': 'You do not have permission to delete items from this list'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            if not can_edit:
                print(
                    f"❌ Permission denied: {request.user.username} cannot delete items")
                return Response(
                    {'error': 'You do not have permission to delete items from this list'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Store item info before deletion for WebSocket notification
            item_id = str(item.id)
            item_name = item.name
            list_id = str(shopping_list.id)

            # Perform the deletion
            response = super().destroy(request, *args, **kwargs)

            # Send WebSocket notification to all connected users
            try:
                from channels.layers import get_channel_layer

                channel_layer = get_channel_layer()
                if channel_layer:
                    user_color = getattr(
                        request.user, 'personal_color', '#4F46E5')
                    async_to_sync(channel_layer.group_send)(
                        f'shopping_list_{list_id}',
                        {
                            'type': 'item_deleted',
                            'item_id': item_id,
                            'deleted_by': {
                                'id': str(request.user.id),
                                'username': request.user.username,
                                'color': user_color
                            }
                        }
                    )
                    print(
                        f"📡 WebSocket notification sent for deleted item: {item_name}")
            except Exception as ws_error:
                print(
                    f"⚠️ WebSocket notification failed for item deletion: {ws_error}")

            return response

        except Exception as e:
            print(f"❌ Error deleting item: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to delete item: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """Update shopping item (including quantity)"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()

            print(f"🔄 Updating item: {instance.name} (partial={partial})")
            print(f"📝 Update data: {request.data}")
            print(f"🔍 Request method: {request.method}")

            # Check permissions properly
            shopping_list = instance.shopping_list
            is_creator = shopping_list.creator == request.user

            if is_creator:
                # Creator has all permissions
                can_edit = True
            else:
                # Check collaborator permissions
                try:
                    collaborator = shopping_list.collaborators.get(
                        user=request.user)
                    can_edit = collaborator.can_edit
                    print(
                        f"🔒 Collaborator {request.user.username} can_edit: {can_edit}")
                except shopping_list.collaborators.model.DoesNotExist:
                    print(
                        f"❌ User {request.user.username} is not a collaborator")
                    return Response(
                        {'error': 'You do not have permission to update items in this list'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            if not can_edit:
                print(
                    f"❌ Permission denied: {request.user.username} cannot edit items")
                return Response(
                    {'error': 'You do not have permission to update items in this list'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = self.get_serializer(
                instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            print(f"✅ Item updated successfully: {instance.name}")

            # Send WebSocket notification for quantity changes
            if 'quantity' in request.data:
                try:
                    channel_layer = get_channel_layer()
                    if channel_layer:
                        user_color = getattr(
                            request.user, 'personal_color', '#4F46E5')
                        async_to_sync(channel_layer.group_send)(
                            f'shopping_list_{instance.shopping_list.id}',
                            {
                                'type': 'item_updated',
                                'item': ShoppingItemSerializer(instance).data,
                                'user': {
                                    'id': str(request.user.id),
                                    'username': request.user.username,
                                    'color': user_color
                                }
                            }
                        )
                        print(
                            f"📡 WebSocket notification sent for updated item: {instance.name}")
                except Exception as ws_error:
                    print(f"⚠️ WebSocket notification failed: {ws_error}")

            return Response(serializer.data)

        except Exception as e:
            print(f"❌ Error updating item: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to update item: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def partial_update(self, request, *args, **kwargs):
        """Partial update (PATCH) support"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def toggle_complete(self, request, pk=None):
        """Toggle item completion status"""
        try:
            item = self.get_object()
            shopping_list = item.shopping_list
            print(
                f"🔄 Toggling completion for item: {item.name} by user: {request.user.username}")

            # Check permissions
            is_creator = shopping_list.creator == request.user

            if is_creator:
                # Creator has all permissions
                can_edit = True
            else:
                # Check collaborator permissions
                try:
                    collaborator = shopping_list.collaborators.get(
                        user=request.user)
                    can_edit = collaborator.can_edit
                    print(
                        f"🔒 Collaborator {request.user.username} can_edit: {can_edit}")
                except shopping_list.collaborators.model.DoesNotExist:
                    print(
                        f"❌ User {request.user.username} is not a collaborator")
                    return Response(
                        {'error': 'You do not have permission to edit items in this list'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            if not can_edit:
                print(
                    f"❌ Permission denied: {request.user.username} cannot edit items")
                return Response(
                    {'error': 'You do not have permission to edit items in this list'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if item.is_completed:
                item.is_completed = False
                item.completed_by = None
                item.completed_at = None
                print(f"✅ Item marked as incomplete: {item.name}")
            else:
                item.is_completed = True
                item.completed_by = request.user
                from django.utils import timezone
                item.completed_at = timezone.now()
                print(f"✅ Item marked as complete: {item.name}")

            item.save()

            # Send WebSocket notification
            try:
                channel_layer = get_channel_layer()
                if channel_layer:
                    user_color = getattr(
                        request.user, 'personal_color', '#4F46E5')
                    async_to_sync(channel_layer.group_send)(
                        f'shopping_list_{item.shopping_list.id}',
                        {
                            'type': 'item_toggled',
                            'item': ShoppingItemSerializer(item).data,
                            'user': {
                                'id': str(request.user.id),
                                'username': request.user.username,
                                'color': user_color
                            }
                        }
                    )
                    print(
                        f"📡 WebSocket notification sent for toggled item: {item.name}")
            except Exception as ws_error:
                print(f"⚠️ WebSocket notification failed: {ws_error}")
                # Don't fail the request if WebSocket fails

            return Response(ShoppingItemSerializer(item).data)

        except Exception as e:
            print(f"❌ Error toggling item completion: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to toggle item: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['patch'])
    def update_weight_quantity(self, request, pk=None):
        """Update item weight quantity"""
        try:
            item = self.get_object()
            weight_quantity = request.data.get('weight_quantity', 0)

            print(
                f"📊 Updating weight quantity for item: {item.name} to: {weight_quantity}g")

            # Check permissions properly
            shopping_list = item.shopping_list
            is_creator = shopping_list.creator == request.user

            if is_creator:
                # Creator has all permissions
                can_edit = True
            else:
                # Check collaborator permissions
                try:
                    collaborator = shopping_list.collaborators.get(
                        user=request.user)
                    can_edit = collaborator.can_edit
                    print(
                        f"🔒 Collaborator {request.user.username} can_edit: {can_edit}")
                except shopping_list.collaborators.model.DoesNotExist:
                    print(
                        f"❌ User {request.user.username} is not a collaborator")
                    return Response(
                        {'error': 'You do not have permission to update items in this list'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            if not can_edit:
                print(
                    f"❌ Permission denied: {request.user.username} cannot edit items")
                return Response(
                    {'error': 'You do not have permission to update items in this list'},
                    status=status.HTTP_403_FORBIDDEN
                )

            item.weight_quantity = weight_quantity
            item.save()

            print(f"✅ Weight quantity updated successfully: {item.name}")

            # Send WebSocket notification
            try:
                channel_layer = get_channel_layer()
                if channel_layer:
                    user_color = getattr(
                        request.user, 'personal_color', '#4F46E5')
                    async_to_sync(channel_layer.group_send)(
                        f'shopping_list_{item.shopping_list.id}',
                        {
                            'type': 'item_updated',
                            'item': ShoppingItemSerializer(item).data,
                            'user': {
                                'id': str(request.user.id),
                                'username': request.user.username,
                                'color': user_color
                            }
                        }
                    )
                    print(
                        f"📡 WebSocket notification sent for weight update: {item.name}")
            except Exception as ws_error:
                print(f"⚠️ WebSocket notification failed: {ws_error}")

            return Response(ShoppingItemSerializer(item).data)

        except Exception as e:
            print(f"❌ Error updating weight quantity: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to update weight quantity: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['patch'])
    def update_liquid_quantity(self, request, pk=None):
        """Update item liquid quantity"""
        try:
            item = self.get_object()
            liquid_quantity = request.data.get('liquid_quantity', 0)

            print(
                f"🥤 Updating liquid quantity for item: {item.name} to: {liquid_quantity}ml")

            # Check permissions properly
            shopping_list = item.shopping_list
            is_creator = shopping_list.creator == request.user

            if is_creator:
                # Creator has all permissions
                can_edit = True
            else:
                # Check collaborator permissions
                try:
                    collaborator = shopping_list.collaborators.get(
                        user=request.user)
                    can_edit = collaborator.can_edit
                    print(
                        f"🔒 Collaborator {request.user.username} can_edit: {can_edit}")
                except shopping_list.collaborators.model.DoesNotExist:
                    print(
                        f"❌ User {request.user.username} is not a collaborator")
                    return Response(
                        {'error': 'You do not have permission to update items in this list'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            if not can_edit:
                print(
                    f"❌ Permission denied: {request.user.username} cannot edit items")
                return Response(
                    {'error': 'You do not have permission to update items in this list'},
                    status=status.HTTP_403_FORBIDDEN
                )

            item.liquid_quantity = liquid_quantity
            item.save()

            print(f"✅ Liquid quantity updated successfully: {item.name}")

            # Send WebSocket notification
            try:
                channel_layer = get_channel_layer()
                if channel_layer:
                    user_color = getattr(
                        request.user, 'personal_color', '#4F46E5')
                    async_to_sync(channel_layer.group_send)(
                        f'shopping_list_{item.shopping_list.id}',
                        {
                            'type': 'item_updated',
                            'item': ShoppingItemSerializer(item).data,
                            'user': {
                                'id': str(request.user.id),
                                'username': request.user.username,
                                'color': user_color
                            }
                        }
                    )
                    print(
                        f"📡 WebSocket notification sent for liquid update: {item.name}")
            except Exception as ws_error:
                print(f"⚠️ WebSocket notification failed: {ws_error}")

            return Response(ShoppingItemSerializer(item).data)

        except Exception as e:
            print(f"❌ Error updating liquid quantity: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to update liquid quantity: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InventoryViewSet(viewsets.ModelViewSet):
    """Inventory management"""
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get user's inventory"""
        return Inventory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get items expiring in next 7 days"""
        from datetime import timedelta
        from django.utils import timezone

        expiry_date = timezone.now().date() + timedelta(days=7)
        items = self.get_queryset().filter(
            expiration_date__lte=expiry_date,
            expiration_date__gte=timezone.now().date()
        )

        return Response(InventorySerializer(items, many=True).data)

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get low stock items"""
        items = []
        for item in self.get_queryset():
            if item.is_low_stock:
                items.append(item)

        return Response(InventorySerializer(items, many=True).data)
