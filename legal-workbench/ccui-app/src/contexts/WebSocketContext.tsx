/**
 * Contexto WebSocket para ccui-app.
 * Adaptado de ccui-v2/WebSocketContext -- removida autenticacao (JWT/cookie/dev token).
 * Conexao sob demanda: nao conecta no mount. Conectar ao selecionar um caso.
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import type { ClientMessage, ServerMessage } from "../types/protocol";

const BASE_URL = "ws://localhost:8005/ws";
const MAX_RETRIES = 5;
const INITIAL_BACKOFF_MS = 1000;

export type WsStatus = "idle" | "connecting" | "connected" | "disconnected" | "error";

interface WebSocketContextValue {
  status: WsStatus;
  retryCount: number;
  maxRetries: number;
  send: (msg: ClientMessage) => void;
  connect: () => Promise<void>;
  disconnect: () => void;
  retryManual: () => void;
  /** Registra listener para mensagens do servidor. Retorna funcao de cleanup. */
  onMessage: (handler: (msg: ServerMessage) => void) => () => void;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const wsRef = useRef<WebSocket | null>(null);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryCountRef = useRef(0);
  const handlersRef = useRef<Set<(msg: ServerMessage) => void>>(new Set());
  const intentionalCloseRef = useRef(false);

  const [status, setStatus] = useState<WsStatus>("idle");
  const [retryCount, setRetryCount] = useState(0);

  const clearRetryTimer = () => {
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }
  };

  const connect = useCallback((): Promise<void> => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      intentionalCloseRef.current = false;
      setStatus("connecting");

      const ws = new WebSocket(BASE_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        retryCountRef.current = 0;
        setRetryCount(0);
        setStatus("connected");
        clearRetryTimer();
        resolve();
      };

      ws.onmessage = (event: MessageEvent) => {
        try {
          const msg = JSON.parse(event.data as string) as ServerMessage;
          handlersRef.current.forEach((handler) => handler(msg));
        } catch {
          // mensagem malformada -- ignorar
        }
      };

      ws.onerror = () => {
        setStatus("error");
        reject(new Error("WebSocket connection failed"));
      };

      ws.onclose = () => {
        wsRef.current = null;
        if (intentionalCloseRef.current) {
          setStatus("idle");
          return;
        }

        const attempt = retryCountRef.current;
        if (attempt >= MAX_RETRIES) {
          setStatus("disconnected");
          return;
        }

        setStatus("connecting");
        const delay = INITIAL_BACKOFF_MS * Math.pow(2, attempt);
        retryCountRef.current = attempt + 1;
        setRetryCount(attempt + 1);

        retryTimerRef.current = setTimeout(() => {
          connect();
        }, delay);
      };
    });
  }, []);

  const disconnect = useCallback(() => {
    intentionalCloseRef.current = true;
    clearRetryTimer();
    wsRef.current?.close();
    wsRef.current = null;
    setStatus("idle");
  }, []);

  const retryManual = useCallback(() => {
    clearRetryTimer();
    retryCountRef.current = 0;
    setRetryCount(0);
    connect();
  }, [connect]);

  const send = useCallback((msg: ClientMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  const onMessage = useCallback((handler: (msg: ServerMessage) => void) => {
    handlersRef.current.add(handler);
    return () => {
      handlersRef.current.delete(handler);
    };
  }, []);

  // Cleanup ao desmontar
  useEffect(() => {
    return () => {
      intentionalCloseRef.current = true;
      clearRetryTimer();
      wsRef.current?.close();
    };
  }, []);

  return (
    <WebSocketContext.Provider
      value={{ status, retryCount, maxRetries: MAX_RETRIES, send, connect, disconnect, retryManual, onMessage }}
    >
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket(): WebSocketContextValue {
  const ctx = useContext(WebSocketContext);
  if (!ctx) {
    throw new Error("useWebSocket deve ser usado dentro de WebSocketProvider");
  }
  return ctx;
}
