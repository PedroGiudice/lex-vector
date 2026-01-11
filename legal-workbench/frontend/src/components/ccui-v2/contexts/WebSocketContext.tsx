import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useRef,
  useCallback,
  ReactNode,
} from 'react';
import { setDevAuthCookie } from '../utils/devToken';

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error' | 'disabled';

export interface WebSocketError {
  type: 'connection' | 'timeout' | 'server' | 'unknown';
  message: string;
  timestamp: Date;
  code?: number;
}

interface WebSocketContextValue {
  socket: WebSocket | null;
  isConnected: boolean;
  lastMessage: unknown | null;
  sendMessage: (msg: unknown) => void;
  connectionState: ConnectionStatus;
  connectionStatus: ConnectionStatus;
  lastError: WebSocketError | null;
  retryCount: number;
  maxRetries: number;
  retry: () => void;
  clearError: () => void;
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
  maxRetries: 10,
  initialRetryDelay: 1000, // 1 second
  maxRetryDelay: 30000, // 30 seconds
};

// Calculate exponential backoff delay
const getBackoffDelay = (retryAttempt: number): number => {
  const delay = Math.min(
    WS_CONFIG.initialRetryDelay * Math.pow(2, retryAttempt),
    WS_CONFIG.maxRetryDelay
  );
  // Add jitter (random 0-1000ms) to prevent thundering herd
  return delay + Math.random() * 1000;
};

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({
  children,
  wsUrl,
  maxRetries = WS_CONFIG.maxRetries,
  enabled = WS_CONFIG.enabled,
}) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<unknown | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(
    enabled ? 'disconnected' : 'disabled'
  );
  const [lastError, setLastError] = useState<WebSocketError | null>(null);
  const [currentRetryCount, setCurrentRetryCount] = useState(0);

  const retryCount = useRef(0);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isManualRetry = useRef(false);

  // Helper to get cookie by name
  const getCookie = (name: string): string | null => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
    return null;
  };

  // Set error with type detection
  const setError = useCallback((code?: number, message?: string) => {
    let errorType: WebSocketError['type'] = 'unknown';
    let errorMessage = message || 'An unknown error occurred';

    if (code === 1006) {
      errorType = 'connection';
      errorMessage = 'Connection closed abnormally. The server may be unavailable.';
    } else if (code === 1001) {
      errorType = 'server';
      errorMessage = 'Server is going away.';
    } else if (code === 1011) {
      errorType = 'server';
      errorMessage = 'Server encountered an unexpected condition.';
    } else if (code === 1013) {
      errorType = 'server';
      errorMessage = 'Server is overloaded. Try again later.';
    } else if (!code) {
      errorType = 'connection';
      errorMessage = 'Failed to establish connection. Is the backend running?';
    }

    setLastError({
      type: errorType,
      message: errorMessage,
      timestamp: new Date(),
      code,
    });
  }, []);

  const clearError = useCallback(() => {
    setLastError(null);
  }, []);

  const connect = useCallback(async (): Promise<WebSocket | null> => {
    if (!enabled) {
      setConnectionStatus('disabled');
      return null;
    }

    // Clear any pending reconnect
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    if (retryCount.current >= maxRetries && !isManualRetry.current) {
      console.log(`[WS] Max retries (${maxRetries}) reached. WebSocket disabled.`);
      setConnectionStatus('error');
      setError(undefined, `Failed to connect after ${maxRetries} attempts.`);
      return null;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;

      // Check for existing JWT, generate dev token if not present
      let token = getCookie('jwt');
      if (!token) {
        console.log('[WS] No JWT found, generating dev token...');
        token = await setDevAuthCookie();
        console.log('[WS] Dev token generated');
      }

      const url = wsUrl || `${protocol}//${host}/ws?token=${token}`;

      if (retryCount.current === 0) {
        console.log('[WS] Connecting to:', url);
      } else {
        const delay = getBackoffDelay(retryCount.current - 1);
        console.log(
          `[WS] Retry ${retryCount.current}/${maxRetries} (backoff: ${Math.round(delay / 1000)}s)`
        );
      }

      setConnectionStatus('connecting');
      clearError();
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('[WS] Connected');
        setIsConnected(true);
        setConnectionStatus('connected');
        retryCount.current = 0;
        setCurrentRetryCount(0);
        isManualRetry.current = false;
        clearError();
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        setSocket(null);

        // Only retry if not a clean close and under max retries
        if (!event.wasClean && retryCount.current < maxRetries) {
          retryCount.current += 1;
          setCurrentRetryCount(retryCount.current);
          setConnectionStatus('disconnected');

          const delay = getBackoffDelay(retryCount.current - 1);
          console.log(
            `[WS] Disconnected (code: ${event.code}). Retry ${retryCount.current}/${maxRetries} in ${Math.round(delay / 1000)}s`
          );

          setError(event.code, `Connection closed (code: ${event.code})`);

          reconnectTimeout.current = setTimeout(() => {
            connect();
          }, delay);
        } else if (retryCount.current >= maxRetries) {
          console.log('[WS] Connection unavailable. Running in offline mode.');
          setConnectionStatus('error');
          setError(event.code, `Connection failed after ${maxRetries} retries.`);
        } else {
          // Clean close
          setConnectionStatus('disconnected');
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
    } catch (err) {
      console.log('[WS] Connection failed:', err);
      setConnectionStatus('error');
      setError(undefined, 'Failed to create WebSocket connection');
      return null;
    }
  }, [enabled, maxRetries, wsUrl, setError, clearError]);

  // Manual retry function - resets retry count
  const retry = useCallback(() => {
    console.log('[WS] Manual retry requested');
    isManualRetry.current = true;
    retryCount.current = 0;
    setCurrentRetryCount(0);
    clearError();

    // Close existing socket if any
    if (socket && socket.readyState !== WebSocket.CLOSED) {
      socket.close(1000, 'Manual reconnect');
    }

    // Clear any pending reconnect
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    connect();
  }, [connect, socket, clearError]);

  useEffect(() => {
    let currentWs: WebSocket | null = null;

    const initConnection = async () => {
      currentWs = await connect();
    };

    initConnection();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (currentWs && currentWs.readyState === WebSocket.OPEN) {
        currentWs.close(1000, 'Component unmount');
      }
    };
  }, [connect]);

  const sendMessage = useCallback(
    (msg: unknown): void => {
      if (socket && isConnected) {
        socket.send(JSON.stringify(msg));
      } else {
        console.warn('[WS] Not connected, cannot send:', msg);
        setError(undefined, 'Cannot send message: not connected');
      }
    },
    [socket, isConnected, setError]
  );

  return (
    <WebSocketContext.Provider
      value={{
        socket,
        isConnected,
        lastMessage,
        sendMessage,
        connectionState: connectionStatus, // Backwards compatibility
        connectionStatus,
        lastError,
        retryCount: currentRetryCount,
        maxRetries,
        retry,
        clearError,
      }}
    >
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
