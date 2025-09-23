from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from asgiref.sync import async_to_sync
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


class ShoppingListViewSet(viewsets.ModelViewSet):
    """Shopping list management with real-time sync"""
    serializer_class = ShoppingListSerializer
    permission_classes = [IsAuthenticated]

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

            # Check if user is creator or collaborator (simplified permission check)
            is_creator = shopping_list.creator == request.user
            is_collaborator = hasattr(shopping_list, 'collaborators') and shopping_list.collaborators.filter(
                user=request.user).exists()

            if not (is_creator or is_collaborator):
                print(f"❌ Permission denied for user {request.user.username}")
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

    @action(detail=True, methods=['post'])
    def ai_add_items(self, request, pk=None):
        """Add items using natural language"""
        shopping_list = self.get_object()
        text = request.data.get('text', '')

        # Process with AI
        orchestrator = AIOrchestrator()
        context = {
            'inventory': list(Inventory.objects.filter(
                user=request.user
            ).values('name', 'quantity')),
            'preferences': {
                'dietary_restrictions': request.user.dietary_restrictions,
                'allergies': request.user.allergies
            }
        }

        # Use sync version for now
        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            orchestrator.process_natural_language(text, context)
        )

        if result['success'] and result.get('action') == 'add_items':
            items_created = []
            for item_data in result['items']:
                item_data['shopping_list'] = shopping_list.id
                item_data['added_by'] = request.user.id
                item_data['ai_suggested'] = True

                serializer = ShoppingItemSerializer(data=item_data)
                if serializer.is_valid():
                    item = serializer.save()
                    items_created.append(item)

            # Send WebSocket notification for batch add
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f'shopping_list_{shopping_list.id}',
                    {
                        'type': 'items_batch_added',
                        'items': [ShoppingItemSerializer(i).data for i in items_created],
                        'user': request.user.username
                    }
                )

            return Response({
                'success': True,
                'items_added': len(items_created),
                'items': [ShoppingItemSerializer(i).data for i in items_created]
            })

        return Response({
            'success': False,
            'message': result.get('message', 'Failed to process request')
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def mock_store_order(self, request):
        """Simulate store order"""
        store_type = request.data.get('store_type', 'wolt')
        items = request.data.get('items', [])

        from config.external_services import MockStoreServices
        services = MockStoreServices()

        import asyncio
        loop = asyncio.new_event_loop()

        if store_type == 'wolt':
            result = loop.run_until_complete(
                services.wolt_order_simulation(items)
            )
        elif store_type == 'shufersal':
            item_names = [item['name'] for item in items]
            result = loop.run_until_complete(
                services.shufersal_price_check(item_names)
            )
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

            if created:
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
                    print(
                        f"📡 WebSocket notifications sent for new collaborator: {collaborator_user.username} to list: {shopping_list.name}")

                return Response({
                    'success': True,
                    'message': f'Successfully added {collaborator_user.username} as collaborator',
                    'collaborator': {
                        'id': str(collaborator_user.id),
                        'username': collaborator_user.username,
                        'first_name': collaborator_user.first_name,
                        'color': collaborator_user.personal_color
                    }
                })
            else:
                return Response(
                    {'error': 'User is already a collaborator'},
                    status=status.HTTP_400_BAD_REQUEST
                )

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
        """Soft delete the shopping list (move to archive)"""
        shopping_list = self.get_object()

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
        shopping_list.soft_delete(request.user)

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

        return Response({
            'message': f'List "{list_name}" moved to archive',
            'deleted_at': shopping_list.deleted_at
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def archived(self, request):
        """Get archived (deleted) lists for the user"""
        archived_lists = ShoppingList.objects.filter(
            Q(creator=request.user) | Q(participants=request.user),
            deleted_at__isnull=False
        ).distinct().prefetch_related('collaborators__user', 'items')

        archived_data = []
        for shopping_list in archived_lists:
            archived_data.append({
                'id': str(shopping_list.id),
                'name': shopping_list.name,
                'deleted_at': shopping_list.deleted_at,
                'items_count': shopping_list.items.count(),
                'creator': {
                    'username': shopping_list.creator.username,
                    'first_name': shopping_list.creator.first_name,
                },
                'can_restore': shopping_list.can_user_restore(request.user),
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
        """Permanently delete a list from archive or remove user from archived list"""
        try:
            # Get archived list
            shopping_list = ShoppingList.objects.get(
                id=pk,
                deleted_at__isnull=False
            )

            list_name = shopping_list.name

            # If user is the creator, permanently delete the entire list
            if shopping_list.creator == request.user:
                shopping_list.delete()  # This will permanently delete
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

    def update(self, request, *args, **kwargs):
        """Update shopping item (including quantity)"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()

            print(f"🔄 Updating item: {instance.name} (partial={partial})")
            print(f"📝 Update data: {request.data}")
            print(f"🔍 Request method: {request.method}")

            # Check permissions
            user_lists = ShoppingList.objects.filter(
                Q(creator=request.user) | Q(participants=request.user)
            )
            if instance.shopping_list not in user_lists:
                return Response(
                    {'error': 'You do not have permission to update this item'},
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
            print(
                f"🔄 Toggling completion for item: {item.name} by user: {request.user.username}")

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

            # Check permissions
            user_lists = ShoppingList.objects.filter(
                Q(creator=request.user) | Q(participants=request.user)
            )
            if item.shopping_list not in user_lists:
                return Response(
                    {'error': 'You do not have permission to update this item'},
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

            # Check permissions
            user_lists = ShoppingList.objects.filter(
                Q(creator=request.user) | Q(participants=request.user)
            )
            if item.shopping_list not in user_lists:
                return Response(
                    {'error': 'You do not have permission to update this item'},
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
