/**
 * useChatMessages.js - Chat Message State Management Hook
 *
 * Custom React hook for managing chat messages in Claude Code UI.
 * Handles message state, streaming updates, tool calls, and session message loading.
 *
 * @module hooks/useChatMessages
 */

import { useState, useCallback, useRef, useMemo } from 'react';
import { api } from '../utils/api';

/**
 * @typedef {Object} ContentBlock
 * @property {string} type - Type of content block ('text', 'tool_use', 'tool_result')
 * @property {string} [text] - Text content (for type='text')
 * @property {string} [name] - Tool name (for type='tool_use')
 * @property {string} [id] - Tool use ID (for type='tool_use')
 * @property {Object} [input] - Tool input parameters (for type='tool_use')
 * @property {string} [tool_use_id] - Reference to tool use (for type='tool_result')
 * @property {*} [content] - Result content (for type='tool_result')
 * @property {boolean} [is_error] - Whether result is an error (for type='tool_result')
 */

/**
 * @typedef {Object} ToolCall
 * @property {string} id - Unique tool call ID
 * @property {string} name - Tool name
 * @property {Object} input - Tool input parameters
 * @property {Object} [result] - Tool execution result
 * @property {boolean} [isError] - Whether result is an error
 * @property {Date} [timestamp] - Result timestamp
 */

/**
 * @typedef {Object} Message
 * @property {string} id - Unique message ID
 * @property {'user'|'assistant'|'error'} type - Message type/role
 * @property {string|ContentBlock[]} content - Message content
 * @property {Date} timestamp - Message timestamp
 * @property {boolean} [isStreaming] - Whether message is being streamed
 * @property {boolean} [isToolUse] - Whether message represents a tool call
 * @property {string} [toolName] - Tool name (if isToolUse)
 * @property {string} [toolInput] - Tool input as string (if isToolUse)
 * @property {string} [toolId] - Tool use ID (if isToolUse)
 * @property {Object} [toolResult] - Tool execution result (if isToolUse)
 * @property {boolean} [isInteractivePrompt] - Whether message is an interactive prompt
 */

/**
 * @typedef {Object} UseChatMessagesReturn
 * @property {Message[]} messages - Array of chat messages
 * @property {Function} addUserMessage - Add a user message to the chat
 * @property {Function} addAssistantMessage - Add an assistant message to the chat
 * @property {Function} updateStreamingMessage - Update the last streaming message with new content
 * @property {Function} addToolCall - Add a tool call message to the chat
 * @property {Function} updateToolResult - Update a tool call with its result
 * @property {Function} clearMessages - Clear all messages
 * @property {Function} loadMessages - Load messages from session (JSONL file)
 * @property {Function} loadMoreMessages - Load more messages with pagination
 * @property {boolean} isLoading - Whether messages are being loaded
 * @property {boolean} isLoadingMore - Whether more messages are being loaded
 * @property {boolean} hasMore - Whether there are more messages to load
 * @property {number} totalMessages - Total number of messages in session
 * @property {Function} setMessages - Direct setter for messages (for advanced use cases)
 * @property {Function} finalizeStreamingMessage - Mark the current streaming message as complete
 */

/**
 * Hook for managing chat messages with support for streaming, tool calls, and pagination
 *
 * @param {string} [sessionId] - Current session ID
 * @param {Object} [options] - Hook options
 * @param {number} [options.messagesPerPage=20] - Number of messages to load per page
 * @param {Function} [options.onMessageAdded] - Callback when a message is added
 * @param {Function} [options.onMessagesLoaded] - Callback when messages are loaded
 * @returns {UseChatMessagesReturn} Chat messages state and methods
 *
 * @example
 * const {
 *   messages,
 *   addUserMessage,
 *   addAssistantMessage,
 *   updateStreamingMessage,
 *   loadMessages,
 *   isLoading
 * } = useChatMessages(sessionId);
 */
export const useChatMessages = (sessionId, options = {}) => {
  const {
    messagesPerPage = 20,
    onMessageAdded,
    onMessagesLoaded
  } = options;

  // State
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [messagesOffset, setMessagesOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [totalMessages, setTotalMessages] = useState(0);

  // Refs for streaming optimization
  const streamBufferRef = useRef('');
  const streamTimerRef = useRef(null);
  const messageIdCounterRef = useRef(0);

  /**
   * Generate a unique message ID
   * @private
   */
  const generateMessageId = useCallback(() => {
    return `msg_${Date.now()}_${++messageIdCounterRef.current}`;
  }, []);

  /**
   * Add a user message to the chat
   *
   * @param {string|ContentBlock[]} content - Message content
   * @param {Object} [metadata] - Additional message metadata
   * @returns {string} The generated message ID
   *
   * @example
   * addUserMessage('Hello, Claude!');
   * addUserMessage([
   *   { type: 'text', text: 'Analyze this image' },
   *   { type: 'image', source: { type: 'base64', data: '...' } }
   * ]);
   */
  const addUserMessage = useCallback((content, metadata = {}) => {
    const messageId = generateMessageId();
    const newMessage = {
      id: messageId,
      type: 'user',
      content,
      timestamp: new Date(),
      ...metadata
    };

    setMessages(prev => [...prev, newMessage]);

    if (onMessageAdded) {
      onMessageAdded(newMessage);
    }

    return messageId;
  }, [generateMessageId, onMessageAdded]);

  /**
   * Add an assistant message to the chat
   *
   * @param {string|ContentBlock[]} content - Message content
   * @param {Object} [metadata] - Additional message metadata
   * @returns {string} The generated message ID
   *
   * @example
   * addAssistantMessage('Hello! How can I help you?');
   * addAssistantMessage('', { isStreaming: true });
   */
  const addAssistantMessage = useCallback((content, metadata = {}) => {
    const messageId = generateMessageId();
    const newMessage = {
      id: messageId,
      type: 'assistant',
      content,
      timestamp: new Date(),
      ...metadata
    };

    setMessages(prev => [...prev, newMessage]);

    if (onMessageAdded) {
      onMessageAdded(newMessage);
    }

    return messageId;
  }, [generateMessageId, onMessageAdded]);

  /**
   * Update the last streaming message with new content
   * Uses throttling to batch rapid updates for better performance
   *
   * @param {string} chunk - Content chunk to append
   * @param {Object} [options] - Update options
   * @param {number} [options.throttleMs=100] - Throttle delay in milliseconds
   * @param {boolean} [options.immediate=false] - Skip throttling and update immediately
   *
   * @example
   * // Streaming response handling
   * updateStreamingMessage('Hello');
   * updateStreamingMessage(' world');
   * finalizeStreamingMessage(); // Mark as complete
   */
  const updateStreamingMessage = useCallback((chunk, updateOptions = {}) => {
    const { throttleMs = 100, immediate = false } = updateOptions;

    if (!chunk?.trim()) return;

    if (immediate) {
      // Immediate update without throttling
      setMessages(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];

        if (last && last.type === 'assistant' && !last.isToolUse && last.isStreaming) {
          // Update existing streaming message
          last.content = last.content ? `${last.content}\n${chunk}` : chunk;
        } else {
          // Create new streaming message
          updated.push({
            id: generateMessageId(),
            type: 'assistant',
            content: chunk,
            timestamp: new Date(),
            isStreaming: true
          });
        }

        return updated;
      });
    } else {
      // Throttled update
      streamBufferRef.current += (streamBufferRef.current ? `\n${chunk}` : chunk);

      if (!streamTimerRef.current) {
        streamTimerRef.current = setTimeout(() => {
          const bufferedChunk = streamBufferRef.current;
          streamBufferRef.current = '';
          streamTimerRef.current = null;

          if (!bufferedChunk) return;

          setMessages(prev => {
            const updated = [...prev];
            const last = updated[updated.length - 1];

            if (last && last.type === 'assistant' && !last.isToolUse && last.isStreaming) {
              last.content = last.content ? `${last.content}\n${bufferedChunk}` : bufferedChunk;
            } else {
              updated.push({
                id: generateMessageId(),
                type: 'assistant',
                content: bufferedChunk,
                timestamp: new Date(),
                isStreaming: true
              });
            }

            return updated;
          });
        }, throttleMs);
      }
    }
  }, [generateMessageId]);

  /**
   * Finalize the current streaming message by removing the streaming flag
   * and flushing any buffered content
   *
   * @example
   * updateStreamingMessage('Final chunk');
   * finalizeStreamingMessage();
   */
  const finalizeStreamingMessage = useCallback(() => {
    // Flush any buffered content
    if (streamTimerRef.current) {
      clearTimeout(streamTimerRef.current);
      streamTimerRef.current = null;
    }

    const pendingChunk = streamBufferRef.current;
    streamBufferRef.current = '';

    setMessages(prev => {
      const updated = [...prev];
      const last = updated[updated.length - 1];

      if (last && last.type === 'assistant' && last.isStreaming) {
        // Append any pending chunk
        if (pendingChunk) {
          last.content = last.content ? `${last.content}\n${pendingChunk}` : pendingChunk;
        }
        // Remove streaming flag
        delete last.isStreaming;
      }

      return updated;
    });
  }, []);

  /**
   * Add a tool call message to the chat
   *
   * @param {string} toolName - Name of the tool being called
   * @param {Object} toolInput - Tool input parameters
   * @param {string} [toolId] - Unique tool call ID
   * @returns {string} The generated message ID
   *
   * @example
   * addToolCall('Read', { file_path: '/path/to/file.js' }, 'tool_123');
   */
  const addToolCall = useCallback((toolName, toolInput, toolId) => {
    const messageId = generateMessageId();
    const toolInputStr = toolInput ? JSON.stringify(toolInput, null, 2) : '';

    const newMessage = {
      id: messageId,
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      isToolUse: true,
      toolName,
      toolInput: toolInputStr,
      toolId: toolId || messageId,
      toolResult: null
    };

    setMessages(prev => [...prev, newMessage]);

    if (onMessageAdded) {
      onMessageAdded(newMessage);
    }

    return messageId;
  }, [generateMessageId, onMessageAdded]);

  /**
   * Update a tool call message with its execution result
   *
   * @param {string} toolId - Tool use ID to update
   * @param {*} content - Result content
   * @param {boolean} [isError=false] - Whether the result is an error
   *
   * @example
   * updateToolResult('tool_123', 'File contents...', false);
   * updateToolResult('tool_456', 'File not found', true);
   */
  const updateToolResult = useCallback((toolId, content, isError = false) => {
    setMessages(prev => prev.map(msg => {
      if (msg.isToolUse && msg.toolId === toolId) {
        return {
          ...msg,
          toolResult: {
            content,
            isError,
            timestamp: new Date()
          }
        };
      }
      return msg;
    }));
  }, []);

  /**
   * Add an error message to the chat
   *
   * @param {string} errorMessage - Error message content
   * @returns {string} The generated message ID
   *
   * @example
   * addErrorMessage('Failed to connect to server');
   */
  const addErrorMessage = useCallback((errorMessage) => {
    const messageId = generateMessageId();
    const newMessage = {
      id: messageId,
      type: 'error',
      content: `Error: ${errorMessage}`,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newMessage]);

    if (onMessageAdded) {
      onMessageAdded(newMessage);
    }

    return messageId;
  }, [generateMessageId, onMessageAdded]);

  /**
   * Clear all messages
   *
   * @example
   * clearMessages();
   */
  const clearMessages = useCallback(() => {
    // Clear any pending streaming updates
    if (streamTimerRef.current) {
      clearTimeout(streamTimerRef.current);
      streamTimerRef.current = null;
    }
    streamBufferRef.current = '';

    setMessages([]);
    setMessagesOffset(0);
    setHasMore(false);
    setTotalMessages(0);
  }, []);

  /**
   * Load messages from session (initial load or reload)
   *
   * @param {string} projectName - Project name
   * @param {string} targetSessionId - Session ID to load
   * @returns {Promise<Message[]>} Array of loaded messages
   *
   * @example
   * await loadMessages('my-project', 'session_123');
   */
  const loadMessages = useCallback(async (projectName, targetSessionId) => {
    if (!projectName || !targetSessionId) {
      console.warn('loadMessages: Missing projectName or sessionId');
      return [];
    }

    setIsLoading(true);

    try {
      const response = await api.sessionMessages(
        projectName,
        targetSessionId,
        messagesPerPage,
        0 // Start from beginning
      );

      if (!response.ok) {
        throw new Error('Failed to load session messages');
      }

      const data = await response.json();

      // Handle paginated response
      if (data.hasMore !== undefined) {
        setHasMore(data.hasMore);
      }

      if (data.total !== undefined) {
        setTotalMessages(data.total);
      }

      const loadedMessages = data.messages || [];

      // Update offset for next page
      setMessagesOffset(loadedMessages.length);

      // Convert raw messages to UI message format
      const convertedMessages = convertRawMessages(loadedMessages);
      setMessages(convertedMessages);

      if (onMessagesLoaded) {
        onMessagesLoaded(convertedMessages);
      }

      return convertedMessages;
    } catch (error) {
      console.error('Error loading session messages:', error);
      addErrorMessage(error.message || 'Failed to load messages');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [messagesPerPage, onMessagesLoaded, addErrorMessage]);

  /**
   * Load more messages (pagination)
   *
   * @param {string} projectName - Project name
   * @param {string} targetSessionId - Session ID to load
   * @returns {Promise<Message[]>} Array of newly loaded messages
   *
   * @example
   * const moreMessages = await loadMoreMessages('my-project', 'session_123');
   */
  const loadMoreMessages = useCallback(async (projectName, targetSessionId) => {
    if (!projectName || !targetSessionId) {
      console.warn('loadMoreMessages: Missing projectName or sessionId');
      return [];
    }

    if (!hasMore || isLoadingMore) {
      return [];
    }

    setIsLoadingMore(true);

    try {
      const response = await api.sessionMessages(
        projectName,
        targetSessionId,
        messagesPerPage,
        messagesOffset
      );

      if (!response.ok) {
        throw new Error('Failed to load more messages');
      }

      const data = await response.json();

      // Update pagination state
      if (data.hasMore !== undefined) {
        setHasMore(data.hasMore);
      }

      const loadedMessages = data.messages || [];

      // Update offset
      setMessagesOffset(prev => prev + loadedMessages.length);

      // Convert and prepend messages (older messages go at the top)
      const convertedMessages = convertRawMessages(loadedMessages);
      setMessages(prev => [...convertedMessages, ...prev]);

      return convertedMessages;
    } catch (error) {
      console.error('Error loading more messages:', error);
      addErrorMessage(error.message || 'Failed to load more messages');
      return [];
    } finally {
      setIsLoadingMore(false);
    }
  }, [hasMore, isLoadingMore, messagesPerPage, messagesOffset, addErrorMessage]);

  /**
   * Convert raw session messages to UI message format
   * @private
   */
  const convertRawMessages = useCallback((rawMessages) => {
    if (!Array.isArray(rawMessages)) return [];

    return rawMessages.map((msg, index) => {
      const messageId = msg.id || `msg_loaded_${Date.now()}_${index}`;

      // Handle different message formats
      if (typeof msg === 'string') {
        // Simple string message
        return {
          id: messageId,
          type: 'assistant',
          content: msg,
          timestamp: new Date()
        };
      }

      // Structured message object
      return {
        id: messageId,
        type: msg.role || msg.type || 'assistant',
        content: msg.content || '',
        timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
        ...(msg.isToolUse && {
          isToolUse: true,
          toolName: msg.toolName,
          toolInput: msg.toolInput,
          toolId: msg.toolId,
          toolResult: msg.toolResult
        })
      };
    });
  }, []);

  /**
   * Reset pagination state (useful when switching sessions)
   */
  const resetPagination = useCallback(() => {
    setMessagesOffset(0);
    setHasMore(false);
    setTotalMessages(0);
  }, []);

  // Cleanup on unmount
  useMemo(() => {
    return () => {
      if (streamTimerRef.current) {
        clearTimeout(streamTimerRef.current);
      }
    };
  }, []);

  return {
    // State
    messages,
    isLoading,
    isLoadingMore,
    hasMore,
    totalMessages,

    // Message operations
    addUserMessage,
    addAssistantMessage,
    updateStreamingMessage,
    finalizeStreamingMessage,
    addToolCall,
    updateToolResult,
    addErrorMessage,
    clearMessages,

    // Session operations
    loadMessages,
    loadMoreMessages,
    resetPagination,

    // Advanced
    setMessages // Direct setter for advanced use cases
  };
};

export default useChatMessages;
