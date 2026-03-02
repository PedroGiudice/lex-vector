/**
 * Tipos do protocolo WebSocket ccui-backend.
 * Fonte de verdade: legal-workbench/ccui-backend/src/ws.rs
 */

// ---- Client -> Server ----

export type ClientMessage =
  | { type: "create_session"; case_id?: string }
  | { type: "input"; channel: string; text: string }
  | { type: "chat_input"; session_id: string; text: string }
  | { type: "resize"; channel: string; cols: number; rows: number }
  | { type: "destroy_session"; session_id: string }
  | { type: "ping" };

// ---- Stream-JSON Message Parts ----

export type MessagePartType =
  | "text"
  | "thinking"
  | "tool_use"
  | "tool_result"
  ;

export interface MessagePart {
  type: MessagePartType;
  content: string;
  metadata?: {
    toolName?: string;
    toolId?: string;
    filePath?: string;
    exitCode?: number;
    isError?: boolean;
    language?: string;
    isStreaming?: boolean;
  };
}

// ---- Chat Messages ----

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  parts: MessagePart[];
  timestamp: number;
  isStreaming?: boolean;
}

// ---- Server -> Client ----

export type ServerMessage =
  | { type: "output"; channel: string; data: string }
  | { type: "session_created"; session_id: string; case_id?: string }
  | { type: "session_ended"; session_id: string }
  | { type: "chat_init"; session_id: string; model: string; claude_session_id: string }
  | { type: "chat_start"; message_id: string; session_id: string }
  | { type: "chat_delta"; message_id: string; session_id: string; part: MessagePart }
  | { type: "chat_end"; message_id: string; session_id: string }
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
  title?: string;
  parties?: string;
  tags?: string[];
  progress?: number;
}

export interface SessionInfo {
  session_id: string;
  case_id?: string;
  created_at?: string;
}
