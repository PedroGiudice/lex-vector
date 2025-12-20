import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * WebSocket Connection Status
 * @typedef {'connecting' | 'connected' | 'disconnected' | 'error'} ConnectionStatus
 */

/**
 * WebSocket Message Types
 * @typedef {Object} WebSocketMessage
 * @property {'session-created' | 'claude-message' | 'claude-complete' | 'session-aborted' | 'tool-use' | 'tool-result' | 'thinking' | 'claude-response' | 'claude-output' | 'claude-error' | 'claude-interactive-prompt' | 'cursor-system' | 'cursor-user' | 'cursor-tool-use' | 'cursor-error' | 'cursor-result' | 'cursor-output' | 'projects_updated' | 'taskmaster-project-updated' | 'token-budget'} type
 * @property {*} data
 * @property {string} [sessionId]
 * @property {string} [error]
 */

/**
 * Hook Configuration Options
 * @typedef {Object} UseChatWebSocketOptions
 * @property {string} url - WebSocket server URL
 * @property {(message: WebSocketMessage) => void} [onMessage] - Callback for incoming messages
 * @property {() => void} [onConnect] - Callback when connection opens
 * @property {() => void} [onDisconnect] - Callback when connection closes
 * @property {(error: Event) => void} [onError] - Callback for errors
 * @property {boolean} [autoReconnect=true] - Whether to automatically reconnect on disconnect
 * @property {number} [reconnectDelay=3000] - Delay in ms before reconnection attempt
 * @property {number} [maxReconnectAttempts=Infinity] - Maximum number of reconnection attempts
 * @property {boolean} [token] - Authentication token (for OSS mode)
 * @property {boolean} [isPlatform=false] - Whether running in platform mode
 */

/**
 * Hook Return Value
 * @typedef {Object} UseChatWebSocketReturn
 * @property {boolean} isConnected - Whether WebSocket is connected
 * @property {ConnectionStatus} connectionStatus - Current connection status
 * @property {(message: any) => void} sendMessage - Function to send messages
 * @property {WebSocketMessage | null} lastMessage - Most recent message received
 * @property {Event | null} error - Most recent error
 * @property {() => void} reconnect - Manually trigger reconnection
 * @property {() => void} disconnect - Manually disconnect
 * @property {number} reconnectAttempts - Number of reconnection attempts made
 */

/**
 * Custom React hook for managing WebSocket communication in the Claude Code UI.
 *
 * This hook provides a robust WebSocket connection with automatic reconnection,
 * connection state management, and message handling capabilities.
 *
 * Features:
 * - Automatic connection management
 * - Configurable auto-reconnect with exponential backoff
 * - Connection status tracking
 * - Message buffering during disconnection
 * - Proper cleanup on unmount
 * - Support for both Platform and OSS authentication modes
 *
 * @param {UseChatWebSocketOptions} options - Configuration options
 * @returns {UseChatWebSocketReturn} WebSocket state and control functions
 *
 * @example
 * ```javascript
 * const {
 *   isConnected,
 *   connectionStatus,
 *   sendMessage,
 *   lastMessage,
 *   error
 * } = useChatWebSocket({
 *   url: 'ws://localhost:3000/ws',
 *   onMessage: (msg) => console.log('Received:', msg),
 *   onConnect: () => console.log('Connected'),
 *   onDisconnect: () => console.log('Disconnected'),
 *   autoReconnect: true
 * });
 * ```
 */
export function useChatWebSocket({
  url,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  autoReconnect = true,
  reconnectDelay = 3000,
  maxReconnectAttempts = Infinity,
  token = null,
  isPlatform = false
}) {
  // Connection state
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // Refs to avoid stale closures
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const messageBufferRef = useRef([]);
  const isManualDisconnectRef = useRef(false);
  const mountedRef = useRef(true);

  /**
   * Clear any pending reconnection timeout
   */
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  /**
   * Construct WebSocket URL based on mode and authentication
   */
  const constructWebSocketUrl = useCallback(() => {
    if (!url) {
      throw new Error('WebSocket URL is required');
    }

    // If url is already a full WebSocket URL, use it directly
    if (url.startsWith('ws://') || url.startsWith('wss://')) {
      // For OSS mode, append token if provided
      if (!isPlatform && token) {
        const separator = url.includes('?') ? '&' : '?';
        return `${url}${separator}token=${encodeURIComponent(token)}`;
      }
      return url;
    }

    // Construct from current window location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    let wsUrl = `${protocol}//${window.location.host}${url}`;

    // Add token for OSS mode
    if (!isPlatform && token) {
      const separator = wsUrl.includes('?') ? '&' : '?';
      wsUrl = `${wsUrl}${separator}token=${encodeURIComponent(token)}`;
    }

    return wsUrl;
  }, [url, token, isPlatform]);

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    // Don't connect if already connecting or connected
    if (wsRef.current && (wsRef.current.readyState === WebSocket.CONNECTING || wsRef.current.readyState === WebSocket.OPEN)) {
      return;
    }

    try {
      setConnectionStatus('connecting');
      const wsUrl = constructWebSocketUrl();
      const websocket = new WebSocket(wsUrl);

      websocket.onopen = () => {
        if (!mountedRef.current) {
          websocket.close();
          return;
        }

        console.log('[WebSocket] Connected to', wsUrl);
        setIsConnected(true);
        setConnectionStatus('connected');
        setError(null);
        setReconnectAttempts(0);

        // Send buffered messages
        if (messageBufferRef.current.length > 0) {
          console.log(`[WebSocket] Sending ${messageBufferRef.current.length} buffered messages`);
          messageBufferRef.current.forEach(msg => {
            websocket.send(JSON.stringify(msg));
          });
          messageBufferRef.current = [];
        }

        // Call user callback
        if (onConnect) {
          onConnect();
        }
      };

      websocket.onmessage = (event) => {
        if (!mountedRef.current) return;

        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);

          // Call user callback
          if (onMessage) {
            onMessage(data);
          }
        } catch (parseError) {
          console.error('[WebSocket] Error parsing message:', parseError);
          console.error('[WebSocket] Raw message:', event.data);
        }
      };

      websocket.onclose = (event) => {
        if (!mountedRef.current) return;

        console.log('[WebSocket] Disconnected', event.code, event.reason);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        wsRef.current = null;

        // Call user callback
        if (onDisconnect) {
          onDisconnect();
        }

        // Attempt reconnection if not manually disconnected
        if (autoReconnect && !isManualDisconnectRef.current && reconnectAttempts < maxReconnectAttempts) {
          const delay = Math.min(reconnectDelay * Math.pow(1.5, reconnectAttempts), 30000); // Max 30s
          console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts === Infinity ? '∞' : maxReconnectAttempts})`);

          clearReconnectTimeout();
          reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current) {
              setReconnectAttempts(prev => prev + 1);
              connect();
            }
          }, delay);
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          console.error('[WebSocket] Max reconnection attempts reached');
          setConnectionStatus('error');
        }
      };

      websocket.onerror = (errorEvent) => {
        if (!mountedRef.current) return;

        console.error('[WebSocket] Error:', errorEvent);
        setError(errorEvent);
        setConnectionStatus('error');

        // Call user callback
        if (onError) {
          onError(errorEvent);
        }
      };

      wsRef.current = websocket;

    } catch (err) {
      console.error('[WebSocket] Connection error:', err);
      setConnectionStatus('error');
      setError(err);

      // Retry connection if auto-reconnect is enabled
      if (autoReconnect && reconnectAttempts < maxReconnectAttempts) {
        const delay = Math.min(reconnectDelay * Math.pow(1.5, reconnectAttempts), 30000);
        clearReconnectTimeout();
        reconnectTimeoutRef.current = setTimeout(() => {
          if (mountedRef.current) {
            setReconnectAttempts(prev => prev + 1);
            connect();
          }
        }, delay);
      }
    }
  }, [
    constructWebSocketUrl,
    onConnect,
    onMessage,
    onDisconnect,
    onError,
    autoReconnect,
    reconnectDelay,
    maxReconnectAttempts,
    reconnectAttempts,
    clearReconnectTimeout
  ]);

  /**
   * Disconnect from WebSocket server
   */
  const disconnect = useCallback(() => {
    isManualDisconnectRef.current = true;
    clearReconnectTimeout();

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    setConnectionStatus('disconnected');
    setReconnectAttempts(0);
  }, [clearReconnectTimeout]);

  /**
   * Manually trigger reconnection
   */
  const reconnect = useCallback(() => {
    isManualDisconnectRef.current = false;
    setReconnectAttempts(0);

    if (wsRef.current) {
      wsRef.current.close();
    }

    connect();
  }, [connect]);

  /**
   * Send a message through the WebSocket
   * Messages are buffered if not connected
   */
  const sendMessage = useCallback((message) => {
    if (!message) {
      console.warn('[WebSocket] Attempted to send empty message');
      return;
    }

    const serializedMessage = typeof message === 'string' ? message : JSON.stringify(message);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(serializedMessage);
      } catch (err) {
        console.error('[WebSocket] Error sending message:', err);
        // Buffer the message for retry
        messageBufferRef.current.push(message);
      }
    } else {
      console.warn('[WebSocket] Not connected, buffering message');
      messageBufferRef.current.push(message);
    }
  }, []);

  // Initial connection on mount
  useEffect(() => {
    mountedRef.current = true;
    isManualDisconnectRef.current = false;
    connect();

    // Cleanup on unmount
    return () => {
      mountedRef.current = false;
      clearReconnectTimeout();

      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    isConnected,
    connectionStatus,
    sendMessage,
    lastMessage,
    error,
    reconnect,
    disconnect,
    reconnectAttempts
  };
}

export default useChatWebSocket;
