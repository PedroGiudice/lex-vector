/**
 * Contexto de sessao ccui-app.
 * Gerencia: case_id selecionado, session_id ativo.
 * Consome mensagens do WebSocketContext (session_created, session_ended).
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useReducer,
} from "react";
import { useWebSocket } from "./WebSocketContext";

interface SessionState {
  caseId: string | null;
  sessionId: string | null;
}

type SessionAction =
  | { type: "SET_CASE"; caseId: string }
  | { type: "SESSION_CREATED"; sessionId: string; caseId?: string }
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
      };

    case "RESET":
      return { caseId: null, sessionId: null };

    default:
      return state;
  }
}

interface SessionContextValue extends SessionState {
  selectCase: (caseId: string) => void;
  createSession: (caseId: string) => void;
  reset: () => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const { send, onMessage } = useWebSocket();
  const [state, dispatch] = useReducer(reducer, {
    caseId: null,
    sessionId: null,
  });

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

  const reset = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  return (
    <SessionContext.Provider
      value={{ ...state, selectCase, createSession, reset }}
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
