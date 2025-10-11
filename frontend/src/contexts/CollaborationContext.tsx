import React, { createContext, useContext, useState, useEffect, useRef, useCallback, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import WebSocketService from '../services/websocket';
import ApiService from '../services/api';
import { userNotificationWS } from '../services/userWebSocket';
import { toast } from 'react-hot-toast';
import { getUserFriendlyError } from '../utils/errorHandler';

// Simplified connection tracking
const connectionTracker = {
    currentListId: null as string | null,
    isConnecting: false
};

interface Collaborator {
    id: string;
    username: string;
    first_name: string;
    color: string;
    can_edit: boolean;
    can_add_items: boolean;
    can_invite_others: boolean;
    is_creator: boolean;
    joined_at: string;
}

interface TypingUser {
    id: string;
    username: string;
}

interface CollaborationContextType {
    // Connection state
    isConnected: boolean;
    connectionState: string;

    // Collaboration data
    collaborators: Collaborator[];
    typingUsers: TypingUser[];
    myCollaborationKey: string | null;
    wsConnectionId: number;

    // Actions
    connectToList: (listId: string) => Promise<void>;
    disconnect: () => void;
    addCollaborator: (friendName: string, collaborationKey: string, canEdit: boolean) => Promise<boolean>;
    updatePermissions: (userId: string, permissions: any) => Promise<boolean>;
    loadCollaborators: (listId: string) => Promise<void>;
    loadMyCollaborationKey: () => Promise<void>;
    generateNewCollaborationKey: () => Promise<void>;

    // Event handlers
    onItemAdded: (callback: (data: any) => void) => (() => void);
    onItemToggled: (callback: (data: any) => void) => (() => void);
    onItemUpdated: (callback: (data: any) => void) => (() => void);
    onItemDeleted: (callback: (data: any) => void) => (() => void);
    onItemsBatchAdded: (callback: (data: any) => void) => (() => void);
    onQuantityTypeChanged: (callback: (data: any) => void) => (() => void);
    onCollaboratorAdded: (callback: (data: any) => void) => void;
    onUserJoined: (callback: (data: any) => void) => void;
    onUserLeft: (callback: (data: any) => void) => void;
    onListDeleted: (callback: (data: any) => void) => (() => void);
    onListAccessGranted: (callback: (data: any) => void) => (() => void);
    sendTyping: (isTyping: boolean) => void;
    sendCustomMessage: (messageData: any) => void;
}

const CollaborationContext = createContext<CollaborationContextType | undefined>(undefined);

export const useCollaboration = () => {
    const context = useContext(CollaborationContext);
    if (!context) {
        throw new Error('useCollaboration must be used within CollaborationProvider');
    }
    return context;
};

interface CollaborationProviderProps {
    children: ReactNode;
}

export const CollaborationProvider: React.FC<CollaborationProviderProps> = ({ children }) => {
    const { token } = useAuth();
    const [isConnected, setIsConnected] = useState(false);
    const [connectionState, setConnectionState] = useState('DISCONNECTED');
    const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
    const [typingUsers, setTypingUsers] = useState<TypingUser[]>([]);
    const [myCollaborationKey, setMyCollaborationKey] = useState<string | null>(null);
    const [wsConnectionId, setWsConnectionId] = useState<number>(0); // Track WS connection changes

    const wsService = useRef<WebSocketService | null>(null);
    const api = useRef(new ApiService(token));
    const currentListId = useRef<string | null>(null);
    const connectionInProgress = useRef<boolean>(false);
    const listenersSetupRef = useRef<boolean>(false); // Track if listeners are already set up

    // Update API service when token changes
    useEffect(() => {
        api.current = new ApiService(token);
    }, [token]);

    // Helper functions (declared first to avoid dependency issues)
    const loadCollaborators = useCallback(async (listId: string): Promise<void> => {
        try {
            const response = await api.current.getCollaborators(listId);
            setCollaborators(response.collaborators || []);
        } catch (error) {
            console.error('❌ Failed to load collaborators:', error);
        }
    }, []); // Empty dependency array - function doesn't depend on external variables

    // Connect to user notification WebSocket when token is available
    useEffect(() => {
        if (token && !listenersSetupRef.current) {
            console.log('🔌 Connecting to user notification WebSocket...');

            // Clear all existing listeners first to prevent duplicates
            userNotificationWS.removeAllListeners();

            userNotificationWS.connect(token)
                .then(() => {
                    console.log('✅ User notification WebSocket connected');
                    console.log('✅ Setting up collaboration_key_regenerated listener...');
                    userNotificationWS.startHeartbeat();

                    // Mark that listeners have been set up
                    listenersSetupRef.current = true;

                    // Set up listeners for user-level notifications
                    userNotificationWS.on('list_access_granted', (data: any) => {
                        console.log('🎉 User notification: List access granted:', data);
                        toast.success(`You have been added to "${data.list.name}" by ${data.invited_by.username}`);

                        // Trigger a custom event that ShoppingList component can listen to
                        window.dispatchEvent(new CustomEvent('listsChanged', {
                            detail: { type: 'access_granted', data }
                        }));
                    });

                    userNotificationWS.on('participant_left', (data: any) => {
                        console.log('👋 User notification: Participant left:', data);
                        toast(`${data.participant.username} has left "${data.list_name}"`);

                        // Trigger lists refresh if current user is viewing this list
                        window.dispatchEvent(new CustomEvent('listsChanged', {
                            detail: { type: 'participant_left', data }
                        }));
                    });


                    userNotificationWS.on('list_permanently_deleted', (data: any) => {
                        console.log('🗑️ User notification: List permanently deleted:', data);
                        toast(`${data.permanently_deleted_by.username} permanently deleted "${data.list_name}".`);

                        // Trigger archive refresh 
                        window.dispatchEvent(new CustomEvent('listsChanged', {
                            detail: { type: 'list_permanently_deleted', data }
                        }));
                    });

                    userNotificationWS.on('ownership_transferred', (data: any) => {
                        console.log('👑 User notification: Ownership transferred:', data);
                        toast.success(data.message);

                        // Trigger lists refresh as ownership has changed
                        window.dispatchEvent(new CustomEvent('listsChanged', {
                            detail: { type: 'ownership_transferred', data }
                        }));
                    });

                    userNotificationWS.on('deletion_warning', (data: any) => {
                        console.log('⚠️ User notification: Deletion warning:', data);
                        toast(`⚠️ ${data.message}`, {
                            duration: 10000,
                            style: {
                                background: '#fef3c7',
                                color: '#92400e',
                                border: '1px solid #fcd34d'
                            }
                        });
                    });

                    userNotificationWS.on('collaborator_joined', (data: any) => {
                        console.log('👥 User notification: Collaborator joined:', data);
                        toast(`${data.collaborator.username} was added to "${data.list.name}"`);

                        // If this is about the current list, reload collaborators
                        if (currentListId.current === data.list.id) {
                            loadCollaborators(data.list.id);
                        }
                    });

                    userNotificationWS.on('collaboration_key_regenerated', (data: any) => {
                        console.log('🔑 *** COLLABORATION KEY REGENERATED NOTIFICATION RECEIVED ***');
                        console.log('🔑 User notification: Collaboration key regenerated:', data);
                        console.log('🔑 Old key in state:', myCollaborationKey);
                        console.log('🔑 New key from notification:', data.new_collaboration_key);

                        // Update the collaboration key in state
                        setMyCollaborationKey(data.new_collaboration_key);
                        console.log('🔑 Key state updated successfully');

                        // Show notification to the user
                        toast.success(`${data.message}`, {
                            duration: 6000,
                            style: {
                                background: '#d1fae5',
                                color: '#065f46',
                                border: '1px solid #34d399'
                            }
                        });
                        console.log('🔑 Toast notification shown');
                    });
                })
                .catch((error) => {
                    console.error('❌ Failed to connect to user notification WebSocket:', error);
                    // Don't show toast error for this - it's a background service
                });
        } else if (!token && listenersSetupRef.current) {
            // Disconnect when no token
            console.log('🔌 No token - disconnecting user notification WebSocket');
            userNotificationWS.removeAllListeners();
            userNotificationWS.disconnect();
            listenersSetupRef.current = false;
        }

        // Cleanup on unmount
        return () => {
            console.log('🧹 CollaborationContext unmounting - cleaning up WebSocket');
            userNotificationWS.removeAllListeners();
            userNotificationWS.disconnect();
            listenersSetupRef.current = false;
        };
    }, [token]); // Removed loadCollaborators since it's now stable

    const setupWebSocketListeners = useCallback(() => {
        if (!wsService.current) return;

        wsService.current.on('initial_data', (data: any) => {
            if (data.data.collaborators) {
                setCollaborators(data.data.collaborators);
            }
        });

        wsService.current.on('user_joined', (data: any) => {
            toast.success(`${data.user.username} joined the shopping list`);
        });

        wsService.current.on('user_left', (data: any) => {
            toast.success(`${data.user.username} left the shopping list`);
        });

        wsService.current.on('collaborator_added', (data: any) => {
            setCollaborators(prev => [...prev, data.collaborator]);
            toast.success(`${data.collaborator.username} has been added as collaborator`);

            // Reload collaborators to ensure we have the complete and up-to-date list
            if (currentListId.current) {
                loadCollaborators(currentListId.current);
            }

            // Trigger lists refresh to update participant counts in sidebar
            window.dispatchEvent(new CustomEvent('listsChanged', {
                detail: { type: 'collaborator_added', data }
            }));
        });

        wsService.current.on('user_typing', (data: any) => {
            setTypingUsers(prev => {
                const filtered = prev.filter(user => user.id !== data.user.id);
                if (data.is_typing) {
                    return [...filtered, data.user];
                }
                return filtered;
            });

            // Clear typing after 3 seconds
            if (data.is_typing) {
                setTimeout(() => {
                    setTypingUsers(prev => prev.filter(user => user.id !== data.user.id));
                }, 3000);
            }
        });

        wsService.current.on('permissions_updated', (data: any) => {
            setCollaborators(prev =>
                prev.map(collab =>
                    collab.id === data.user_id
                        ? { ...collab, ...data.permissions }
                        : collab
                )
            );
            toast.success('Collaborator permissions updated');
        });

        wsService.current.on('participant_left', (data: any) => {
            console.log('👋 Participant left notification received:', data);

            // Remove the participant from collaborators list
            setCollaborators(prev =>
                prev.filter(collab => collab.id !== data.participant.id)
            );

            // Show notification to remaining users
            toast.success(`${data.participant.username} has left the list`);
        });

        wsService.current.on('list_access_granted', (data: any) => {
            console.log('🎉 List access granted notification received:', data);

            // Show notification to the user
            toast.success(`${data.message}`);

            // Trigger a refresh of the shopping lists
            // This will be handled by the ShoppingList component
        });

    }, []); // Removed loadCollaborators - it's stable and doesn't need to be a dependency

    const connectToList = useCallback(async (listId: string): Promise<void> => {
        try {
            console.log(`🔗 connectToList called for listId: ${listId}`);

            if (!listId || listId === 'undefined') {
                throw new Error('Invalid list ID');
            }

            // Set currentListId
            console.log(`🔗 Setting currentListId to: ${listId} (was: ${currentListId.current})`);
            currentListId.current = listId;

            // Prevent connecting to the same list multiple times
            if (connectionTracker.currentListId === listId && wsService.current?.isConnected) {
                console.log('✅ Already connected to this list, skipping reconnection');
                return;
            }

            // Prevent multiple connection attempts while one is in progress  
            if (connectionTracker.isConnecting) {
                console.log('🔄 Connection already in progress, skipping duplicate attempt');
                return;
            }

            console.log(`🔌 Connecting to shopping list: ${listId}`);

            // Set connection tracking
            connectionTracker.isConnecting = true;
            connectionTracker.currentListId = listId;

            // Set local state
            connectionInProgress.current = true;
            setConnectionState('CONNECTING');

            // Disconnect existing connection
            if (wsService.current) {
                console.log('🔌 Disconnecting existing WebSocket');
                wsService.current.disconnect();
            }

            wsService.current = new WebSocketService(token);
            // currentListId.current is already set above

            // Increment connection ID to trigger re-registration of event handlers
            setWsConnectionId(prev => prev + 1);

            // Set up event listeners for the new WebSocket connection
            setupWebSocketListeners();

            console.log('🔄 WebSocket service recreated, connection ID:', wsConnectionId + 1);

            // Give the connection more time and better error handling
            try {
                await wsService.current.connect(listId);
                setIsConnected(true);
                setConnectionState('CONNECTED');
                console.log('✅ WebSocket connection successful');
                console.log('✅ Setting isConnected to TRUE');
            } catch (connectionError) {
                console.log('⚠️ WebSocket connection failed, but continuing with HTTP-only mode');
                setIsConnected(false);
                setConnectionState('DISCONNECTED');
                // Don't show error toast immediately - real-time features just won't work
            }

            // Load initial collaborators (always try this regardless of WebSocket status)
            await loadCollaborators(listId);

        } catch (error) {
            console.error('❌ Failed to set up shopping list connection:', error);
            setIsConnected(false);
            setConnectionState('DISCONNECTED');
            // Only show error for serious issues, not just WebSocket failures
            if (error instanceof Error && error.message !== 'WebSocket connection failed') {
                toast.error('Failed to load shopping list');
            }
        } finally {
            // Always clear the connection locks when done
            console.log(`🔒 Clearing connection locks for ${listId}`);
            connectionTracker.isConnecting = false;
            connectionInProgress.current = false;
        }
    }, [token, wsConnectionId]); // Removed setupWebSocketListeners and loadCollaborators - they're stable

    const disconnect = useCallback(() => {
        if (wsService.current) {
            wsService.current.disconnect();
            wsService.current = null;
        }
        setIsConnected(false);
        setConnectionState('DISCONNECTED');
        setCollaborators([]);
        setTypingUsers([]);
        currentListId.current = null;
        connectionInProgress.current = false; // Clear connection lock on disconnect

        // Clear connection tracker
        console.log('🔒 Clearing connection tracker on disconnect');
        connectionTracker.isConnecting = false;
        connectionTracker.currentListId = null;
    }, []);

    const addCollaborator = useCallback(async (friendName: string, collaborationKey: string, canEdit: boolean): Promise<boolean> => {
        try {
            console.log(`👥 addCollaborator called with: friendName=${friendName}, collaborationKey=${collaborationKey}, canEdit=${canEdit}, currentListId=${currentListId.current}`);

            if (!currentListId.current) {
                console.error('❌ addCollaborator: No current list ID');
                return false;
            }

            const response = await api.current.addCollaborator(currentListId.current, {
                friend_name: friendName,
                collaboration_key: collaborationKey,
                can_edit: canEdit,
                can_add_items: canEdit,
                can_invite_others: false
            });

            if (response.success) {
                // Check if participant's collaboration key was auto-regenerated
                if (response.key_regenerated_for === 'participant' && response.participant_new_key) {
                    console.log(`🔑 Participant's collaboration key auto-regenerated: ${response.participant_new_key}`);
                    toast.success(`${response.collaborator?.username || 'Collaborator'} added successfully! Their collaboration key has been automatically updated for security.`, {
                        duration: 6000,
                        style: {
                            background: '#d1fae5',
                            color: '#065f46',
                            border: '1px solid #34d399'
                        }
                    });
                } else {
                    toast.success(`${response.collaborator?.username || 'Collaborator'} added successfully!`);
                }

                // WebSocket will handle the UI update, but also manually reload to ensure consistency
                if (currentListId.current) {
                    loadCollaborators(currentListId.current);
                }
                return true;
            } else {
                toast.error(response.error || 'Failed to add collaborator');
                return false;
            }
        } catch (error: any) {
            console.error('❌ Error adding collaborator:', error);

            // Use the error handler utility for user-friendly messages
            const errorMessage = getUserFriendlyError(error);
            toast.error(errorMessage);
            return false;
        }
    }, []); // Removed loadCollaborators - it's stable

    const updatePermissions = useCallback(async (userId: string, permissions: any): Promise<boolean> => {
        try {
            console.log('🔧 updatePermissions called with:', { userId, permissions, currentListId: currentListId.current });

            if (!currentListId.current) {
                console.error('❌ No current list ID for permission update');
                return false;
            }

            const requestData = {
                user_id: userId,
                ...permissions
            };
            console.log('🔧 Making API call with data:', requestData);

            const response = await api.current.updateCollaboratorPermissions(currentListId.current, requestData);
            console.log('🔧 API response:', response);

            if (response.success) {
                console.log('✅ Permission update successful');
                return true;
            } else {
                console.error('❌ Permission update failed - no success flag');
                toast.error('Failed to update permissions');
                return false;
            }
        } catch (error: any) {
            console.error('❌ Permission update error:', error);
            const errorMessage = getUserFriendlyError(error);
            toast.error(errorMessage);
            return false;
        }
    }, []);

    const loadMyCollaborationKey = useCallback(async (): Promise<void> => {
        try {
            const response = await api.current.getMyCollaborationKey();
            setMyCollaborationKey(response.collaboration_key);
        } catch (error) {
            console.error('❌ Failed to load collaboration key:', error);
        }
    }, []);

    const generateNewCollaborationKey = useCallback(async (): Promise<void> => {
        try {
            const response = await api.current.generateCollaborationKey();
            setMyCollaborationKey(response.collaboration_key);
            toast.success('New collaboration key generated!');
        } catch (error) {
            console.error('❌ Failed to generate collaboration key:', error);
            const errorMessage = getUserFriendlyError(error);
            toast.error(errorMessage);
        }
    }, []);

    const onQuantityTypeChanged = useCallback((callback: (data: any) => void): (() => void) => {
        wsService.current?.on('quantity_type_changed', callback);
        return () => wsService.current?.off('quantity_type_changed', callback);
    }, []);

    const onCollaboratorAdded = useCallback((callback: (data: any) => void) => {
        wsService.current?.on('collaborator_added', callback);
    }, []);

    const onUserJoined = useCallback((callback: (data: any) => void) => {
        wsService.current?.on('user_joined', callback);
    }, []);

    const onUserLeft = useCallback((callback: (data: any) => void) => {
        wsService.current?.on('user_left', callback);
    }, []);

    const onListDeleted = useCallback((callback: (data: any) => void): (() => void) => {
        wsService.current?.on('list_deleted', callback);
        return () => wsService.current?.off('list_deleted', callback);
    }, []);

    const onListAccessGranted = useCallback((callback: (data: any) => void): (() => void) => {
        wsService.current?.on('list_access_granted', callback);
        return () => wsService.current?.off('list_access_granted', callback);
    }, []);

    // Item event handlers
    const onItemAdded = useCallback((callback: (data: any) => void): (() => void) => {
        wsService.current?.on('item_added', callback);
        return () => wsService.current?.off('item_added', callback);
    }, []);

    const onItemToggled = useCallback((callback: (data: any) => void): (() => void) => {
        wsService.current?.on('item_toggled', callback);
        return () => wsService.current?.off('item_toggled', callback);
    }, []);

    const onItemUpdated = useCallback((callback: (data: any) => void): (() => void) => {
        wsService.current?.on('item_updated', callback);
        return () => wsService.current?.off('item_updated', callback);
    }, []);

    const onItemDeleted = useCallback((callback: (data: any) => void): (() => void) => {
        wsService.current?.on('item_deleted', callback);
        return () => wsService.current?.off('item_deleted', callback);
    }, []);

    const onItemsBatchAdded = useCallback((callback: (data: any) => void): (() => void) => {
        wsService.current?.on('items_batch_added', callback);
        return () => wsService.current?.off('items_batch_added', callback);
    }, []);

    const sendTyping = useCallback((isTyping: boolean) => {
        wsService.current?.sendTyping(isTyping);
    }, []);

    const sendCustomMessage = useCallback((messageData: any) => {
        console.log('📤 sendCustomMessage called with:', messageData);
        console.log('📤 wsService.current exists:', !!wsService.current);
        console.log('📤 wsService.current.isConnected:', wsService.current?.isConnected);
        if (wsService.current) {
            wsService.current.send(messageData);
        } else {
            console.warn('⚠️ wsService.current is null, cannot send message');
        }
    }, []);

    // Load collaboration key on mount
    useEffect(() => {
        if (token) {
            loadMyCollaborationKey();
        }
    }, [token, loadMyCollaborationKey]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            disconnect();
        };
    }, [disconnect]);

    return (
        <CollaborationContext.Provider
            value={{
                isConnected,
                connectionState,
                collaborators,
                typingUsers,
                myCollaborationKey,
                wsConnectionId,
                connectToList,
                disconnect,
                addCollaborator,
                updatePermissions,
                loadCollaborators,
                loadMyCollaborationKey,
                generateNewCollaborationKey,
                onItemAdded,
                onItemToggled,
                onItemUpdated,
                onItemDeleted,
                onItemsBatchAdded,
                onQuantityTypeChanged,
                onCollaboratorAdded,
                onUserJoined,
                onUserLeft,
                onListDeleted,
                onListAccessGranted,
                sendTyping,
                sendCustomMessage
            }}
        >
            {children}
        </CollaborationContext.Provider>
    );
};
