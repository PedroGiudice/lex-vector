import React, { useState, useEffect, useCallback } from 'react';
import { CCuiLayout } from './components/ccui';
import { useAuth } from './contexts/AuthContext';
import { useWebSocketContext } from './contexts/WebSocketContext';
import { api, authenticatedFetch } from './utils/api';

/**
 * CCuiApp - CCui-themed app connected to real backend
 *
 * This wraps CCuiLayout with real WebSocket, session, and auth functionality.
 */
export default function CCuiApp() {
  const { user, isAuthenticated } = useAuth();
  const { ws, sendMessage: wsSend, isConnected } = useWebSocketContext();

  // State
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [contextPercent, setContextPercent] = useState(0);

  // Load projects on mount
  useEffect(() => {
    if (user) {
      loadProjects();
    }
  }, [user]);

  // Load sessions when project changes
  useEffect(() => {
    if (selectedProject) {
      loadSessions(selectedProject.name);
    }
  }, [selectedProject]);

  // WebSocket message handler
  useEffect(() => {
    if (!ws) return;

    const handleMessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWsMessage(data);
      } catch (e) {
        console.error('WebSocket parse error:', e);
      }
    };

    ws.addEventListener('message', handleMessage);
    return () => ws.removeEventListener('message', handleMessage);
  }, [ws]);

  const loadProjects = async () => {
    try {
      const response = await api.projects();
      if (response.ok) {
        const data = await response.json();
        setProjects(data.projects || []);
        if (data.projects?.length > 0 && !selectedProject) {
          setSelectedProject(data.projects[0]);
        }
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const loadSessions = async (projectName) => {
    try {
      const response = await api.sessions(projectName, 50, 0);
      if (response.ok) {
        const data = await response.json();
        // Transform sessions to have required fields
        const transformedSessions = (data.sessions || []).map(s => ({
          ...s,
          id: s.session_id || s.id,
          title: s.name || s.title || 'New Chat',
          updatedAt: s.updated_at || s.updatedAt || s.created_at || new Date().toISOString(),
          createdAt: s.created_at || s.createdAt || new Date().toISOString(),
        }));
        setSessions(transformedSessions);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const handleWsMessage = useCallback((data) => {
    const msgType = data.type || data.msgType;

    switch (msgType) {
      case 'message':
      case 'claude-response':
        setMessages(prev => {
          // Check if we're updating an existing streaming message
          const existingIdx = prev.findIndex(m => m.id === data.messageId && m.isStreaming);
          if (existingIdx >= 0) {
            const updated = [...prev];
            updated[existingIdx] = {
              ...updated[existingIdx],
              content: data.content || data.message || '',
              isStreaming: false,
            };
            return updated;
          }
          // Add new message
          return [...prev, {
            id: data.messageId || Date.now(),
            role: data.role || 'assistant',
            content: data.content || data.message || '',
            type: 'text',
            timestamp: new Date(),
          }];
        });
        setIsProcessing(false);
        break;

      case 'thinking':
      case 'claude-thinking':
        setMessages(prev => [...prev, {
          id: `thinking-${Date.now()}`,
          role: 'assistant',
          content: data.content || data.thinking || 'Thinking...',
          type: 'thought',
          label: 'Reasoning',
          isStreaming: true,
        }]);
        break;

      case 'thinking-complete':
        setMessages(prev => prev.map(m =>
          m.type === 'thought' && m.isStreaming
            ? { ...m, isStreaming: false, duration: data.duration }
            : m
        ));
        break;

      case 'processing':
      case 'claude-start':
        setIsProcessing(true);
        break;

      case 'complete':
      case 'claude-complete':
        setIsProcessing(false);
        break;

      case 'context-update':
        if (data.percentUsed !== undefined) {
          setContextPercent(Math.round(data.percentUsed));
        }
        break;

      case 'stream-start':
        setMessages(prev => [...prev, {
          id: data.messageId || Date.now(),
          role: 'assistant',
          content: '',
          type: 'text',
          isStreaming: true,
        }]);
        break;

      case 'stream-chunk':
        setMessages(prev => {
          const lastIdx = prev.length - 1;
          if (lastIdx >= 0 && prev[lastIdx].isStreaming) {
            const updated = [...prev];
            updated[lastIdx] = {
              ...updated[lastIdx],
              content: updated[lastIdx].content + (data.chunk || data.content || ''),
            };
            return updated;
          }
          return prev;
        });
        break;

      case 'stream-end':
        setMessages(prev => prev.map(m =>
          m.isStreaming ? { ...m, isStreaming: false } : m
        ));
        setIsProcessing(false);
        break;

      default:
        // Unknown message type - log for debugging
        if (import.meta.env.DEV) {
          console.log('Unknown WS message:', data);
        }
        break;
    }
  }, []);

  const handleSessionSelect = useCallback(async (sessionId) => {
    setActiveSessionId(sessionId);
    setMessages([]);

    // Load session messages
    if (selectedProject) {
      try {
        const response = await api.sessionMessages(selectedProject.name, sessionId);
        if (response.ok) {
          const data = await response.json();
          const transformedMessages = (data.messages || []).map(m => ({
            id: m.id || m.message_id || Date.now(),
            role: m.role || 'user',
            content: m.content || m.message || '',
            type: m.type || 'text',
            timestamp: m.timestamp || m.created_at,
          }));
          setMessages(transformedMessages);
        }
      } catch (error) {
        console.error('Failed to load messages:', error);
      }
    }
  }, [selectedProject]);

  const handleNewChat = useCallback(() => {
    setActiveSessionId(null);
    setMessages([]);
  }, []);

  const handleSendMessage = useCallback((content) => {
    if (!content.trim()) return;

    // Add user message to UI immediately
    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: content.trim(),
      type: 'text',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsProcessing(true);

    // Send via WebSocket
    if (wsSend) {
      wsSend({
        type: 'chat-message',
        content: content.trim(),
        sessionId: activeSessionId,
        projectName: selectedProject?.name,
      });
    }
  }, [activeSessionId, selectedProject, wsSend]);

  const handleSettingsClick = useCallback(() => {
    // Navigate to settings or open settings panel
    console.log('Settings clicked');
  }, []);

  // Project path for header
  const projectPath = selectedProject
    ? `~/${selectedProject.displayName || selectedProject.name}`
    : '~/project';

  return (
    <CCuiLayout
      projectPath={projectPath}
      currentModel="Claude Sonnet"
      sessions={sessions}
      activeSessionId={activeSessionId}
      messages={messages}
      isProcessing={isProcessing}
      contextPercent={contextPercent}
      onSessionSelect={handleSessionSelect}
      onNewChat={handleNewChat}
      onSendMessage={handleSendMessage}
      onSettingsClick={handleSettingsClick}
    />
  );
}
