/**
 * useChatMessages.example.jsx - Usage examples for useChatMessages hook
 *
 * This file demonstrates various usage patterns for the useChatMessages hook.
 */

import React, { useEffect, useRef } from 'react';
import { useChatMessages } from './useChatMessages';

/**
 * Example 1: Basic Chat Component
 *
 * Simple chat interface with message display and input handling.
 */
export const BasicChatExample = ({ sessionId, projectName }) => {
  const {
    messages,
    addUserMessage,
    isLoading,
    loadMessages
  } = useChatMessages(sessionId);

  const [input, setInput] = React.useState('');

  // Load messages when session changes
  useEffect(() => {
    if (sessionId && projectName) {
      loadMessages(projectName, sessionId);
    }
  }, [sessionId, projectName, loadMessages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      addUserMessage(input.trim());
      setInput('');
      // Send to backend...
    }
  };

  if (isLoading) {
    return <div>Loading messages...</div>;
  }

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.type}`}>
            <div className="message-content">{msg.content}</div>
            <div className="message-timestamp">
              {msg.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
};

/**
 * Example 2: Streaming Response Handler
 *
 * Demonstrates handling streaming responses from SSE or WebSocket.
 */
export const StreamingChatExample = ({ sessionId, websocket }) => {
  const {
    messages,
    addUserMessage,
    updateStreamingMessage,
    finalizeStreamingMessage
  } = useChatMessages(sessionId);

  useEffect(() => {
    if (!websocket) return;

    const handleMessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'claude-output':
          // Stream incoming chunks
          if (data.content?.trim()) {
            updateStreamingMessage(data.content);
          }
          break;

        case 'claude-complete':
          // Finalize streaming when complete
          finalizeStreamingMessage();
          break;

        case 'claude-error':
          finalizeStreamingMessage();
          // Handle error...
          break;

        default:
          break;
      }
    };

    websocket.addEventListener('message', handleMessage);

    return () => {
      websocket.removeEventListener('message', handleMessage);
    };
  }, [websocket, updateStreamingMessage, finalizeStreamingMessage]);

  return (
    <div className="streaming-chat">
      {messages.map((msg) => (
        <div key={msg.id} className={msg.isStreaming ? 'streaming' : ''}>
          {msg.content}
          {msg.isStreaming && <span className="cursor">▊</span>}
        </div>
      ))}
    </div>
  );
};

/**
 * Example 3: Tool Call Visualization
 *
 * Displays tool calls and their results in the chat.
 */
export const ToolCallChatExample = ({ sessionId }) => {
  const {
    messages,
    addToolCall,
    updateToolResult
  } = useChatMessages(sessionId);

  // Simulate tool execution
  const executeToolCall = async (toolName, toolInput, toolId) => {
    // Add tool call message
    addToolCall(toolName, toolInput, toolId);

    try {
      // Execute tool (simulated)
      const result = await mockToolExecution(toolName, toolInput);

      // Update with result
      updateToolResult(toolId, result, false);
    } catch (error) {
      // Update with error
      updateToolResult(toolId, error.message, true);
    }
  };

  return (
    <div className="tool-call-chat">
      {messages.map((msg) => {
        if (msg.isToolUse) {
          return (
            <div key={msg.id} className="tool-call">
              <div className="tool-header">
                <strong>{msg.toolName}</strong>
                {msg.toolResult ? (
                  msg.toolResult.isError ? (
                    <span className="error">Failed</span>
                  ) : (
                    <span className="success">Success</span>
                  )
                ) : (
                  <span className="loading">Running...</span>
                )}
              </div>

              <details>
                <summary>Input</summary>
                <pre>{msg.toolInput}</pre>
              </details>

              {msg.toolResult && (
                <details open>
                  <summary>Result</summary>
                  <pre className={msg.toolResult.isError ? 'error' : 'success'}>
                    {typeof msg.toolResult.content === 'string'
                      ? msg.toolResult.content
                      : JSON.stringify(msg.toolResult.content, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          );
        }

        return (
          <div key={msg.id} className={`message ${msg.type}`}>
            {msg.content}
          </div>
        );
      })}
    </div>
  );
};

/**
 * Example 4: Infinite Scroll with Pagination
 *
 * Load older messages as user scrolls to top.
 */
export const InfiniteScrollChatExample = ({ sessionId, projectName }) => {
  const {
    messages,
    loadMessages,
    loadMoreMessages,
    hasMore,
    isLoadingMore
  } = useChatMessages(sessionId);

  const scrollContainerRef = useRef(null);
  const [isNearTop, setIsNearTop] = React.useState(false);

  // Initial load
  useEffect(() => {
    if (sessionId && projectName) {
      loadMessages(projectName, sessionId);
    }
  }, [sessionId, projectName, loadMessages]);

  // Handle scroll events
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const nearTop = container.scrollTop < 100;
      setIsNearTop(nearTop);
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  // Load more when near top
  useEffect(() => {
    if (isNearTop && hasMore && !isLoadingMore && sessionId && projectName) {
      const container = scrollContainerRef.current;
      const previousScrollHeight = container.scrollHeight;
      const previousScrollTop = container.scrollTop;

      loadMoreMessages(projectName, sessionId).then(() => {
        // Restore scroll position after loading
        setTimeout(() => {
          if (container) {
            const newScrollHeight = container.scrollHeight;
            const scrollDiff = newScrollHeight - previousScrollHeight;
            container.scrollTop = previousScrollTop + scrollDiff;
          }
        }, 0);
      });
    }
  }, [isNearTop, hasMore, isLoadingMore, sessionId, projectName, loadMoreMessages]);

  return (
    <div className="infinite-scroll-chat" ref={scrollContainerRef}>
      {isLoadingMore && (
        <div className="loading-indicator">Loading older messages...</div>
      )}

      {messages.map((msg) => (
        <div key={msg.id} className={`message ${msg.type}`}>
          {msg.content}
        </div>
      ))}
    </div>
  );
};

/**
 * Example 5: Multi-Modal Messages (Text + Images)
 *
 * Handle messages with multiple content blocks including images.
 */
export const MultiModalChatExample = ({ sessionId }) => {
  const { messages, addUserMessage } = useChatMessages(sessionId);

  const handleImageUpload = async (files) => {
    const imageBlocks = await Promise.all(
      Array.from(files).map(async (file) => {
        const base64 = await fileToBase64(file);
        return {
          type: 'image',
          source: {
            type: 'base64',
            media_type: file.type,
            data: base64
          }
        };
      })
    );

    // Add message with text and images
    addUserMessage([
      { type: 'text', text: 'Please analyze these images' },
      ...imageBlocks
    ]);
  };

  const renderContent = (content) => {
    if (typeof content === 'string') {
      return <p>{content}</p>;
    }

    if (Array.isArray(content)) {
      return content.map((block, index) => {
        if (block.type === 'text') {
          return <p key={index}>{block.text}</p>;
        }
        if (block.type === 'image') {
          return (
            <img
              key={index}
              src={`data:${block.source.media_type};base64,${block.source.data}`}
              alt="Uploaded"
              className="message-image"
            />
          );
        }
        return null;
      });
    }

    return null;
  };

  return (
    <div className="multi-modal-chat">
      {messages.map((msg) => (
        <div key={msg.id} className={`message ${msg.type}`}>
          {renderContent(msg.content)}
        </div>
      ))}

      <input
        type="file"
        accept="image/*"
        multiple
        onChange={(e) => handleImageUpload(e.target.files)}
      />
    </div>
  );
};

/**
 * Example 6: Chat with Callbacks and Side Effects
 *
 * Use callbacks for analytics, logging, or notifications.
 */
export const ChatWithCallbacksExample = ({ sessionId, projectName }) => {
  const [notifications, setNotifications] = React.useState([]);

  const handleMessageAdded = (message) => {
    // Analytics
    if (typeof window !== 'undefined' && window.analytics) {
      window.analytics.track('Message Added', {
        type: message.type,
        sessionId,
        timestamp: message.timestamp
      });
    }

    // Show notification for assistant messages
    if (message.type === 'assistant') {
      setNotifications(prev => [
        ...prev,
        { id: message.id, text: 'New response received' }
      ]);
    }
  };

  const handleMessagesLoaded = (messages) => {
    console.log(`Loaded ${messages.length} messages for session ${sessionId}`);
  };

  const {
    messages,
    addUserMessage,
    loadMessages,
    isLoading
  } = useChatMessages(sessionId, {
    onMessageAdded: handleMessageAdded,
    onMessagesLoaded: handleMessagesLoaded
  });

  useEffect(() => {
    if (sessionId && projectName) {
      loadMessages(projectName, sessionId);
    }
  }, [sessionId, projectName, loadMessages]);

  return (
    <div className="chat-with-callbacks">
      <div className="notifications">
        {notifications.map((notif) => (
          <div key={notif.id} className="notification">
            {notif.text}
          </div>
        ))}
      </div>

      <div className="messages">
        {messages.map((msg) => (
          <div key={msg.id}>{msg.content}</div>
        ))}
      </div>
    </div>
  );
};

/**
 * Helper Functions
 */

const mockToolExecution = async (toolName, toolInput) => {
  // Simulate API call
  await new Promise(resolve => setTimeout(resolve, 1000));
  return `Tool ${toolName} executed successfully`;
};

const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const base64 = reader.result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
  });
};

/**
 * Example 7: Integration with WebSocket for Real-Time Chat
 */
export const WebSocketChatExample = ({ sessionId, projectName, wsUrl }) => {
  const {
    messages,
    addUserMessage,
    addAssistantMessage,
    updateStreamingMessage,
    finalizeStreamingMessage,
    addToolCall,
    updateToolResult,
    loadMessages
  } = useChatMessages(sessionId);

  const wsRef = useRef(null);

  // Initialize WebSocket and load messages
  useEffect(() => {
    if (!sessionId || !projectName) return;

    // Load existing messages
    loadMessages(projectName, sessionId);

    // Connect WebSocket
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'claude-message':
          if (Array.isArray(data.content)) {
            data.content.forEach((block) => {
              if (block.type === 'tool_use') {
                addToolCall(block.name, block.input, block.id);
              } else if (block.type === 'text' && block.text?.trim()) {
                addAssistantMessage(block.text);
              }
            });
          }
          break;

        case 'claude-output':
          updateStreamingMessage(data.content);
          break;

        case 'claude-complete':
          finalizeStreamingMessage();
          break;

        case 'tool-result':
          updateToolResult(data.toolId, data.result, data.isError);
          break;

        default:
          break;
      }
    };

    return () => {
      ws.close();
    };
  }, [sessionId, projectName, wsUrl]);

  const handleSendMessage = (text) => {
    if (!text.trim() || !wsRef.current) return;

    // Add user message to UI
    addUserMessage(text.trim());

    // Send to WebSocket
    wsRef.current.send(JSON.stringify({
      type: 'user-message',
      content: text.trim(),
      sessionId
    }));
  };

  return (
    <div className="websocket-chat">
      <MessageList messages={messages} />
      <MessageInput onSend={handleSendMessage} />
    </div>
  );
};

// Placeholder components for the example
const MessageList = ({ messages }) => (
  <div className="message-list">
    {messages.map(msg => (
      <div key={msg.id}>{msg.content}</div>
    ))}
  </div>
);

const MessageInput = ({ onSend }) => {
  const [value, setValue] = React.useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSend(value);
    setValue('');
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Type a message..."
      />
      <button type="submit">Send</button>
    </form>
  );
};
