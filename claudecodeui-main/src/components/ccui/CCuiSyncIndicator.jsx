import React from 'react';

export default function CCuiSyncIndicator({ status = 'disconnected', sessionId, className = '' }) {
  const statusConfig = {
    connected: { color: 'bg-green-500', label: 'Live', pulse: true },
    connecting: { color: 'bg-yellow-500', label: 'Connecting', pulse: true },
    disconnected: { color: 'bg-gray-600', label: 'Offline', pulse: false },
    error: { color: 'bg-red-500', label: 'Error', pulse: false }
  };
  const config = statusConfig[status] || statusConfig.disconnected;

  return (
    <div className={`flex items-center gap-2 font-mono text-xs ${className}`}>
      <div className="relative">
        <div className={`w-2 h-2 rounded-full ${config.color}`} />
        {config.pulse && <div className={`absolute inset-0 w-2 h-2 rounded-full ${config.color} animate-ping opacity-75`} />}
      </div>
      <span className="text-gray-400">{config.label}</span>
      {sessionId && status === 'connected' && <span className="text-[#FF6B4A]">{sessionId.slice(0, 6)}</span>}
    </div>
  );
}
