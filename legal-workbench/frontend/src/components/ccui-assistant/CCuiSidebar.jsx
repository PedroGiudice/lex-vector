import React from 'react';
import { Clock, Plus } from 'lucide-react';

/**
 * Helper function to group sessions by time
 * @param {Array} sessions - Array of session objects with timestamp
 * @returns {Object} Grouped sessions by time category
 */
const groupSessionsByTime = (sessions) => {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const sevenDaysAgo = new Date(today);
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

  const groups = {
    today: [],
    yesterday: [],
    previous7Days: [],
    older: []
  };

  sessions.forEach(session => {
    const sessionDate = new Date(session.timestamp);

    if (sessionDate >= today) {
      groups.today.push(session);
    } else if (sessionDate >= yesterday) {
      groups.yesterday.push(session);
    } else if (sessionDate >= sevenDaysAgo) {
      groups.previous7Days.push(session);
    } else {
      groups.older.push(session);
    }
  });

  return groups;
};

/**
 * Format time for display
 * @param {Date|string|number} timestamp
 * @returns {string} Formatted time (HH:MM)
 */
const formatTime = (timestamp) => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
};

/**
 * SessionGroup - Renders a group of sessions
 */
const SessionGroup = ({ title, sessions, activeSessionId, onSessionSelect }) => {
  if (sessions.length === 0) return null;

  return (
    <div className="mb-4">
      <h3 className="text-xs font-semibold text-ccui-text-muted uppercase tracking-wide px-3 mb-2">
        {title}
      </h3>
      <div className="flex flex-col gap-0.5">
        {sessions.map(session => {
          const isActive = session.id === activeSessionId;

          return (
            <button
              key={session.id}
              onClick={() => onSessionSelect(session.id)}
              className={`
                relative w-full px-3 py-2 text-left transition-colors
                ${isActive
                  ? 'bg-ccui-bg-primary text-ccui-text-primary'
                  : 'text-ccui-text-secondary hover:bg-ccui-bg-primary/50 hover:text-ccui-text-primary'
                }
              `}
            >
              {/* Active Indicator Bar */}
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-8 bg-ccui-accent rounded-r" />
              )}

              <div className="flex items-start gap-2">
                <Clock size={14} className="mt-0.5 text-ccui-text-muted flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">{session.title || 'Untitled Session'}</p>
                  <p className="text-xs text-ccui-text-muted">
                    {formatTime(session.timestamp)}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

/**
 * CCuiSidebar - Chat-centric sidebar with temporal session grouping
 *
 * @param {Object} props
 * @param {Array} props.sessions - Array of session objects
 * @param {string} props.activeSessionId - Currently active session ID
 * @param {Function} props.onSessionSelect - Session select handler
 * @param {Function} props.onNewChat - New chat button click handler
 */
const CCuiSidebar = ({
  sessions = [],
  activeSessionId,
  onSessionSelect,
  onNewChat
}) => {
  const groupedSessions = groupSessionsByTime(sessions);

  return (
    <aside className="w-64 bg-ccui-bg-secondary border-r border-ccui-border-primary flex flex-col">
      {/* Header with New Chat Button */}
      <div className="p-3 border-b border-ccui-border-primary">
        <button
          onClick={onNewChat}
          className="w-full px-4 py-2 bg-ccui-accent hover:bg-ccui-accent/90 text-white rounded flex items-center justify-center gap-2 transition-colors"
        >
          <Plus size={16} />
          <span className="text-sm font-medium">New Chat</span>
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto py-4">
        <SessionGroup
          title="Today"
          sessions={groupedSessions.today}
          activeSessionId={activeSessionId}
          onSessionSelect={onSessionSelect}
        />
        <SessionGroup
          title="Yesterday"
          sessions={groupedSessions.yesterday}
          activeSessionId={activeSessionId}
          onSessionSelect={onSessionSelect}
        />
        <SessionGroup
          title="Previous 7 Days"
          sessions={groupedSessions.previous7Days}
          activeSessionId={activeSessionId}
          onSessionSelect={onSessionSelect}
        />
        <SessionGroup
          title="Older"
          sessions={groupedSessions.older}
          activeSessionId={activeSessionId}
          onSessionSelect={onSessionSelect}
        />
      </div>
    </aside>
  );
};

export default CCuiSidebar;
