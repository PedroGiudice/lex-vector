/**
 * Tipos do protocolo WebSocket ccui-backend.
 * Fonte de verdade: legal-workbench/ccui-backend/src/ws.rs
 */

// ---- Client -> Server ----

export type ClientMessage =
  | { type: "create_session"; case_id?: string }
  | { type: "input"; channel: string; text: string }
  | { type: "resize"; channel: string; cols: number; rows: number }
  | { type: "destroy_session"; session_id: string }
  | { type: "ping" };

// ---- Server -> Client ----

export type ServerMessage =
  | { type: "output"; channel: string; data: string }
  | { type: "session_created"; session_id: string; case_id?: string }
  | { type: "session_ended"; session_id: string }
  | { type: "agent_joined"; name: string; color: string; model: string; pane_id: string }
  | { type: "agent_left"; name: string }
  | { type: "agent_crashed"; name: string }
  | { type: "error"; message: string }
  | { type: "pong" };

// ---- Tipos auxiliares ----

export interface Channel {
  name: string;
  pane_id: string;
  color?: string;
  model?: string;
}

export interface CaseInfo {
  id: string;
  path: string;
  ready: boolean;
  doc_count: number;
  last_modified: string;
}

export interface SessionInfo {
  session_id: string;
  case_id?: string;
  created_at?: string;
}
