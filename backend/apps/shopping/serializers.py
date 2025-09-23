from rest_framework import serializers
from .models import ShoppingList, ShoppingItem, ShoppingListCollaborator, Inventory, ShoppingEvent
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

    class Meta:
        model = ShoppingItem
        fields = [
            'id', 'name', 'quantity', 'unit', 'weight_quantity', 'liquid_quantity',
            'category', 'notes', 'is_completed', 'completed_by', 'completed_by_name',
            'completed_at', 'added_by', 'added_by_name', 'added_by_first_name',
            'ai_suggested', 'nutrition_data', 'estimated_price',
            'user_color', 'priority', 'display_color', 'is_recent',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'added_by', 'user_color',
                            'priority', 'created_at', 'updated_at']


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
        fields = ['name', 'is_collaborative']

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
    is_expired = serializers.BooleanField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Inventory
        fields = [
            'id', 'name', 'quantity', 'unit', 'category',
            'expiration_date', 'location', 'nutrition_data',
            'barcode', 'low_stock_threshold', 'auto_add_to_list',
            'is_expired', 'is_low_stock', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ShoppingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingEvent
        fields = [
            'id', 'store_name', 'store_type', 'total_amount',
            'currency', 'items_data', 'receipt_image', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']
