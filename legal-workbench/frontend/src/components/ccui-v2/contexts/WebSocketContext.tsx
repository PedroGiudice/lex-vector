import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

interface WebSocketContextValue {
  socket: WebSocket | null;
  isConnected: boolean;
  lastMessage: unknown | null;
  sendMessage: (msg: unknown) => void;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<unknown | null>(null);

  // Helper to get cookie by name
  const getCookie = (name: string): string | null => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
    return null;
  };

  const connect = (): WebSocket | null => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const token = getCookie('jwt') || 'dev-token'; // Fallback for dev
      const wsUrl = `${protocol}//${host}/ws?token=${token}`;

      console.log('Connecting to WS:', wsUrl);
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WS Connected');
        setIsConnected(true);
      };

      ws.onclose = () => {
        console.log('WS Disconnected');
        setIsConnected(false);
        // Reconnect logic could go here
        setTimeout(connect, 5000);
      };

      ws.onerror = (err) => {
        console.error('WS Error:', err);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
        } catch (e) {
          console.error('Failed to parse WS message', e);
        }
      };

      setSocket(ws);

      return ws;
    } catch (e) {
      console.error("WS Connection failed", e);
      return null;
    }
  };

  useEffect(() => {
    const ws = connect();
    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  const sendMessage = (msg: unknown): void => {
    if (socket && isConnected) {
      socket.send(JSON.stringify(msg));
    } else {
      console.warn("WS not connected, cannot send:", msg);
    }
  };

  return (
    <WebSocketContext.Provider value={{ socket, isConnected, lastMessage, sendMessage }}>
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
