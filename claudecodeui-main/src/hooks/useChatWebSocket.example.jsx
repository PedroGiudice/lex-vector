import React, { useState, useCallback, useEffect } from 'react';
import { useChatWebSocket } from './useChatWebSocket';

/**
 * Example 1: Basic Usage
 * Demonstrates simple WebSocket connection with message handling
 */
export function BasicChatExample() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');

  const handleMessage = useCallback((message) => {
    console.log('Received message:', message);
    setMessages(prev => [...prev, message]);
  }, []);

  const {
    isConnected,
    connectionStatus,
    sendMessage,
    error
  } = useChatWebSocket({
    url: '/ws',
    onMessage: handleMessage,
    onConnect: () => console.log('Connected to WebSocket'),
    onDisconnect: () => console.log('Disconnected from WebSocket'),
    autoReconnect: true
  });

  const handleSendMessage = useCallback(() => {
    if (!inputValue.trim()) return;

    sendMessage({
      type: 'user-message',
      content: inputValue,
      timestamp: new Date().toISOString()
    });

    setInputValue('');
  }, [inputValue, sendMessage]);

  return (
    <div className="chat-container">
      <div className="connection-status">
        Status: {connectionStatus}
        {error && <span className="error"> (Error: {error.message})</span>}
      </div>

      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.type}`}>
            {JSON.stringify(msg)}
          </div>
        ))}
      </div>

      <div className="input-area">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          disabled={!isConnected}
          placeholder={isConnected ? 'Type a message...' : 'Connecting...'}
        />
        <button onClick={handleSendMessage} disabled={!isConnected}>
          Send
        </button>
      </div>
    </div>
  );
}

/**
 * Example 2: Advanced Chat Interface with Message Type Handling
 * Demonstrates handling different message types (similar to ChatInterface.jsx)
 */
export function AdvancedChatExample() {
  const [chatMessages, setChatMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  const handleWebSocketMessage = useCallback((message) => {
    switch (message.type) {
      case 'session-created':
        setSessionId(message.sessionId);
        console.log('Session created:', message.sessionId);
        break;

      case 'claude-response':
        const content = message.data?.content || message.data?.message?.content;
        if (content) {
          setChatMessages(prev => [...prev, {
            type: 'assistant',
            content,
            timestamp: new Date()
          }]);
        }
        break;

      case 'claude-complete':
        setIsProcessing(false);
        console.log('Response complete');
        break;

      case 'session-aborted':
        setIsProcessing(false);
        setChatMessages(prev => [...prev, {
          type: 'system',
          content: 'Session interrupted by user.',
          timestamp: new Date()
        }]);
        break;

      case 'tool-use':
        setChatMessages(prev => [...prev, {
          type: 'tool',
          toolName: message.data?.name,
          toolInput: message.data?.input,
          timestamp: new Date()
        }]);
        break;

      case 'claude-error':
        setChatMessages(prev => [...prev, {
          type: 'error',
          content: message.error || 'An error occurred',
          timestamp: new Date()
        }]);
        setIsProcessing(false);
        break;

      default:
        console.log('Unhandled message type:', message.type);
    }
  }, []);

  const {
    isConnected,
    connectionStatus,
    sendMessage,
    reconnect
  } = useChatWebSocket({
    url: '/ws',
    onMessage: handleWebSocketMessage,
    autoReconnect: true,
    reconnectDelay: 3000
  });

  const handleUserMessage = useCallback((content) => {
    if (!content.trim() || !isConnected) return;

    // Add user message to chat
    setChatMessages(prev => [...prev, {
      type: 'user',
      content,
      timestamp: new Date()
    }]);

    // Send to server
    setIsProcessing(true);
    sendMessage({
      type: 'user-message',
      content,
      sessionId
    });
  }, [isConnected, sessionId, sendMessage]);

  return (
    <div className="advanced-chat">
      <div className="chat-header">
        <span>Status: {connectionStatus}</span>
        {sessionId && <span>Session: {sessionId}</span>}
        {!isConnected && (
          <button onClick={reconnect}>Reconnect</button>
        )}
      </div>

      <div className="chat-messages">
        {chatMessages.map((msg, idx) => (
          <MessageComponent key={idx} message={msg} />
        ))}
        {isProcessing && <div className="typing-indicator">Claude is typing...</div>}
      </div>

      <ChatInput onSend={handleUserMessage} disabled={!isConnected || isProcessing} />
    </div>
  );
}

/**
 * Example 3: With Custom Reconnection Strategy
 * Demonstrates exponential backoff and max attempts
 */
export function CustomReconnectionExample() {
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const handleError = useCallback((error) => {
    console.error('WebSocket error:', error);
  }, []);

  const handleDisconnect = useCallback(() => {
    console.log('Disconnected, will attempt to reconnect...');
  }, []);

  const {
    isConnected,
    connectionStatus,
    reconnectAttempts: attempts,
    reconnect
  } = useChatWebSocket({
    url: '/ws',
    autoReconnect: true,
    reconnectDelay: 2000, // Start with 2 seconds
    maxReconnectAttempts: 5, // Try 5 times
    onError: handleError,
    onDisconnect: handleDisconnect
  });

  useEffect(() => {
    setReconnectAttempts(attempts);
  }, [attempts]);

  return (
    <div className="reconnection-example">
      <h3>Connection Status: {connectionStatus}</h3>
      {isConnected ? (
        <p className="success">Connected successfully!</p>
      ) : (
        <>
          <p className="warning">
            Not connected. Reconnection attempts: {reconnectAttempts}/5
          </p>
          <button onClick={reconnect}>Manual Reconnect</button>
        </>
      )}
    </div>
  );
}

/**
 * Example 4: With Authentication Token (OSS Mode)
 * Demonstrates token-based authentication
 */
export function AuthenticatedChatExample() {
  const [token, setToken] = useState(null);

  useEffect(() => {
    // Retrieve token from localStorage
    const authToken = localStorage.getItem('auth-token');
    setToken(authToken);
  }, []);

  const {
    isConnected,
    sendMessage
  } = useChatWebSocket({
    url: '/ws',
    token,
    isPlatform: false, // OSS mode
    autoReconnect: true
  });

  // Only render chat if we have a token
  if (!token) {
    return <div>Please log in to use chat.</div>;
  }

  return (
    <div className="authenticated-chat">
      {isConnected ? (
        <div>Connected with authentication</div>
      ) : (
        <div>Connecting...</div>
      )}
    </div>
  );
}

/**
 * Example 5: Integration with Existing ChatInterface Pattern
 * Shows how to refactor existing ChatInterface.jsx to use this hook
 */
export function RefactoredChatInterface({ selectedProject, selectedSession }) {
  const [chatMessages, setChatMessages] = useState([]);
  const [sessionId, setSessionId] = useState(selectedSession?.id || null);

  // Message handler that processes all WebSocket message types
  const processWebSocketMessage = useCallback((message) => {
    // Filter by session ID to prevent cross-session interference
    const globalMessageTypes = ['projects_updated', 'taskmaster-project-updated', 'session-created', 'claude-complete'];
    const isGlobalMessage = globalMessageTypes.includes(message.type);

    if (!isGlobalMessage && message.sessionId && sessionId && message.sessionId !== sessionId) {
      console.log('Skipping message for different session');
      return;
    }

    // Handle different message types
    switch (message.type) {
      case 'session-created':
        if (message.sessionId && !sessionId) {
          setSessionId(message.sessionId);
        }
        break;

      case 'claude-response':
        // Handle content blocks
        const messageData = message.data.message || message.data;
        if (Array.isArray(messageData.content)) {
          messageData.content.forEach(part => {
            if (part.type === 'tool_use') {
              setChatMessages(prev => [...prev, {
                type: 'assistant',
                isToolUse: true,
                toolName: part.name,
                toolInput: part.input,
                toolId: part.id,
                timestamp: new Date()
              }]);
            } else if (part.type === 'text' && part.text?.trim()) {
              setChatMessages(prev => [...prev, {
                type: 'assistant',
                content: part.text,
                timestamp: new Date()
              }]);
            }
          });
        }
        break;

      case 'claude-complete':
      case 'session-aborted':
        // Session finished
        break;

      case 'claude-error':
        setChatMessages(prev => [...prev, {
          type: 'error',
          content: `Error: ${message.error}`,
          timestamp: new Date()
        }]);
        break;

      default:
        console.log('Unhandled message type:', message.type);
    }
  }, [sessionId]);

  const {
    isConnected,
    sendMessage
  } = useChatWebSocket({
    url: '/ws',
    onMessage: processWebSocketMessage,
    autoReconnect: true,
    reconnectDelay: 3000
  });

  const handleUserMessage = useCallback((content, files = []) => {
    if (!content.trim() && files.length === 0) return;

    // Add user message
    setChatMessages(prev => [...prev, {
      type: 'user',
      content,
      files,
      timestamp: new Date()
    }]);

    // Send to backend
    sendMessage({
      type: 'user-message',
      content,
      files,
      sessionId,
      projectName: selectedProject?.name
    });
  }, [selectedProject, sessionId, sendMessage]);

  return (
    <div className="chat-interface">
      <div className="connection-indicator">
        {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>

      <div className="messages-container">
        {chatMessages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.type}`}>
            {msg.isToolUse ? (
              <div className="tool-use">
                <strong>Tool:</strong> {msg.toolName}
                <pre>{JSON.stringify(msg.toolInput, null, 2)}</pre>
              </div>
            ) : (
              <div className="message-content">{msg.content}</div>
            )}
          </div>
        ))}
      </div>

      <div className="input-area">
        <button
          onClick={() => handleUserMessage('Hello, Claude!')}
          disabled={!isConnected}
        >
          Send Test Message
        </button>
      </div>
    </div>
  );
}

// Helper components
function MessageComponent({ message }) {
  switch (message.type) {
    case 'user':
      return <div className="message-user">{message.content}</div>;
    case 'assistant':
      return <div className="message-assistant">{message.content}</div>;
    case 'tool':
      return (
        <div className="message-tool">
          <strong>{message.toolName}</strong>
          <pre>{JSON.stringify(message.toolInput, null, 2)}</pre>
        </div>
      );
    case 'error':
      return <div className="message-error">{message.content}</div>;
    case 'system':
      return <div className="message-system">{message.content}</div>;
    default:
      return <div className="message-unknown">{JSON.stringify(message)}</div>;
  }
}

function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (value.trim()) {
      onSend(value);
      setValue('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="chat-input-form">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
        placeholder="Type your message..."
      />
      <button type="submit" disabled={disabled || !value.trim()}>
        Send
      </button>
    </form>
  );
}

export default BasicChatExample;
