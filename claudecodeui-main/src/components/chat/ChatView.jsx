import { useState, useEffect, useRef, useCallback } from 'react';
import ChatHeader from './ChatHeader';
import ChatInput from './ChatInput';
import MessageList from './MessageList';
import ThinkingIndicator from './ThinkingIndicator';
import { safeLocalStorage } from '../../utils/chatUtils';

/**
 * ChatView - Container component that orchestrates the modular chat interface
 *
 * This component replaces the monolithic ChatInterface.jsx (4788 lines) with a clean,
 * modular architecture using smaller, focused components.
 *
 * Architecture:
 * - ChatHeader: Model selection and header controls
 * - MessageList: Displays conversation messages with auto-scroll
 * - ThinkingIndicator: Shows AI processing state
 * - ChatInput: Message input with send functionality
 *
 * @param {Object} props
 * @param {Object} props.selectedProject - Currently selected project
 * @param {Object} props.selectedSession - Currently selected chat session
 * @param {WebSocket} props.ws - WebSocket connection for real-time communication
 * @param {Function} props.sendMessage - Function to send messages via WebSocket
 * @param {Array} props.messages - Array of chat messages
 * @param {Function} props.onFileOpen - Callback when a file is clicked
 * @param {Function} props.onInputFocusChange - Callback for input focus changes
 * @param {Function} props.onSessionActive - Callback when session becomes active
 * @param {Function} props.onSessionInactive - Callback when session becomes inactive
 * @param {Function} props.onSessionProcessing - Callback when session starts processing
 * @param {Function} props.onSessionNotProcessing - Callback when session stops processing
 * @param {Set} props.processingSessions - Set of currently processing session IDs
 * @param {Function} props.onReplaceTemporarySession - Callback to replace temporary session
 * @param {Function} props.onNavigateToSession - Callback to navigate to a session
 * @param {Function} props.onShowSettings - Callback to show settings panel
 * @param {boolean} props.autoExpandTools - Whether to auto-expand tool calls
 * @param {boolean} props.showRawParameters - Whether to show raw parameters
 * @param {boolean} props.showThinking - Whether to show thinking indicator
 * @param {boolean} props.autoScrollToBottom - Whether to auto-scroll to bottom
 * @param {boolean} props.sendByCtrlEnter - Whether to send by Ctrl+Enter
 * @param {number} props.externalMessageUpdate - External trigger for message updates
 * @param {Function} props.onShowAllTasks - Callback to show all tasks
 */
export default function ChatView({
  selectedProject,
  selectedSession,
  ws,
  sendMessage,
  messages = [],
  onFileOpen,
  onInputFocusChange,
  onSessionActive,
  onSessionInactive,
  onSessionProcessing,
  onSessionNotProcessing,
  processingSessions,
  onReplaceTemporarySession,
  onNavigateToSession,
  onShowSettings,
  autoExpandTools = false,
  showRawParameters = false,
  showThinking = true,
  autoScrollToBottom = true,
  sendByCtrlEnter = false,
  externalMessageUpdate,
  onShowAllTasks
}) {
  // State management
  const [chatMessages, setChatMessages] = useState([]);
  const [currentModel, setCurrentModel] = useState('claude-sonnet-4-20250514');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [input, setInput] = useState('');

  // Refs
  const wsRef = useRef(ws);
  const sessionIdRef = useRef(currentSessionId);

  // Update refs when props change
  useEffect(() => {
    wsRef.current = ws;
  }, [ws]);

  useEffect(() => {
    sessionIdRef.current = currentSessionId;
  }, [currentSessionId]);

  // Load saved model preference
  useEffect(() => {
    if (selectedProject) {
      const savedModel = safeLocalStorage.getItem(`chat_model_${selectedProject.name}`);
      if (savedModel) {
        setCurrentModel(savedModel);
      }
    }
  }, [selectedProject]);

  // Save model preference when it changes
  useEffect(() => {
    if (selectedProject && currentModel) {
      safeLocalStorage.setItem(`chat_model_${selectedProject.name}`, currentModel);
    }
  }, [selectedProject, currentModel]);

  // Load messages from props or localStorage
  useEffect(() => {
    if (messages && messages.length > 0) {
      setChatMessages(messages);
    } else if (selectedProject) {
      const saved = safeLocalStorage.getItem(`chat_messages_${selectedProject.name}`);
      if (saved) {
        try {
          setChatMessages(JSON.parse(saved));
        } catch (e) {
          console.error('Failed to parse saved messages:', e);
          setChatMessages([]);
        }
      }
    }
  }, [selectedProject, messages]);

  // Save messages to localStorage
  useEffect(() => {
    if (selectedProject && chatMessages.length > 0) {
      safeLocalStorage.setItem(
        `chat_messages_${selectedProject.name}`,
        JSON.stringify(chatMessages)
      );
    }
  }, [selectedProject, chatMessages]);

  // Update session ID when selected session changes
  useEffect(() => {
    if (selectedSession?.id) {
      setCurrentSessionId(selectedSession.id);
    }
  }, [selectedSession]);

  // Handle WebSocket messages
  useEffect(() => {
    if (!ws) return;

    const handleMessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'session-created':
            handleSessionCreated(data);
            break;
          case 'message':
            handleIncomingMessage(data);
            break;
          case 'thinking':
            setIsThinking(true);
            break;
          case 'thinking-complete':
            setIsThinking(false);
            break;
          case 'processing-start':
            setIsProcessing(true);
            if (onSessionProcessing) {
              onSessionProcessing(currentSessionId);
            }
            break;
          case 'processing-complete':
          case 'claude-complete':
            setIsProcessing(false);
            setIsThinking(false);
            if (onSessionNotProcessing) {
              onSessionNotProcessing(currentSessionId);
            }
            if (onSessionInactive) {
              onSessionInactive(currentSessionId);
            }
            break;
          case 'session-aborted':
            setIsProcessing(false);
            setIsThinking(false);
            if (onSessionInactive) {
              onSessionInactive(currentSessionId);
            }
            break;
          case 'error':
            handleError(data);
            break;
          default:
            break;
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.addEventListener('message', handleMessage);

    return () => {
      ws.removeEventListener('message', handleMessage);
    };
  }, [ws, currentSessionId, onSessionProcessing, onSessionNotProcessing, onSessionInactive]);

  // Handle session creation
  const handleSessionCreated = useCallback((data) => {
    const newSessionId = data.sessionId;
    setCurrentSessionId(newSessionId);

    // Replace temporary session if callback provided
    if (onReplaceTemporarySession && data.temporaryId) {
      onReplaceTemporarySession(data.temporaryId, newSessionId);
    }
  }, [onReplaceTemporarySession]);

  // Handle incoming messages
  const handleIncomingMessage = useCallback((data) => {
    const newMessage = {
      id: data.messageId || Date.now(),
      role: data.role || 'assistant',
      type: data.role === 'user' ? 'user' : 'assistant',
      content: data.content || '',
      timestamp: new Date(data.timestamp || Date.now()),
      toolCalls: data.toolCalls,
      toolResults: data.toolResults
    };

    setChatMessages(prev => {
      // Prevent duplicate messages
      const exists = prev.some(msg => msg.id === newMessage.id);
      if (exists) return prev;
      return [...prev, newMessage];
    });
  }, []);

  // Handle errors
  const handleError = useCallback((data) => {
    const errorMessage = {
      id: Date.now(),
      type: 'error',
      role: 'assistant',
      content: data.message || 'An error occurred',
      timestamp: new Date()
    };

    setChatMessages(prev => [...prev, errorMessage]);
    setIsProcessing(false);
    setIsThinking(false);
  }, []);

  // Handle message send
  const handleSend = useCallback(async (message) => {
    if (!message.trim() || isProcessing || !selectedProject) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      role: 'user',
      content: message.trim(),
      timestamp: new Date()
    };

    // Add user message to chat
    setChatMessages(prev => [...prev, userMessage]);

    // Set processing state
    setIsProcessing(true);
    setIsThinking(true);

    // Determine session ID for this message
    const effectiveSessionId = currentSessionId || `temp-${Date.now()}`;

    // Mark session as active
    if (onSessionActive) {
      onSessionActive(effectiveSessionId);
    }

    // Send message via WebSocket or provided function
    if (sendMessage) {
      sendMessage({
        content: message.trim(),
        sessionId: currentSessionId,
        projectId: selectedProject.id,
        projectName: selectedProject.name,
        model: currentModel
      });
    } else if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'chat-message',
        content: message.trim(),
        sessionId: currentSessionId,
        projectId: selectedProject.id,
        projectName: selectedProject.name,
        model: currentModel
      }));
    } else {
      // WebSocket not ready
      handleError({ message: 'WebSocket connection not available' });
    }
  }, [
    isProcessing,
    selectedProject,
    currentSessionId,
    currentModel,
    sendMessage,
    ws,
    onSessionActive
  ]);

  // Handle model change
  const handleModelChange = useCallback((modelId) => {
    setCurrentModel(modelId);
  }, []);

  // Handle sidebar toggle (placeholder for future implementation)
  const handleToggleSidebar = useCallback(() => {
    // This would be implemented by parent component
    console.log('Toggle sidebar');
  }, []);

  // Handle actions click
  const handleActionsClick = useCallback(() => {
    if (onShowAllTasks) {
      onShowAllTasks();
    }
  }, [onShowAllTasks]);

  // Handle history click
  const handleHistoryClick = useCallback(() => {
    // Navigate to sessions view or show history
    console.log('Show history');
  }, []);

  // Determine if we should show the thinking indicator
  const shouldShowThinking = showThinking && isThinking && isProcessing;

  // Determine placeholder text
  const placeholder = !selectedProject
    ? 'Select a project to start chatting...'
    : isProcessing
    ? 'Claude is processing...'
    : 'Describe your task or enter a command...';

  return (
    <div className="flex flex-col h-full bg-zinc-950">
      {/* Header */}
      <ChatHeader
        currentModel={currentModel}
        onModelChange={handleModelChange}
        onToggleSidebar={handleToggleSidebar}
        projectName={selectedProject?.name}
      />

      {/* Messages */}
      <MessageList
        messages={chatMessages}
        isProcessing={isProcessing}
        autoScroll={autoScrollToBottom}
        onFileOpen={onFileOpen}
      />

      {/* Thinking indicator - shown when processing */}
      {shouldShowThinking && (
        <div className="px-4 pb-2">
          <div className="max-w-4xl mx-auto">
            <ThinkingIndicator />
          </div>
        </div>
      )}

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        onActionsClick={handleActionsClick}
        onHistoryClick={handleHistoryClick}
        isProcessing={isProcessing}
        placeholder={placeholder}
      />
    </div>
  );
}
