import React from 'react';
import { MessageSquare, Files, Search, GitBranch, Bug, Settings } from 'lucide-react';

/**
 * CCuiIconRail - Vertical icon rail for view switching
 *
 * @param {Object} props
 * @param {string} props.activeView - Currently active view ('chat' | 'files' | 'search' | 'git' | 'debug')
 * @param {Function} props.onViewChange - View change handler
 * @param {Function} props.onSettingsClick - Settings button click handler
 */
const CCuiIconRail = ({
  activeView = 'chat',
  onViewChange,
  onSettingsClick
}) => {
  const views = [
    { id: 'chat', icon: MessageSquare, label: 'Chat' },
    { id: 'files', icon: Files, label: 'Files' },
    { id: 'search', icon: Search, label: 'Search' },
    { id: 'git', icon: GitBranch, label: 'Git' },
    { id: 'debug', icon: Bug, label: 'Debug' },
  ];

  const handleViewClick = (viewId) => {
    if (onViewChange) {
      onViewChange(viewId);
    }
  };

  return (
    <nav className="w-12 bg-ccui-bg-secondary border-r border-ccui-border-primary flex flex-col items-center py-2">
      {/* Main Views */}
      <div className="flex-1 flex flex-col gap-1 w-full">
        {views.map(({ id, icon: Icon, label }) => {
          const isActive = activeView === id;

          return (
            <button
              key={id}
              onClick={() => handleViewClick(id)}
              className={`
                relative w-full h-12 flex items-center justify-center
                transition-colors
                ${isActive
                  ? 'text-ccui-text-primary'
                  : 'text-ccui-text-muted hover:text-ccui-text-secondary'
                }
              `}
              aria-label={label}
              aria-current={isActive ? 'page' : undefined}
            >
              {/* Active Indicator Bar */}
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-8 bg-ccui-accent rounded-r" />
              )}

              <Icon size={20} />
            </button>
          );
        })}
      </div>

      {/* Settings at Bottom */}
      <button
        onClick={onSettingsClick}
        className="w-full h-12 flex items-center justify-center text-ccui-text-muted hover:text-ccui-text-secondary transition-colors"
        aria-label="Settings"
      >
        <Settings size={20} />
      </button>
    </nav>
  );
};

export default CCuiIconRail;
