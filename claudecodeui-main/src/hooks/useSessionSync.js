import { useState, useEffect, useCallback, useRef } from 'react';

export function useSessionSync({ projectPath, sessionId, autoConnect = true } = {}) {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [error, setError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const mountedRef = useRef(true);

  const getWsUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/session-sync`;
  }, []);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionStatus('connecting');
    const ws = new WebSocket(getWsUrl());

    ws.onopen = () => {
      if (!mountedRef.current) { ws.close(); return; }
      setIsConnected(true);
      setConnectionStatus('connected');
      setError(null);
      if (projectPath && sessionId) {
        ws.send(JSON.stringify({ type: 'subscribe', projectPath, sessionId }));
      }
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;
      try {
        const data = JSON.parse(event.data);
        switch (data.type) {
          case 'connected': break;
          case 'subscribed': setIsSubscribed(true); break;
          case 'initial_state': setMessages(data.messages || []); break;
          case 'message': setMessages(prev => [...prev, data.message]); break;
          case 'error': setError(data.error); break;
        }
      } catch (err) {
        console.error('[SessionSync] Parse error:', err);
      }
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setIsConnected(false);
      setIsSubscribed(false);
      setConnectionStatus('disconnected');
      if (autoConnect) {
        reconnectTimeoutRef.current = setTimeout(() => {
          if (mountedRef.current) connect();
        }, 3000);
      }
    };

    ws.onerror = () => {
      if (!mountedRef.current) return;
      setError('WebSocket connection error');
      setConnectionStatus('error');
    };

    wsRef.current = ws;
  }, [getWsUrl, projectPath, sessionId, autoConnect]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
  }, []);

  const subscribe = useCallback((newProjectPath, newSessionId) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'subscribe', projectPath: newProjectPath, sessionId: newSessionId }));
    }
  }, []);

  const subscribeToCurrentSession = useCallback((cwd) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'subscribe_current', cwd }));
    }
  }, []);

  const listSessions = useCallback((filterProjectPath) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'list_sessions', projectPath: filterProjectPath }));
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    if (autoConnect) connect();
    return () => { mountedRef.current = false; disconnect(); };
  }, [autoConnect, connect, disconnect]);

  return { messages, isConnected, isSubscribed, connectionStatus, error, connect, disconnect, subscribe, subscribeToCurrentSession, listSessions };
}

export default useSessionSync;
