from rest_framework import serializers
from .models import ShoppingList, ShoppingItem, ShoppingListCollaborator, Inventory, InventoryHistory, ShoppingEvent
from apps.users.serializers import UserSerializer


class ShoppingListCollaboratorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ShoppingListCollaborator
        fields = [
            'user', 'can_edit', 'can_add_items',
            'can_invite_others', 'joined_at'
        ]


class ShoppingItemSerializer(serializers.ModelSerializer):
    added_by_name = serializers.CharField(
        source='added_by.username', read_only=True)
    added_by_first_name = serializers.CharField(
        source='added_by.first_name', read_only=True)
    completed_by_name = serializers.CharField(
        source='completed_by.username', read_only=True)
    display_color = serializers.CharField(read_only=True)
    is_recent = serializers.BooleanField(read_only=True)
    auto_enable_counter = serializers.SerializerMethodField()

    class Meta:
        model = ShoppingItem
        fields = [
            'id', 'name', 'quantity', 'unit', 'weight_quantity', 'liquid_quantity',
            'category', 'notes', 'is_completed', 'completed_by', 'completed_by_name',
            'completed_at', 'added_by', 'added_by_name', 'added_by_first_name',
            'ai_suggested', 'nutrition_data', 'estimated_price',
            'user_color', 'priority', 'display_color', 'is_recent',
            'created_at', 'updated_at', 'auto_enable_counter'
        ]
        read_only_fields = ['id', 'added_by', 'user_color',
                            'priority', 'created_at', 'updated_at']

    def get_auto_enable_counter(self, obj):
        """Get auto-enable counter flag if it exists"""
        return getattr(obj, '_auto_enable_counter', None)


class ShoppingListSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    collaborators = ShoppingListCollaboratorSerializer(
        many=True, read_only=True)
    items = ShoppingItemSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(
        source='items.count', read_only=True)
    completed_items_count = serializers.SerializerMethodField()
    user_permissions = serializers.SerializerMethodField()

    class Meta:
        model = ShoppingList
        fields = [
            'id', 'name', 'creator', 'is_active', 'is_collaborative',
            'completed_at', 'created_at', 'updated_at',
            'collaborators', 'items', 'items_count', 'completed_items_count',
            'user_permissions'
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']

    def get_completed_items_count(self, obj):
        """Get count of completed items"""
        return obj.items.filter(is_completed=True).count()

    def get_user_permissions(self, obj):
        """Get current user's permissions for this list"""
        request = self.context.get('request')
        if request and request.user:
            return obj.get_user_permission(request.user)
        return None


class CreateShoppingListSerializer(serializers.ModelSerializer):
    """Serializer for creating new shopping lists"""

    class Meta:
        model = ShoppingList
        fields = ['id', 'name', 'is_collaborative', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['creator'] = request.user
        return super().create(validated_data)


class AddCollaboratorSerializer(serializers.Serializer):
    """Serializer for adding collaborators to shopping lists"""
    collaboration_key = serializers.CharField(max_length=6)
    friend_name = serializers.CharField(max_length=100, required=False)
    can_edit = serializers.BooleanField(default=True)
    can_add_items = serializers.BooleanField(default=True)
    can_invite_others = serializers.BooleanField(default=False)

    def validate_collaboration_key(self, value):
        """Validate that the collaboration key format is correct"""
        # Only validate format, not existence - let the view handle user lookup for better error messages
        if not value or len(value) != 6:
            raise serializers.ValidationError(
                "Collaboration key must be exactly 6 characters")
        return value


class UpdateCollaboratorPermissionsSerializer(serializers.Serializer):
    """Serializer for updating collaborator permissions"""
    user_id = serializers.UUIDField()
    can_edit = serializers.BooleanField(required=False)
    can_add_items = serializers.BooleanField(required=False)
    can_invite_others = serializers.BooleanField(required=False)


class InventorySerializer(serializers.ModelSerializer):
    """Enhanced inventory serializer with expiry status"""
    is_expired = serializers.BooleanField(read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    expiry_status = serializers.CharField(read_only=True)
    shopping_list_name = serializers.CharField(
        source='shopping_list.name', read_only=True)

    class Meta:
        model = Inventory
        fields = [
            'id', 'name', 'quantity', 'unit', 'category',
            'expiration_date', 'purchase_date', 'location',
            'nutrition_data', 'barcode', 'low_stock_threshold',
            'auto_add_to_list', 'notes',
            'shopping_list', 'shopping_list_name',
            'is_expired', 'is_expiring_soon', 'is_low_stock', 'expiry_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user',
                            'purchase_date', 'created_at', 'updated_at']


class InventoryHistorySerializer(serializers.ModelSerializer):
    """Serializer for inventory history tracking"""
    inventory_name = serializers.CharField(
        source='inventory_item.name', read_only=True)
    recipe_name = serializers.CharField(source='recipe.name', read_only=True)

    class Meta:
        model = InventoryHistory
        fields = [
            'id', 'inventory_item', 'inventory_name',
            'action', 'quantity_change',
            'previous_quantity', 'new_quantity',
            'recipe', 'recipe_name', 'notes', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class AICategorizationSuggestionSerializer(serializers.Serializer):
    """Serializer for AI categorization suggestions"""
    item_id = serializers.UUIDField()
    name = serializers.CharField()
    suggested_location = serializers.ChoiceField(
        choices=['fridge', 'freezer', 'pantry', 'counter'])
    suggested_category = serializers.CharField()
    suggested_expiration_days = serializers.IntegerField()
    suggested_quantity = serializers.DecimalField(
        max_digits=10, decimal_places=2)
    suggested_unit = serializers.CharField()
    confidence = serializers.FloatField()


class BulkInventoryCreateSerializer(serializers.Serializer):
    """Serializer for bulk inventory creation from shopping list"""
    items = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of items to create in inventory"
    )

    def validate_items(self, value):
        """Validate each item has required fields"""
        required_fields = ['name', 'quantity', 'unit', 'location', 'category']
        for item in value:
            for field in required_fields:
                if field not in item:
                    raise serializers.ValidationError(
                        f"Missing required field '{field}' in item"
                    )
        return value


class InventoryConsumeSerializer(serializers.Serializer):
    """Serializer for consuming inventory items (e.g., cooking)"""
    items = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of items to consume"
    )
    recipe_id = serializers.UUIDField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_items(self, value):
        """Validate each item has required fields"""
        for item in value:
            if 'inventory_id' not in item:
                raise serializers.ValidationError(
                    "Missing 'inventory_id' in item")
            if 'quantity_used' not in item:
                raise serializers.ValidationError(
                    "Missing 'quantity_used' in item")
        return value


class RecipeFromInventorySerializer(serializers.Serializer):
    """Serializer for AI-generated recipe suggestions from inventory"""
    name = serializers.CharField()
    priority = serializers.ChoiceField(choices=['urgent', 'high', 'normal'])
    ingredients_from_inventory = serializers.ListField(
        child=serializers.DictField())
    missing_ingredients = serializers.ListField(child=serializers.CharField())
    nutrition = serializers.DictField()
    difficulty = serializers.ChoiceField(
        choices=['easy', 'intermediate', 'advanced'])
    cooking_time = serializers.CharField()
    reasoning = serializers.CharField()


class ShoppingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingEvent
        fields = [
            'id', 'store_name', 'store_type', 'total_amount',
            'currency', 'items_data', 'receipt_image', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']
