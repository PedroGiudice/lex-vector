import React, { useState, useEffect, useRef, useLayoutEffect, useCallback } from 'react';
import {
  ArrowUp,
  Check,
  Copy,
  ChevronDown,
  ChevronRight,
  Command,
  History,
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
  Sparkles,
  CornerDownLeft,
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

const WORKING_DIR =
  import.meta.env.VITE_CLAUDE_CWD || '/home/cmr-auto/claude-work/repos/lex-vector';

declare global {
  interface Window {
    Prism?: {
      highlightElement: (element: HTMLElement) => void;
    };
  }
}

// ============================================================
// Types
// ============================================================

type ToolStatus = 'pending' | 'running' | 'completed' | 'failed';

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

// ============================================================
// CodeBlock
// ============================================================

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
    <div className="relative group my-4 overflow-hidden border border-[#231d15] bg-[#110e0b]">
      <div className="flex items-center justify-between px-4 py-2 bg-[#161210] border-b border-[#231d15]">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-[#b85a30]/60" />
          <span className="lv-mono text-[10px] text-[#b85a30] tracking-wider lowercase font-medium">
            {language}
          </span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-[10px] lv-mono text-[#5a4a32] hover:text-[#a0603a] transition-colors"
          aria-label={copied ? 'Copiado' : 'Copiar codigo'}
        >
          {copied ? <Check className="w-3 h-3 text-[#5a7a3a]" /> : <Copy className="w-3 h-3" />}
          <span>{copied ? 'Copiado' : 'Copiar'}</span>
        </button>
      </div>
      <div className="relative">
        <pre className="!m-0 !p-5 !bg-[#110e0b] !text-sm overflow-x-auto lv-scrollbar lv-mono leading-relaxed">
          <code ref={codeRef} className={`language-${language} !bg-transparent`}>
            {code}
          </code>
          {isStreaming && (
            <span className="inline-block w-2 h-4 bg-[#b85a30] align-middle ml-1 animate-pulse" />
          )}
        </pre>
      </div>
    </div>
  );
};

// ============================================================
// ThinkingBlock
// ============================================================

interface ThinkingBlockProps {
  content: string;
  isStreaming?: boolean;
  label?: string;
  duration?: string;
}

const ThinkingBlock: React.FC<ThinkingBlockProps> = ({
  content,
  isStreaming,
  label = 'Raciocinio',
  duration,
}) => {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="mb-4 group border border-[#231d15] bg-[#110e0b] overflow-hidden">
      <div
        className="flex items-center gap-2.5 cursor-pointer select-none px-4 py-2.5 bg-[#141009] hover:bg-[#181510] transition-colors"
        onClick={() => setIsOpen(!isOpen)}
        role="button"
        tabIndex={0}
        aria-expanded={isOpen}
        onKeyDown={(e) => e.key === 'Enter' && setIsOpen(!isOpen)}
      >
        <div className="w-4 h-4 flex items-center justify-center">
          {isStreaming ? (
            <PhyllotaxisSpinner className="w-full h-full" />
          ) : isOpen ? (
            <ChevronDown className="w-3.5 h-3.5 text-[#5a4a32]" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-[#5a4a32]" />
          )}
        </div>
        <span
          className={`text-[11px] lv-mono tracking-wider ${isStreaming ? 'text-[#a0603a]' : 'text-[#5a4a32]'}`}
        >
          {label.toUpperCase()}
        </span>
        {duration && <span className="text-[10px] text-[#3e3222] lv-mono ml-auto">{duration}</span>}
      </div>

      {isOpen && (
        <div className="px-4 py-3 border-t border-[#1c1710]">
          <div className="text-[13px] text-[#9a8060] lv-mono leading-relaxed whitespace-pre-wrap">
            {content}
            {isStreaming && (
              <span className="inline-block w-2 h-4 bg-[#a0603a] ml-1 animate-pulse" />
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================
// Tool helpers
// ============================================================

const getToolIcon = (toolName: string): React.ReactNode => {
  const cls = 'w-3.5 h-3.5';
  switch (toolName.toLowerCase()) {
    case 'read':
      return <FileText className={cls} />;
    case 'write':
    case 'edit':
      return <FileEdit className={cls} />;
    case 'bash':
      return <Terminal className={cls} />;
    case 'grep':
      return <Search className={cls} />;
    case 'glob':
      return <FolderSearch className={cls} />;
    case 'websearch':
      return <Globe className={cls} />;
    case 'webfetch':
      return <Link className={cls} />;
    case 'todowrite':
      return <ListTodo className={cls} />;
    case 'skill':
      return <Zap className={cls} />;
    default:
      return <Terminal className={cls} />;
  }
};

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

// ============================================================
// ToolCallBlock
// ============================================================

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

  const statusConfig = {
    pending: {
      icon: <div className="w-3 h-3 rounded-full border border-[#3e3222]" />,
      color: 'text-[#5a4a32]',
      label: 'pendente',
    },
    running: {
      icon: <Loader2 className="w-3 h-3 text-[#b85a30] animate-spin" />,
      color: 'text-[#b85a30]',
      label: 'executando',
    },
    completed: {
      icon: <CheckCircle2 className="w-3 h-3 text-[#5a7a3a]" />,
      color: 'text-[#5a7a3a]',
      label: 'concluido',
    },
    failed: {
      icon: <XCircle className="w-3 h-3 text-[#8a3028]" />,
      color: 'text-[#8a3028]',
      label: 'falhou',
    },
  };

  const status = statusConfig[toolCall.status] || statusConfig.pending;
  const displayInput = formatToolInput(toolCall.name, toolCall.input);
  const hasResult = toolCall.result && toolCall.result.length > 0;

  return (
    <div className="mb-2 group border border-[#231d15] bg-[#110e0b] overflow-hidden">
      <div
        className="flex items-center gap-2.5 cursor-pointer select-none px-3 py-2 bg-[#141009] hover:bg-[#181510] transition-colors"
        onClick={() => setIsOpen(!isOpen)}
        role="button"
        tabIndex={0}
        aria-expanded={isOpen}
        onKeyDown={(e) => e.key === 'Enter' && setIsOpen(!isOpen)}
      >
        <div className="w-3.5 h-3.5 flex items-center justify-center text-[#5a4a32]">
          {isOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        </div>

        <div className="flex items-center gap-1.5 text-[#b85a30]">
          {getToolIcon(toolCall.name)}
          <span className="text-[11px] lv-mono font-medium">{toolCall.name}</span>
        </div>

        <div className="flex-1 min-w-0">
          <span className="text-[11px] text-[#4a3d28] lv-mono truncate block">
            {displayInput.length > 50 ? displayInput.substring(0, 47) + '...' : displayInput}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          {status.icon}
          <span className={`text-[9px] lv-mono tracking-wider ${status.color}`}>
            {status.label}
          </span>
        </div>
      </div>

      {isOpen && (
        <div className="px-3 py-2.5 border-t border-[#1c1710]">
          <div className="text-[9px] text-[#3e3222] lv-mono mb-1 tracking-wider">INPUT:</div>
          <pre className="text-[11px] text-[#9a8060] lv-mono leading-relaxed whitespace-pre-wrap bg-[#0d0a08] p-2.5 border border-[#1c1710] overflow-x-auto lv-scrollbar">
            {typeof toolCall.input === 'object'
              ? JSON.stringify(toolCall.input, null, 2)
              : String(toolCall.input)}
          </pre>

          {hasResult && (
            <div className="mt-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowResult(!showResult);
                }}
                className="flex items-center gap-1.5 text-[9px] text-[#4a3d28] lv-mono hover:text-[#7a6545] transition-colors tracking-wider"
              >
                {showResult ? (
                  <ChevronDown className="w-2.5 h-2.5" />
                ) : (
                  <ChevronRight className="w-2.5 h-2.5" />
                )}
                <span>RESULTADO ({toolCall.isError ? 'erro' : 'ok'})</span>
              </button>

              {showResult && (
                <div
                  className={`mt-1.5 p-2.5 border ${toolCall.isError ? 'border-[#8a3028]/30 bg-[#8a3028]/5' : 'border-[#1c1710] bg-[#0d0a08]'}`}
                >
                  <pre
                    className={`text-[11px] lv-mono leading-relaxed whitespace-pre-wrap overflow-x-auto lv-scrollbar ${toolCall.isError ? 'text-[#a04038]' : 'text-[#9a8060]'}`}
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

// ============================================================
// HistoryPanel
// ============================================================

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
  const formatDate = (isoString: string): string => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0)
      return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    if (diffDays === 1) return 'Ontem';
    if (diffDays < 7) return `${diffDays} dias`;
    return date.toLocaleDateString('pt-BR', { month: 'short', day: 'numeric' });
  };

  const getPreview = (conversation: Conversation): string => {
    const lastMessage = conversation.messages[conversation.messages.length - 1];
    if (lastMessage) {
      const content = lastMessage.content.trim();
      return content.length <= 55 ? content : content.substring(0, 52) + '...';
    }
    return 'Sem mensagens';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-full max-w-sm bg-[#110e0b] border-l border-[#231d15] h-full flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#231d15]">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-[#a0603a]" strokeWidth={1.4} />
            <span className="lv-serif text-[16px] text-[#c0a880] italic">Historico</span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-[#3e3222] hover:text-[#7a6545] transition-colors"
            aria-label="Fechar historico"
          >
            <X className="w-4 h-4" strokeWidth={1.4} />
          </button>
        </div>

        <div className="px-3 py-2 border-b border-[#231d15]">
          <button
            onClick={() => {
              onNewChat();
              onClose();
            }}
            className="w-full flex items-center justify-center gap-2 px-3 py-2
              border border-[#a0603a]/20 text-[#a0603a]
              hover:bg-[#a0603a]/5 hover:border-[#a0603a]/35
              lv-mono text-[10px] tracking-wider transition-all duration-200"
          >
            <Plus className="w-3 h-3" strokeWidth={1.8} />
            <span>NOVA SESSAO</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto lv-scrollbar">
          {conversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-5">
              <MessageSquare className="w-8 h-8 text-[#251f16] mb-3" strokeWidth={1} />
              <p className="text-[11px] text-[#3e3222] lv-mono">Nenhuma sessao</p>
            </div>
          ) : (
            <div className="py-1">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`group px-3 py-2.5 mx-1.5 my-0.5 cursor-pointer transition-all duration-150 border ${
                    currentConversationId === conv.id
                      ? 'bg-[#a0603a]/5 border-[#a0603a]/20'
                      : 'border-transparent hover:bg-[#141009] hover:border-[#231d15]'
                  }`}
                  onClick={() => {
                    onSelectConversation(conv);
                    onClose();
                  }}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-[12px] font-medium text-[#c0a880] truncate">
                        {conv.title}
                      </h3>
                      <p className="text-[10px] text-[#4a3d28] mt-0.5 truncate lv-mono">
                        {getPreview(conv)}
                      </p>
                      <p className="text-[9px] text-[#3a301f] mt-1 lv-mono">
                        {formatDate(conv.updatedAt)}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteConversation(conv.id);
                      }}
                      className="p-1 opacity-0 group-hover:opacity-100 text-[#3e3222] hover:text-[#8a3028] transition-all"
                      aria-label="Excluir conversa"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="px-4 py-2 border-t border-[#231d15] text-center">
          <span className="text-[8px] text-[#2e2519] lv-mono tracking-wider">
            {conversations.length}/50 SESSOES
          </span>
        </div>
      </div>
    </div>
  );
};

// ============================================================
// ErrorMessageContent
// ============================================================

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
    <div className="space-y-2">
      <div className="p-3 bg-[#8a3028]/5 border border-[#8a3028]/20">
        <pre className="text-[12px] text-[#a04038] lv-mono whitespace-pre-wrap overflow-x-auto">
          {content}
        </pre>
      </div>
      <div className="flex items-center gap-2">
        {canRetry && onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center gap-1.5 px-2.5 py-1 text-[9px] lv-mono tracking-wider
              bg-[#b85a30]/10 text-[#b85a30] hover:bg-[#b85a30]/20 transition-colors
              border border-[#b85a30]/25"
          >
            <RefreshCw className="w-3 h-3" />
            REENVIAR
          </button>
        )}
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-2.5 py-1 text-[9px] lv-mono tracking-wider
            bg-[#141009] text-[#5a4a32] hover:text-[#9a8060] transition-colors
            border border-[#231d15]"
        >
          {copied ? <Check className="w-3 h-3 text-[#5a7a3a]" /> : <Copy className="w-3 h-3" />}
          {copied ? 'COPIADO' : 'COPIAR'}
        </button>
      </div>
    </div>
  );
};

// ============================================================
// CCuiChatInterface (main)
// ============================================================

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

  const showConnectionError =
    lastError &&
    (connectionStatus === 'error' ||
      connectionStatus === 'disconnected' ||
      connectionStatus === 'disabled');

  const getErrorType = (): ErrorType => {
    if (!lastError) return 'unknown';
    return lastError.type;
  };

  const isInputDisabled = isTyping || !isConnected;

  const getPlaceholderText = (): string => {
    if (isTyping) return 'Processando...';
    if (connectionStatus === 'connecting') {
      return retryCount > 0
        ? `Reconectando... (${retryCount}/${maxRetries})`
        : 'Conectando ao backend...';
    }
    if (connectionStatus === 'disconnected' || connectionStatus === 'error') {
      return 'Conexao perdida. Tente reconectar...';
    }
    if (connectionStatus === 'disabled') {
      return 'Backend indisponivel.';
    }
    return 'Descreva a tarefa ou digite um comando...';
  };

  const {
    conversations,
    currentConversationId,
    saveConversation,
    deleteConversation,
    setCurrentConversationId,
    startNewConversation,
  } = useChatHistory();

  // ---- WebSocket message handler ----
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

    if (wsMessage.type === 'claude-response' && wsMessage.data) {
      const data = wsMessage.data;

      if (data.type === 'tool_use' && data.id && data.name) {
        const newToolCall: ToolCall = {
          id: data.id,
          name: data.name,
          input: data.input || {},
          status: 'running',
        };

        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.role === 'assistant') {
            const existingToolCalls = lastMsg.toolCalls || [];
            return [
              ...prev.slice(0, -1),
              { ...lastMsg, isStreaming: true, toolCalls: [...existingToolCalls, newToolCall] },
            ];
          }
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
        });
        setIsTyping(true);
      }

      if (data.type === 'tool_result' && data.tool_use_id) {
        const resultContent =
          typeof data.content === 'string'
            ? data.content
            : Array.isArray(data.content)
              ? data.content.map((c) => c.text || '').join('')
              : '';

        setMessages((prev) =>
          prev.map((msg) => {
            if (msg.role === 'assistant' && msg.toolCalls) {
              const updatedToolCalls = msg.toolCalls.map((tc) => {
                if (tc.id === data.tool_use_id) {
                  return {
                    ...tc,
                    status: (data.is_error ? 'failed' : 'completed') as ToolStatus,
                    result:
                      resultContent.length > 2000
                        ? resultContent.substring(0, 2000) + '\n... (truncado)'
                        : resultContent,
                    isError: data.is_error,
                  };
                }
                return tc;
              });
              return { ...msg, toolCalls: updatedToolCalls };
            }
            return msg;
          })
        );
      }

      if (data.type === 'content_block_delta' && data.delta?.text) {
        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isStreaming) {
            return [
              ...prev.slice(0, -1),
              { ...lastMsg, content: lastMsg.content + data.delta!.text },
            ];
          }
          return [
            ...prev,
            {
              id: Date.now().toString(),
              role: 'assistant',
              content: data.delta!.text!,
              isStreaming: true,
            },
          ];
        });
        setIsTyping(true);
      }

      if (data.type === 'content_block_stop') {
        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isStreaming) {
            return [...prev.slice(0, -1), { ...lastMsg, isStreaming: false }];
          }
          return prev;
        });
      }

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
            }
            return [
              ...prev,
              {
                id: Date.now().toString(),
                role: 'assistant',
                content: textContent,
                isStreaming: true,
              },
            ];
          });
          setIsTyping(true);
        }
      }
    } else if (wsMessage.type === 'claude-complete') {
      setIsTyping(false);
      setMessages((prev) => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg && lastMsg.role === 'assistant') {
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
    } else if (wsMessage.type === 'claude-error') {
      setIsTyping(false);
      setMessages((prev) => {
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
              content: `Erro: ${wsMessage.error || 'Erro desconhecido'}`,
              isError: true,
            },
          ];
        }
        return [
          ...prev,
          {
            id: Date.now().toString(),
            role: 'assistant',
            content: `Erro: ${wsMessage.error || 'Erro desconhecido'}`,
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

  useEffect(() => {
    if (messages.length > 0 && !isTyping) {
      saveConversation(messages as HistoryMessage[], currentConversationId);
    }
  }, [messages, isTyping, saveConversation, currentConversationId]);

  const handleNewChat = useCallback(() => {
    setMessages([]);
    startNewConversation();
  }, [startNewConversation]);

  const handleSelectConversation = useCallback(
    (conversation: Conversation) => {
      setCurrentConversationId(conversation.id);
      setMessages(conversation.messages as Message[]);
    },
    [setCurrentConversationId]
  );

  const handleDeleteConversation = useCallback(
    (id: string) => {
      deleteConversation(id);
      if (currentConversationId === id) setMessages([]);
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
              'Comandos disponiveis:\n/clear - Limpar chat\n/compact - Modo compacto\n/help - Esta ajuda',
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
            content: `Modo compacto ${!compactMode ? 'ativado' : 'desativado'}.`,
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

    if (!isConnected) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: 'system',
          content: 'Sem conexao com o backend. Aguarde reconexao ou tente manualmente.',
          isSystem: true,
          isError: true,
        },
      ]);
      return;
    }

    const trimmedInput = input.trim();

    if (trimmedInput.startsWith('/')) {
      const [cmd, ...args] = trimmedInput.split(' ');
      if (handleSlashCommand(cmd, args)) {
        setInput('');
        return;
      }
    }

    lastUserMessageRef.current = trimmedInput;

    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: trimmedInput };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    sendWsMessage({
      type: 'claude-command',
      command: trimmedInput,
      options: {
        cwd: WORKING_DIR,
        permissionMode: 'bypassPermissions',
      },
    });
  };

  const handleRetryLastMessage = useCallback(() => {
    if (!lastUserMessageRef.current || isTyping || !isConnected) return;
    setIsTyping(true);
    sendWsMessage({
      type: 'claude-command',
      command: lastUserMessageRef.current,
      options: { cwd: WORKING_DIR, permissionMode: 'bypassPermissions' },
    });
  }, [isTyping, isConnected, sendWsMessage]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const renderToolCalls = (message: Message): React.ReactNode[] => {
    if (!message.toolCalls || message.toolCalls.length === 0) return [];
    return message.toolCalls.map((tc) => (
      <ToolCallBlock
        key={`${message.id}-tool-${tc.id}`}
        toolCall={tc}
        isExpanded={tc.status === 'running' || tc.status === 'failed'}
      />
    ));
  };

  const renderMessageContent = (message: Message) => {
    const content = message.content;
    const elements: React.ReactNode[] = [];

    const toolCallElements = renderToolCalls(message);
    if (toolCallElements.length > 0) {
      elements.push(
        <div key={`${message.id}-tools`} className="mb-3">
          {toolCallElements}
        </div>
      );
    }

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
                label="Raciocinio"
                isStreaming={isStreamingThisBlock}
              />
            );
          }

          if (!part.trim()) return null;

          const isStreamingThisText = message.isStreaming && index === parts.length - 1;
          return (
            <p
              key={message.id + '-text-' + index}
              className={`leading-relaxed whitespace-pre-wrap text-[#c8b088] ${compactMode ? 'text-[12px]' : 'text-[14px]'}`}
            >
              {part}
              {isStreamingThisText && (
                <span className="inline-block w-2 h-5 bg-[#a0603a] align-bottom ml-1 animate-pulse" />
              )}
            </p>
          );
        })
        .filter(Boolean);

      elements.push(...textElements);
    }

    if (
      message.isStreaming &&
      !content?.trim() &&
      (!message.toolCalls || message.toolCalls.length === 0)
    ) {
      elements.push(
        <div key={`${message.id}-streaming`} className="flex items-center gap-2">
          <Loader2 className="w-3.5 h-3.5 text-[#a0603a] animate-spin" />
          <span className="text-[11px] text-[#5a4a32] lv-mono">Processando...</span>
        </div>
      );
    }

    return elements;
  };

  return (
    <div className="flex flex-col h-full">
      {showConnectionError && lastError && (
        <div className="flex-none px-6 pt-3">
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

      <div className="flex-1 overflow-y-auto lv-scrollbar px-6 py-6 flex flex-col">
        {messages.length === 0 && !isTyping ? (
          <div className="flex flex-col items-center justify-center h-full text-center select-none">
            <div className="mb-6 opacity-80">
              <ReactorSpinner />
            </div>

            <h1 className="lv-serif text-[36px] text-[#a0603a]/80 italic tracking-wide mb-2">
              Lex Vector
            </h1>
            <p className="lv-mono text-[10px] tracking-[0.25em] text-[#3e3222] uppercase">
              Interface de Comando Juridico
            </p>

            <div className="mt-10 flex items-center gap-4">
              <div className="flex items-center gap-1.5 px-3 py-1.5 border border-[#231d15] bg-[#110e0b]">
                <Terminal className="w-3 h-3 text-[#3e3222]" strokeWidth={1.4} />
                <span className="lv-mono text-[9px] text-[#3e3222]">/help</span>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1.5 border border-[#231d15] bg-[#110e0b]">
                <Sparkles className="w-3 h-3 text-[#3e3222]" strokeWidth={1.4} />
                <span className="lv-mono text-[9px] text-[#3e3222]">pergunte qualquer coisa</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-4xl w-full mx-auto space-y-6">
            {messages.map((msg) => (
              <div key={msg.id} className="group">
                {msg.role === 'user' ? (
                  <div className="flex justify-end">
                    <div className="max-w-[80%] px-4 py-3 bg-[#a0603a]/5 border border-[#a0603a]/12">
                      <p
                        className={`whitespace-pre-wrap text-[#c8b088] ${compactMode ? 'text-[12px]' : 'text-[14px]'}`}
                      >
                        {msg.content}
                      </p>
                    </div>
                  </div>
                ) : msg.isSystem ? (
                  <div className="flex justify-center">
                    <div
                      className={`px-4 py-2 lv-mono text-[11px] ${
                        msg.isError
                          ? 'text-[#a04038] border border-[#8a3028]/20 bg-[#8a3028]/5'
                          : 'text-[#5a4a32] border border-[#231d15] bg-[#110e0b]'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                ) : (
                  <div className="flex gap-0">
                    <div
                      className={`w-[2px] flex-none mr-4 mt-1 ${
                        msg.isError ? 'bg-[#8a3028]/60' : 'bg-[#a0603a]/30'
                      }`}
                    />

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        {msg.isError ? (
                          <AlertTriangle className="w-3 h-3 text-[#8a3028]" strokeWidth={1.4} />
                        ) : (
                          <div className="w-1.5 h-1.5 rounded-full bg-[#a0603a]/60" />
                        )}
                        <span
                          className={`lv-mono text-[9px] tracking-[0.12em] ${
                            msg.isError ? 'text-[#8a3028]' : 'text-[#5a4a32]'
                          }`}
                        >
                          {msg.isError ? 'ERRO' : 'CLAUDE'}
                        </span>
                        <span className="lv-mono text-[8px] text-[#2e2519]">
                          {new Date().toLocaleTimeString('pt-BR', {
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
                )}
              </div>
            ))}

            {isTyping && (
              <div className="flex gap-0">
                <div className="w-[2px] flex-none mr-4 mt-1 bg-[#a0603a]/30" />
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6">
                    <PhyllotaxisSpinner className="w-full h-full" />
                  </div>
                  <span className="text-[11px] text-[#5a4a32] lv-mono animate-pulse">
                    Processando...
                  </span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="flex-none px-6 pb-4 pt-2 w-full max-w-4xl mx-auto">
        <div className="flex justify-end mb-1.5">
          <ConnectionStatus
            status={connectionStatus}
            retryCount={retryCount}
            maxRetries={maxRetries}
            onRetry={retryConnection}
          />
        </div>

        <div
          className={`
            relative flex items-end gap-3 bg-[#110e0b] border px-4 py-3 transition-all duration-300
            ${
              isInputDisabled
                ? 'border-[#231d15] opacity-60'
                : 'border-[#a0603a]/15 focus-within:border-[#a0603a]/35 shadow-[0_-4px_24px_rgba(0,0,0,0.4)] focus-within:shadow-[0_-4px_32px_rgba(160,96,58,0.04)]'
            }
            ${!isConnected && !isTyping ? 'border-[#8a3028]/20' : ''}
          `}
        >
          <span
            className={`lv-mono text-[14px] font-medium select-none pb-0.5 ${
              isConnected ? 'text-[#a0603a]/60' : 'text-[#3e3222]'
            }`}
          >
            {'>'}
          </span>

          <textarea
            ref={textareaRef}
            className={`flex-1 resize-none overflow-hidden max-h-40 bg-transparent focus:outline-none
              placeholder-[#3e3222] lv-scrollbar lv-mono text-[13px] leading-relaxed
              ${isInputDisabled ? 'text-[#5a4a32] cursor-not-allowed' : 'text-[#c8b088]'}`}
            placeholder={getPlaceholderText()}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isInputDisabled}
            rows={1}
            autoFocus
            aria-label="Campo de mensagem"
          />

          <button
            onClick={handleSendMessage}
            className={`transition-all duration-200 p-1.5 ${
              input.trim() === '' || isInputDisabled
                ? 'text-[#2e2519]'
                : 'text-[#a0603a] hover:text-[#b85a30] hover:bg-[#a0603a]/5'
            }`}
            disabled={input.trim() === '' || isInputDisabled}
            aria-label="Enviar mensagem"
          >
            <ArrowUp className="w-5 h-5" strokeWidth={2} />
          </button>
        </div>

        <div className="flex justify-center items-center gap-6 mt-3 select-none">
          <button className="flex items-center gap-1.5 text-[#3e3222] hover:text-[#7a6545] transition-colors group">
            <Command className="w-3 h-3 group-hover:text-[#a0603a]" strokeWidth={1.4} />
            <span className="lv-mono text-[9px] tracking-wider">ACOES</span>
          </button>
          <button
            onClick={() => setHistoryPanelOpen(true)}
            className="flex items-center gap-1.5 text-[#3e3222] hover:text-[#7a6545] transition-colors group"
          >
            <History className="w-3 h-3 group-hover:text-[#a0603a]" strokeWidth={1.4} />
            <span className="lv-mono text-[9px] tracking-wider">HISTORICO</span>
            {conversations.length > 0 && (
              <span className="text-[8px] text-[#a0603a] lv-mono">{conversations.length}</span>
            )}
          </button>
          <div className="flex items-center gap-1 text-[#2e2519]">
            <CornerDownLeft className="w-2.5 h-2.5" strokeWidth={1.4} />
            <span className="lv-mono text-[8px]">ENTER</span>
          </div>
        </div>
      </div>

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
