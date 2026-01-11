// CCui v2 Components
// Terminal-style UI for Claude Code integration

export { default as CCuiLayout } from './CCuiLayout';
export { default as CCuiChatInterface } from './CCuiChatInterface';
export { default as CCuiFileTree } from './CCuiFileTree';
export { ReactorSpinner, PhyllotaxisSpinner } from './Spinners';

// Error handling components
export { ErrorBanner } from './ErrorBanner';
export type { ErrorType, ErrorBannerProps } from './ErrorBanner';
export { ConnectionStatus } from './ConnectionStatus';
export type { ConnectionState, ConnectionStatusProps } from './ConnectionStatus';

// Re-export contexts
export { WebSocketProvider, useWebSocket } from './contexts/WebSocketContext';
export type {
  ConnectionStatus as WsConnectionStatus,
  WebSocketError,
} from './contexts/WebSocketContext';
export { AuthProvider, useAuth } from './contexts/AuthContext';
export { ChatHistoryProvider, useChatHistory } from './contexts/ChatHistoryContext';
export type { Message, Conversation } from './contexts/ChatHistoryContext';

// Re-export utils
export { api } from './utils/api';
