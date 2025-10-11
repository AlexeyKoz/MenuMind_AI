class WebSocketService {
    private socket: WebSocket | null = null;
    private token: string | null = null;
    private listeners: { [event: string]: Function[] } = {};
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 3;
    private reconnectDelay = 5000;
    private lastReconnectAttempt = 0;
    private lastConnectionAttempt = 0;
    private minConnectionDelay = 1000; // Minimum 1 second between connection attempts

    constructor(token: string | null) {
        this.token = token;
    }

    connect(listId: string): Promise<void> {
        return new Promise((resolve, reject) => {
            if (!listId || listId === 'undefined') {
                reject(new Error('Invalid list ID'));
                return;
            }

            // Prevent rapid connections with minimum delay
            const now = Date.now();
            if (this.lastConnectionAttempt > 0 && (now - this.lastConnectionAttempt) < this.minConnectionDelay) {
                console.log(`🛑 Too soon since last connection attempt, waiting... (${now - this.lastConnectionAttempt}ms < ${this.minConnectionDelay}ms)`);
                reject(new Error('Connection attempt too soon'));
                return;
            }
            this.lastConnectionAttempt = now;

            // Prevent rapid connections
            if (this.socket?.readyState === WebSocket.CONNECTING) {
                console.log('🛑 WebSocket already connecting, waiting...');
                reject(new Error('Connection already in progress'));
                return;
            }

            if (this.socket?.readyState === WebSocket.OPEN) {
                console.log('✅ WebSocket already connected');
                resolve();
                return;
            }

            // Close any existing socket first
            if (this.socket && this.socket.readyState !== WebSocket.CLOSED) {
                console.log('🔌 Closing existing socket before new connection');
                this.socket.close(1000, 'New connection requested');
            }

            const wsUrl = `ws://localhost:8000/ws/shopping/${listId}/?token=${this.token}`;
            console.log(`🔌 Creating new WebSocket connection to: ${wsUrl.substring(0, 80)}...`);
            this.socket = new WebSocket(wsUrl);

            // Add connection timeout
            const connectionTimeout = setTimeout(() => {
                console.log('⏰ WebSocket connection timeout');
                if (this.socket && this.socket.readyState === WebSocket.CONNECTING) {
                    this.socket.close();
                    reject(new Error('Connection timeout'));
                }
            }, 30000); // 30 second timeout (increased from 10)

            this.socket.onopen = () => {
                console.log('🔗 WebSocket connected successfully');
                console.log(`🔗 WebSocket state: ${this.socket?.readyState}, isConnected: ${this.isConnected}`);
                clearTimeout(connectionTimeout);
                this.reconnectAttempts = 0;
                resolve();
            };

            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('❌ Error parsing WebSocket message:', error);
                }
            };

            this.socket.onclose = (event) => {
                console.log('🔌 WebSocket disconnected', event.code, event.reason);
                clearTimeout(connectionTimeout);

                // Handle different close codes
                switch (event.code) {
                    case 1000: // Normal closure
                        console.log('🔌 Connection closed normally, not reconnecting');
                        return;
                    case 1001: // Going away
                        console.log('🔌 Connection closed (going away), not reconnecting');
                        return;
                    case 1006: // Abnormal closure
                        console.log('⚠️ Connection closed abnormally, will retry');
                        break;
                    case 4001: // Unauthorized
                        console.log('❌ Authentication failed, not reconnecting');
                        return;
                    case 4003: // Forbidden
                        console.log('❌ Access forbidden, not reconnecting');
                        return;
                    default:
                        console.log(`⚠️ Connection closed with code ${event.code}, will retry`);
                        break;
                }

                this.handleReconnect(listId);
            };

            this.socket.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                clearTimeout(connectionTimeout);
                reject(error);
            };
        });
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.listeners = {};
        this.reconnectAttempts = 0;
    }

    private handleMessage(data: any) {
        const { type } = data;
        console.log(`📨 WebSocket received message of type: ${type}`, data);

        if (this.listeners[type]) {
            console.log(`📤 Dispatching to ${this.listeners[type].length} listeners for type: ${type}`);
            this.listeners[type].forEach(callback => callback(data));
        } else {
            console.log(`⚠️ No listeners registered for message type: ${type}`);
        }

        // Also trigger 'message' event for all messages
        if (this.listeners['message']) {
            this.listeners['message'].forEach(callback => callback(data));
        }
    }

    private handleReconnect(listId: string) {
        // Add a cooldown to prevent rapid reconnections
        const now = Date.now();
        if (this.lastReconnectAttempt && (now - this.lastReconnectAttempt) < 10000) {
            console.log('🛑 Reconnection cooldown active, skipping attempt');
            return;
        }

        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.lastReconnectAttempt = now;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

            console.log(`🔄 Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);

            setTimeout(() => {
                this.connect(listId).catch(console.error);
            }, delay);
        } else {
            console.error('❌ Max reconnection attempts reached');
        }
    }

    // Event listeners
    on(event: string, callback: Function) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    off(event: string, callback: Function) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }

    // Send messages
    send(data: any) {
        console.log(`📤 SEND ATTEMPT: WebSocket state = ${this.socket?.readyState}, OPEN = ${WebSocket.OPEN}`);
        if (this.socket?.readyState === WebSocket.OPEN) {
            console.log(`📤 Sending WebSocket message:`, data);
            this.socket.send(JSON.stringify(data));
        } else {
            console.warn(`⚠️ WebSocket not connected. Cannot send message. Socket state: ${this.socket?.readyState}, Data:`, data);
        }
    }

    // Specific message senders
    addItem(item: any) {
        this.send({
            type: 'add_item',
            item
        });
    }

    toggleItem(itemId: string) {
        this.send({
            type: 'toggle_item',
            item_id: itemId
        });
    }

    addCollaborator(collaboratorData: any) {
        this.send({
            type: 'add_collaborator',
            ...collaboratorData
        });
    }

    updatePermissions(permissionData: any) {
        this.send({
            type: 'update_permissions',
            ...permissionData
        });
    }

    sendTyping(isTyping: boolean) {
        this.send({
            type: 'typing',
            is_typing: isTyping
        });
    }

    // Status getters
    get isConnected(): boolean {
        return this.socket?.readyState === WebSocket.OPEN;
    }

    get connectionState(): string {
        if (!this.socket) return 'DISCONNECTED';

        switch (this.socket.readyState) {
            case WebSocket.CONNECTING: return 'CONNECTING';
            case WebSocket.OPEN: return 'CONNECTED';
            case WebSocket.CLOSING: return 'CLOSING';
            case WebSocket.CLOSED: return 'DISCONNECTED';
            default: return 'UNKNOWN';
        }
    }
}

export default WebSocketService;
