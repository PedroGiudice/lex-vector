/**
 * CCui Legal AI Assistant - TypeScript Declarations
 */

import { FC, ReactNode } from 'react';

interface CCuiHeaderProps {
  projectPath?: string;
  currentModel?: string;
  onSettingsClick?: () => void;
  onSearchClick?: () => void;
}

interface CCuiIconRailProps {
  activeView?: string;
  onViewChange?: (view: string) => void;
  onSettingsClick?: () => void;
}

interface Session {
  id: string;
  title: string;
  updatedAt: string;
  createdAt?: string;
}

interface CCuiSidebarProps {
  sessions?: Session[];
  activeSessionId?: string | null;
  onSessionSelect?: (sessionId: string) => void;
  onNewChat?: () => void;
}

interface CCuiStatusBarProps {
  isProcessing?: boolean;
  contextPercent?: number;
  encoding?: string;
  language?: string;
}

interface CCuiCodeBlockProps {
  code: string;
  language?: string;
  isStreaming?: boolean;
}

interface CCuiThinkingBlockProps {
  content: string;
  isStreaming?: boolean;
  label?: string;
  duration?: number;
}

interface CCuiChatInputProps {
  onSend?: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
  onActionsClick?: () => void;
  onHistoryClick?: () => void;
}

interface Message {
  id?: string | number;
  role: 'user' | 'assistant';
  content: string;
  type?: 'text' | 'thought';
  label?: string;
  duration?: number;
  isStreaming?: boolean;
}

interface CCuiMessageProps {
  message: Message;
  isStreaming?: boolean;
}

interface CCuiLayoutProps {
  projectPath?: string;
  currentModel?: string;
  sessions?: Session[];
  activeSessionId?: string | null;
  messages?: Message[];
  isProcessing?: boolean;
  contextPercent?: number;
  onSessionSelect?: (sessionId: string) => void;
  onNewChat?: () => void;
  onSendMessage?: (content: string) => void;
  onSettingsClick?: () => void;
  children?: ReactNode;
}

export const CCuiHeader: FC<CCuiHeaderProps>;
export const CCuiIconRail: FC<CCuiIconRailProps>;
export const CCuiSidebar: FC<CCuiSidebarProps>;
export const CCuiStatusBar: FC<CCuiStatusBarProps>;
export const CCuiCodeBlock: FC<CCuiCodeBlockProps>;
export const CCuiThinkingBlock: FC<CCuiThinkingBlockProps>;
export const CCuiChatInput: FC<CCuiChatInputProps>;
export const CCuiMessage: FC<CCuiMessageProps>;
export const CCuiLayout: FC<CCuiLayoutProps>;
