export class UserNotificationWebSocket {
    private ws: WebSocket | null = null;
    private listeners: { [eventType: string]: ((data: any) => void)[] } = {};
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 3000;
    private isConnecting = false;
    private isConnected = false;
    private token: string | null = null;
    private lastReconnectAttempt = 0;
    private reconnectCooldown = 10000; // 10 seconds
    private connectionTimeout = 30000; // 30 seconds

    connect(token: string): Promise<void> {
        this.token = token;

        return new Promise((resolve, reject) => {
            // Prevent multiple simultaneous connection attempts
            if (this.isConnecting) {
                console.log('⚠️ User notification WebSocket connection already in progress, waiting...');
                resolve();
                return;
            }

            if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
                console.log('✅ User notification WebSocket already connected and open');
                resolve();
                return;
            }

            console.log('🔌 Connecting to user notification WebSocket...');
            this.isConnecting = true;

            // Force close existing connection if any
            if (this.ws) {
                console.log('🔌 Closing existing WebSocket connection');
                this.ws.close(1000, 'Reconnecting');
                this.ws = null;
            }

            this.isConnected = false;

            try {
                const wsUrl = `ws://localhost:8000/ws/user/notifications/?token=${token}`;
                console.log('🔌 Creating user notification WebSocket connection to:', wsUrl);

                this.ws = new WebSocket(wsUrl);

                // Set connection timeout
                const timeout = setTimeout(() => {
                    if (this.isConnecting) {
                        console.log('⏰ User notification WebSocket connection timeout');
                        this.ws?.close();
                        this.isConnecting = false;
                        reject(new Error('Connection timeout'));
                    }
                }, this.connectionTimeout);

                this.ws.onopen = () => {
                    clearTimeout(timeout);
                    this.isConnecting = false;
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    console.log('🔗 User notification WebSocket connected successfully');
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        console.log('📨 User notification WebSocket received:', data);
                        this.handleMessage(data);
                    } catch (error) {
                        console.error('❌ Error parsing user notification WebSocket message:', error);
                    }
                };

                this.ws.onclose = (event) => {
                    clearTimeout(timeout);
                    this.isConnecting = false;
                    this.isConnected = false;
                    console.log('🔌 User notification WebSocket disconnected', event.code, event.reason);

                    // Handle different close codes
                    if (event.code === 1000 || event.code === 1001) {
                        console.log('🔌 User notification connection closed normally, not reconnecting');
                        return;
                    }

                    if (event.code === 4001) {
                        console.log('🔌 User notification authentication failed, not reconnecting');
                        reject(new Error('Authentication failed'));
                        return;
                    }

                    if (event.code === 4003) {
                        console.log('🔌 User notification access forbidden, not reconnecting');
                        reject(new Error('Access forbidden'));
                        return;
                    }

                    // Try to reconnect for other errors
                    if (this.reconnectAttempts < this.maxReconnectAttempts) {
                        // Implement reconnection cooldown
                        const now = Date.now();
                        if (now - this.lastReconnectAttempt < this.reconnectCooldown) {
                            console.log('🛑 User notification reconnection cooldown active, skipping attempt');
                            return;
                        }

                        this.lastReconnectAttempt = now;
                        this.reconnectAttempts++;
                        console.log(`🔄 User notification attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${this.reconnectDelay}ms`);

                        setTimeout(() => {
                            if (this.token) {
                                this.connect(this.token).catch(console.error);
                            }
                        }, this.reconnectDelay);
                    } else {
                        console.log('🛑 User notification max reconnection attempts reached');
                        reject(new Error('Max reconnection attempts reached'));
                    }
                };

                this.ws.onerror = (error) => {
                    clearTimeout(timeout);
                    console.error('❌ User notification WebSocket error:', error);
                    this.isConnecting = false;
                };

            } catch (error) {
                this.isConnecting = false;
                console.error('❌ Error creating user notification WebSocket:', error);
                reject(error);
            }
        });
    }

    disconnect() {
        console.log('🔌 Disconnecting user notification WebSocket...');
        if (this.ws) {
            this.ws.close(1000, 'User disconnect');
            this.ws = null;
        }
        this.isConnected = false;
        this.isConnecting = false;
        this.removeAllListeners();
    }

    removeAllListeners() {
        console.log('🧹 Removing all user notification listeners');
        this.listeners = {};
    }

    on(eventType: string, callback: (data: any) => void) {
        if (!this.listeners[eventType]) {
            this.listeners[eventType] = [];
        }
        this.listeners[eventType].push(callback);
        console.log(`📺 User notification listener registered for: ${eventType}`);
    }

    off(eventType: string, callback: (data: any) => void) {
        if (this.listeners[eventType]) {
            const index = this.listeners[eventType].indexOf(callback);
            if (index > -1) {
                this.listeners[eventType].splice(index, 1);
                console.log(`📺 User notification listener removed for: ${eventType}`);
            }
        }
    }

    private handleMessage(data: any) {
        const { type } = data;
        console.log(`📨 *** USER NOTIFICATION MESSAGE RECEIVED ***`);
        console.log(`📨 Message type: ${type}`);
        console.log(`📨 Full message data:`, data);
        console.log(`📨 Available listeners:`, Object.keys(this.listeners));

        // Count total listeners to detect duplicates
        const totalListeners = Object.values(this.listeners).reduce((sum, arr) => sum + arr.length, 0);
        console.log(`📨 Total listeners across all types: ${totalListeners}`);

        if (this.listeners[type]) {
            const listenerCount = this.listeners[type].length;
            console.log(`📤 Dispatching to ${listenerCount} listeners for type: ${type}`);

            if (listenerCount > 1) {
                console.error(`❌❌❌ DUPLICATE LISTENERS DETECTED! ${listenerCount} listeners for type: ${type}`);
                console.error(`❌ This is causing duplicate notifications!`);
                console.error(`❌ Listener count breakdown:`, Object.entries(this.listeners).map(([t, arr]) => `${t}: ${arr.length}`));
            }

            this.listeners[type].forEach((callback, index) => {
                console.log(`📤 Calling listener ${index + 1}/${listenerCount} for type: ${type}`);
                callback(data);
            });
        } else {
            console.log(`⚠️ No listeners registered for user notification message type: ${type}`);
            console.log(`⚠️ Available listeners:`, Object.keys(this.listeners));
        }

        // Also trigger 'message' event for all messages
        if (this.listeners['message']) {
            this.listeners['message'].forEach(callback => callback(data));
        }
    }

    send(data: any) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.error('❌ Cannot send user notification message: WebSocket not connected');
        }
    }

    // Send periodic ping to keep connection alive
    startHeartbeat() {
        setInterval(() => {
            if (this.isConnected) {
                this.send({ type: 'ping', timestamp: Date.now() });
            }
        }, 30000); // Send ping every 30 seconds
    }
}

// Export singleton instance
export const userNotificationWS = new UserNotificationWebSocket();

