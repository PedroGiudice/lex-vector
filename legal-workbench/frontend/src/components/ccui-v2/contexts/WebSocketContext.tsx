import React, { createContext, useContext, useEffect, useState, useRef, useCallback, ReactNode } from 'react';

interface WebSocketContextValue {
  socket: WebSocket | null;
  isConnected: boolean;
  lastMessage: unknown | null;
  sendMessage: (msg: unknown) => void;
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'disabled';
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

interface WebSocketProviderProps {
  children: ReactNode;
  wsUrl?: string;
  maxRetries?: number;
  enabled?: boolean;
}

// Configuration
const WS_CONFIG = {
  enabled: import.meta.env.VITE_WS_ENABLED !== 'false',
  maxRetries: 3,
  retryDelay: 5000,
};

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({
  children,
  wsUrl,
  maxRetries = WS_CONFIG.maxRetries,
  enabled = WS_CONFIG.enabled
}) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<unknown | null>(null);
  const [connectionState, setConnectionState] = useState<'disconnected' | 'connecting' | 'connected' | 'disabled'>(
    enabled ? 'disconnected' : 'disabled'
  );

  const retryCount = useRef(0);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Helper to get cookie by name
  const getCookie = (name: string): string | null => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
    return null;
  };

  const connect = useCallback((): WebSocket | null => {
    if (!enabled) {
      setConnectionState('disabled');
      return null;
    }

    if (retryCount.current >= maxRetries) {
      console.log(`[WS] Max retries (${maxRetries}) reached. WebSocket disabled.`);
      setConnectionState('disabled');
      return null;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const token = getCookie('jwt') || 'dev-token';
      const url = wsUrl || `${protocol}//${host}/ws?token=${token}`;

      if (retryCount.current === 0) {
        console.log('[WS] Connecting to:', url);
      }

      setConnectionState('connecting');
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('[WS] Connected');
        setIsConnected(true);
        setConnectionState('connected');
        retryCount.current = 0; // Reset on successful connection
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        setConnectionState('disconnected');

        // Only retry if not a clean close and under max retries
        if (!event.wasClean && retryCount.current < maxRetries) {
          retryCount.current += 1;
          console.log(`[WS] Disconnected. Retry ${retryCount.current}/${maxRetries} in ${WS_CONFIG.retryDelay / 1000}s`);
          reconnectTimeout.current = setTimeout(connect, WS_CONFIG.retryDelay);
        } else if (retryCount.current >= maxRetries) {
          console.log('[WS] Connection unavailable. Running in offline mode.');
          setConnectionState('disabled');
        }
      };

      ws.onerror = () => {
        // Errors are followed by onclose, so just log minimally
        if (retryCount.current === 0) {
          console.log('[WS] Backend not available');
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
        } catch {
          console.warn('[WS] Failed to parse message');
        }
      };

      setSocket(ws);
      return ws;
    } catch {
      console.log('[WS] Connection failed');
      setConnectionState('disabled');
      return null;
    }
  }, [enabled, maxRetries, wsUrl]);

  useEffect(() => {
    const ws = connect();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close(1000, 'Component unmount');
      }
    };
  }, [connect]);

  const sendMessage = (msg: unknown): void => {
    if (socket && isConnected) {
      socket.send(JSON.stringify(msg));
    } else {
      console.warn("WS not connected, cannot send:", msg);
    }
  };

  return (
    <WebSocketContext.Provider value={{ socket, isConnected, lastMessage, sendMessage, connectionState }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = (): WebSocketContextValue => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};
