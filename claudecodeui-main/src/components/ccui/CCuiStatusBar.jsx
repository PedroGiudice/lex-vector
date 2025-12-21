import React, { useState, useEffect } from 'react';
import { Activity, Clock } from 'lucide-react';
import CCuiSyncIndicator from './CCuiSyncIndicator';
import { useSessionSync } from '../../hooks/useSessionSync';

/**
 * Format elapsed time in HH:MM:SS
 * @param {number} seconds
 * @returns {string}
 */
const formatElapsedTime = (seconds) => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

/**
 * CCuiStatusBar - Minimal status bar like VS Code
 *
 * @param {Object} props
 * @param {boolean} props.isProcessing - Whether the system is currently processing
 * @param {number} props.contextPercent - Context usage percentage (0-100)
 * @param {string} props.encoding - File encoding (e.g., 'UTF-8')
 * @param {string} props.language - Current language/file type
 */
const CCuiStatusBar = ({
  isProcessing = false,
  contextPercent = 0,
  encoding = 'UTF-8',
  language = 'JavaScript'
}) => {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Session sync hook
  const { connectionStatus, isSubscribed } = useSessionSync({ autoConnect: true });

  // Derive sessionId from subscription status (placeholder for now)
  const sessionId = isSubscribed ? 'session-active' : null;

  // Session timer
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedSeconds(prev => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <footer className="h-6 bg-ccui-bg-secondary border-t border-ccui-border-primary flex items-center justify-between px-3 text-xs">
      {/* Left: Status Indicator */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          {isProcessing ? (
            <>
              <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
              <span className="text-ccui-text-secondary">BUSY</span>
            </>
          ) : (
            <>
              <div className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-ccui-text-secondary">READY</span>
            </>
          )}
        </div>

        {/* Session Sync Indicator */}
        <CCuiSyncIndicator
          status={connectionStatus}
          sessionId={sessionId}
          className="text-ccui-text-secondary"
        />

        {/* Context Usage */}
        <div className="flex items-center gap-1.5 text-ccui-text-muted">
          <Activity size={12} />
          <span>{contextPercent}% ctx</span>
        </div>
      </div>

      {/* Center: Session Timer with clock icon */}
      <div className="flex items-center gap-1.5 text-ccui-text-muted font-mono">
        <Clock size={12} />
        <span>{formatElapsedTime(elapsedSeconds)}</span>
      </div>

      {/* Right: Encoding and Language */}
      <div className="flex items-center gap-4 text-ccui-text-muted">
        <span>{encoding}</span>
        <span>{language}</span>
      </div>
    </footer>
  );
};

export default CCuiStatusBar;
