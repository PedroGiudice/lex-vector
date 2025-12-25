import React from 'react';
import FileTree from '../FileTree';
import GitPanel from '../GitPanel';
import Shell from '../Shell';
import CCuiSearchView from './CCuiSearchView';
import CCuiConsoleView from './CCuiConsoleView';
import { Clock, Plus } from 'lucide-react';

/**
 * CCuiSidebar - Dynamic sidebar that changes content based on activeView
 *
 * BASE-UI Pattern: Icon Rail controls sidebar content, not main content
 *
 * @param {Object} props
 * @param {string} props.activeView - 'chat' | 'files' | 'search' | 'shell' | 'git' | 'console'
 * @param {Array} props.sessions - Session list for chat view
 * @param {Object} props.selectedSession - Currently selected session
 * @param {Function} props.onSessionSelect - Session selection handler
 * @param {Function} props.onNewSession - New session handler
 */
const CCuiSidebar = ({
  activeView = 'chat',
  sessions = [],
  selectedSession,
  onSessionSelect,
  onNewSession,
  projectPath = '',
}) => {

  // Group sessions by time
  const groupSessionsByTime = (sessions) => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);

    const groups = {
      today: [],
      yesterday: [],
      thisWeek: [],
      older: []
    };

    sessions.forEach(session => {
      const date = new Date(session.lastActivity || session.createdAt);
      if (date >= today) {
        groups.today.push(session);
      } else if (date >= yesterday) {
        groups.yesterday.push(session);
      } else if (date >= weekAgo) {
        groups.thisWeek.push(session);
      } else {
        groups.older.push(session);
      }
    });

    return groups;
  };

  const renderChatHistory = () => {
    const groupedSessions = groupSessionsByTime(sessions);

    return (
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-ccui-border-primary">
          <h2 className="text-xs font-semibold text-ccui-text-muted uppercase tracking-wider">CHATS</h2>
          <div className="flex items-center gap-1">
            <button className="p-1 rounded hover:bg-ccui-bg-hover text-ccui-text-subtle hover:text-ccui-text-secondary transition-colors">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </button>
            <button className="p-1 rounded hover:bg-ccui-bg-hover text-ccui-text-subtle hover:text-ccui-text-secondary transition-colors">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
              </svg>
            </button>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="px-3 py-2">
          <button
            onClick={onNewSession}
            className="w-full flex items-center justify-center gap-2 bg-ccui-bg-hover hover:bg-ccui-bg-active text-ccui-text-primary text-xs py-2 rounded border border-ccui-border-secondary transition-colors"
          >
            <Plus size={14} className="text-ccui-accent" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Session List */}
        <div className="flex-1 overflow-y-auto ccui-scrollbar">
          {sessions.length === 0 ? (
            <div className="px-4 py-8 text-center text-ccui-text-subtle text-xs">
              No sessions yet
            </div>
          ) : (
            <>
              {groupedSessions.today.length > 0 && (
                <div className="py-2">
                  <div className="px-4 py-1.5 text-[10px] text-ccui-text-subtle uppercase tracking-wider font-semibold">TODAY</div>
                  {groupedSessions.today.map(session => (
                    <SessionItem
                      key={session.id}
                      session={session}
                      isSelected={selectedSession?.id === session.id}
                      onSelect={() => onSessionSelect?.(session)}
                    />
                  ))}
                </div>
              )}

              {groupedSessions.yesterday.length > 0 && (
                <div className="py-2">
                  <div className="px-4 py-1.5 text-[10px] text-ccui-text-subtle uppercase tracking-wider font-semibold">YESTERDAY</div>
                  {groupedSessions.yesterday.map(session => (
                    <SessionItem
                      key={session.id}
                      session={session}
                      isSelected={selectedSession?.id === session.id}
                      onSelect={() => onSessionSelect?.(session)}
                    />
                  ))}
                </div>
              )}

              {groupedSessions.thisWeek.length > 0 && (
                <div className="py-2">
                  <div className="px-4 py-1.5 text-[10px] text-ccui-text-subtle uppercase tracking-wider font-semibold">PREVIOUS 7 DAYS</div>
                  {groupedSessions.thisWeek.map(session => (
                    <SessionItem
                      key={session.id}
                      session={session}
                      isSelected={selectedSession?.id === session.id}
                      onSelect={() => onSessionSelect?.(session)}
                    />
                  ))}
                </div>
              )}

              {groupedSessions.older.length > 0 && (
                <div className="py-2">
                  <div className="px-4 py-1.5 text-[10px] text-ccui-text-subtle uppercase tracking-wider font-semibold">OLDER</div>
                  {groupedSessions.older.map(session => (
                    <SessionItem
                      key={session.id}
                      session={session}
                      isSelected={selectedSession?.id === session.id}
                      onSelect={() => onSessionSelect?.(session)}
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    );
  };

  const renderContent = () => {
    switch (activeView) {
      case 'chat':
        return renderChatHistory();
      case 'files':
        return (
          <div className="h-full">
            <div className="px-4 py-3 border-b border-ccui-border-primary">
              <h2 className="text-xs font-semibold text-ccui-text-muted uppercase tracking-wider">FILES</h2>
            </div>
            <FileTree projectPath={projectPath} />
          </div>
        );
      case 'search':
        return <CCuiSearchView />;
      case 'shell':
        return (
          <div className="h-full flex flex-col">
            <div className="px-4 py-3 border-b border-ccui-border-primary">
              <h2 className="text-xs font-semibold text-ccui-text-muted uppercase tracking-wider">SHELL</h2>
            </div>
            <div className="flex-1">
              <Shell />
            </div>
          </div>
        );
      case 'git':
        return (
          <div className="h-full">
            <div className="px-4 py-3 border-b border-ccui-border-primary">
              <h2 className="text-xs font-semibold text-ccui-text-muted uppercase tracking-wider">GIT</h2>
            </div>
            <GitPanel projectPath={projectPath} />
          </div>
        );
      case 'console':
        return <CCuiConsoleView />;
      default:
        return renderChatHistory();
    }
  };

  return (
    <div className="w-60 flex flex-col h-full bg-ccui-bg-secondary border-r border-ccui-border-primary text-ccui-text-primary">
      {renderContent()}
    </div>
  );
};

// Session item component with coral left border for selected
const SessionItem = ({ session, isSelected, onSelect }) => {
  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <button
      onClick={onSelect}
      className={`
        w-full px-4 py-2 text-left transition-all border-l-2
        ${isSelected
          ? 'border-ccui-accent bg-ccui-bg-active text-ccui-text-primary'
          : 'border-transparent text-ccui-text-secondary hover:bg-ccui-bg-hover hover:text-ccui-text-primary'
        }
      `}
    >
      <div className="text-xs truncate font-medium">
        {session.summary || session.name || 'New Session'}
      </div>
      <div className="flex items-center gap-1 mt-0.5 text-[10px] text-ccui-text-subtle">
        <Clock size={10} />
        <span>{formatTime(session.lastActivity || session.createdAt)}</span>
      </div>
    </button>
  );
};

export default CCuiSidebar;
