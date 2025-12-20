import React, { useState, useCallback, useRef, useEffect } from 'react';
import CCuiHeader from './CCuiHeader';
import CCuiIconRail from './CCuiIconRail';
import CCuiSidebar from './CCuiSidebar';
import CCuiStatusBar from './CCuiStatusBar';
import CCuiChatInput from './CCuiChatInput';
import CCuiMessage from './CCuiMessage';

/**
 * CCuiLayout - Main application layout with CCui design
 *
 * This component provides the visual shell. Parent components
 * should pass real data (sessions, messages, WebSocket state).
 *
 * @param {Object} props
 * @param {string} props.projectPath - Current project path
 * @param {string} props.currentModel - Current AI model
 * @param {Array} props.sessions - Session list for sidebar
 * @param {string} props.activeSessionId - Active session ID
 * @param {Array} props.messages - Current chat messages
 * @param {boolean} props.isProcessing - Whether AI is processing
 * @param {number} props.contextPercent - Context usage percentage
 * @param {Function} props.onSessionSelect - Session selection handler
 * @param {Function} props.onNewChat - New chat handler
 * @param {Function} props.onSendMessage - Message send handler
 * @param {Function} props.onSettingsClick - Settings click handler
 * @param {React.ReactNode} props.children - Optional custom content area
 */
export default function CCuiLayout({
  projectPath = '~/project',
  currentModel = 'Claude Sonnet',
  sessions = [],
  activeSessionId,
  messages = [],
  isProcessing = false,
  contextPercent = 0,
  onSessionSelect,
  onNewChat,
  onSendMessage,
  onSettingsClick,
  children,
}) {
  const [sidebarView, setSidebarView] = useState('chat');
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [messages]);

  const handleViewChange = useCallback((view) => {
    setSidebarView(view);
  }, []);

  return (
    <div className="flex flex-col h-screen w-full bg-ccui-bg-primary text-ccui-text-primary font-sans overflow-hidden ccui-selection">
      {/* Header */}
      <CCuiHeader
        projectPath={projectPath}
        currentModel={currentModel}
        onSettingsClick={onSettingsClick}
      />

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Icon Rail */}
        <CCuiIconRail
          activeView={sidebarView}
          onViewChange={handleViewChange}
          onSettingsClick={onSettingsClick}
        />

        {/* Sidebar - hidden on mobile */}
        <div className="hidden md:block">
          <CCuiSidebar
            sessions={sessions}
            activeSessionId={activeSessionId}
            onSessionSelect={onSessionSelect}
            onNewChat={onNewChat}
          />
        </div>

        {/* Main Content */}
        <main className="flex-1 flex flex-col relative bg-ccui-bg-primary">
          {/* Custom content or default chat view */}
          {children || (
            <>
              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto p-4 md:p-8 pb-32 ccui-scrollbar">
                <div className="max-w-3xl mx-auto space-y-6">
                  {messages.length === 0 && (
                    <div className="text-center py-20">
                      <div className="text-ccui-text-muted text-sm mb-2">
                        Welcome to Claude Code UI
                      </div>
                      <div className="text-ccui-text-subtle text-xs">
                        Start a conversation or select a previous chat
                      </div>
                    </div>
                  )}
                  {messages.map((msg, index) => (
                    <CCuiMessage
                      key={msg.id || index}
                      message={msg}
                      isStreaming={msg.isStreaming}
                    />
                  ))}
                  <div ref={messagesEndRef} className="h-4" />
                </div>
              </div>

              {/* Input Area */}
              <CCuiChatInput
                onSend={onSendMessage}
                disabled={isProcessing}
                placeholder={
                  isProcessing
                    ? 'Claude is thinking...'
                    : 'Describe your task or enter a command...'
                }
              />
            </>
          )}
        </main>
      </div>

      {/* Status Bar */}
      <CCuiStatusBar
        isProcessing={isProcessing}
        contextPercent={contextPercent}
      />
    </div>
  );
}
