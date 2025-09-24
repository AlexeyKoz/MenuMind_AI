import json
import uuid
import decimal
import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from django.conf import settings
import jwt

User = get_user_model()


class UUIDEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle UUID, Decimal, and datetime objects"""

    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        return super().default(obj)


class UserNotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for user-level notifications (not tied to specific lists)"""

    async def connect(self):
        """Handle WebSocket connection for user notifications"""
        print("🔗 User notification WebSocket connecting...")

        # Authenticate user from token
        await self.authenticate_user()

        if not self.user or self.user == AnonymousUser():
            print("❌ User notification WebSocket rejected: No authenticated user")
            await self.close(code=4001)  # Unauthorized
            return

        # Join user-specific group for personal notifications
        self.user_group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        await self.accept()
        print(
            f"✅ User notification WebSocket connected for user: {self.user.username}")
        print(
            f"👤 Added user {self.user.username} to personal notification group: {self.user_group_name}")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
            print(
                f"🚪 User {getattr(self.user, 'username', 'Unknown')} left personal notification group: {self.user_group_name}")

    async def authenticate_user(self):
        """Authenticate user from WebSocket token"""
        try:
            # Get token from query string
            query_string = self.scope['query_string'].decode()
            print(
                f"🔍 User notification WebSocket auth - Query string: {query_string}")

            # Parse token from query string
            token = None
            if query_string:
                for param in query_string.split('&'):
                    if param.startswith('token='):
                        token = param.split('=')[1]
                        break

            if not token:
                print("❌ No token found in user notification WebSocket query string")
                self.user = AnonymousUser()
                return

            print(
                f"🔑 Token found in user notification WebSocket: {token[:20]}...")

            # Decode and validate token
            try:
                UntypedToken(token)
                decoded_data = jwt.decode(
                    token, settings.SECRET_KEY, algorithms=["HS256"])
                user_id = decoded_data['user_id']

                # Get user from database
                self.user = await database_sync_to_async(User.objects.get)(id=user_id)
                print(
                    f"✅ User notification authentication successful for user: {self.user.username}")

            except (InvalidToken, TokenError, User.DoesNotExist) as e:
                print(f"❌ User notification authentication failed: {e}")
                self.user = AnonymousUser()

        except Exception as e:
            print(f"❌ Error during user notification authentication: {e}")
            self.user = AnonymousUser()

    async def receive(self, text_data):
        """Handle incoming WebSocket messages (for heartbeat/ping)"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', '')

            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.datetime.now().isoformat()
                }, cls=UUIDEncoder))

        except Exception as e:
            print(f"⚠️ Error handling user notification message: {e}")

    async def list_access_granted(self, event):
        """Send list access granted notification to WebSocket"""
        print(
            f"📡 Sending list_access_granted notification to user {self.user.username}")
        await self.send(text_data=json.dumps({
            'type': 'list_access_granted',
            'list': event['list'],
            'invited_by': event['invited_by'],
            'message': event['message']
        }, cls=UUIDEncoder))

    async def participant_left(self, event):
        """Send participant left notification to WebSocket"""
        print(
            f"📡 Sending participant_left notification to user {self.user.username}")
        await self.send(text_data=json.dumps({
            'type': 'participant_left',
            'list_id': event['list_id'],
            'list_name': event['list_name'],
            'participant': event['participant'],
            'message': event['message']
        }, cls=UUIDEncoder))

    async def list_permanently_deleted(self, event):
        """Send list permanently deleted notification to WebSocket"""
        print(
            f"📡 Sending list_permanently_deleted notification to user {self.user.username}")
        await self.send(text_data=json.dumps({
            'type': 'list_permanently_deleted',
            'list_id': event['list_id'],
            'list_name': event['list_name'],
            'permanently_deleted_by': event['permanently_deleted_by'],
            'message': event['message']
        }, cls=UUIDEncoder))

    async def ownership_transferred(self, event):
        """Send ownership transferred notification to WebSocket"""
        print(
            f"📡 Sending ownership_transferred notification to user {self.user.username}")
        await self.send(text_data=json.dumps({
            'type': 'ownership_transferred',
            'list': event['list'],
            'new_owner': event['new_owner'],
            'previous_owner': event['previous_owner'],
            'message': event['message']
        }, cls=UUIDEncoder))

    async def deletion_warning(self, event):
        """Send deletion warning notification to WebSocket"""
        print(
            f"📡 Sending deletion_warning notification to user {self.user.username}")
        await self.send(text_data=json.dumps({
            'type': 'deletion_warning',
            'list': event['list'],
            'message': event['message'],
            'days_remaining': event['days_remaining']
        }, cls=UUIDEncoder))

    async def collaborator_joined(self, event):
        """Send collaborator joined notification to WebSocket"""
        print(
            f"📡 Sending collaborator_joined notification to user {self.user.username}")
        await self.send(text_data=json.dumps({
            'type': 'collaborator_joined',
            'list': event['list'],
            'collaborator': event['collaborator'],
            'invited_by': event['invited_by'],
            'message': event['message']
        }, cls=UUIDEncoder))

    async def collaboration_key_regenerated(self, event):
        """Send collaboration key regenerated notification to WebSocket"""
        print(
            f"📡 Sending collaboration_key_regenerated notification to user {self.user.username}")
        await self.send(text_data=json.dumps({
            'type': 'collaboration_key_regenerated',
            'new_collaboration_key': event['new_collaboration_key'],
            'message': event['message']
        }, cls=UUIDEncoder))
