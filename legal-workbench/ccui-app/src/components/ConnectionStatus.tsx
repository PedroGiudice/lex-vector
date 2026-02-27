import { useState } from "react";
import { Wifi, WifiOff, Loader2 } from "lucide-react";
import type { WsStatus } from "../contexts/WebSocketContext";

export type ConnectionState = WsStatus;

export interface ConnectionStatusProps {
  status: ConnectionState;
  retryCount?: number;
  maxRetries?: number;
  onRetry?: () => void;
}

const statusConfig: Record<
  ConnectionState,
  {
    dotColor: string;
    label: string;
    description: string;
    pulse: boolean;
  }
> = {
  connected: {
    dotColor: "#4ade80",
    label: "Conectado",
    description: "Sessao ativa",
    pulse: false,
  },
  connecting: {
    dotColor: "#fbbf24",
    label: "Conectando",
    description: "Estabelecendo conexao...",
    pulse: true,
  },
  disconnected: {
    dotColor: "#f87171",
    label: "Desconectado",
    description: "Conexao perdida. Clique para reconectar.",
    pulse: false,
  },
  error: {
    dotColor: "#f87171",
    label: "Erro",
    description: "Falha na conexao. Clique para tentar novamente.",
    pulse: false,
  },
  idle: {
    dotColor: "#3a3735",
    label: "Inativo",
    description: "Sem sessao ativa.",
    pulse: false,
  },
};

export function ConnectionStatus({
  status,
  retryCount,
  maxRetries,
  onRetry,
}: ConnectionStatusProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const config = statusConfig[status];
  const isRetrying =
    status === "connecting" && retryCount !== undefined && retryCount > 0;
  const canRetry = (status === "disconnected" || status === "error") && !!onRetry;

  const getDescription = () => {
    if (isRetrying && maxRetries !== undefined) {
      return `Reconectando... (${retryCount}/${maxRetries})`;
    }
    return config.description;
  };

  return (
    <div className="relative inline-flex items-center">
      <button
        className="flex items-center gap-2 px-2 py-1.5 rounded-md transition-colors duration-150"
        style={{ cursor: canRetry ? "pointer" : "default" }}
        onClick={() => canRetry && onRetry?.()}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        disabled={!canRetry}
        aria-label={`Status: ${config.label}`}
      >
        {/* Dot */}
        <span className="relative flex h-2 w-2">
          {config.pulse && (
            <span
              className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-60"
              style={{ backgroundColor: config.dotColor }}
            />
          )}
          <span
            className="relative inline-flex rounded-full h-2 w-2"
            style={{ backgroundColor: config.dotColor }}
          />
        </span>

        {/* Icone */}
        {status === "connecting" && (
          <Loader2 className="w-3.5 h-3.5 animate-spin" style={{ color: "#fbbf24" }} />
        )}
        {status === "connected" && (
          <Wifi className="w-3.5 h-3.5 opacity-50" style={{ color: "#4ade80" }} />
        )}
        {(status === "disconnected" || status === "error") && (
          <WifiOff className="w-3.5 h-3.5" style={{ color: "#f87171" }} />
        )}
      </button>

      {/* Tooltip */}
      {showTooltip && (
        <div
          className="absolute z-50 px-3 py-2 text-xs rounded-lg shadow-xl
                     bottom-full left-1/2 -translate-x-1/2 mb-2 whitespace-nowrap"
          style={{
            background: "var(--bg-elevated)",
            border: "1px solid var(--border-mid)",
          }}
        >
          <p className="font-semibold" style={{ color: "var(--text-primary)" }}>
            {config.label}
          </p>
          <p className="mt-0.5" style={{ color: "var(--text-secondary)" }}>
            {getDescription()}
          </p>
          {canRetry && (
            <p className="mt-1 text-[10px]" style={{ color: "var(--accent)" }}>
              Clique para reconectar
            </p>
          )}
          {/* Seta */}
          <div
            className="absolute top-full left-1/2 -translate-x-1/2 -mt-px
                       border-4 border-transparent"
            style={{ borderTopColor: "var(--border-mid)" }}
          />
        </div>
      )}
    </div>
  );
}

export default ConnectionStatus;
