import React, { useState, useEffect, useRef, useLayoutEffect, useCallback } from 'react';
import {
  ArrowUp,
  Sparkles,
  Check,
  Copy,
  ChevronDown,
  ChevronRight,
  Command,
  History,
  Info,
  Plus,
  Trash2,
  X,
  MessageSquare,
  FileText,
  FileEdit,
  Terminal,
  Search,
  FolderSearch,
  Globe,
  Link,
  ListTodo,
  Zap,
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react';
import { useWebSocket } from './contexts/WebSocketContext';
import { ErrorBanner, type ErrorType } from './ErrorBanner';
import { ConnectionStatus } from './ConnectionStatus';
import {
  useChatHistory,
  type Message as HistoryMessage,
  type Conversation,
} from './contexts/ChatHistoryContext';
import { ReactorSpinner, PhyllotaxisSpinner } from './Spinners';

// Working directory for Claude CLI (configurable)
const WORKING_DIR =
  import.meta.env.VITE_CLAUDE_CWD || '/home/cmr-auto/claude-work/repos/lex-vector';

// Extend Window interface for Prism
declare global {
  interface Window {
    Prism?: {
      highlightElement: (element: HTMLElement) => void;
    };
  }
}

// Tool call state
type ToolStatus = 'pending' | 'running' | 'completed' | 'failed';

// Tool call data stored in messages
interface ToolCall {
  id: string;
  name: string;
  input: Record<string, unknown>;
  status: ToolStatus;
  result?: string;
  isError?: boolean;
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  isStreaming?: boolean;
  isError?: boolean;
  isSystem?: boolean;
  toolCalls?: ToolCall[];
}

interface CodeBlockProps {
  code: string;
  language?: string;
  isStreaming?: boolean;
}

const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language = 'javascript',
  isStreaming = false,
}) => {
  const [copied, setCopied] = useState(false);
  const codeRef = useRef<HTMLElement>(null);

  useLayoutEffect(() => {
    if (window.Prism && codeRef.current) {
      window.Prism.highlightElement(codeRef.current);
    }
  }, [code, language]);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-5 rounded-lg overflow-hidden border border-[#27272a] bg-[#050505] shadow-lg">
      <div className="flex items-center justify-between px-5 py-2.5 bg-[#121212] border-b border-[#27272a]">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-[#d97757] font-mono lowercase font-bold">{language}</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center space-x-2 text-xs text-[#b5b5b5] hover:text-[#e3e1de] transition-colors"
        >
          {copied ? <Check className="w-4 h-4 text-[#d97757]" /> : <Copy className="w-4 h-4" />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
      <div className="relative">
        <pre className="!m-0 !p-6 !bg-[#050505] !text-base overflow-x-auto custom-scrollbar font-mono leading-relaxed">
          <code ref={codeRef} className={`language-${language} !bg-transparent !text-shadow-none`}>
            {code}
          </code>
          {isStreaming && (
            <span className="inline-block w-2.5 h-5 bg-[#d97757] align-middle ml-1.5 animate-pulse"></span>
          )}
        </pre>
      </div>
    </div>
  );
};

interface ThinkingBlockProps {
  content: string;
  isStreaming?: boolean;
  label?: string;
  duration?: string;
}

const ThinkingBlock: React.FC<ThinkingBlockProps> = ({
  content,
  isStreaming,
  label = 'Reasoning',
  duration,
}) => {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="mb-5 group border border-[#27272a] rounded-lg bg-[#080808] overflow-hidden">
      <div
        className="flex items-center gap-3 cursor-pointer select-none px-5 py-3 bg-[#111] hover:bg-[#151515] transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="w-5 h-5 flex items-center justify-center">
          {isStreaming ? (
            <PhyllotaxisSpinner className="w-full h-full" />
          ) : isOpen ? (
            <ChevronDown className="w-5 h-5 text-[#b5b5b5]" />
          ) : (
            <ChevronRight className="w-5 h-5 text-[#b5b5b5]" />
          )}
        </div>
        <span
          className={`text-sm font-mono font-medium tracking-tight ${isStreaming ? 'text-[#e3e1de]' : 'text-[#b5b5b5]'}`}
        >
          {label}
        </span>
        {duration && <span className="text-sm text-[#888] font-mono ml-auto">{duration}</span>}
      </div>

      {isOpen && (
        <div className="px-5 py-4">
          <div className="text-base text-[#c0c0c0] font-mono leading-relaxed whitespace-pre-wrap">
            {content}
            {isStreaming && (
              <span className="inline-block w-2.5 h-5 bg-[#d97757] ml-1 animate-pulse" />
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Tool icon mapping
const getToolIcon = (toolName: string): React.ReactNode => {
  const iconClass = 'w-4 h-4';
  switch (toolName.toLowerCase()) {
    case 'read':
      return <FileText className={iconClass} />;
    case 'write':
    case 'edit':
      return <FileEdit className={iconClass} />;
    case 'bash':
      return <Terminal className={iconClass} />;
    case 'grep':
      return <Search className={iconClass} />;
    case 'glob':
      return <FolderSearch className={iconClass} />;
    case 'websearch':
      return <Globe className={iconClass} />;
    case 'webfetch':
      return <Link className={iconClass} />;
    case 'todowrite':
      return <ListTodo className={iconClass} />;
    case 'skill':
      return <Zap className={iconClass} />;
    default:
      return <Terminal className={iconClass} />;
  }
};

// Format tool input for display
const formatToolInput = (toolName: string, input: Record<string, unknown>): string => {
  switch (toolName.toLowerCase()) {
    case 'read':
      return (input.file_path as string) || '';
    case 'write':
    case 'edit':
      return (input.file_path as string) || '';
    case 'bash':
      return (input.command as string) || '';
    case 'grep':
      return `"${input.pattern || ''}" in ${input.path || '.'}`;
    case 'glob':
      return `${input.pattern || ''} in ${input.path || '.'}`;
    case 'websearch':
      return (input.query as string) || '';
    case 'webfetch':
      return (input.url as string) || '';
    default:
      return JSON.stringify(input, null, 2);
  }
};

// ToolCallBlock component
interface ToolCallBlockProps {
  toolCall: ToolCall;
  isExpanded?: boolean;
}

const ToolCallBlock: React.FC<ToolCallBlockProps> = ({
  toolCall,
  isExpanded: defaultExpanded = false,
}) => {
  const [isOpen, setIsOpen] = useState(defaultExpanded);
  const [showResult, setShowResult] = useState(false);

  const statusIcon = () => {
    switch (toolCall.status) {
      case 'pending':
        return <div className="w-4 h-4 rounded-full border-2 border-[#555]" />;
      case 'running':
        return <Loader2 className="w-4 h-4 text-[#d97757] animate-spin" />;
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  const statusColor = () => {
    switch (toolCall.status) {
      case 'pending':
        return 'text-[#888]';
      case 'running':
        return 'text-[#d97757]';
      case 'completed':
        return 'text-green-500';
      case 'failed':
        return 'text-red-500';
      default:
        return 'text-[#888]';
    }
  };

  const displayInput = formatToolInput(toolCall.name, toolCall.input);
  const hasResult = toolCall.result && toolCall.result.length > 0;

  return (
    <div className="mb-3 group border border-[#27272a] rounded-lg bg-[#080808] overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center gap-3 cursor-pointer select-none px-4 py-2.5 bg-[#111] hover:bg-[#151515] transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="w-5 h-5 flex items-center justify-center">
          {isOpen ? (
            <ChevronDown className="w-4 h-4 text-[#b5b5b5]" />
          ) : (
            <ChevronRight className="w-4 h-4 text-[#b5b5b5]" />
          )}
        </div>

        <div className="flex items-center gap-2 text-[#d97757]">
          {getToolIcon(toolCall.name)}
          <span className="text-sm font-mono font-semibold">{toolCall.name}</span>
        </div>

        <div className="flex-1 min-w-0">
          <span className="text-sm text-[#888] font-mono truncate block">
            {displayInput.length > 60 ? displayInput.substring(0, 57) + '...' : displayInput}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {statusIcon()}
          <span className={`text-xs font-mono ${statusColor()}`}>{toolCall.status}</span>
        </div>
      </div>

      {/* Expanded Input Details */}
      {isOpen && (
        <div className="px-4 py-3 border-t border-[#1a1a1a]">
          <div className="text-xs text-[#666] font-mono mb-1">Input:</div>
          <pre className="text-sm text-[#c0c0c0] font-mono leading-relaxed whitespace-pre-wrap bg-[#050505] p-3 rounded border border-[#1a1a1a] overflow-x-auto custom-scrollbar">
            {typeof toolCall.input === 'object'
              ? JSON.stringify(toolCall.input, null, 2)
              : String(toolCall.input)}
          </pre>

          {/* Result section (collapsible) */}
          {hasResult && (
            <div className="mt-3">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowResult(!showResult);
                }}
                className="flex items-center gap-2 text-xs text-[#888] font-mono hover:text-[#b5b5b5] transition-colors"
              >
                {showResult ? (
                  <ChevronDown className="w-3 h-3" />
                ) : (
                  <ChevronRight className="w-3 h-3" />
                )}
                <span>Result ({toolCall.isError ? 'error' : 'success'})</span>
              </button>

              {showResult && (
                <div
                  className={`mt-2 p-3 rounded border ${toolCall.isError ? 'border-red-500/30 bg-red-500/5' : 'border-[#1a1a1a] bg-[#050505]'}`}
                >
                  <pre
                    className={`text-sm font-mono leading-relaxed whitespace-pre-wrap overflow-x-auto custom-scrollbar ${toolCall.isError ? 'text-red-400' : 'text-[#c0c0c0]'}`}
                  >
                    {toolCall.result}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// History Panel Component
interface HistoryPanelProps {
  isOpen: boolean;
  onClose: () => void;
  conversations: Conversation[];
  currentConversationId: string | null;
  onSelectConversation: (conversation: Conversation) => void;
  onDeleteConversation: (id: string) => void;
  onNewChat: () => void;
}

const HistoryPanel: React.FC<HistoryPanelProps> = ({
  isOpen,
  onClose,
  conversations,
  currentConversationId,
  onSelectConversation,
  onDeleteConversation,
  onNewChat,
}) => {
  // Format date for display
  const formatDate = (isoString: string): string => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  // Get last message preview
  const getPreview = (conversation: Conversation): string => {
    const lastMessage = conversation.messages[conversation.messages.length - 1];
    if (lastMessage) {
      const content = lastMessage.content.trim();
      if (content.length <= 60) return content;
      return content.substring(0, 57) + '...';
    }
    return 'No messages';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Panel */}
      <div className="relative w-full max-w-md bg-[#0a0a0a] border-l border-[#27272a] h-full flex flex-col animate-in slide-in-from-right duration-300">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#27272a]">
          <div className="flex items-center gap-3">
            <History className="w-5 h-5 text-[#d97757]" />
            <h2 className="text-lg font-semibold text-[#e3e1de]">Chat History</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-[#1a1a1a] transition-colors text-[#888] hover:text-[#e3e1de]"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="px-4 py-3 border-b border-[#27272a]">
          <button
            onClick={() => {
              onNewChat();
              onClose();
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[#d97757]/10 border border-[#d97757]/30 text-[#d97757] hover:bg-[#d97757]/20 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span className="font-medium">New Chat</span>
          </button>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {conversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-6">
              <MessageSquare className="w-12 h-12 text-[#333] mb-4" />
              <p className="text-[#666] text-sm">No conversations yet</p>
              <p className="text-[#555] text-xs mt-1">Start a chat to see your history here</p>
            </div>
          ) : (
            <div className="py-2">
              {conversations.map((conversation) => (
                <div
                  key={conversation.id}
                  className={`group px-4 py-3 mx-2 my-1 rounded-lg cursor-pointer transition-colors ${
                    currentConversationId === conversation.id
                      ? 'bg-[#d97757]/10 border border-[#d97757]/30'
                      : 'hover:bg-[#1a1a1a] border border-transparent'
                  }`}
                  onClick={() => {
                    onSelectConversation(conversation);
                    onClose();
                  }}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium text-[#e3e1de] truncate">
                        {conversation.title}
                      </h3>
                      <p className="text-xs text-[#666] mt-1 truncate">
                        {getPreview(conversation)}
                      </p>
                      <p className="text-xs text-[#555] mt-2">
                        {formatDate(conversation.updatedAt)}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteConversation(conversation.id);
                      }}
                      className="p-1.5 rounded opacity-0 group-hover:opacity-100 hover:bg-[#2a2a2a] text-[#666] hover:text-red-400 transition-all"
                      title="Delete conversation"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-[#27272a] text-center">
          <p className="text-xs text-[#555]">{conversations.length} / 50 conversations stored</p>
        </div>
      </div>
    </div>
  );
};

// Error Message Content with Retry and Copy
interface ErrorMessageContentProps {
  content: string;
  onRetry?: () => void;
  canRetry?: boolean;
}

const ErrorMessageContent: React.FC<ErrorMessageContentProps> = ({
  content,
  onRetry,
  canRetry = false,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-3">
      <div className="p-4 rounded-lg bg-red-500/5 border border-red-500/20">
        <pre className="text-sm text-red-400 font-mono whitespace-pre-wrap overflow-x-auto">
          {content}
        </pre>
      </div>
      <div className="flex items-center gap-2">
        {canRetry && onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium
              bg-[#d97757]/10 text-[#d97757] hover:bg-[#d97757]/20 transition-colors
              border border-[#d97757]/30"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry Message
          </button>
        )}
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium
            bg-[#1a1a1a] text-[#888] hover:text-[#e3e1de] transition-colors
            border border-[#27272a]"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-green-500" />
              Copied
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              Copy Error
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default function CCuiChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [compactMode, setCompactMode] = useState(false);
  const [historyPanelOpen, setHistoryPanelOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lastUserMessageRef = useRef<string>('');

  const {
    sendMessage: sendWsMessage,
    lastMessage,
    connectionStatus,
    lastError,
    retryCount,
    maxRetries,
    retry: retryConnection,
    clearError,
    isConnected,
  } = useWebSocket();

  // Derive error banner state from connection status
  const showConnectionError =
    lastError &&
    (connectionStatus === 'error' ||
      connectionStatus === 'disconnected' ||
      connectionStatus === 'disabled');

  // Get error type for banner
  const getErrorType = (): ErrorType => {
    if (!lastError) return 'unknown';
    return lastError.type;
  };

  // Check if input should be disabled
  const isInputDisabled = isTyping || !isConnected;

  // Get placeholder text based on connection status
  const getPlaceholderText = (): string => {
    if (isTyping) return 'Thinking...';
    if (connectionStatus === 'connecting') {
      return retryCount > 0
        ? `Reconnecting... (${retryCount}/${maxRetries})`
        : 'Connecting to Claude...';
    }
    if (connectionStatus === 'disconnected' || connectionStatus === 'error') {
      return 'Connection lost. Click retry or check backend...';
    }
    if (connectionStatus === 'disabled') {
      return 'Backend unavailable. Running in offline mode...';
    }
    return 'Describe your task or enter a command...';
  };

  // Chat history integration
  const {
    conversations,
    currentConversationId,
    saveConversation,
    deleteConversation,
    setCurrentConversationId,
    startNewConversation,
  } = useChatHistory();

  // Handle incoming WS messages (claudecodeui backend format)
  useEffect(() => {
    if (!lastMessage) return;

    const wsMessage = lastMessage as unknown as {
      type: string;
      data?: {
        type: string;
        id?: string;
        name?: string;
        input?: Record<string, unknown>;
        tool_use_id?: string;
        content?: string | Array<{ type: string; text?: string }>;
        is_error?: boolean;
        delta?: { text?: string };
        message?: { content?: Array<{ type: string; text?: string }> };
      };
      error?: string;
    };

    // Handle claude-response messages (streaming content)
    if (wsMessage.type === 'claude-response' && wsMessage.data) {
      const data = wsMessage.data;

      // Handle tool_use - Claude is invoking a tool
      if (data.type === 'tool_use' && data.id && data.name) {
        const newToolCall: ToolCall = {
          id: data.id,
          name: data.name,
          input: data.input || {},
          status: 'running',
        };

        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1];
          // Append to existing assistant message or create new one
          if (lastMsg && lastMsg.role === 'assistant') {
            const existingToolCalls = lastMsg.toolCalls || [];
            return [
              ...prev.slice(0, -1),
              {
                ...lastMsg,
                isStreaming: true,
                toolCalls: [...existingToolCalls, newToolCall],
              },
            ];
          } else {
            return [
              ...prev,
              {
                id: Date.now().toString(),
                role: 'assistant',
                content: '',
                isStreaming: true,
                toolCalls: [newToolCall],
              },
            ];
          }
        });
        setIsTyping(true);
      }

      // Handle tool_result - Result from tool execution
      if (data.type === 'tool_result' && data.tool_use_id) {
        const resultContent =
          typeof data.content === 'string'
            ? data.content
            : Array.isArray(data.content)
              ? data.content.map((c) => c.text || '').join('')
              : '';

        setMessages((prev) => {
          return prev.map((msg) => {
            if (msg.role === 'assistant' && msg.toolCalls) {
              const updatedToolCalls = msg.toolCalls.map((tc) => {
                if (tc.id === data.tool_use_id) {
                  return {
                    ...tc,
                    status: (data.is_error ? 'failed' : 'completed') as ToolStatus,
                    result:
                      resultContent.length > 2000
                        ? resultContent.substring(0, 2000) + '\n... (truncated)'
                        : resultContent,
                    isError: data.is_error,
                  };
                }
                return tc;
              });
              return { ...msg, toolCalls: updatedToolCalls };
            }
            return msg;
          });
        });
      }

      // Handle streaming deltas (content_block_delta)
      if (data.type === 'content_block_delta' && data.delta?.text) {
        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isStreaming) {
            return [
              ...prev.slice(0, -1),
              { ...lastMsg, content: lastMsg.content + data.delta!.text },
            ];
          } else {
            return [
              ...prev,
              {
                id: Date.now().toString(),
                role: 'assistant',
                content: data.delta!.text!,
                isStreaming: true,
              },
            ];
          }
        });
        setIsTyping(true);
      }

      // Handle end of content block
      if (data.type === 'content_block_stop') {
        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isStreaming) {
            return [...prev.slice(0, -1), { ...lastMsg, isStreaming: false }];
          }
          return prev;
        });
      }

      // Handle assistant messages with content array
      if (data.type === 'assistant' && data.message?.content) {
        const textContent = data.message.content
          .filter((c) => c.type === 'text')
          .map((c) => c.text || '')
          .join('');
        if (textContent) {
          setMessages((prev) => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isStreaming) {
              return [...prev.slice(0, -1), { ...lastMsg, content: lastMsg.content + textContent }];
            } else {
              return [
                ...prev,
                {
                  id: Date.now().toString(),
                  role: 'assistant',
                  content: textContent,
                  isStreaming: true,
                },
              ];
            }
          });
          setIsTyping(true);
        }
      }
    }

    // Handle completion
    else if (wsMessage.type === 'claude-complete') {
      setIsTyping(false);
      setMessages((prev) => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg && lastMsg.role === 'assistant') {
          // Mark any running tool calls as completed
          const updatedToolCalls = lastMsg.toolCalls?.map((tc) =>
            tc.status === 'running' ? { ...tc, status: 'completed' as ToolStatus } : tc
          );
          return [
            ...prev.slice(0, -1),
            { ...lastMsg, isStreaming: false, toolCalls: updatedToolCalls },
          ];
        }
        return prev;
      });
    }

    // Handle errors
    else if (wsMessage.type === 'claude-error') {
      setIsTyping(false);
      setMessages((prev) => {
        // Mark any running tool calls as failed
        const lastMsg = prev[prev.length - 1];
        if (lastMsg && lastMsg.role === 'assistant' && lastMsg.toolCalls) {
          const updatedToolCalls = lastMsg.toolCalls.map((tc) =>
            tc.status === 'running' ? { ...tc, status: 'failed' as ToolStatus } : tc
          );
          return [
            ...prev.slice(0, -1),
            { ...lastMsg, isStreaming: false, toolCalls: updatedToolCalls },
            {
              id: Date.now().toString(),
              role: 'assistant',
              content: `Error: ${wsMessage.error || 'Unknown error'}`,
              isError: true,
            },
          ];
        }
        return [
          ...prev,
          {
            id: Date.now().toString(),
            role: 'assistant',
            content: `Error: ${wsMessage.error || 'Unknown error'}`,
            isError: true,
          },
        ];
      });
    }
  }, [lastMessage]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Auto-save conversation when messages change (only when not streaming)
  useEffect(() => {
    // Only save when we have messages and are not currently streaming
    if (messages.length > 0 && !isTyping) {
      // Cast Message[] to HistoryMessage[] (they're compatible)
      saveConversation(messages as HistoryMessage[], currentConversationId);
    }
  }, [messages, isTyping, saveConversation, currentConversationId]);

  // Handle new chat
  const handleNewChat = useCallback(() => {
    setMessages([]);
    startNewConversation();
  }, [startNewConversation]);

  // Handle selecting a conversation from history
  const handleSelectConversation = useCallback(
    (conversation: Conversation) => {
      setCurrentConversationId(conversation.id);
      // Cast HistoryMessage[] to Message[] (they're compatible)
      setMessages(conversation.messages as Message[]);
    },
    [setCurrentConversationId]
  );

  // Handle deleting a conversation
  const handleDeleteConversation = useCallback(
    (id: string) => {
      deleteConversation(id);
      // If we deleted the current conversation, clear messages
      if (currentConversationId === id) {
        setMessages([]);
      }
    },
    [deleteConversation, currentConversationId]
  );

  const handleSlashCommand = (cmd: string, _args: string[]): boolean => {
    switch (cmd.toLowerCase()) {
      case '/clear':
      case '/cls':
        setMessages([]);
        return true;
      case '/help':
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: 'system',
            content:
              'Available commands:\n/clear - Clear chat history\n/compact - Toggle compact mode\n/help - Show this help message',
            isSystem: true,
          },
        ]);
        return true;
      case '/compact':
        setCompactMode(!compactMode);
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: 'system',
            content: `Compact mode ${!compactMode ? 'enabled' : 'disabled'}.`,
            isSystem: true,
          },
        ]);
        return true;
      default:
        return false;
    }
  };

  const handleSendMessage = async () => {
    if (input.trim() === '' || isTyping) return;

    // Check connection before sending
    if (!isConnected) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: 'system',
          content:
            'Cannot send message: not connected to backend. Please wait for reconnection or click retry.',
          isSystem: true,
          isError: true,
        },
      ]);
      return;
    }

    const trimmedInput = input.trim();

    // Check for slash commands
    if (trimmedInput.startsWith('/')) {
      const [cmd, ...args] = trimmedInput.split(' ');
      if (handleSlashCommand(cmd, args)) {
        setInput('');
        return;
      }
    }

    // Store for retry functionality
    lastUserMessageRef.current = trimmedInput;

    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: trimmedInput };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // Send message via WebSocket in claudecodeui backend format
    sendWsMessage({
      type: 'claude-command',
      command: trimmedInput,
      options: {
        cwd: WORKING_DIR,
        permissionMode: 'bypassPermissions',
      },
    });
  };

  // Retry last message (used for error recovery)
  const handleRetryLastMessage = useCallback(() => {
    if (!lastUserMessageRef.current || isTyping || !isConnected) return;

    setIsTyping(true);
    sendWsMessage({
      type: 'claude-command',
      command: lastUserMessageRef.current,
      options: {
        cwd: WORKING_DIR,
        permissionMode: 'bypassPermissions',
      },
    });
  }, [isTyping, isConnected, sendWsMessage]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Render tool calls for a message
  const renderToolCalls = (message: Message): React.ReactNode[] => {
    if (!message.toolCalls || message.toolCalls.length === 0) {
      return [];
    }

    return message.toolCalls.map((toolCall) => (
      <ToolCallBlock
        key={`${message.id}-tool-${toolCall.id}`}
        toolCall={toolCall}
        isExpanded={toolCall.status === 'running' || toolCall.status === 'failed'}
      />
    ));
  };

  const renderMessageContent = (message: Message) => {
    const content = message.content;
    const elements: React.ReactNode[] = [];

    // First render any tool calls
    const toolCallElements = renderToolCalls(message);
    if (toolCallElements.length > 0) {
      elements.push(
        <div key={`${message.id}-tools`} className="mb-4">
          {toolCallElements}
        </div>
      );
    }

    // Then render the text content
    if (content && content.trim()) {
      const parts = content.split(/(```[\w\s]*?\n[\s\S]*?```)/g);

      const textElements = parts
        .map((part, index) => {
          if (part.startsWith('```') && part.endsWith('```')) {
            const match = part.match(/```(\w+)?\n([\s\S]*?)```/);
            if (match) {
              const [, language = 'text', code] = match;
              const isStreamingThisBlock = message.isStreaming && index === parts.length - 1;
              return (
                <CodeBlock
                  key={message.id + '-code-' + index}
                  code={code.trim()}
                  language={language.trim()}
                  isStreaming={isStreamingThisBlock}
                />
              );
            }
          }

          if (part.trim().startsWith('THINKING:')) {
            const thinkingContent = part.substring('THINKING:'.length).trim();
            const isStreamingThisBlock = message.isStreaming && index === parts.length - 1;
            return (
              <ThinkingBlock
                key={message.id + '-thinking-' + index}
                content={thinkingContent}
                label="Reasoning"
                isStreaming={isStreamingThisBlock}
              />
            );
          }

          // Skip empty parts
          if (!part.trim()) return null;

          const isStreamingThisText = message.isStreaming && index === parts.length - 1;
          return (
            <p
              key={message.id + '-text-' + index}
              className={`leading-relaxed whitespace-pre-wrap font-sans text-[#e3e1de] ${compactMode ? 'text-sm' : 'text-lg'}`}
            >
              {part}
              {isStreamingThisText && (
                <span className="inline-block w-3 h-6 bg-[#d97757] align-bottom ml-1.5 animate-pulse"></span>
              )}
            </p>
          );
        })
        .filter(Boolean);

      elements.push(...textElements);
    }

    // Show streaming indicator if message is streaming but has no content yet
    if (
      message.isStreaming &&
      !content?.trim() &&
      (!message.toolCalls || message.toolCalls.length === 0)
    ) {
      elements.push(
        <div key={`${message.id}-streaming`} className="flex items-center gap-2">
          <Loader2 className="w-4 h-4 text-[#d97757] animate-spin" />
          <span className="text-sm text-[#888]">Processing...</span>
        </div>
      );
    }

    return elements;
  };

  return (
    <div className="flex flex-col h-full bg-[#000000]">
      {/* Connection Error Banner */}
      {showConnectionError && lastError && (
        <div className="flex-none px-8 pt-4">
          <ErrorBanner
            type={getErrorType()}
            message={lastError.message}
            onRetry={retryConnection}
            onDismiss={clearError}
            autoDismiss={!['connection', 'server'].includes(lastError.type)}
            autoDismissDelay={8000}
          />
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-8 flex flex-col space-y-10">
        {messages.length === 0 && !isTyping ? (
          <div className="flex flex-col items-center justify-center h-[75%] text-center select-none animate-in fade-in zoom-in-95 duration-500">
            {/* Reactor Spinner for Empty State */}
            <div className="mb-8 opacity-90">
              <ReactorSpinner />
            </div>

            {/* Empty State Title */}
            <h1 className="text-4xl text-[#c0c0c0] font-serif tracking-wide mb-4">
              Claude Code CLI
            </h1>
            <p className="text-sm text-[#888] font-medium tracking-[0.2em] uppercase">
              Ready for input
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in duration-300 slide-in-from-bottom-3`}
            >
              <div
                className={`max-w-[85%] ${
                  msg.role === 'user'
                    ? 'bg-[#d97757]/10 border border-[#d97757]/20 shadow-[0_0_20px_rgba(217,119,87,0.05)]'
                    : msg.isError
                      ? 'bg-red-500/5 border border-red-500/30'
                      : 'bg-[#000000]'
                } rounded-xl p-3`}
              >
                {msg.role === 'assistant' ? (
                  <div className="flex gap-5">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center flex-none mt-1 shadow-sm ${
                        msg.isError
                          ? 'bg-red-500/10 border border-red-500/30'
                          : 'bg-[#111] border border-[#27272a]'
                      }`}
                    >
                      {msg.isError ? (
                        <AlertTriangle className="w-5 h-5 text-red-500" />
                      ) : (
                        <Sparkles className="w-5 h-5 text-[#d97757]" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-3">
                        <span
                          className={`text-base font-bold ${msg.isError ? 'text-red-400' : 'text-[#e3e1de]'}`}
                        >
                          {msg.isError ? 'Error' : 'Claude'}
                        </span>
                        <span className="text-sm text-[#888] font-mono">
                          {new Date().toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                      {msg.isError ? (
                        <ErrorMessageContent
                          content={msg.content}
                          onRetry={handleRetryLastMessage}
                          canRetry={isConnected && !isTyping && !!lastUserMessageRef.current}
                        />
                      ) : (
                        renderMessageContent(msg)
                      )}
                    </div>
                  </div>
                ) : msg.isSystem ? (
                  <div
                    className={`px-6 py-4 rounded-2xl text-lg leading-relaxed ${
                      msg.isError
                        ? 'bg-red-500/10 text-red-400 border border-red-500/30'
                        : 'bg-[#111] text-[#888] border border-[#27272a]'
                    }`}
                  >
                    <p className="whitespace-pre-wrap font-sans">{msg.content}</p>
                  </div>
                ) : (
                  <div className="px-6 py-4 rounded-2xl bg-[#1a1a1a] text-[#e3e1de] border border-[#27272a] text-lg leading-relaxed">
                    <p className="whitespace-pre-wrap font-sans">{msg.content}</p>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {isTyping && (
          <div className="flex justify-start">
            <div className="flex gap-5">
              <div className="w-10 h-10 rounded-full bg-[#111] border border-[#27272a] flex items-center justify-center flex-none mt-1">
                <Sparkles className="w-5 h-5 text-[#d97757]" />
              </div>
              <div className="flex items-center gap-4 mt-2">
                {/* Phyllotaxis Spinner for Loading */}
                <div className="w-8 h-8">
                  <PhyllotaxisSpinner className="w-full h-full" />
                </div>
                <span className="text-base text-[#888] animate-pulse">Thinking...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="flex-none p-8 w-full max-w-5xl mx-auto z-30">
        {/* Connection Status Indicator */}
        <div className="flex justify-end mb-2">
          <ConnectionStatus
            status={connectionStatus}
            retryCount={retryCount}
            maxRetries={maxRetries}
            onRetry={retryConnection}
          />
        </div>

        <div
          className={`
             relative flex items-center gap-5 bg-[#0a0a0a] border rounded-xl px-6 py-5 transition-all duration-300
             ${
               isInputDisabled
                 ? 'border-[#27272a] opacity-70 cursor-not-allowed'
                 : 'border-[#d97757]/40 focus-within:border-[#d97757] shadow-[0_0_30px_rgba(0,0,0,0.7)] focus-within:shadow-[0_0_40px_rgba(217,119,87,0.1)]'
             }
             ${!isConnected && !isTyping ? 'border-red-500/30' : ''}
        `}
        >
          <span
            className={`font-mono text-xl font-bold select-none ${isConnected ? 'text-[#d97757]' : 'text-[#555]'}`}
          >{`>_`}</span>
          <textarea
            ref={textareaRef}
            className={`flex-1 resize-none overflow-hidden max-h-48 bg-transparent focus:outline-none placeholder-[#666] custom-scrollbar font-mono text-lg leading-relaxed ${
              isInputDisabled ? 'text-[#888] cursor-not-allowed' : 'text-[#e3e1de]'
            }`}
            placeholder={getPlaceholderText()}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isInputDisabled}
            rows={1}
            autoFocus
          />
          <button
            onClick={handleSendMessage}
            className={`transition-all duration-200 p-2.5 rounded-lg ${
              input.trim() === '' || isInputDisabled
                ? 'text-[#333]'
                : 'text-[#d97757] hover:bg-[#d97757]/10 hover:scale-105'
            }`}
            disabled={input.trim() === '' || isInputDisabled}
            aria-label="Send message"
          >
            <ArrowUp className="w-7 h-7 stroke-[2.5px]" />
          </button>
        </div>

        {/* Helper Links */}
        <div className="flex justify-center items-center gap-10 mt-5 text-sm text-[#666] font-medium tracking-wide select-none">
          <button className="flex items-center gap-2.5 hover:text-[#b5b5b5] transition-colors group">
            <Command className="w-4 h-4 group-hover:text-[#d97757]" />
            <span>Actions</span>
          </button>
          <button
            onClick={() => setHistoryPanelOpen(true)}
            className="flex items-center gap-2.5 hover:text-[#b5b5b5] transition-colors group"
          >
            <History className="w-4 h-4 group-hover:text-[#d97757]" />
            <span>History</span>
            {conversations.length > 0 && (
              <span className="text-xs text-[#d97757] bg-[#d97757]/10 px-1.5 py-0.5 rounded-full">
                {conversations.length}
              </span>
            )}
          </button>
          <button className="flex items-center gap-2.5 hover:text-[#b5b5b5] transition-colors group">
            <Info className="w-4 h-4 group-hover:text-[#d97757]" />
            <span>Guide</span>
          </button>
        </div>
      </div>

      {/* History Panel */}
      <HistoryPanel
        isOpen={historyPanelOpen}
        onClose={() => setHistoryPanelOpen(false)}
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
        onNewChat={handleNewChat}
      />
    </div>
  );
}
