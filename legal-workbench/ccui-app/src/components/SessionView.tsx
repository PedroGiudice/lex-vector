import { useCallback, useRef, useState, useEffect } from "react";
import { useTauriStore } from "../hooks/useTauriStore";
import {
  MessageSquare,
  Files,
  Search,
  Settings,
  Send,
  Briefcase,
  Wifi,
  WifiOff,
  Activity,
  Clock,
  Columns,
  Layers,
  FolderOpen,
  FileText,
  Loader2,
} from "lucide-react";
import { useSession } from "../contexts/SessionContext";
import { useWebSocket } from "../contexts/WebSocketContext";
import { useChat } from "../hooks/useChat";
import { useAgents } from "../hooks/useAgents";
import { useSessionMeta } from "../hooks/useSessionMeta";
import { useSessions } from "../hooks/useCcuiApi";
import { ModeToggle } from "./ModeToggle";
import type { ViewMode } from "./ModeToggle";
import { ChatView } from "./ChatView";

interface SessionViewProps {
  onClose: () => void;
}

type SidebarTab = "sessions" | "files" | "search" | "settings";
type LayoutMode = "tab" | "split";

const MODE_STORAGE_KEY = "ccui-view-mode";
const LAYOUT_STORAGE_KEY = "ccui-layout-mode";

/* -- Icon Strip Button -- */
function IconBtn({
  icon: Icon,
  active,
  onClick,
  tooltip,
}: {
  icon: typeof MessageSquare;
  active: boolean;
  onClick: () => void;
  tooltip: string;
}) {
  return (
    <button
      onClick={onClick}
      title={tooltip}
      aria-label={tooltip}
      className="relative w-full flex justify-center items-center py-3 transition-all duration-200"
      style={{ color: active ? "var(--accent)" : "var(--text-muted)" }}
    >
      <Icon className="w-[17px] h-[17px]" strokeWidth={1.4} />
      {active && (
        <span
          className="absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-r-full"
          style={{ background: "var(--accent)" }}
        />
      )}
    </button>
  );
}

/* -- Agent Tab -- */
function AgentTab({
  name,
  color,
  active,
  onClick,
}: {
  name: string;
  color: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 px-3 py-1.5 text-[12px] transition-all duration-150"
      style={{
        fontFamily: "var(--font-mono)",
        background: active ? "var(--bg-cards)" : "transparent",
        borderRadius: "var(--radius-md)",
        color: active ? "var(--text-primary)" : "var(--text-muted)",
      }}
    >
      <span
        className="w-2 h-2 rounded-full"
        style={{ background: color }}
      />
      {name}
    </button>
  );
}

/* -- Sessions List (sidebar) -- */
function SessionsList({
  currentSessionId,
  onSwitchSession,
}: {
  currentSessionId: string | null;
  onSwitchSession: (caseId: string) => void;
}) {
  const { sessions, loading, fetchSessions } = useSessions();

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-3 py-4">
        <Loader2 className="w-3 h-3 animate-spin" style={{ color: "var(--text-muted)" }} />
        <span className="text-[11px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
          Carregando...
        </span>
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="px-3 py-4">
        <span className="text-[11px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
          Nenhuma sessao ativa
        </span>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-0.5 p-1.5">
      {sessions.map((s) => (
        <div
          key={s.session_id}
          className="flex items-center gap-2 px-2.5 py-2 rounded-md cursor-pointer transition-colors"
          style={{
            background: "var(--bg-cards)",
            border: s.session_id === currentSessionId ? "1px solid var(--accent)" : "1px solid transparent",
          }}
          onClick={() => s.case_id && onSwitchSession(s.case_id)}
        >
          <MessageSquare className="w-3 h-3 shrink-0" style={{ color: "var(--accent)" }} />
          <div className="flex flex-col min-w-0">
            <span
              className="text-[11px] truncate"
              style={{ fontFamily: "var(--font-mono)", color: "var(--text-primary)" }}
            >
              {s.case_id ?? s.session_id?.slice(0, 8) ?? "sessao"}
            </span>
            {s.created_at && (
              <span className="text-[9px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
                {new Date(s.created_at).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

/* -- File Tree (sidebar) -- */
function FileTree({ caseId }: { caseId: string | null }) {
  if (!caseId) {
    return (
      <div className="px-3 py-4">
        <span className="text-[11px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
          Selecione um caso
        </span>
      </div>
    );
  }

  // Placeholder - seria populado via endpoint REST do backend
  return (
    <div className="flex flex-col gap-0.5 p-1.5">
      <div className="flex items-center gap-2 px-2.5 py-1.5">
        <FolderOpen className="w-3 h-3" style={{ color: "var(--accent)" }} />
        <span className="text-[11px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-primary)" }}>
          {caseId}
        </span>
      </div>
      {["base/", "embeddings/", "metadata/"].map((dir) => (
        <div key={dir} className="flex items-center gap-2 px-2.5 py-1 ml-4">
          <FolderOpen className="w-3 h-3" style={{ color: "var(--text-muted)" }} />
          <span className="text-[11px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>
            {dir}
          </span>
        </div>
      ))}
      <div className="flex items-center gap-2 px-2.5 py-1 ml-4">
        <FileText className="w-3 h-3" style={{ color: "var(--text-muted)" }} />
        <span className="text-[11px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>
          CLAUDE.md
        </span>
      </div>
    </div>
  );
}

/* -- Split Panel (agentes secundarios) -- */
function SplitPanel({
  agents,
  activeAgent,
}: {
  agents: { name: string; color: string }[];
  activeAgent: string;
}) {
  const secondaryAgents = agents.filter((a) => a.name !== activeAgent);

  if (secondaryAgents.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="text-[11px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
          Sem agentes secundarios
        </span>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full divide-y" style={{ borderColor: "var(--bg-borders)" }}>
      {secondaryAgents.map((agent) => (
        <div key={agent.name} className="flex-1 flex flex-col min-h-0">
          <div
            className="flex items-center gap-2 px-3 py-1.5 shrink-0"
            style={{ borderBottom: "1px solid var(--bg-borders)" }}
          >
            <span className="w-2 h-2 rounded-full" style={{ background: agent.color }} />
            <span
              className="text-[11px]"
              style={{ fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}
            >
              {agent.name}
            </span>
          </div>
          <div className="flex-1 overflow-y-auto px-3 py-2">
            <span className="text-[10px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
              Output do agente
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

/* -- Main -- */
export const SessionView: React.FC<SessionViewProps> = ({ onClose }) => {
  const { caseId, sessionId, createSession, reset } = useSession();
  const { status, send } = useWebSocket();
  const { messages, isStreaming, sendMessage } = useChat();
  const { agents: wsAgents } = useAgents();
  const sessionMeta = useSessionMeta();

  const [viewMode, setViewMode] = useTauriStore<ViewMode>(MODE_STORAGE_KEY, "client");
  const [layoutMode, setLayoutMode] = useTauriStore<LayoutMode>(LAYOUT_STORAGE_KEY, "tab");
  const [inputText, setInputText] = useState("");
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>("sessions");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeAgent, setActiveAgent] = useState("Main");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Agentes: usar WS reais se disponivel, senao fallback "Main"
  const displayAgents = wsAgents.length > 0
    ? wsAgents.map((a) => ({ name: a.name, color: a.color }))
    : [{ name: "Main", color: "var(--agent-terracota)" }];

  const handleModeChange = useCallback((mode: ViewMode) => {
    setViewMode(mode);
  }, [setViewMode]);

  const toggleLayout = useCallback(() => {
    const next = layoutMode === "tab" ? "split" : "tab";
    setLayoutMode(next);
  }, [layoutMode, setLayoutMode]);

  const handleSend = useCallback(() => {
    const text = inputText.trim();
    if (!text || !sessionId) return;
    sendMessage(text);
    setInputText("");
    textareaRef.current?.focus();
  }, [inputText, sessionId, sendMessage]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSwitchSession = useCallback((newCaseId: string) => {
    if (sessionId) {
      send({ type: "destroy_session", session_id: sessionId });
    }
    createSession(newCaseId);
  }, [sessionId, send, createSession]);

  const handleClose = useCallback(() => {
    if (sessionId) {
      send({ type: "destroy_session", session_id: sessionId });
    }
    reset();
    onClose();
  }, [sessionId, send, reset, onClose]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Cmd+B: toggle sidebar
      if ((e.metaKey || e.ctrlKey) && e.key === "b") {
        e.preventDefault();
        setSidebarOpen((prev) => !prev);
      }
      // Ctrl+\: toggle tab/split
      if (e.ctrlKey && e.key === "\\") {
        e.preventDefault();
        toggleLayout();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [toggleLayout]);

  const isConnected = status === "connected";
  const canSend = isConnected && !!sessionId && !!inputText.trim();

  // Clock
  const [time, setTime] = useState(() =>
    new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
  );
  useEffect(() => {
    const iv = setInterval(() => {
      setTime(new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }));
    }, 30_000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="flex flex-col h-screen" style={{ background: "var(--bg-base)" }}>
      {/* Header with agent tabs */}
      <header
        className="flex items-center shrink-0 px-2"
        style={{
          height: 40,
          background: "var(--bg-header)",
          borderBottom: "1px solid var(--bg-borders)",
        }}
      >
        {/* Spacer for icon strip width */}
        <div style={{ width: "var(--icon-strip)" }} className="shrink-0" />
        {sidebarOpen && <div style={{ width: "var(--side-panel)" }} className="shrink-0" />}

        {/* Agent tabs */}
        <div className="flex items-center gap-1 flex-1">
          {displayAgents.map((a) => (
            <AgentTab
              key={a.name}
              name={a.name}
              color={a.color}
              active={activeAgent === a.name}
              onClick={() => setActiveAgent(a.name)}
            />
          ))}
        </div>

        {/* Layout toggle + Mode toggle + close */}
        <div className="flex items-center gap-2 shrink-0 pr-2">
          <button
            onClick={toggleLayout}
            title={layoutMode === "tab" ? "Modo split (Ctrl+\\)" : "Modo tab (Ctrl+\\)"}
            aria-label={layoutMode === "tab" ? "Ativar split view" : "Ativar tab view"}
            className="flex items-center justify-center w-7 h-7 rounded-md transition-colors"
            style={{
              color: layoutMode === "split" ? "var(--accent)" : "var(--text-muted)",
              background: layoutMode === "split" ? "var(--accent-dim)" : "transparent",
            }}
          >
            {layoutMode === "split" ? (
              <Columns className="w-3.5 h-3.5" />
            ) : (
              <Layers className="w-3.5 h-3.5" />
            )}
          </button>
          <ModeToggle mode={viewMode} onChange={handleModeChange} />
          <button
            onClick={handleClose}
            className="text-[11px] px-2 py-1 transition-colors"
            style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}
          >
            Encerrar
          </button>
        </div>
      </header>

      {/* Body: icon strip + sidebar + chat + split panel */}
      <div className="flex flex-1 overflow-hidden">
        {/* Icon strip */}
        <aside
          className="shrink-0 flex flex-col items-center py-2"
          style={{
            width: "var(--icon-strip)",
            background: "var(--bg-header)",
            borderRight: "1px solid var(--bg-borders)",
          }}
        >
          <IconBtn icon={MessageSquare} active={sidebarTab === "sessions"} onClick={() => { setSidebarTab("sessions"); setSidebarOpen(true); }} tooltip="Sessoes" />
          <IconBtn icon={Files} active={sidebarTab === "files"} onClick={() => { setSidebarTab("files"); setSidebarOpen(true); }} tooltip="Arquivos" />
          <IconBtn icon={Search} active={sidebarTab === "search"} onClick={() => { setSidebarTab("search"); setSidebarOpen(true); }} tooltip="Busca" />
          <div className="flex-1" />
          <IconBtn icon={Settings} active={sidebarTab === "settings"} onClick={() => { setSidebarTab("settings"); setSidebarOpen(true); }} tooltip="Configuracoes" />
        </aside>

        {/* Side panel */}
        {sidebarOpen && (
          <aside
            className="shrink-0 flex flex-col anim-fade-in overflow-hidden"
            style={{
              width: "var(--side-panel)",
              background: "var(--bg-header)",
              borderRight: "1px solid var(--bg-borders)",
            }}
          >
            <div className="px-3 py-2.5" style={{ borderBottom: "1px solid var(--bg-borders)" }}>
              <span
                className="text-[9px] tracking-[0.15em] uppercase"
                style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}
              >
                {sidebarTab === "sessions" ? "SESSOES" : sidebarTab === "files" ? "ARQUIVOS" : sidebarTab.toUpperCase()}
              </span>
            </div>
            <div className="flex-1 overflow-y-auto">
              {sidebarTab === "sessions" && <SessionsList currentSessionId={sessionId} onSwitchSession={handleSwitchSession} />}
              {sidebarTab === "files" && <FileTree caseId={caseId} />}
              {sidebarTab === "search" && (
                <div className="px-3 py-4">
                  <span className="text-[10px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
                    Busca em breve
                  </span>
                </div>
              )}
              {sidebarTab === "settings" && (
                <div className="px-3 py-4">
                  <span className="text-[10px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
                    Configuracoes em breve
                  </span>
                </div>
              )}
            </div>
          </aside>
        )}

        {/* Chat area */}
        <main className="flex-1 flex flex-col overflow-hidden" style={{ minWidth: 0 }}>
          {/* Case info bar */}
          <div
            className="flex items-center gap-2 px-4 py-1.5 shrink-0"
            style={{ borderBottom: "1px solid var(--bg-borders)", background: "var(--bg-panels)" }}
          >
            <Briefcase className="w-3 h-3" style={{ color: "var(--accent)" }} />
            <span className="text-[11px] tracking-[0.06em] uppercase" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
              Caso
            </span>
            <span className="text-[13px] font-medium" style={{ fontFamily: "var(--font-mono)", color: "var(--text-primary)" }}>
              {caseId ?? "--"}
            </span>
          </div>

          {/* Messages area: tab mode = full, split mode = 70% + detail panel */}
          <div className="flex flex-1 overflow-hidden">
            <div className={layoutMode === "split" ? "flex-[7] min-w-0" : "flex-1"}>
              <ChatView messages={messages} isStreaming={isStreaming} viewMode={viewMode} />
            </div>

            {/* Split panel */}
            {layoutMode === "split" && (
              <aside
                className="shrink-0 overflow-hidden anim-fade-in"
                style={{
                  width: "var(--detail-panel)",
                  borderLeft: "1px solid var(--bg-borders)",
                  background: "var(--bg-panels)",
                }}
              >
                <SplitPanel agents={displayAgents} activeAgent={activeAgent} />
              </aside>
            )}
          </div>

          {/* Input */}
          <div className="shrink-0 px-4 py-3" style={{ borderTop: "1px solid var(--bg-borders)", background: "var(--bg-panels)" }}>
            <div className="max-w-[var(--chat-max-width)] mx-auto">
              <div
                className="flex items-end gap-3 px-4 py-3 transition-colors"
                style={{
                  background: "var(--bg-cards)",
                  border: "1px solid var(--bg-borders)",
                  borderRadius: "var(--radius-lg)",
                }}
                onFocusCapture={(e) => (e.currentTarget.style.borderColor = "var(--accent)")}
                onBlurCapture={(e) => (e.currentTarget.style.borderColor = "var(--bg-borders)")}
              >
                <textarea
                  ref={textareaRef}
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={!isConnected ? "Aguardando conexao..." : "Instruir o Claude..."}
                  rows={1}
                  className="flex-1 resize-none bg-transparent text-sm outline-none max-h-36 overflow-y-auto"
                  style={{
                    color: "var(--text-primary)",
                    fontFamily: "var(--font-ui)",
                    lineHeight: "var(--lh-body)",
                  }}
                  disabled={!isConnected || !sessionId}
                />
                <button
                  onClick={handleSend}
                  disabled={!canSend}
                  title="Enviar (Enter)"
                  className="flex items-center justify-center w-7 h-7 rounded-md shrink-0 transition-all"
                  style={{
                    color: canSend ? "var(--accent)" : "var(--text-muted)",
                    background: canSend ? "var(--accent-dim)" : "transparent",
                  }}
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* Status bar */}
      <footer
        className="shrink-0 flex items-center justify-between px-3"
        style={{
          height: 24,
          background: "var(--bg-header)",
          borderTop: "1px solid var(--bg-borders)",
        }}
      >
        <div className="flex items-center gap-5">
          <div className="flex items-center gap-1.5">
            {isConnected ? (
              <Wifi className="w-2.5 h-2.5" style={{ color: "var(--agent-oliva)" }} />
            ) : (
              <WifiOff className="w-2.5 h-2.5" style={{ color: "#8a3028" }} />
            )}
            <span
              className="text-[9px] tracking-[0.1em]"
              style={{ fontFamily: "var(--font-mono)", color: isConnected ? "var(--agent-oliva)" : "#8a3028" }}
            >
              {isConnected ? "ONLINE" : "OFFLINE"}
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <Activity className="w-2.5 h-2.5" style={{ color: "var(--accent)" }} />
            <span className="text-[9px]" style={{ fontFamily: "var(--font-mono)", color: "var(--accent)" }}>
              {sessionMeta.model ?? "..."}
            </span>
          </div>

          <span className="text-[9px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
            {displayAgents.length} agente{displayAgents.length !== 1 ? "s" : ""} ativo{displayAgents.length !== 1 ? "s" : ""}
          </span>

          {layoutMode === "split" && (
            <span className="text-[9px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
              SPLIT
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          <Clock className="w-2.5 h-2.5" style={{ color: "var(--text-muted)" }} />
          <span className="text-[9px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
            {time}
          </span>
        </div>
      </footer>
    </div>
  );
};

export default SessionView;
