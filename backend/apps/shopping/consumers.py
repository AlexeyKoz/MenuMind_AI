import json
import asyncio
import uuid
from decimal import Decimal
from datetime import datetime, date
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from .models import ShoppingList, ShoppingItem, ShoppingListCollaborator
from .serializers import ShoppingItemSerializer, ShoppingListSerializer


class UUIDEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle UUID, Decimal, and datetime objects"""

    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


User = get_user_model()


class ShoppingListConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time collaborative shopping lists"""

    # Class variable to track active connections per list
    active_connections = {}

    async def connect(self):
        self.list_id = self.scope['url_route']['kwargs']['list_id']
        self.room_group_name = f'shopping_list_{self.list_id}'
        self.user = None

        # Authenticate user from token
        await self.authenticate_user()

        if not self.user or self.user == AnonymousUser():
            print("❌ WebSocket connection rejected: No authenticated user")
            await self.close(code=4001)  # Unauthorized
            return

        # Check if user has access to this shopping list
        has_access = await self.check_list_access()
        if not has_access:
            print(
                f"❌ WebSocket connection rejected: User {self.user.username} has no access to list {self.list_id}")
            await self.close(code=4003)  # Forbidden
            return

        # Allow multiple connections but log them
        connection_key = f"{self.user.id}_{self.list_id}"
        if connection_key in self.active_connections:
            print(
                f"📝 Found existing connection for user {self.user.username} to list {self.list_id}, replacing it")
            # Don't close the existing connection forcefully, just replace the reference

        # Register this connection
        self.active_connections[connection_key] = self
        self.connection_key = connection_key
        print(
            f"🔗 Registered connection for user {self.user.username} to list {self.list_id}")

        # Join room group for this specific list
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Also join user-specific group for personal notifications
        user_group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(
            user_group_name,
            self.channel_name
        )
        print(
            f"👤 Added user {self.user.username} to personal group: {user_group_name}")

        await self.accept()

        print(
            f"🔗 WebSocket connected successfully for user: {self.user.username}")

        # Send current list state to the user
        try:
            print(f"📤 Sending initial data for list: {self.list_id}")
            await self.send_initial_data()
            print(f"✅ Initial data sent successfully")
        except Exception as e:
            print(f"❌ Error sending initial data: {e}")
            await self.close(code=4000)
            return

        # Notify other users that someone joined
        try:
            print(f"👋 Notifying other users that {self.user.username} joined")
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'user': {
                        'id': str(self.user.id),
                        'username': self.user.username,
                        'first_name': self.user.first_name,
                        'color': getattr(self.user, 'personal_color', '#4F46E5')
                    }
                }
            )
            print(f"✅ User join notification sent")
        except Exception as e:
            print(f"❌ Error sending user joined notification: {e}")
            await self.close(code=4000)
            return

    async def authenticate_user(self):
        """Authenticate user from JWT token in query parameters"""
        try:
            # Get token from query parameters
            query_string = self.scope['query_string'].decode('utf-8')
            token = None

            # Parse query parameters manually
            for param in query_string.split('&'):
                if param.startswith('token='):
                    token = param.split('=', 1)[1]
                    break

            if not token:
                self.user = AnonymousUser()
                return

            # Validate the token
            try:
                validated_token = UntypedToken(token)
                user_id = validated_token['user_id']
                self.user = await database_sync_to_async(User.objects.get)(id=user_id)
            except (InvalidToken, TokenError, User.DoesNotExist):
                self.user = AnonymousUser()

        except Exception:
            self.user = AnonymousUser()

    async def send_initial_data(self):
        """Send current list state to the newly connected user"""
        try:
            shopping_list = await database_sync_to_async(ShoppingList.objects.get)(id=self.list_id)
            items = await database_sync_to_async(lambda: list(shopping_list.items.all()))()
            collaborators = await database_sync_to_async(lambda: list(shopping_list.collaborators.all()))()

            # Serialize the data
            serialized_items = []
            for item in items:
                serialized_items.append({
                    'id': str(item.id),
                    'name': item.name,
                    'quantity': item.quantity,
                    'unit': item.unit or '',
                    'category': item.category or '',
                    'is_completed': item.is_completed,
                    'user_color': item.user_color or '',
                    'priority': item.priority,
                    'added_by_name': item.added_by.username if item.added_by else None,
                    'added_by_first_name': item.added_by.first_name if item.added_by else None,
                    'completed_by_name': item.completed_by.username if item.completed_by else None,
                    'created_at': item.created_at.isoformat() if item.created_at else None,
                    'is_recent': getattr(item, 'is_recent', False),
                    'display_color': getattr(item, 'display_color', item.user_color or ''),
                })

            await self.send(text_data=json.dumps({
                'type': 'initial_data',
                'data': {
                    'items': serialized_items,
                    'collaborators': [
                        {
                            'id': str(c.user.id),
                            'username': c.user.username or '',
                            'first_name': c.user.first_name or '',
                            'color': getattr(c.user, 'personal_color', '#4F46E5'),
                            'can_edit': c.can_edit,
                            'can_add_items': c.can_add_items,
                            'can_invite_others': c.can_invite_others,
                            'joined_at': c.joined_at.isoformat() if c.joined_at else None,
                        } for c in collaborators
                    ]
                }
            }, cls=UUIDEncoder))
        except Exception as e:
            await self.send_error(f"Failed to load initial data: {str(e)}")

    async def send_error(self, message):
        """Send error message to the user"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }, cls=UUIDEncoder))

    async def disconnect(self, close_code):
        print(
            f"🔌 WebSocket disconnecting - Code: {close_code}, User: {getattr(self.user, 'username', 'Unknown')}")

        # Clean up connection tracking
        if hasattr(self, 'connection_key') and self.connection_key in self.active_connections:
            if self.active_connections[self.connection_key] == self:
                del self.active_connections[self.connection_key]
                print(
                    f"🗑️ Removed connection tracking for {getattr(self.user, 'username', 'Unknown')}")

        if hasattr(self, 'room_group_name') and self.user:
            try:
                # Notify other users that someone left
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_left',
                        'user': {
                            'id': str(self.user.id),
                            'username': self.user.username
                        }
                    }
                )
                print(f"👋 Notified other users that {self.user.username} left")
            except Exception as e:
                print(f"❌ Error notifying users of disconnect: {e}")

            try:
                # Leave room group
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
                print(f"🚪 Left room group: {self.room_group_name}")

                # Leave user-specific group
                user_group_name = f'user_{self.user.id}'
                await self.channel_layer.group_discard(
                    user_group_name,
                    self.channel_name
                )
                print(f"🚪 Left personal group: {user_group_name}")
            except Exception as e:
                print(f"❌ Error leaving groups: {e}")

        print(
            f"✅ WebSocket disconnection complete for {getattr(self.user, 'username', 'Unknown')}")

    async def receive(self, text_data):
        # Debug log
        print(f"📨 WebSocket received message: {text_data[:200]}...")
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            print(f"📨 Parsed message type: {message_type}")  # Debug log

            if message_type == 'add_item':
                print(f"🔄 Processing add_item message")  # Debug log
                await self.handle_add_item(data)
            elif message_type == 'toggle_item':
                print(f"🔄 Processing toggle_item message")  # Debug log
                await self.handle_toggle_item(data)
            elif message_type == 'update_item':
                print(f"🔄 Processing update_item message")  # Debug log
                await self.handle_update_item(data)
            elif message_type == 'delete_item':
                print(f"🔄 Processing delete_item message")  # Debug log
                await self.handle_delete_item(data)
            elif message_type == 'add_collaborator':
                print(f"🔄 Processing add_collaborator message")  # Debug log
                await self.handle_add_collaborator(data)
            elif message_type == 'update_permissions':
                print(f"🔄 Processing update_permissions message")  # Debug log
                await self.handle_update_permissions(data)
            elif message_type == 'typing':
                print(f"🔄 Processing typing message")  # Debug log
                await self.handle_typing(data)
            elif message_type == 'quantity_type_changed':
                print(f"🔄 Processing quantity_type_changed message")  # Debug log
                await self.handle_quantity_type_changed(data)
            else:
                print(f"❌ Unknown message type: {message_type}")  # Debug log

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }, cls=UUIDEncoder))

    # Authentication and authorization methods
    async def authenticate_user(self):
        """Authenticate user from WebSocket headers"""
        try:
            # Get token from query string or headers
            query_string = self.scope.get('query_string', b'').decode()
            token = None

            print(f"🔍 WebSocket auth - Query string: {query_string}")

            if 'token=' in query_string:
                token = query_string.split('token=')[1].split('&')[0]
                print(f"🔑 Token found in query string: {token[:20]}...")

            if not token:
                # Try to get from headers
                headers = dict(self.scope.get('headers', []))
                auth_header = headers.get(b'authorization', b'').decode()
                print(f"🔍 Auth header: {auth_header}")
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    print(f"🔑 Token found in header: {token[:20]}...")

            if token:
                # Validate JWT token
                try:
                    UntypedToken(token)
                    self.user = await self.get_user_from_token(token)
                    print(
                        f"✅ Authentication successful for user: {self.user.username}")
                except Exception as e:
                    print(f"❌ Token validation failed: {e}")
                    self.user = AnonymousUser()
            else:
                print("❌ No token found in request")
                self.user = AnonymousUser()

        except (InvalidToken, TokenError) as e:
            print(f"❌ Authentication error: {e}")
            self.user = AnonymousUser()

    @database_sync_to_async
    def get_user_from_token(self, token):
        """Get user from JWT token"""
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id)
        except (User.DoesNotExist, KeyError):
            return AnonymousUser()

    @database_sync_to_async
    def check_list_access(self):
        """Check if user has access to the shopping list"""
        try:
            shopping_list = ShoppingList.objects.get(id=self.list_id)
            # Check if user is creator or collaborator
            if shopping_list.creator == self.user:
                return True
            return ShoppingListCollaborator.objects.filter(
                shopping_list=shopping_list,
                user=self.user
            ).exists()
        except ShoppingList.DoesNotExist:
            return False

    @database_sync_to_async
    def get_shopping_list_data(self):
        """Get shopping list with items and collaborators"""
        try:
            shopping_list = ShoppingList.objects.prefetch_related(
                'items', 'collaborators__user'
            ).get(id=self.list_id)

            # Serialize data
            list_serializer = ShoppingListSerializer(shopping_list)
            items_serializer = ShoppingItemSerializer(
                shopping_list.items.all(), many=True)

            return {
                'list': list_serializer.data,
                'items': items_serializer.data,
                'collaborators': [
                    {
                        'id': str(collab.user.id),
                        'username': collab.user.username,
                        'first_name': collab.user.first_name,
                        'color': getattr(collab.user, 'personal_color', '#4F46E5'),
                        'can_edit': collab.can_edit,
                        'can_add_items': collab.can_add_items,
                        'can_invite_others': collab.can_invite_others,
                        'is_creator': shopping_list.creator == collab.user
                    }
                    for collab in shopping_list.collaborators.all()
                ]
            }
        except ShoppingList.DoesNotExist:
            return None

    # Event handlers

    async def handle_add_item(self, data):
        """Handle adding new item to shopping list"""
        print(f"📦 handle_add_item called with data: {data}")
        print(
            f"📦 User: {self.user.username if hasattr(self.user, 'username') else 'Anonymous'}")
        print(f"📦 List ID: {self.list_id}")

        if not await self.check_add_permission():
            print(f"❌ Permission denied for user {self.user.username}")
            await self.send_error("You don't have permission to add items")
            return

        item_data = data.get('item', {})
        print(f"📦 Extracted item_data: {item_data}")
        item = await self.create_shopping_item(item_data)

        if item:
            print(
                f"✅ Item created successfully: {item.get('name', 'Unknown')} (ID: {item.get('id', 'Unknown')})")
            # Broadcast to all connected users
            print(f"📡 Broadcasting to group: {self.room_group_name}")
            # Ensure all UUIDs are converted to strings for channel serialization
            serialized_item = self._serialize_item_data(item)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'item_added',
                    'item': serialized_item,
                    'user': {
                        'id': str(self.user.id),
                        'username': self.user.username,
                        'color': getattr(self.user, 'personal_color', '#4F46E5')
                    }
                }
            )
            print(f"📡 Broadcast sent successfully")
        else:
            print(f"❌ Failed to create item")
            await self.send_error("Failed to create item")

    async def handle_toggle_item(self, data):
        """Handle toggling item completion status"""
        item_id = data.get('item_id')
        if not item_id:
            return

        item_data = await self.toggle_shopping_item(item_id)
        if item_data:
            # Ensure all UUIDs are converted to strings for channel serialization
            serialized_item = self._serialize_item_data(item_data)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'item_toggled',
                    'item': serialized_item,
                    'user': {
                        'id': str(self.user.id),
                        'username': self.user.username
                    }
                }
            )

    async def handle_add_collaborator(self, data):
        """Handle adding new collaborator to the list"""
        if not await self.check_invite_permission():
            await self.send_error("You don't have permission to invite collaborators")
            return

        collaborator_data = await self.add_list_collaborator(data)
        if collaborator_data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'collaborator_added',
                    'collaborator': collaborator_data,
                    'invited_by': {
                        'id': str(self.user.id),
                        'username': self.user.username
                    }
                }
            )

            # If key was regenerated, send notification to participant (not creator)
            if collaborator_data.get('key_regenerated'):
                # Send notification to the participant about their key change
                participant_id = collaborator_data.get('id')
                if participant_id:
                    await self.channel_layer.group_send(
                        f'user_{participant_id}',
                        {
                            'type': 'collaboration_key_regenerated',
                            'new_collaboration_key': collaborator_data['new_collaboration_key'],
                            'message': 'Your collaboration key has been automatically updated for security after being added to a list'
                        }
                    )

    async def handle_typing(self, data):
        """Handle typing indicator"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_typing',
                'user': {
                    'id': str(self.user.id),
                    'username': self.user.username
                },
                'is_typing': data.get('is_typing', False)
            }
        )

    async def handle_quantity_type_changed(self, data):
        """Handle quantity type change notification"""
        print(f"🔄 Handling quantity type change: {data}")
        # Broadcast the quantity type change to all connected users
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'quantity_type_changed',
                'item_id': data.get('item_id'),
                'item_name': data.get('item_name'),
                'quantity_type': data.get('quantity_type'),
                'changed_by': data.get('changed_by', self.user.username)
            }
        )

    async def handle_update_item(self, data):
        """Handle item update via WebSocket"""
        print(f"📦 Handling item update via WebSocket: {data}")
        try:
            item_data = data.get('item', {})
            item = await self.update_shopping_item(item_data)

            if item:
                print(f"✅ Item updated successfully: {item.name}")
                # Serialize the item using async-wrapped serializer
                serialized_item_data = await self.serialize_item(item)
                # Apply our serialization helper to handle UUIDs and Decimals
                safe_item_data = self._serialize_item_data(
                    serialized_item_data)

                # Broadcast to all connected users in this list
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'item_updated',
                        'item': safe_item_data,
                        'updated_by': {
                            'id': str(self.user.id),
                            'username': self.user.username
                        }
                    }
                )
            else:
                await self.send_error("Failed to update item")
        except Exception as e:
            print(f"❌ Error updating item: {e}")
            await self.send_error(f"Error updating item: {str(e)}")

    async def handle_delete_item(self, data):
        """Handle item deletion via WebSocket"""
        print(f"🗑️ Handling item deletion via WebSocket: {data}")
        try:
            item_id = data.get('item_id')
            success = await self.delete_shopping_item(item_id)

            if success:
                print(f"✅ Item deleted successfully: {item_id}")
                # Broadcast to all connected users in this list
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'item_deleted',
                        'item_id': item_id,
                        'deleted_by': {
                            'id': str(self.user.id),
                            'username': self.user.username
                        }
                    }
                )
            else:
                await self.send_error("Failed to delete item")
        except Exception as e:
            print(f"❌ Error deleting item: {e}")
            await self.send_error(f"Error deleting item: {str(e)}")

    async def handle_update_permissions(self, data):
        """Handle permission update via WebSocket"""
        print(f"🔧 Handling permission update via WebSocket: {data}")
        try:
            user_id = data.get('user_id')
            permissions = data.get('permissions', {})
            success = await self.update_collaborator_permissions(user_id, permissions)

            if success:
                print(
                    f"✅ Permissions updated successfully for user: {user_id}")
                # Broadcast to all connected users in this list
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'permissions_updated',
                        'user_id': user_id,
                        'permissions': permissions,
                        'updated_by': {
                            'id': str(self.user.id),
                            'username': self.user.username
                        }
                    }
                )
            else:
                await self.send_error("Failed to update permissions")
        except Exception as e:
            print(f"❌ Error updating permissions: {e}")
            await self.send_error(f"Error updating permissions: {str(e)}")

    # Database operations
    @database_sync_to_async
    def create_shopping_item(self, item_data):
        """Create new shopping item"""
        try:
            shopping_list = ShoppingList.objects.get(id=self.list_id)

            # Set priority based on user role (creator items get higher priority)
            priority = 1 if shopping_list.creator == self.user else 0

            item = ShoppingItem.objects.create(
                shopping_list=shopping_list,
                added_by=self.user,
                user_color=getattr(self.user, 'personal_color', '#4F46E5'),
                priority=priority,
                name=item_data.get('name', ''),
                quantity=item_data.get('quantity', 1),
                unit=item_data.get('unit', 'unit'),
                category=item_data.get('category', 'other'),
                notes=item_data.get('notes', '')
            )

            return ShoppingItemSerializer(item).data
        except Exception as e:
            print(f"Error creating item: {e}")
            return None

    @database_sync_to_async
    def toggle_shopping_item(self, item_id):
        """Toggle shopping item completion status"""
        try:
            item = ShoppingItem.objects.get(
                id=item_id,
                shopping_list_id=self.list_id
            )

            if item.is_completed:
                item.is_completed = False
                item.completed_by = None
                item.completed_at = None
            else:
                item.mark_completed(self.user)

            item.save()
            return ShoppingItemSerializer(item).data
        except ShoppingItem.DoesNotExist:
            return None

    @database_sync_to_async
    def update_shopping_item(self, item_data):
        """Update shopping item"""
        try:
            item_id = item_data.get('id')
            item = ShoppingItem.objects.get(
                id=item_id,
                shopping_list_id=self.list_id
            )

            # Update allowed fields
            if 'name' in item_data:
                item.name = item_data['name']
            if 'quantity' in item_data:
                item.quantity = item_data['quantity']
            if 'weight_quantity' in item_data:
                item.weight_quantity = item_data['weight_quantity']
            if 'liquid_quantity' in item_data:
                item.liquid_quantity = item_data['liquid_quantity']
            if 'unit' in item_data:
                item.unit = item_data['unit']
            if 'category' in item_data:
                item.category = item_data['category']
            if 'is_completed' in item_data:
                item.is_completed = item_data['is_completed']
                if item.is_completed:
                    item.mark_completed(self.user)
                else:
                    item.completed_by = None
                    item.completed_at = None

            item.save()
            return item
        except ShoppingItem.DoesNotExist:
            print(f"❌ Item not found: {item_data.get('id')}")
            return None
        except Exception as e:
            print(f"❌ Error updating item: {e}")
            return None

    @database_sync_to_async
    def delete_shopping_item(self, item_id):
        """Delete shopping item"""
        try:
            item = ShoppingItem.objects.get(
                id=item_id,
                shopping_list_id=self.list_id
            )
            item.delete()
            return True
        except ShoppingItem.DoesNotExist:
            print(f"❌ Item not found for deletion: {item_id}")
            return False
        except Exception as e:
            print(f"❌ Error deleting item: {e}")
            return False

    @database_sync_to_async
    def update_collaborator_permissions(self, user_id, permissions):
        """Update collaborator permissions"""
        try:
            collaborator = ShoppingListCollaborator.objects.get(
                shopping_list_id=self.list_id,
                user_id=user_id
            )

            # Update permissions
            if 'can_edit' in permissions:
                collaborator.can_edit = permissions['can_edit']
            if 'can_add_items' in permissions:
                collaborator.can_add_items = permissions['can_add_items']
            if 'can_invite_others' in permissions:
                collaborator.can_invite_others = permissions['can_invite_others']

            collaborator.save()
            return True
        except ShoppingListCollaborator.DoesNotExist:
            print(f"❌ Collaborator not found: {user_id}")
            return False
        except Exception as e:
            print(f"❌ Error updating permissions: {e}")
            return False

    @database_sync_to_async
    def add_list_collaborator(self, data):
        """Add collaborator to shopping list"""
        try:
            collaboration_key = data.get('collaboration_key')
            can_edit = data.get('can_edit', True)

            # Find user by collaboration key
            collaborator_user = User.objects.get(
                collaboration_key=collaboration_key)
            shopping_list = ShoppingList.objects.get(id=self.list_id)

            # Add collaborator
            collaborator, created = shopping_list.add_collaborator(
                user=collaborator_user,
                can_edit=can_edit,
                can_add_items=can_edit,
                can_invite_others=False
            )

            # ALWAYS regenerate key for the PARTICIPANT (not creator) when adding collaborator
            print(
                f"🔄 Always regenerating key for PARTICIPANT for security when adding collaborator")
            old_key = collaborator_user.collaboration_key
            new_key = collaborator_user.generate_collaboration_key()  # This now saves the model
            print(
                f"🔑 Auto-regenerated collaboration key for PARTICIPANT {collaborator_user.username}: {old_key} → {new_key}")

            if created:
                print(f"✅ New collaborator added via WebSocket")
                return {
                    'id': str(collaborator_user.id),
                    'username': collaborator_user.username,
                    'first_name': collaborator_user.first_name,
                    'color': getattr(collaborator_user, 'personal_color', '#4F46E5'),
                    'can_edit': collaborator.can_edit,
                    'can_add_items': collaborator.can_add_items,
                    'can_invite_others': collaborator.can_invite_others,
                    'new_collaboration_key': new_key,
                    'key_regenerated': True
                }
            else:
                print(f"✅ Existing collaborator - but key was regenerated")
                return {
                    'id': str(collaborator_user.id),
                    'username': collaborator_user.username,
                    'first_name': collaborator_user.first_name,
                    'color': getattr(collaborator_user, 'personal_color', '#4F46E5'),
                    'can_edit': collaborator.can_edit,
                    'can_add_items': collaborator.can_add_items,
                    'can_invite_others': collaborator.can_invite_others,
                    'new_collaboration_key': new_key,
                    'key_regenerated': True,
                    'already_existed': True
                }
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def check_add_permission(self):
        """Check if user can add items"""
        try:
            shopping_list = ShoppingList.objects.get(id=self.list_id)
            permissions = shopping_list.get_user_permission(self.user)
            return permissions and permissions['can_add_items']
        except ShoppingList.DoesNotExist:
            return False

    @database_sync_to_async
    def check_invite_permission(self):
        """Check if user can invite others"""
        try:
            shopping_list = ShoppingList.objects.get(id=self.list_id)
            permissions = shopping_list.get_user_permission(self.user)
            return permissions and permissions['can_invite_others']
        except ShoppingList.DoesNotExist:
            return False

    # WebSocket event methods
    async def item_added(self, event):
        """Send item_added event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'item_added',
            'item': event['item'],
            'user': event['user']
        }, cls=UUIDEncoder))

    async def item_toggled(self, event):
        """Send item_toggled event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'item_toggled',
            'item': event['item'],
            'user': event['user']
        }, cls=UUIDEncoder))

    async def item_updated(self, event):
        """Send item_updated event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'item_updated',
            'item': event['item'],
            'updated_by': event.get('updated_by', {})
        }, cls=UUIDEncoder))

    async def item_deleted(self, event):
        """Send item_deleted event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'item_deleted',
            'item_id': event['item_id'],
            'deleted_by': event.get('deleted_by', {})
        }, cls=UUIDEncoder))

    async def permissions_updated(self, event):
        """Send permissions_updated event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'permissions_updated',
            'user_id': event['user_id'],
            'permissions': event['permissions'],
            'updated_by': event.get('updated_by', {})
        }, cls=UUIDEncoder))

    async def collaborator_added(self, event):
        """Send collaborator_added event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'collaborator_added',
            'collaborator': event['collaborator'],
            'invited_by': event['invited_by']
        }, cls=UUIDEncoder))

    async def user_joined(self, event):
        """Send user_joined event to WebSocket"""
        # Don't send to the user who just joined
        if event['user']['id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user': event['user']
            }, cls=UUIDEncoder))

    async def user_left(self, event):
        """Send user_left event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user': event['user']
        }, cls=UUIDEncoder))

    async def user_typing(self, event):
        """Send typing indicator to other users"""
        # Don't send typing indicator back to the user who's typing
        if event['user']['id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'user_typing',
                'user': event['user'],
                'is_typing': event['is_typing']
            }, cls=UUIDEncoder))

    async def list_deleted(self, event):
        """Send list deletion notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'list_deleted',
            'list_id': event['list_id'],
            'list_name': event['list_name'],
            'deleted_by': event['deleted_by'],
            'message': event['message']
        }, cls=UUIDEncoder))

    async def participant_left(self, event):
        """Send participant left notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'participant_left',
            'list_id': event['list_id'],
            'list_name': event['list_name'],
            'participant': event['participant'],
            'message': event['message']
        }, cls=UUIDEncoder))

    async def list_access_granted(self, event):
        """Send list access granted notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'list_access_granted',
            'list': event['list'],
            'invited_by': event['invited_by'],
            'message': event['message']
        }, cls=UUIDEncoder))

    async def quantity_type_changed(self, event):
        """Send quantity_type_changed event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'quantity_type_changed',
            'item_id': event['item_id'],
            'item_name': event['item_name'],
            'quantity_type': event['quantity_type'],
            'changed_by': event['changed_by']
        }, cls=UUIDEncoder))

    @database_sync_to_async
    def serialize_item(self, item):
        """Serialize item using Django serializer in async context"""
        from apps.shopping.serializers import ShoppingItemSerializer
        return ShoppingItemSerializer(item).data

    def _serialize_item_data(self, item_data):
        """Convert all UUID and Decimal objects to serializable types for channel serialization"""
        if isinstance(item_data, dict):
            serialized = {}
            for key, value in item_data.items():
                if isinstance(value, uuid.UUID):
                    serialized[key] = str(value)
                elif isinstance(value, Decimal):
                    serialized[key] = float(value)
                elif isinstance(value, (datetime, date)):
                    serialized[key] = value.isoformat()
                elif isinstance(value, dict):
                    serialized[key] = self._serialize_item_data(value)
                elif isinstance(value, list):
                    serialized[key] = [self._serialize_item_data(item) if isinstance(item, (dict, uuid.UUID, Decimal)) else str(
                        item) if isinstance(item, uuid.UUID) else float(item) if isinstance(item, Decimal) else item for item in value]
                else:
                    serialized[key] = value
            return serialized
        elif isinstance(item_data, uuid.UUID):
            return str(item_data)
        elif isinstance(item_data, Decimal):
            return float(item_data)
        elif isinstance(item_data, (datetime, date)):
            return item_data.isoformat()
        else:
            return item_data

    async def send_error(self, message):
        """Send error message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }, cls=UUIDEncoder))
