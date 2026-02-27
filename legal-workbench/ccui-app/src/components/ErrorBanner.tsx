import React, { useCallback, useEffect, useState } from "react";
import { AlertTriangle, WifiOff, Clock, Server, HelpCircle, X, RefreshCw } from "lucide-react";

export type ErrorType = "connection" | "timeout" | "server" | "unknown";

export interface ErrorBannerProps {
  type: ErrorType;
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  autoDismiss?: boolean;
  autoDismissDelay?: number;
}

const errorConfig: Record<
  ErrorType,
  {
    icon: React.ReactNode;
    bgColor: string;
    borderColor: string;
    textColor: string;
    iconColor: string;
    isCritical: boolean;
    defaultMessage: string;
  }
> = {
  connection: {
    icon: <WifiOff className="w-5 h-5" />,
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/30",
    textColor: "text-red-400",
    iconColor: "text-red-500",
    isCritical: true,
    defaultMessage: "Conexao perdida. Verifique o tunnel SSH e tente novamente.",
  },
  timeout: {
    icon: <Clock className="w-5 h-5" />,
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/30",
    textColor: "text-yellow-400",
    iconColor: "text-yellow-500",
    isCritical: false,
    defaultMessage: "Tempo limite excedido. O servidor pode estar ocupado.",
  },
  server: {
    icon: <Server className="w-5 h-5" />,
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/30",
    textColor: "text-red-400",
    iconColor: "text-red-500",
    isCritical: true,
    defaultMessage: "Erro no servidor. Tente novamente em alguns instantes.",
  },
  unknown: {
    icon: <HelpCircle className="w-5 h-5" />,
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/30",
    textColor: "text-yellow-400",
    iconColor: "text-yellow-500",
    isCritical: false,
    defaultMessage: "Ocorreu um erro inesperado.",
  },
};

export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  type,
  message,
  onRetry,
  onDismiss,
  autoDismiss = false,
  autoDismissDelay = 5000,
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isExiting, setIsExiting] = useState(false);

  const config = errorConfig[type];
  const displayMessage = message || config.defaultMessage;

  const handleDismiss = useCallback(() => {
    setIsExiting(true);
    setTimeout(() => {
      setIsVisible(false);
      onDismiss?.();
    }, 300);
  }, [onDismiss]);

  useEffect(() => {
    if (autoDismiss && !config.isCritical) {
      const timer = setTimeout(() => {
        handleDismiss();
      }, autoDismissDelay);
      return () => clearTimeout(timer);
    }
  }, [autoDismiss, autoDismissDelay, config.isCritical, handleDismiss]);

  if (!isVisible) return null;

  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${config.bgColor} ${config.borderColor} transition-all duration-300 ease-in-out ${
        isExiting ? "opacity-0 translate-y-[-10px]" : "opacity-100 translate-y-0"
      }`}
      role="alert"
    >
      <div className={`flex-shrink-0 ${config.iconColor}`}>
        <AlertTriangle className="w-5 h-5" />
      </div>

      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium ${config.textColor}`}>{displayMessage}</p>
      </div>

      <div className="flex items-center gap-2 flex-shrink-0">
        {onRetry && (
          <button
            onClick={onRetry}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium ${config.bgColor} ${config.textColor} hover:bg-opacity-20 transition-colors border ${config.borderColor}`}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Tentar novamente
          </button>
        )}

        {onDismiss && (
          <button
            onClick={handleDismiss}
            className={`p-1 rounded hover:bg-white/5 transition-colors ${config.textColor}`}
            aria-label="Fechar erro"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorBanner;
