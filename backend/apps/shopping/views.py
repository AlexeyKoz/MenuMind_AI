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
        print("="*80)
        print("🚀 ADD_ITEM METHOD CALLED - NEW CODE VERSION 2.0")
        print("="*80)
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
            print(f"📝 Full request data keys: {list(request.data.keys())}")
            
            # NEW: Debug weight/liquid quantities from recipe
            weight_qty = item_data.get('weight_quantity', 0)
            liquid_qty = item_data.get('liquid_quantity', 0)
            auto_counter = item_data.get('_auto_enable_counter', None)
            
            print(f"⚖️ [RECIPE ADD DEBUG] weight_quantity: {weight_qty}")
            print(f"🥤 [RECIPE ADD DEBUG] liquid_quantity: {liquid_qty}")
            print(f"🎯 [RECIPE ADD DEBUG] _auto_enable_counter: {auto_counter}")

            # Use safe defaults for missing attributes
            user_color = getattr(request.user, 'personal_color', '#4F46E5')
            priority = 1 if is_creator else 0

            # NEW: Translate manually-added item to all languages
            item_name = item_data.get('name', '')
            print(f"[MANUAL ITEM MULTILANG] Translating item: {item_name}")

            # Get multilang translator
            from apps.shopping.multilang_translator import get_multilang_translator
            translator = get_multilang_translator()

            # Create ingredient-like structure for translator
            temp_ingredient = [{
                'name': item_name,
                'ingredient_key': None  # Manual items don't have IML keys
            }]

            # Translate to all languages
            try:
                translated = translator.translate_ingredients_batch(
                    temp_ingredient,
                    source_language='en'
                )
                name_translations = translated[0].get('name_translations', {})
                print(
                    f"[MANUAL ITEM MULTILANG] ✅ Translations: {name_translations}")
            except Exception as e:
                print(f"[MANUAL ITEM MULTILANG] ⚠️ Translation failed: {e}")
                # Fallback: just use English
                name_translations = {'en': item_name}

            # Import Decimal for proper number handling
            from decimal import Decimal
            
            # Create the item with translations AND weight/liquid quantities
            item = ShoppingItem.objects.create(
                shopping_list=shopping_list,
                added_by=request.user,
                name=item_data.get('name', ''),
                name_translations=name_translations,  # NEW!
                original_language='en',  # NEW!
                quantity=Decimal(str(item_data.get('quantity', 1))),
                unit=item_data.get('unit', 'unit'),
                weight_quantity=Decimal(str(weight_qty)),  # NEW: From recipe
                liquid_quantity=Decimal(str(liquid_qty)),  # NEW: From recipe
                category=item_data.get('category', 'other'),
                notes=item_data.get('notes', ''),
                user_color=user_color,
                priority=priority
            )

            print(f"✅ Item created successfully: {item.name}")
            print(f"✅ Stored translations: {item.name_translations}")
            print(f"✅ Stored weight_quantity: {item.weight_quantity}g")
            print(f"✅ Stored liquid_quantity: {item.liquid_quantity}ml")
            
            # Set auto-enable counter flag if provided (for frontend)
            # This must be set BEFORE serialization so the serializer can access it
            if auto_counter:
                item._auto_enable_counter = auto_counter
                print(f"✅ Set auto_enable_counter: {auto_counter}")
            # If no explicit flag but we have weight/liquid quantities, infer the counter
            elif weight_qty > 0:
                item._auto_enable_counter = 'weight'
                print(f"✅ Auto-inferred counter: weight (from weight_quantity={weight_qty})")
            elif liquid_qty > 0:
                item._auto_enable_counter = 'liquid'
                print(f"✅ Auto-inferred counter: liquid (from liquid_quantity={liquid_qty})")

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
                    # Serialize with request context for language-aware display_name
                    serializer = ShoppingItemSerializer(
                        item, context={'request': request})

                    # Import UUID converter from consumers
                    from uuid import UUID
                    from decimal import Decimal
                    import json

                    # Convert UUIDs and Decimals in serialized data
                    def convert_for_channels(data):
                        if isinstance(data, dict):
                            return {k: convert_for_channels(v) for k, v in data.items()}
                        elif isinstance(data, list):
                            return [convert_for_channels(item) for item in data]
                        elif isinstance(data, UUID):
                            return str(data)
                        elif isinstance(data, Decimal):
                            return float(data)
                        return data

                    item_data = convert_for_channels(serializer.data)
                    
                    # Debug: Log what's being sent
                    print(f"📡 [WEBSOCKET] Sending item_added notification:")
                    print(f"📡 [WEBSOCKET] - auto_enable_counter: {item_data.get('auto_enable_counter')}")
                    print(f"📡 [WEBSOCKET] - weight_quantity: {item_data.get('weight_quantity')}")
                    print(f"📡 [WEBSOCKET] - liquid_quantity: {item_data.get('liquid_quantity')}")

                    async_to_sync(channel_layer.group_send)(
                        f'shopping_list_{shopping_list.id}',
                        {
                            'type': 'item_added',
                            'item': item_data,
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
                    print(f"📡 With translations: {name_translations}")
            except Exception as ws_error:
                print(f"⚠️ WebSocket notification failed: {ws_error}")
                # Don't fail the request if WebSocket fails

            # Return success response with request context
            return Response(
                ShoppingItemSerializer(
                    item, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

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
        IMPROVED: Fast AI-powered recipe finder with two-phase processing

        PHASE 1 (FAST - 5-10 seconds):
        - Check deduplication (existing recipe)
        - If not exists: Fast extract ingredients only
        - Translate to user's language
        - Add to shopping list immediately

        PHASE 2 (BACKGROUND - 30-40 seconds):
        - Extract full recipe (steps, nutrition)
        - Translate to remaining languages
        - Create canonical recipe
        - Notify user via WebSocket
        
        Security: Input is validated and sanitized
        """
        from apps.core.security import AIInputValidator
        
        print("[FAST AI RECIPE] ========== START ai_add_items ==========")
        shopping_list = self.get_object()
        query = request.data.get('text', '')
        print(f"[FAST AI RECIPE] Original query: '{query}'")
        print(f"[FAST AI RECIPE] Shopping list: {shopping_list.id}")

        if not query:
            print("[FAST AI RECIPE] ERROR: No query provided")
            return Response({
                'success': False,
                'message': 'Please describe what you want to cook'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 🔒 SECURITY: Validate and sanitize AI input
        is_valid, error_message, sanitized_query = AIInputValidator.validate_description_input(
            query, field_name="recipe request"
        )
        
        if not is_valid:
            print(f"[FAST AI RECIPE] ERROR: Validation failed - {error_message}")
            return Response({
                'success': False,
                'message': f'Input validation failed: {error_message}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        query = sanitized_query

        # VALIDATION: Detect and translate keyboard layout issues (e.g., Russian layout typing English words)
        # Example: "ьфкпрфкшеу" (Russian layout) → "margharita" (English)
        if self._is_wrong_keyboard_layout(query):
            print(
                f"[FAST AI RECIPE] ⚠️ Detected wrong keyboard layout: '{query}'")
            translated_query = self._translate_keyboard_layout(query)
            if translated_query and translated_query != query:
                print(
                    f"[FAST AI RECIPE] ✅ Translated to: '{translated_query}'")
                query = translated_query

        print(f"[FAST AI RECIPE] Final query for processing: '{query}'")

        # Import services
        try:
            print("[FAST AI RECIPE] Importing services...")
            from apps.recipes.services import RecipeAgentService
            from apps.recipes.models import CanonicalRecipe, Recipe
            from apps.shopping.fast_recipe_service import FastRecipeIngredientService
            from apps.shopping.tasks import complete_shopping_list_recipe
            from apps.recipes.brave_firecrawl_scraper import BraveFirecrawlScraper
            print("[FAST AI RECIPE] ✅ Services imported successfully")
        except ImportError as e:
            print(f"[ERROR] Required service not available: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': 'Recipe service is not available'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Get user preferences
        user_language = getattr(request.user, 'preferred_language', 'en')
        user_weight_unit = getattr(request.user, 'weight_unit', 'kg')
        user_unit_system = 'metric' if user_weight_unit == 'kg' else 'imperial'

        user_preferences = {
            'dietary_restrictions': getattr(request.user, 'dietary_restrictions', ''),
            'allergies': getattr(request.user, 'allergies', ''),
            'language': user_language,
            'unit_system': user_unit_system
        }

        print(
            f"[FAST AI RECIPE] User language: {user_language}, Unit system: {user_unit_system}")

        try:
            # STEP 1: Check deduplication using AI semantic matching
            print(
                f"[FAST AI RECIPE] Checking for existing recipe using AI: {query}")
            from apps.core.deduplication_service import get_deduplication_service

            dedup_service = get_deduplication_service()
            existing_canonical = async_to_sync(dedup_service.find_duplicate)(
                recipe_name=query,
                user_language=user_language
            )

            if existing_canonical:
                print(
                    f"[FAST AI RECIPE] ✅ AI found existing recipe: {existing_canonical.name}")

                # Use existing recipe - get ingredients in user's language
                recipe_name = existing_canonical.name
                canonical_recipe_id = str(existing_canonical.id)
                is_new = False

                # Get ingredients from base_ingredients (RCIP format)
                ingredients_data = existing_canonical.base_ingredients

                # Validate ingredients_data format
                if not ingredients_data or not isinstance(ingredients_data, list):
                    print(
                        f"[FAST AI RECIPE] ⚠️ Invalid base_ingredients format, fetching from Recipe model...")

                    # Fallback: Try to get from the first Recipe translation
                    recipe_translation = Recipe.objects.filter(
                        canonical_recipe=existing_canonical).first()
                    if recipe_translation and hasattr(recipe_translation, 'ingredients'):
                        ingredients_data = recipe_translation.ingredients
                    else:
                        print(
                            f"[FAST AI RECIPE] ❌ No ingredients found for existing recipe!")
                        return Response({
                            'success': False,
                            'message': f'Recipe "{existing_canonical.name}" exists but has no ingredients. Please regenerate it.'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                print(
                    f"[FAST AI RECIPE] Using {len(ingredients_data)} ingredients from existing recipe")

                # Ensure ingredients have name_translations (for multilang support)
                # If they don't, we need to translate them now
                from apps.shopping.multilang_translator import get_multilang_translator
                translator = get_multilang_translator()

                for ing in ingredients_data:
                    if 'name_translations' not in ing or not ing['name_translations']:
                        print(
                            f"[FAST AI RECIPE] ⚠️ Ingredient '{ing.get('name')}' missing translations, translating now...")
                        temp_ing = [
                            {'name': ing.get('name', ''), 'ingredient_key': ing.get('ingredient_key')}]
                        translated = translator.translate_ingredients_batch(
                            temp_ing, source_language='en')
                        ing['name_translations'] = translated[0].get(
                            'name_translations', {'en': ing.get('name', '')})
                        print(
                            f"[FAST AI RECIPE] ✅ Added translations: {ing['name_translations']}")

            else:
                # STEP 2: Recipe doesn't exist - FAST EXTRACTION
                print(
                    f"[FAST AI RECIPE] Recipe not found, starting fast extraction...")

                # Search and scrape (Brave + Firecrawl)
                scraper = BraveFirecrawlScraper()
                scraped_recipes = scraper.search_and_scrape(
                    query, max_results=1)

                if not scraped_recipes:
                    return Response({
                        'success': False,
                        'message': 'Could not find recipe online'
                    }, status=status.HTTP_404_NOT_FOUND)

                scraped_data = scraped_recipes[0]
                print(
                    f"[FAST AI RECIPE] ✅ Scraped from: {scraped_data['url']}")

                # FAST EXTRACTION: Ingredients only + user language translation
                fast_service = FastRecipeIngredientService()

                fast_result = async_to_sync(fast_service.extract_ingredients_fast)(
                    scraped_data=scraped_data,
                    recipe_name=query,
                    user_language=user_language,
                    user_unit_system=user_unit_system
                )

                print(
                    f"[FAST AI RECIPE] 📊 fast_result type: {type(fast_result)}")
                print(
                    f"[FAST AI RECIPE] 📊 fast_result keys: {fast_result.keys() if fast_result else 'None'}")

                if not fast_result or not fast_result.get('ingredients'):
                    # Generate helpful suggestions based on the query
                    suggestions = self._generate_recipe_suggestions(
                        query, user_language)

                    return Response({
                        'success': False,
                        'message': 'Could not extract ingredients from recipe',
                        'show_suggestions': True,
                        'failed_query': query,
                        'suggestions': suggestions
                    }, status=status.HTTP_404_NOT_FOUND)

                print(
                    f"[FAST AI RECIPE] ✅ Fast extraction complete: {len(fast_result['ingredients'])} ingredients")

                # Get recipe name (base English name)
                recipe_name = fast_result['recipe_name']
                recipe_name_translations = fast_result.get(
                    'recipe_name_translations', {'en': recipe_name})
                ingredients_data = fast_result['ingredients']
                recipe_hash = fast_result['recipe_hash']
                canonical_recipe_id = None  # Will be created in background
                is_new = True

                print(f"[FAST AI RECIPE] Recipe name: {recipe_name}")
                print(
                    f"[FAST AI RECIPE] Recipe translations: {recipe_name_translations}")

                # STEP 3: Trigger BACKGROUND TASK for full recipe processing
                print(
                    f"[FAST AI RECIPE] Triggering background task for full recipe...")

                complete_shopping_list_recipe.delay(
                    recipe_hash=recipe_hash,
                    scraped_data=scraped_data,
                    recipe_name=fast_result['recipe_name'],  # English name
                    user_id=request.user.id,
                    shopping_list_id=shopping_list.id,
                    user_language=user_language
                )

                print(f"[FAST AI RECIPE] ✅ Background task triggered")

            # STEP 4: Add ingredients to shopping list (FAST)
            items_created = []
            items_updated = []
            user_color = getattr(request.user, 'personal_color', '#4F46E5')

            print(
                f"[FAST AI RECIPE] Adding {len(ingredients_data)} ingredients to shopping list...")

            # Process each ingredient
            for ing_data in ingredients_data:
                # Get ingredient name (now we have translations for ALL languages!)
                raw_name = ing_data.get('name', '')
                name_translations = ing_data.get('name_translations', {})
                
                # CRITICAL FIX: If name is already a dict (translation object), extract the English name
                if isinstance(raw_name, dict):
                    ingredient_name = raw_name.get('en') or raw_name.get(list(raw_name.keys())[0]) if raw_name else ''
                    # Also use it for translations if no separate translations provided
                    if not name_translations:
                        name_translations = raw_name
                else:
                    ingredient_name = raw_name

                # DEBUG: Log translation data
                print(
                    f"[MULTILANG DEBUG] Processing ingredient: {ingredient_name}")
                print(
                    f"[MULTILANG DEBUG] Translations received: {name_translations}")
                print(
                    f"[MULTILANG DEBUG] Translation source: {ing_data.get('_translation_source', 'unknown')}")

                # Fallback: if no translations, create basic dict
                if not name_translations:
                    name_translations = {'en': ingredient_name}
                    print(
                        f"[MULTILANG DEBUG] ⚠️ No translations found, using fallback")

                if not ingredient_name:
                    continue

                # Skip if it looks like an AI message
                if len(ingredient_name) > 100:
                    print(
                        f"[FAST AI RECIPE] Skipping long text: {ingredient_name[:50]}...")
                    continue

                # Get quantity and unit from IML mapping
                quantity = ing_data.get('quantity', 1)
                unit = ing_data.get('unit', 'pieces')
                unit_type = ing_data.get('unit_type', 'none')
                ingredient_key = ing_data.get('ingredient_key')

                # Determine counter type from unit_type
                if unit_type == 'weight':
                    counter_type = 'weight'
                    # Convert to grams (base unit for weight)
                    weight_in_grams = self._convert_to_grams(quantity, unit)
                    weight_quantity = weight_in_grams
                    liquid_quantity = 0
                    item_quantity = 1  # Default to 1 for weight items
                elif unit_type == 'volume':
                    counter_type = 'liquid'
                    # Convert to ml (base unit for liquid)
                    liquid_in_ml = self._convert_to_ml(quantity, unit)
                    weight_quantity = 0
                    liquid_quantity = liquid_in_ml
                    item_quantity = 1  # Default to 1 for liquid items
                else:
                    counter_type = 'none'
                    weight_quantity = 0
                    liquid_quantity = 0
                    item_quantity = quantity if quantity else 1

                print(
                    f"[FAST AI RECIPE] {ingredient_name}: {quantity} {unit} ({counter_type})")
                print(f"[FAST AI RECIPE] 🌍 Translations: {name_translations}")

                # Check for existing item
                existing_item = ShoppingItem.objects.filter(
                    shopping_list=shopping_list,
                    name__iexact=ingredient_name,
                    is_completed=False
                ).first()

                from decimal import Decimal

                if existing_item:
                    # Update existing item (and merge translations)
                    if counter_type == 'weight':
                        existing_item.weight_quantity += Decimal(
                            str(weight_quantity))
                    elif counter_type == 'liquid':
                        existing_item.liquid_quantity += Decimal(
                            str(liquid_quantity))
                    else:
                        existing_item.quantity += Decimal(
                            str(item_quantity))

                    # Update translations if we have them
                    if name_translations:
                        existing_item.name_translations = name_translations

                    existing_item.save()
                    items_updated.append(existing_item)
                    print(f"[FAST AI RECIPE] ✅ Updated: {ingredient_name}")
                else:
                    # Create new item with translations
                    print(f"[MULTILANG DEBUG] Creating new item with translations:")
                    print(f"[MULTILANG DEBUG]   name: {ingredient_name}")
                    print(
                        f"[MULTILANG DEBUG]   name_translations: {name_translations}")
                    print(f"[MULTILANG DEBUG]   original_language: en")

                    new_item = ShoppingItem.objects.create(
                        shopping_list=shopping_list,
                        name=ingredient_name,
                        name_translations=name_translations,  # NEW!
                        original_language='en',  # NEW!
                        quantity=Decimal(str(item_quantity)),
                        unit=unit or 'unit',
                        weight_quantity=Decimal(str(weight_quantity)),
                        liquid_quantity=Decimal(str(liquid_quantity)),
                        added_by=request.user,
                        user_color=user_color,
                        ingredient_key=ingredient_key
                    )

                    # Verify it was saved
                    print(
                        f"[MULTILANG DEBUG] ✅ Item created. Stored translations: {new_item.name_translations}")

                    # Add auto-enable flag for frontend to open counter
                    # This is NOT a model field, just a response attribute
                    if counter_type == 'weight' and weight_quantity > 0:
                        new_item._auto_enable_counter = 'weight'
                    elif counter_type == 'liquid' and liquid_quantity > 0:
                        new_item._auto_enable_counter = 'liquid'

                    items_created.append(new_item)
                    print(f"[FAST AI RECIPE] ✅ Created: {ingredient_name}")

            # STEP 5: Return success response
            print(
                f"[FAST AI RECIPE] ✅ Successfully added {len(items_created)} new items and updated {len(items_updated)} items")

            # Serialize items for response
            from .serializers import ShoppingItemSerializer
            created_serializer = ShoppingItemSerializer(
                items_created, many=True, context={'request': request})
            updated_serializer = ShoppingItemSerializer(
                items_updated, many=True, context={'request': request})

            # Prepare message
            message_content = f"Added {len(items_created)} ingredients from {recipe_name}"
            if is_new:
                message_content += " (full recipe generating in background...)"

            # STEP 6: Send WebSocket notification with multilang support
            try:
                channel_layer = get_channel_layer()
                if channel_layer:
                    # Get recipe name translations
                    if is_new and 'fast_result' in locals():
                        recipe_name_translations = fast_result.get(
                            'recipe_name_translations', {'en': recipe_name})
                    else:
                        # For existing recipes, use the canonical recipe's title_translations
                        if existing_canonical and hasattr(existing_canonical, 'title_translations'):
                            recipe_name_translations = existing_canonical.title_translations or {
                                'en': recipe_name}
                        else:
                            recipe_name_translations = {'en': recipe_name}

                    async_to_sync(channel_layer.group_send)(
                        f'shopping_list_{shopping_list.id}',
                        {
                            'type': 'items_added',
                            'items': created_serializer.data,
                            'recipe_name': recipe_name,
                            'recipe_name_translations': recipe_name_translations,  # NEW!
                            'user': {
                                'id': str(request.user.id),
                                'username': request.user.username,
                                'first_name': request.user.first_name,
                                'color': user_color
                            }
                        }
                    )
                    print(
                        f"[FAST AI RECIPE] 📡 WebSocket notification sent with multilang data")
            except Exception as ws_error:
                print(
                    f"[FAST AI RECIPE] ⚠️ WebSocket notification failed: {ws_error}")

            # DEBUG: Print what we're about to return
            print(f"[FAST AI RECIPE] 📤 Returning response:")
            print(f"  - recipe_name: {recipe_name}")
            print(f"  - canonical_recipe_id: {canonical_recipe_id}")
            print(f"  - is_new: {is_new}")
            print(f"  - is_generating: {is_new}")

            return Response({
                'success': True,
                'message': message_content,
                'recipe_name': recipe_name,
                # NEW!
                'recipe_name_translations': recipe_name_translations if 'recipe_name_translations' in locals() else {'en': recipe_name},
                'canonical_recipe_id': canonical_recipe_id,
                'is_new': is_new,
                'is_generating': is_new,
                'items_created': created_serializer.data,
                'items_updated': updated_serializer.data
            })

        except Exception as e:
            print(f"[ERROR] Exception in ai_add_items: {e}")
            import traceback
            print(f"[ERROR] Full traceback:")
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

    @action(detail=True, methods=['post'])
    def send_to_inventory(self, request, pk=None):
        """
        Transfer completed items from shopping list to inventory with AI categorization

        POST /api/shopping/lists/{id}/send_to_inventory/
        Body:
        {
            "item_ids": [uuid, uuid, ...],  // IDs of completed items
            "ai_categorize": true
        }

        Returns AI categorization suggestions for review
        """
        from .inventory_services import InventoryCategorizationService

        shopping_list = self.get_object()
        item_ids = request.data.get('item_ids', [])
        ai_categorize = request.data.get('ai_categorize', True)

        if not item_ids:
            return Response(
                {'error': 'item_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the shopping items
        items = ShoppingItem.objects.filter(
            id__in=item_ids,
            shopping_list=shopping_list,
            is_completed=True  # Only completed items
        )

        if not items.exists():
            return Response(
                {'error': 'No completed items found with provided IDs'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prepare items for categorization
        items_for_categorization = []
        # Get user's language preference
        user_language = request.query_params.get('lang', 'en')
        
        for item in items:
            # Extract the correct name from translations
            if isinstance(item.name, dict):
                item_name = item.name.get(user_language) or item.name.get('en') or list(item.name.values())[0]
            else:
                item_name = item.name
                
            items_for_categorization.append({
                'id': str(item.id),
                'name': item_name
            })

        # Get AI categorization suggestions
        suggestions = []
        if ai_categorize:
            service = InventoryCategorizationService()
            suggestions = service.categorize_items(items_for_categorization)
        else:
            # Return items without AI suggestions
            for item in items:
                # Extract the correct name from translations
                if isinstance(item.name, dict):
                    item_name = item.name.get(user_language) or item.name.get('en') or list(item.name.values())[0]
                else:
                    item_name = item.name
                    
                suggestions.append({
                    'item_id': str(item.id),
                    'name': item_name,
                    'suggested_location': 'pantry',
                    'suggested_category': 'other',
                    'suggested_expiration_days': 30,
                    'suggested_quantity': 1,
                    'suggested_unit': 'units',
                    'confidence': 0.5
                })

        return Response({
            'success': True,
            'shopping_list_id': str(shopping_list.id),
            'shopping_list_name': shopping_list.name,
            'item_count': items.count(),
            'suggestions': suggestions,
            'message': 'Review and confirm the categorization before adding to inventory'
        })

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

                    # No participants or transfer failed - mark as permanently deleted
                    print(
                        f"🗑️ No participants available, marking list as permanently deleted: {list_name}")
                    shopping_list.permanent_delete_by_creator(request.user)

                    return Response({
                        'message': f'List "{list_name}" permanently deleted',
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

    def _is_wrong_keyboard_layout(self, query: str) -> bool:
        """
        Detect if user typed with wrong keyboard layout
        (e.g., typing English words but keyboard was on Russian/Hebrew layout)
        """
        # Check if query contains mostly non-Latin characters
        non_latin_count = sum(
            1 for c in query if not c.isascii() and c.isalpha())
        total_alpha = sum(1 for c in query if c.isalpha())

        if total_alpha == 0:
            return False

        non_latin_ratio = non_latin_count / total_alpha

        # If more than 80% non-Latin, might be wrong keyboard layout
        return non_latin_ratio > 0.8

    def _translate_keyboard_layout(self, query: str) -> str:
        """
        Attempt to translate keyboard layout errors
        Uses Russian/English keyboard mapping as example
        """
        # Russian to English keyboard map (most common issue)
        rus_to_eng = {
            'й': 'q', 'ц': 'w', 'у': 'e', 'к': 'r', 'е': 't', 'н': 'y', 'г': 'u', 'ш': 'i', 'щ': 'o', 'з': 'p',
            'ф': 'a', 'ы': 's', 'в': 'd', 'а': 'f', 'п': 'g', 'р': 'h', 'о': 'j', 'л': 'k', 'д': 'l',
            'я': 'z', 'ч': 'x', 'с': 'c', 'м': 'v', 'и': 'b', 'т': 'n', 'ь': 'm',
            'х': '[', 'ъ': ']', 'ж': ';', 'э': "'", 'б': ',', 'ю': '.'
        }

        # Try to transliterate
        transliterated = ''.join(rus_to_eng.get(c.lower(), c) for c in query)

        if transliterated != query:
            print(f"[KEYBOARD] Transliterated '{query}' → '{transliterated}'")
            return transliterated

        return query

    def _generate_recipe_suggestions(self, query: str, user_language: str = 'en') -> list:
        """
        Generate helpful recipe suggestions based on failed query
        Returns language-appropriate suggestions
        """
        # Multilingual popular recipes by category
        suggestions_db = {
            'en': {
                'desserts': ['chocolate cake', 'apple pie', 'brownies', 'cheesecake', 'tiramisu', 'panna cotta'],
                'pasta': ['spaghetti carbonara', 'lasagna', 'fettuccine alfredo', 'penne arrabbiata', 'pasta bolognese'],
                'chicken': ['chicken curry', 'roasted chicken', 'chicken stir fry', 'chicken tikka masala', 'fried chicken'],
                'soup': ['tomato soup', 'chicken soup', 'minestrone', 'french onion soup', 'cream of mushroom'],
                'salad': ['caesar salad', 'greek salad', 'caprese salad', 'nicoise salad', 'cobb salad'],
                'breakfast': ['pancakes', 'french toast', 'omelette', 'shakshuka', 'eggs benedict'],
                'popular': ['pizza margherita', 'burger', 'tacos', 'sushi rolls', 'pad thai', 'ramen']
            },
            'ru': {
                'desserts': ['шарлотка', 'наполеон', 'медовик', 'тирамису', 'чизкейк', 'брауни'],
                'pasta': ['паста карбонара', 'лазанья', 'спагетти болоньезе', 'паста альфредо', 'пенне аррабиата'],
                'chicken': ['куриное карри', 'жареная курица', 'курица в духовке', 'куриный суп', 'котлеты'],
                'soup': ['борщ', 'солянка', 'куриный суп', 'грибной суп', 'томатный суп'],
                'salad': ['оливье', 'цезарь', 'греческий салат', 'винегрет', 'салат с тунцом'],
                'breakfast': ['блины', 'сырники', 'омлет', 'яичница', 'каша'],
                'popular': ['пельмени', 'борщ', 'блины', 'оливье', 'плов', 'шашлык']
            },
            'he': {
                'desserts': ['עוגת שוקולד', 'טירמיסו', 'פאי תפוחים', 'צ\'יזקייק', 'בראוניז', 'עוגיות'],
                'pasta': ['פסטה קרבונרה', 'לזניה', 'ספגטי בולונז', 'פסטה אלפרדו', 'פנה ארביאטה'],
                'chicken': ['קארי עוף', 'עוף בתנור', 'שניצל', 'עוף מוקפץ', 'עוף טיקה מסאלה'],
                'soup': ['מרק עוף', 'מרק עגבניות', 'מרק ירקות', 'מרק פטריות', 'מרק בצל'],
                'salad': ['סלט ירקות', 'סלט יווני', 'סלט קיסר', 'סלט ניסואז', 'סלט כרוב'],
                'breakfast': ['שקשוקה', 'חביתה', 'פנקייק', 'טוסט צרפתי', 'ביצים בנדיקט'],
                'popular': ['שקשוקה', 'חומוס', 'פלאפל', 'שניצל', 'סלט ישראלי', 'סבי']
            }
        }

        # Get suggestions for the user's language
        lang_suggestions = suggestions_db.get(
            user_language, suggestions_db['en'])

        # Try to find relevant category based on query keywords
        query_lower = query.lower()
        matched_suggestions = []

        # Category keyword matching
        category_keywords = {
            'desserts': ['cake', 'pie', 'sweet', 'dessert', 'chocolate', 'торт', 'пирог', 'сладкое', 'עוגה', 'מתוק'],
            'pasta': ['pasta', 'spaghetti', 'noodle', 'паста', 'спагетти', 'лапша', 'פסטה', 'ספגטי'],
            'chicken': ['chicken', 'курица', 'עוף'],
            'soup': ['soup', 'суп', 'מרק'],
            'salad': ['salad', 'салат', 'סלט'],
            'breakfast': ['breakfast', 'egg', 'pancake', 'завтрак', 'яйцо', 'блин', 'ארוחת בוקר', 'ביצה']
        }

        # Find matching category
        for category, keywords in category_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                matched_suggestions.extend(lang_suggestions.get(category, []))
                break

        # If no category match, use popular recipes
        if not matched_suggestions:
            matched_suggestions = lang_suggestions.get('popular', [])

        # Return max 6 suggestions
        return matched_suggestions[:6]


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
