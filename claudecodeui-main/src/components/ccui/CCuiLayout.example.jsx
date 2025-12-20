import React, { useState } from 'react';
import {
  CCuiHeader,
  CCuiIconRail,
  CCuiSidebar,
  CCuiStatusBar
} from './index';

/**
 * Example usage of CCui Layout Components
 *
 * This demonstrates how to compose all CCui components together
 * to create a Claude Code-inspired interface.
 */
const CCuiLayoutExample = () => {
  const [activeView, setActiveView] = useState('chat');
  const [activeSessionId, setActiveSessionId] = useState('session-1');
  const [isProcessing, setIsProcessing] = useState(false);

  // Example sessions data
  const exampleSessions = [
    {
      id: 'session-1',
      title: 'Build authentication system',
      timestamp: new Date().toISOString()
    },
    {
      id: 'session-2',
      title: 'Fix navbar responsive design',
      timestamp: new Date(Date.now() - 3600000).toISOString() // 1 hour ago
    },
    {
      id: 'session-3',
      title: 'Add dark mode toggle',
      timestamp: new Date(Date.now() - 86400000).toISOString() // Yesterday
    },
    {
      id: 'session-4',
      title: 'Optimize database queries',
      timestamp: new Date(Date.now() - 3 * 86400000).toISOString() // 3 days ago
    },
    {
      id: 'session-5',
      title: 'Create landing page',
      timestamp: new Date(Date.now() - 10 * 86400000).toISOString() // 10 days ago
    }
  ];

  const handleNewChat = () => {
    console.log('New chat clicked');
    // Implementation: Create new session
  };

  const handleSettingsClick = () => {
    console.log('Settings clicked');
    // Implementation: Open settings modal
  };

  const handleSearchClick = () => {
    console.log('Search clicked');
    // Implementation: Open search modal
  };

  return (
    <div className="h-screen flex flex-col bg-ccui-bg-primary text-ccui-text-primary">
      {/* Header */}
      <CCuiHeader
        projectPath="/home/user/projects/my-awesome-app"
        currentModel="claude-sonnet-4-5"
        onSettingsClick={handleSettingsClick}
        onSearchClick={handleSearchClick}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Icon Rail */}
        <CCuiIconRail
          activeView={activeView}
          onViewChange={setActiveView}
          onSettingsClick={handleSettingsClick}
        />

        {/* Sidebar (shown when chat view is active) */}
        {activeView === 'chat' && (
          <CCuiSidebar
            sessions={exampleSessions}
            activeSessionId={activeSessionId}
            onSessionSelect={setActiveSessionId}
            onNewChat={handleNewChat}
          />
        )}

        {/* Main Content */}
        <main className="flex-1 bg-ccui-bg-primary overflow-auto">
          <div className="p-8">
            <h1 className="text-2xl font-semibold mb-4">
              {activeView === 'chat' && 'Chat View'}
              {activeView === 'files' && 'Files View'}
              {activeView === 'search' && 'Search View'}
              {activeView === 'git' && 'Git View'}
              {activeView === 'debug' && 'Debug View'}
            </h1>
            <p className="text-ccui-text-secondary">
              Main content area for {activeView} view.
            </p>

            {/* Demo: Toggle Processing State */}
            <button
              onClick={() => setIsProcessing(!isProcessing)}
              className="mt-4 px-4 py-2 bg-ccui-accent hover:bg-ccui-accent/90 text-white rounded transition-colors"
            >
              Toggle Processing State
            </button>
          </div>
        </main>
      </div>

      {/* Status Bar */}
      <CCuiStatusBar
        isProcessing={isProcessing}
        contextPercent={45}
        encoding="UTF-8"
        language="JavaScript"
      />
    </div>
  );
};

export default CCuiLayoutExample;
