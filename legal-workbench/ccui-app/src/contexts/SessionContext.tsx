/**
 * Contexto de sessao ccui-app.
 * Gerencia: case_id selecionado, session_id ativo, canais registrados.
 * Consome mensagens do WebSocketContext (session_created, agent_joined, agent_left, agent_crashed).
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useReducer,
} from "react";
import type { Channel } from "../types/protocol";
import { useWebSocket } from "./WebSocketContext";

interface SessionState {
  caseId: string | null;
  sessionId: string | null;
  channels: Channel[];
}

type SessionAction =
  | { type: "SET_CASE"; caseId: string }
  | { type: "SESSION_CREATED"; sessionId: string; caseId?: string }
  | { type: "ADD_CHANNEL"; channel: Channel }
  | { type: "REMOVE_CHANNEL"; name: string }
  | { type: "RESET" };

function reducer(state: SessionState, action: SessionAction): SessionState {
  switch (action.type) {
    case "SET_CASE":
      return { ...state, caseId: action.caseId };

    case "SESSION_CREATED":
      return {
        ...state,
        sessionId: action.sessionId,
        caseId: action.caseId ?? state.caseId,
        // Canal "main" registrado automaticamente pelo backend
        channels: [{ name: "main", pane_id: "main" }],
      };

    case "ADD_CHANNEL": {
      const exists = state.channels.some((c) => c.name === action.channel.name);
      if (exists) return state;
      return { ...state, channels: [...state.channels, action.channel] };
    }

    case "REMOVE_CHANNEL":
      return {
        ...state,
        channels: state.channels.filter((c) => c.name !== action.name),
      };

    case "RESET":
      return { caseId: null, sessionId: null, channels: [] };

    default:
      return state;
  }
}

interface SessionContextValue extends SessionState {
  selectCase: (caseId: string) => void;
  createSession: (caseId: string) => void;
  addChannel: (channel: Channel) => void;
  removeChannel: (name: string) => void;
  reset: () => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const { send, onMessage } = useWebSocket();
  const [state, dispatch] = useReducer(reducer, {
    caseId: null,
    sessionId: null,
    channels: [],
  });

  // Consome mensagens WS relevantes para sessao
  useEffect(() => {
    return onMessage((msg) => {
      switch (msg.type) {
        case "session_created":
          dispatch({
            type: "SESSION_CREATED",
            sessionId: msg.session_id,
            caseId: msg.case_id,
          });
          break;

        case "agent_joined":
          dispatch({
            type: "ADD_CHANNEL",
            channel: {
              name: msg.name,
              pane_id: msg.pane_id,
              color: msg.color,
              model: msg.model,
            },
          });
          break;

        case "agent_left":
        case "agent_crashed":
          dispatch({ type: "REMOVE_CHANNEL", name: msg.name });
          break;

        case "session_ended":
          dispatch({ type: "RESET" });
          break;
      }
    });
  }, [onMessage]);

  const selectCase = useCallback((caseId: string) => {
    dispatch({ type: "SET_CASE", caseId });
  }, []);

  const createSession = useCallback(
    (caseId: string) => {
      dispatch({ type: "SET_CASE", caseId });
      send({ type: "create_session", case_id: caseId });
    },
    [send]
  );

  const addChannel = useCallback((channel: Channel) => {
    dispatch({ type: "ADD_CHANNEL", channel });
  }, []);

  const removeChannel = useCallback((name: string) => {
    dispatch({ type: "REMOVE_CHANNEL", name });
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  return (
    <SessionContext.Provider
      value={{ ...state, selectCase, createSession, addChannel, removeChannel, reset }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) {
    throw new Error("useSession deve ser usado dentro de SessionProvider");
  }
  return ctx;
}
