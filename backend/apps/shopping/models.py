from django.db import models
from django.utils import timezone
from apps.users.models import User
import uuid


class ShoppingListCollaborator(models.Model):
    """Collaboration permissions for shopping lists"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shopping_list = models.ForeignKey(
        'ShoppingList', on_delete=models.CASCADE, related_name='collaborators')
    can_edit = models.BooleanField(default=True)
    can_add_items = models.BooleanField(default=True)
    can_invite_others = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    items_added_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ['user', 'shopping_list']
        db_table = 'shopping_list_collaborators'


class ShoppingListOwnershipTransfer(models.Model):
    """Track ownership transfers for shopping lists"""

    shopping_list = models.ForeignKey(
        'ShoppingList', on_delete=models.CASCADE, related_name='ownership_transfers')
    from_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transferred_from_lists')
    to_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='transferred_to_lists')
    reason = models.CharField(max_length=100, choices=[
        ('creator_deleted', 'Creator Deleted List'),
        ('auto_cleanup', 'Auto Cleanup After 60 Days'),
        ('manual_transfer', 'Manual Transfer')
    ], default='creator_deleted')
    transferred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shopping_list_ownership_transfers'
        ordering = ['-transferred_at']


class ShoppingList(models.Model):
    """Collaborative shopping list that can be shared between multiple users"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, default='Shopping List')
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='created_lists')
    participants = models.ManyToManyField(
        User, through='ShoppingListCollaborator', related_name='participating_lists')

    is_active = models.BooleanField(default=True)
    is_collaborative = models.BooleanField(default=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Archive/soft delete fields
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='deleted_lists'
    )
    # Permanent deletion by creator (but stays in DB for collaborator claims)
    permanently_deleted_at = models.DateTimeField(null=True, blank=True)
    permanently_deleted_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='permanently_deleted_lists'
    )

    # Auto-cleanup tracking fields
    deletion_warning_sent = models.BooleanField(default=False)
    deletion_warning_sent_at = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_user_permission(self, user):
        """Get collaboration permissions for a specific user"""
        if user == self.creator:
            return {
                'can_edit': True,
                'can_add_items': True,
                'can_invite_others': True,
                'is_creator': True
            }

        try:
            collaborator = self.collaborators.get(user=user)
            return {
                'can_edit': collaborator.can_edit,
                'can_add_items': collaborator.can_add_items,
                'can_invite_others': collaborator.can_invite_others,
                'is_creator': False
            }
        except ShoppingListCollaborator.DoesNotExist:
            return None

    def add_collaborator(self, user, can_edit=True, can_add_items=True, can_invite_others=False):
        """Add a new collaborator to the shopping list"""
        collaborator, created = ShoppingListCollaborator.objects.get_or_create(
            user=user,
            shopping_list=self,
            defaults={
                'can_edit': can_edit,
                'can_add_items': can_add_items,
                'can_invite_others': can_invite_others
            }
        )
        return collaborator, created

    def soft_delete(self, user):
        """Soft delete the shopping list (move to archive)"""
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.is_active = False
        self.save()

    def restore(self):
        """Restore the shopping list from archive"""
        self.deleted_at = None
        self.deleted_by = None
        self.is_active = True
        self.save()

    def permanent_delete_by_creator(self, user):
        """Mark list as permanently deleted by creator (but keep in DB for claims)"""
        self.permanently_deleted_at = timezone.now()
        self.permanently_deleted_by = user
        self.save()

    def can_user_restore(self, user):
        """Check if user can restore this list from archive"""
        # Can only restore if deleted but not permanently deleted, and user is creator or deleter
        return (self.deleted_at is not None and
                self.permanently_deleted_at is None and
                (user == self.creator or user == self.deleted_by))

    def is_permanently_deleted(self):
        """Check if list has been permanently deleted by creator"""
        return self.permanently_deleted_at is not None

    def is_archived_only(self):
        """Check if list is only archived (soft deleted) but not permanently deleted"""
        return self.deleted_at is not None and self.permanently_deleted_at is None

    def get_next_owner(self):
        """
        Determine the next owner based on participation criteria:
        1. Sort by joined_at (ascending) - oldest participant first
        2. Sort by items_added_count (descending) - most active participant
        3. Sort by username (ascending) - alphabetical as tiebreaker
        Returns the ShoppingListCollaborator object or None if no participants
        """
        try:
            # Get all current participants excluding the current creator
            participants = self.collaborators.exclude(user=self.creator).order_by(
                'joined_at',                    # Primary: oldest first
                '-items_added_count',           # Secondary: most active first
                'user__username'                # Tertiary: alphabetical
            )

            return participants.first()
        except Exception as e:
            print(f"Error in get_next_owner: {e}")
            # Fallback to simple ordering
            try:
                participants = self.collaborators.exclude(
                    user=self.creator).order_by('id')
                return participants.first()
            except Exception as e2:
                print(f"Error in fallback get_next_owner: {e2}")
                return None

    def transfer_ownership_to_next_participant(self, reason='creator_deleted'):
        """
        Automatically transfer ownership to the next eligible participant.
        Returns tuple (success: bool, new_owner: User|None, message: str)
        """
        next_owner_collaborator = self.get_next_owner()

        if not next_owner_collaborator:
            return False, None, "No participants available for ownership transfer"

        old_creator = self.creator
        new_owner = next_owner_collaborator.user

        # Record the transfer
        transfer_record = ShoppingListOwnershipTransfer.objects.create(
            shopping_list=self,
            from_user=old_creator,
            to_user=new_owner,
            reason=reason
        )

        # Transfer ownership
        self.creator = new_owner

        # Remove the new creator from participants to avoid duplication
        next_owner_collaborator.delete()

        # Remove the old creator from participants since they permanently deleted the list
        # They should not automatically get access when the new owner restores it
        try:
            old_creator_collaborator = self.collaborators.get(user=old_creator)
            old_creator_collaborator.delete()
            print(
                f"🗑️ Removed old creator {old_creator.username} from participants during ownership transfer")
        except ShoppingListCollaborator.DoesNotExist:
            print(
                f"🗑️ Old creator {old_creator.username} was not a participant - no removal needed")

        # Keep the list in archive for the new owner - they can restore it manually
        # Only clear the permanently_deleted fields to prevent permanent deletion
        if self.deleted_at and reason == 'creator_deleted':
            self.permanently_deleted_at = None
            self.permanently_deleted_by = None
            # Keep deleted_at, deleted_by, and is_active=False so list stays in archive

        self.save()

        return True, new_owner, f"Ownership transferred from {old_creator.username} to {new_owner.username}"

    def is_auto_delete_eligible(self):
        """Check if list should be auto-deleted (60 days after deletion)"""
        if not self.deleted_at:
            return False

        from datetime import timedelta
        auto_delete_date = self.deleted_at + timedelta(days=60)
        return timezone.now() >= auto_delete_date

    @property
    def days_until_auto_delete(self):
        """Get number of days until auto-deletion"""
        if not self.deleted_at:
            return None

        from datetime import timedelta
        auto_delete_date = self.deleted_at + timedelta(days=60)
        remaining = auto_delete_date - timezone.now()
        return max(0, remaining.days)

    class Meta:
        db_table = 'shopping_lists'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['creator', '-updated_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_collaborative']),
            models.Index(fields=['deleted_at']),
            models.Index(fields=['deleted_by']),
        ]


class ShoppingItem(models.Model):
    """Individual item in shopping list"""

    CATEGORIES = [
        ('produce', 'Produce'),
        ('dairy', 'Dairy'),
        ('meat', 'Meat & Fish'),
        ('bakery', 'Bakery'),
        ('frozen', 'Frozen'),
        ('pantry', 'Pantry'),
        ('beverages', 'Beverages'),
        ('snacks', 'Snacks'),
        ('household', 'Household'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shopping_list = models.ForeignKey(
        ShoppingList,
        on_delete=models.CASCADE,
        related_name='items'
    )

    name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit = models.CharField(max_length=20, default='unit')

    # Additional quantity measurements
    weight_quantity = models.DecimalField(
        max_digits=10, decimal_places=3, default=0,
        help_text='Weight quantity in grams (converted to user preference on display)'
    )
    liquid_quantity = models.DecimalField(
        max_digits=10, decimal_places=3, default=0,
        help_text='Liquid quantity in milliliters (converted to user preference on display)'
    )

    category = models.CharField(
        max_length=20, choices=CATEGORIES, default='other')

    is_completed = models.BooleanField(default=False)
    completed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='completed_items'
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    added_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='added_items')
    notes = models.TextField(blank=True)

    # AI-enhanced fields
    ai_suggested = models.BooleanField(default=False)
    nutrition_data = models.JSONField(default=dict, blank=True)
    estimated_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)

    # Collaboration fields
    # Store user's color when item was added
    user_color = models.CharField(max_length=7, blank=True)
    # For sorting (creator items on top)
    priority = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_recent(self):
        """Check if item was added recently (within last hour)"""
        from datetime import timedelta
        return timezone.now() - self.created_at < timedelta(hours=1)

    @property
    def display_color(self):
        """Get display color based on recency"""
        if self.user_color:
            if self.is_recent:
                return self.user_color  # Full color for recent items
            else:
                return self.user_color + '80'  # 50% opacity for older items
        return '#6B7280'  # Default gray

    def mark_completed(self, user):
        """Mark item as completed"""
        self.is_completed = True
        self.completed_by = user
        self.completed_at = timezone.now()
        self.save()

    class Meta:
        db_table = 'shopping_items'
        ordering = ['-priority', '-created_at', 'category', 'name']
        indexes = [
            models.Index(fields=['shopping_list', 'is_completed']),
            models.Index(fields=['category']),
            models.Index(fields=['added_by']),
            models.Index(fields=['priority', '-created_at']),
        ]


class Inventory(models.Model):
    """Track household inventory"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='inventory_items')

    name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default='unit')
    category = models.CharField(
        max_length=20,
        choices=ShoppingItem.CATEGORIES,
        default='other'
    )

    expiration_date = models.DateField(null=True, blank=True)
    location = models.CharField(
        max_length=20,
        choices=[
            ('fridge', 'Refrigerator'),
            ('freezer', 'Freezer'),
            ('pantry', 'Pantry'),
            ('counter', 'Counter'),
        ],
        default='pantry'
    )

    nutrition_data = models.JSONField(default=dict, blank=True)
    barcode = models.CharField(max_length=50, blank=True)

    low_stock_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1
    )
    auto_add_to_list = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_expired(self):
        if not self.expiration_date:
            return False
        return self.expiration_date < timezone.now().date()

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

    class Meta:
        db_table = 'inventory'
        ordering = ['expiration_date', 'name']
        indexes = [
            models.Index(fields=['user', 'expiration_date']),
            models.Index(fields=['category']),
            models.Index(fields=['barcode']),
        ]


class ShoppingEvent(models.Model):
    """Track shopping trips and purchases"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shopping_events')
    shopping_list = models.ForeignKey(
        ShoppingList,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    store_name = models.CharField(max_length=100)
    store_type = models.CharField(
        max_length=20,
        choices=[
            ('wolt', 'Wolt'),
            ('shufersal', 'Shufersal'),
            ('rami_levy', 'Rami Levy'),
            ('other', 'Other'),
        ]
    )

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='NIS')

    items_data = models.JSONField(default=list)
    receipt_image = models.ImageField(
        upload_to='receipts/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shopping_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['store_type']),
        ]
