import React, { useState } from 'react';
import { Wifi, WifiOff, Loader2 } from 'lucide-react';

export type ConnectionState = 'connected' | 'connecting' | 'disconnected' | 'error' | 'disabled';

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
    pulseColor: string;
    label: string;
    description: string;
    showPulse: boolean;
  }
> = {
  connected: {
    dotColor: 'bg-green-500',
    pulseColor: 'bg-green-500/50',
    label: 'Connected',
    description: 'Connected to Claude backend',
    showPulse: false,
  },
  connecting: {
    dotColor: 'bg-yellow-500',
    pulseColor: 'bg-yellow-500/50',
    label: 'Connecting',
    description: 'Establishing connection...',
    showPulse: true,
  },
  disconnected: {
    dotColor: 'bg-red-500',
    pulseColor: 'bg-red-500/50',
    label: 'Disconnected',
    description: 'Connection lost. Click to retry.',
    showPulse: false,
  },
  error: {
    dotColor: 'bg-red-500',
    pulseColor: 'bg-red-500/50',
    label: 'Error',
    description: 'Connection error. Click to retry.',
    showPulse: false,
  },
  disabled: {
    dotColor: 'bg-gray-500',
    pulseColor: 'bg-gray-500/50',
    label: 'Offline',
    description: 'WebSocket disabled. Running in offline mode.',
    showPulse: false,
  },
};

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  status,
  retryCount,
  maxRetries,
  onRetry,
}) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const config = statusConfig[status];

  const isRetrying = status === 'connecting' && retryCount !== undefined && retryCount > 0;
  const canRetry =
    (status === 'disconnected' || status === 'error' || status === 'disabled') && onRetry;

  const handleClick = () => {
    if (canRetry) {
      onRetry?.();
    }
  };

  const getDescription = () => {
    if (isRetrying && maxRetries !== undefined) {
      return `Reconnecting... (${retryCount}/${maxRetries})`;
    }
    return config.description;
  };

  return (
    <div className="relative inline-flex items-center">
      <button
        className={`
          flex items-center gap-2 px-2 py-1 rounded-md
          transition-colors duration-200
          ${canRetry ? 'hover:bg-[#1a1a1a] cursor-pointer' : 'cursor-default'}
        `}
        onClick={handleClick}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        disabled={!canRetry}
        aria-label={`Connection status: ${config.label}`}
      >
        {/* Status Dot */}
        <span className="relative flex h-2.5 w-2.5">
          {config.showPulse && (
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full ${config.pulseColor} opacity-75`}
            />
          )}
          <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${config.dotColor}`} />
        </span>

        {/* Status Icon (optional, shown on hover or specific states) */}
        {status === 'connecting' && (
          <Loader2 className="w-3.5 h-3.5 text-yellow-500 animate-spin" />
        )}
        {status === 'connected' && <Wifi className="w-3.5 h-3.5 text-green-500 opacity-60" />}
        {(status === 'disconnected' || status === 'error') && (
          <WifiOff className="w-3.5 h-3.5 text-red-500" />
        )}
      </button>

      {/* Tooltip */}
      {showTooltip && (
        <div
          className={`
            absolute z-50 px-3 py-2 text-xs rounded-lg shadow-lg
            bg-[#1a1a1a] border border-[#27272a]
            bottom-full left-1/2 transform -translate-x-1/2 mb-2
            whitespace-nowrap
            animate-in fade-in zoom-in-95 duration-150
          `}
        >
          <div className="flex flex-col gap-1">
            <span className="font-semibold text-[#e3e1de]">{config.label}</span>
            <span className="text-[#888]">{getDescription()}</span>
            {canRetry && <span className="text-[#d97757] text-[10px]">Click to reconnect</span>}
          </div>

          {/* Tooltip Arrow */}
          <div
            className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-px
            border-4 border-transparent border-t-[#27272a]"
          />
        </div>
      )}
    </div>
  );
};

export default ConnectionStatus;
