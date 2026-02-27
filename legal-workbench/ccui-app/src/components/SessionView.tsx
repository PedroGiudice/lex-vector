import React, { useCallback, useRef, useState } from "react";
import { LogOut, Send, Briefcase } from "lucide-react";
import { useSession } from "../contexts/SessionContext";
import { useWebSocket } from "../contexts/WebSocketContext";
import { ConnectionStatus } from "./ConnectionStatus";
import { ChannelTabs } from "./ChannelTabs";
import { TerminalPane } from "./TerminalPane";

interface SessionViewProps {
  onClose: () => void;
}

export const SessionView: React.FC<SessionViewProps> = ({ onClose }) => {
  const { caseId, sessionId, channels, reset } = useSession();
  const { status, retryCount, maxRetries, send, retryManual } = useWebSocket();

  const [activeChannel, setActiveChannel] = useState("main");
  const [inputText, setInputText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const channelNames = channels.map((c) => c.name);
  const safeActive = channelNames.includes(activeChannel) ? activeChannel : "main";

  const handleSend = useCallback(() => {
    const text = inputText.trim();
    if (!text || !sessionId) return;
    send({ type: "input", channel: safeActive, text });
    setInputText("");
    textareaRef.current?.focus();
  }, [inputText, sessionId, safeActive, send]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClose = useCallback(() => {
    if (sessionId) {
      send({ type: "destroy_session", session_id: sessionId });
    }
    reset();
    onClose();
  }, [sessionId, send, reset, onClose]);

  const isConnected = status === "connected";
  const canSend = isConnected && !!sessionId && !!inputText.trim();

  return (
    <div
      className="flex flex-col h-screen anim-fade-in"
      style={{ background: "var(--bg-base)", color: "var(--text-primary)" }}
    >
      {/* Header */}
      <header
        className="flex items-center justify-between px-5 py-3 border-b shrink-0"
        style={{ borderColor: "var(--border)", background: "var(--bg-surface)" }}
      >
        {/* Caso ativo */}
        <div className="flex items-center gap-2.5 min-w-0">
          <Briefcase
            className="w-3.5 h-3.5 shrink-0"
            style={{ color: "var(--accent)" }}
          />
          <span className="text-[11px] font-medium tracking-[0.08em] uppercase text-[var(--text-secondary)] shrink-0">
            Caso
          </span>
          <span
            className="text-sm font-semibold text-[var(--text-primary)] truncate"
            title={caseId ?? ""}
          >
            {caseId ?? "—"}
          </span>
        </div>

        {/* Controles direita */}
        <div className="flex items-center gap-1 shrink-0">
          <ConnectionStatus
            status={status}
            retryCount={retryCount}
            maxRetries={maxRetries}
            onRetry={retryManual}
          />
          <div
            className="w-px h-4 mx-1"
            style={{ background: "var(--border-mid)" }}
          />
          <button
            onClick={handleClose}
            title="Encerrar sessao"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-colors duration-150"
            style={{ color: "var(--text-secondary)" }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.color = "var(--text-primary)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.color = "var(--text-secondary)")
            }
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Encerrar</span>
          </button>
        </div>
      </header>

      {/* Abas de canal (so exibe quando ha mais de um) */}
      {channels.length > 1 && (
        <ChannelTabs
          channels={channels}
          activeChannel={safeActive}
          onSelect={setActiveChannel}
        />
      )}

      {/* Area de output do terminal */}
      <div className="flex-1 overflow-hidden" style={{ background: "var(--bg-input)" }}>
        <TerminalPane channel={safeActive} />
      </div>

      {/* Input */}
      <div
        className="shrink-0 border-t p-4"
        style={{ borderColor: "var(--border)", background: "var(--bg-surface)" }}
      >
        <div
          className="flex items-end gap-3 rounded-lg border px-4 py-3 transition-colors duration-150"
          style={{
            borderColor: "var(--border-mid)",
            background: "var(--bg-elevated)",
          }}
          onFocusCapture={(e) =>
            ((e.currentTarget as HTMLDivElement).style.borderColor =
              "rgba(217,119,87,0.45)")
          }
          onBlurCapture={(e) =>
            ((e.currentTarget as HTMLDivElement).style.borderColor =
              "var(--border-mid)")
          }
        >
          <textarea
            ref={textareaRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              !isConnected
                ? "Aguardando conexao..."
                : `Instruir o ${safeActive === "main" ? "Claude" : safeActive}...`
            }
            rows={1}
            className="flex-1 resize-none bg-transparent text-sm leading-relaxed outline-none
                       max-h-36 overflow-y-auto placeholder-[var(--text-muted)]"
            style={{
              color: "var(--text-primary)",
              fontFamily: "var(--font-ui)",
            }}
            disabled={!isConnected || !sessionId}
          />
          <button
            onClick={handleSend}
            disabled={!canSend}
            title="Enviar (Enter)"
            className="flex items-center justify-center w-7 h-7 rounded-md
                       transition-all duration-150 shrink-0"
            style={{
              color: canSend ? "var(--accent)" : "var(--text-muted)",
              background: canSend ? "var(--accent-dim)" : "transparent",
            }}
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
        <p className="mt-1.5 text-[10px] text-right" style={{ color: "var(--text-muted)" }}>
          Enter para enviar · Shift+Enter para nova linha
        </p>
      </div>
    </div>
  );
};

export default SessionView;
