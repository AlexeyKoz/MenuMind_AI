"""
Test data factories for shopping app.

Uses factory_boy to generate realistic test data.
"""
import factory
from factory.django import DjangoModelFactory
from factory import fuzzy
from datetime import timedelta
from django.utils import timezone
from apps.shopping.models import (
    ShoppingList,
    ShoppingListCollaborator,
    ShoppingListOwnershipTransfer,
    ShoppingItem,
    Inventory,
    InventoryHistory
)
from apps.users.tests.factories import UserFactory


# ============================================================================
# SHOPPING LIST FACTORIES
# ============================================================================

class ShoppingListFactory(DjangoModelFactory):
    """Factory for creating ShoppingList instances."""
    
    class Meta:
        model = ShoppingList
    
    name = factory.Faker('sentence', nb_words=3)
    creator = factory.SubFactory(UserFactory)
    is_active = True
    is_collaborative = True
    last_activity = factory.LazyFunction(timezone.now)


class ArchivedShoppingListFactory(ShoppingListFactory):
    """Factory for archived shopping lists."""
    
    is_active = False
    deleted_at = factory.LazyFunction(timezone.now)
    deleted_by = factory.SubFactory(UserFactory)


class CompletedShoppingListFactory(ShoppingListFactory):
    """Factory for completed shopping lists."""
    
    is_active = False
    completed_at = factory.LazyFunction(timezone.now)


# ============================================================================
# SHOPPING LIST COLLABORATOR FACTORIES
# ============================================================================

class ShoppingListCollaboratorFactory(DjangoModelFactory):
    """Factory for ShoppingListCollaborator instances."""
    
    class Meta:
        model = ShoppingListCollaborator
    
    user = factory.SubFactory(UserFactory)
    shopping_list = factory.SubFactory(ShoppingListFactory)
    can_edit = True
    can_add_items = True
    can_invite_others = False
    items_added_count = 0


class ViewOnlyCollaboratorFactory(ShoppingListCollaboratorFactory):
    """Factory for view-only collaborators."""
    
    can_edit = False
    can_add_items = False
    can_invite_others = False


# ============================================================================
# OWNERSHIP TRANSFER FACTORIES
# ============================================================================

class ShoppingListOwnershipTransferFactory(DjangoModelFactory):
    """Factory for ShoppingListOwnershipTransfer instances."""
    
    class Meta:
        model = ShoppingListOwnershipTransfer
    
    shopping_list = factory.SubFactory(ShoppingListFactory)
    from_user = factory.SubFactory(UserFactory)
    to_user = factory.SubFactory(UserFactory)
    reason = 'manual_transfer'


# ============================================================================
# SHOPPING ITEM FACTORIES
# ============================================================================

class ShoppingItemFactory(DjangoModelFactory):
    """Factory for ShoppingItem instances."""
    
    class Meta:
        model = ShoppingItem
    
    shopping_list = factory.SubFactory(ShoppingListFactory)
    name = factory.Faker('word')
    quantity = factory.Faker('pydecimal', left_digits=2, right_digits=1, positive=True, min_value=1, max_value=10)
    unit = factory.Faker('random_element', elements=['kg', 'g', 'L', 'ml', 'pieces', 'pack', 'unit'])
    category = factory.Faker('random_element', elements=[
        'produce', 'dairy', 'meat', 'bakery', 'pantry', 'frozen', 'beverages'
    ])
    is_completed = False
    priority = 0
    added_by = factory.SubFactory(UserFactory)


class CompletedShoppingItemFactory(ShoppingItemFactory):
    """Factory for completed shopping items."""
    
    is_completed = True
    completed_at = factory.LazyFunction(timezone.now)
    completed_by = factory.SubFactory(UserFactory)


# ============================================================================
# INVENTORY FACTORIES
# ============================================================================

class InventoryFactory(DjangoModelFactory):
    """Factory for Inventory instances."""
    
    class Meta:
        model = Inventory
    
    user = factory.SubFactory(UserFactory)
    name = factory.Faker('word')
    quantity = factory.Faker('pydecimal', left_digits=2, right_digits=1, positive=True, min_value=1, max_value=10)
    unit = factory.Faker('random_element', elements=['kg', 'g', 'L', 'ml', 'pieces'])
    category = factory.Faker('random_element', elements=[
        'produce', 'dairy', 'meat', 'bakery', 'pantry', 'frozen', 'beverages'
    ])
    location = factory.Faker('random_element', elements=[
        'fridge', 'freezer', 'pantry', 'counter'
    ])
    expiration_date = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=7))
    purchase_date = factory.LazyFunction(lambda: timezone.now().date())


class ExpiringInventoryFactory(InventoryFactory):
    """Factory for expiring inventory items."""
    
    expiration_date = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=2))


class ExpiredInventoryFactory(InventoryFactory):
    """Factory for expired inventory items."""
    
    expiration_date = factory.LazyFunction(lambda: timezone.now().date() - timedelta(days=1))


class LowStockInventoryFactory(InventoryFactory):
    """Factory for low stock inventory items."""
    
    quantity = factory.Faker('pydecimal', left_digits=1, right_digits=1, positive=True, min_value=0.1, max_value=1)
    low_stock_threshold = factory.Faker('pydecimal', left_digits=1, right_digits=1, positive=True, min_value=2, max_value=5)


# ============================================================================
# INVENTORY HISTORY FACTORIES
# ============================================================================

class InventoryHistoryFactory(DjangoModelFactory):
    """Factory for InventoryHistory instances."""
    
    class Meta:
        model = InventoryHistory
    
    inventory_item = factory.SubFactory(InventoryFactory)
    action = 'added'
    quantity_change = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True, min_value=1, max_value=5)
    previous_quantity = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True, min_value=5, max_value=20)
    new_quantity = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True, min_value=6, max_value=25)
    notes = factory.Faker('sentence')

