/**
 * useChatMessages.test.js - Unit tests for useChatMessages hook
 *
 * Tests message state management, streaming updates, tool calls, and pagination.
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useChatMessages } from '../useChatMessages';
import { api } from '../../utils/api';

// Mock the api module
jest.mock('../../utils/api', () => ({
  api: {
    sessionMessages: jest.fn()
  }
}));

describe('useChatMessages', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Basic message operations', () => {
    test('should initialize with empty messages', () => {
      const { result } = renderHook(() => useChatMessages());

      expect(result.current.messages).toEqual([]);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.hasMore).toBe(false);
    });

    test('should add user message', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.addUserMessage('Hello, Claude!');
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0]).toMatchObject({
        type: 'user',
        content: 'Hello, Claude!',
      });
      expect(result.current.messages[0].id).toBeDefined();
      expect(result.current.messages[0].timestamp).toBeInstanceOf(Date);
    });

    test('should add assistant message', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.addAssistantMessage('Hello! How can I help?');
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0]).toMatchObject({
        type: 'assistant',
        content: 'Hello! How can I help?',
      });
    });

    test('should add multiple messages in sequence', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.addUserMessage('Question 1');
        result.current.addAssistantMessage('Answer 1');
        result.current.addUserMessage('Question 2');
        result.current.addAssistantMessage('Answer 2');
      });

      expect(result.current.messages).toHaveLength(4);
      expect(result.current.messages[0].type).toBe('user');
      expect(result.current.messages[1].type).toBe('assistant');
      expect(result.current.messages[2].type).toBe('user');
      expect(result.current.messages[3].type).toBe('assistant');
    });

    test('should add error message', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.addErrorMessage('Connection failed');
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0]).toMatchObject({
        type: 'error',
        content: 'Error: Connection failed',
      });
    });

    test('should clear all messages', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.addUserMessage('Test message');
        result.current.addAssistantMessage('Response');
      });

      expect(result.current.messages).toHaveLength(2);

      act(() => {
        result.current.clearMessages();
      });

      expect(result.current.messages).toEqual([]);
      expect(result.current.hasMore).toBe(false);
      expect(result.current.totalMessages).toBe(0);
    });
  });

  describe('Streaming message updates', () => {
    test('should update streaming message with throttling', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.updateStreamingMessage('Hello');
        result.current.updateStreamingMessage(' world');
      });

      // Messages should be buffered
      expect(result.current.messages).toHaveLength(0);

      // Fast-forward throttle timer (100ms default)
      act(() => {
        jest.advanceTimersByTime(100);
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0]).toMatchObject({
        type: 'assistant',
        content: 'Hello\n world',
        isStreaming: true,
      });
    });

    test('should update streaming message immediately when specified', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.updateStreamingMessage('Immediate update', { immediate: true });
      });

      // No buffering, immediate update
      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0].content).toBe('Immediate update');
    });

    test('should append to existing streaming message', () => {
      const { result } = renderHook(() => useChatMessages());

      // First chunk
      act(() => {
        result.current.updateStreamingMessage('First chunk');
        jest.advanceTimersByTime(100);
      });

      expect(result.current.messages).toHaveLength(1);

      // Second chunk
      act(() => {
        result.current.updateStreamingMessage('Second chunk');
        jest.advanceTimersByTime(100);
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0].content).toContain('First chunk');
      expect(result.current.messages[0].content).toContain('Second chunk');
    });

    test('should finalize streaming message', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.updateStreamingMessage('Streaming content');
        jest.advanceTimersByTime(100);
      });

      expect(result.current.messages[0].isStreaming).toBe(true);

      act(() => {
        result.current.finalizeStreamingMessage();
      });

      expect(result.current.messages[0].isStreaming).toBeUndefined();
    });

    test('should flush buffered content when finalizing', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.updateStreamingMessage('Buffered');
        // Don't advance timer - content is still buffered
      });

      expect(result.current.messages).toHaveLength(0);

      act(() => {
        result.current.finalizeStreamingMessage();
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0].content).toBe('Buffered');
      expect(result.current.messages[0].isStreaming).toBeUndefined();
    });

    test('should not update with empty chunks', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.updateStreamingMessage('');
        result.current.updateStreamingMessage('   ');
        jest.advanceTimersByTime(100);
      });

      expect(result.current.messages).toHaveLength(0);
    });
  });

  describe('Tool call messages', () => {
    test('should add tool call message', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.addToolCall(
          'Read',
          { file_path: '/test/file.js' },
          'tool_123'
        );
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0]).toMatchObject({
        type: 'assistant',
        isToolUse: true,
        toolName: 'Read',
        toolId: 'tool_123',
        toolResult: null,
      });
      expect(result.current.messages[0].toolInput).toContain('file_path');
    });

    test('should update tool result', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.addToolCall(
          'Read',
          { file_path: '/test/file.js' },
          'tool_123'
        );
      });

      act(() => {
        result.current.updateToolResult('tool_123', 'File contents here', false);
      });

      expect(result.current.messages[0].toolResult).toMatchObject({
        content: 'File contents here',
        isError: false,
      });
      expect(result.current.messages[0].toolResult.timestamp).toBeInstanceOf(Date);
    });

    test('should update tool result with error', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.addToolCall('Read', { file_path: '/missing.js' }, 'tool_456');
      });

      act(() => {
        result.current.updateToolResult('tool_456', 'File not found', true);
      });

      expect(result.current.messages[0].toolResult).toMatchObject({
        content: 'File not found',
        isError: true,
      });
    });

    test('should not update unrelated messages when updating tool result', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.addToolCall('Read', {}, 'tool_1');
        result.current.addToolCall('Write', {}, 'tool_2');
      });

      act(() => {
        result.current.updateToolResult('tool_1', 'Result 1', false);
      });

      expect(result.current.messages[0].toolResult.content).toBe('Result 1');
      expect(result.current.messages[1].toolResult).toBeNull();
    });
  });

  describe('Loading messages from session', () => {
    test('should load messages successfully', async () => {
      const mockMessages = [
        { role: 'user', content: 'Hello' },
        { role: 'assistant', content: 'Hi there!' },
      ];

      api.sessionMessages.mockResolvedValue({
        ok: true,
        json: async () => ({
          messages: mockMessages,
          hasMore: false,
          total: 2,
        }),
      });

      const { result } = renderHook(() => useChatMessages());

      await act(async () => {
        await result.current.loadMessages('test-project', 'session_123');
      });

      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[0].content).toBe('Hello');
      expect(result.current.messages[1].content).toBe('Hi there!');
      expect(result.current.hasMore).toBe(false);
      expect(result.current.totalMessages).toBe(2);
      expect(result.current.isLoading).toBe(false);
    });

    test('should set loading state during load', async () => {
      api.sessionMessages.mockImplementation(() => {
        return new Promise(resolve => {
          setTimeout(() => {
            resolve({
              ok: true,
              json: async () => ({ messages: [], hasMore: false, total: 0 }),
            });
          }, 100);
        });
      });

      const { result } = renderHook(() => useChatMessages());

      let loadPromise;
      act(() => {
        loadPromise = result.current.loadMessages('test-project', 'session_123');
      });

      expect(result.current.isLoading).toBe(true);

      await act(async () => {
        await loadPromise;
      });

      expect(result.current.isLoading).toBe(false);
    });

    test('should handle load error', async () => {
      api.sessionMessages.mockResolvedValue({
        ok: false,
      });

      const { result } = renderHook(() => useChatMessages());

      await act(async () => {
        await result.current.loadMessages('test-project', 'session_123');
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0].type).toBe('error');
      expect(result.current.isLoading).toBe(false);
    });

    test('should not load without project name or session ID', async () => {
      const { result } = renderHook(() => useChatMessages());

      await act(async () => {
        const messages = await result.current.loadMessages('', '');
      });

      expect(api.sessionMessages).not.toHaveBeenCalled();
      expect(result.current.messages).toEqual([]);
    });
  });

  describe('Pagination', () => {
    test('should load more messages', async () => {
      const mockInitialMessages = [
        { role: 'user', content: 'Message 1' },
        { role: 'assistant', content: 'Response 1' },
      ];

      const mockMoreMessages = [
        { role: 'user', content: 'Message 0' },
      ];

      // Initial load
      api.sessionMessages.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          messages: mockInitialMessages,
          hasMore: true,
          total: 3,
        }),
      });

      const { result } = renderHook(() => useChatMessages());

      await act(async () => {
        await result.current.loadMessages('test-project', 'session_123');
      });

      expect(result.current.messages).toHaveLength(2);
      expect(result.current.hasMore).toBe(true);

      // Load more
      api.sessionMessages.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          messages: mockMoreMessages,
          hasMore: false,
        }),
      });

      await act(async () => {
        await result.current.loadMoreMessages('test-project', 'session_123');
      });

      expect(result.current.messages).toHaveLength(3);
      expect(result.current.messages[0].content).toBe('Message 0'); // Older message prepended
      expect(result.current.hasMore).toBe(false);
      expect(result.current.isLoadingMore).toBe(false);
    });

    test('should not load more when hasMore is false', async () => {
      api.sessionMessages.mockResolvedValue({
        ok: true,
        json: async () => ({
          messages: [],
          hasMore: false,
        }),
      });

      const { result } = renderHook(() => useChatMessages());

      await act(async () => {
        await result.current.loadMessages('test-project', 'session_123');
      });

      expect(result.current.hasMore).toBe(false);

      api.sessionMessages.mockClear();

      await act(async () => {
        await result.current.loadMoreMessages('test-project', 'session_123');
      });

      // Should not call API again
      expect(api.sessionMessages).not.toHaveBeenCalled();
    });

    test('should reset pagination', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.setMessages([
          { id: '1', type: 'user', content: 'Test', timestamp: new Date() },
        ]);
        // Simulate loaded state
        result.current.resetPagination();
      });

      expect(result.current.hasMore).toBe(false);
      expect(result.current.totalMessages).toBe(0);
    });
  });

  describe('Callbacks', () => {
    test('should call onMessageAdded callback', () => {
      const onMessageAdded = jest.fn();
      const { result } = renderHook(() =>
        useChatMessages(null, { onMessageAdded })
      );

      act(() => {
        result.current.addUserMessage('Test message');
      });

      expect(onMessageAdded).toHaveBeenCalledTimes(1);
      expect(onMessageAdded).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'user',
          content: 'Test message',
        })
      );
    });

    test('should call onMessagesLoaded callback', async () => {
      const onMessagesLoaded = jest.fn();

      api.sessionMessages.mockResolvedValue({
        ok: true,
        json: async () => ({
          messages: [{ role: 'user', content: 'Test' }],
          hasMore: false,
        }),
      });

      const { result } = renderHook(() =>
        useChatMessages(null, { onMessagesLoaded })
      );

      await act(async () => {
        await result.current.loadMessages('test-project', 'session_123');
      });

      expect(onMessagesLoaded).toHaveBeenCalledTimes(1);
      expect(onMessagesLoaded).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({ content: 'Test' }),
        ])
      );
    });
  });

  describe('Advanced scenarios', () => {
    test('should handle mixed content types', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.addUserMessage([
          { type: 'text', text: 'Analyze this image' },
          { type: 'image', source: { type: 'base64', data: 'base64data' } },
        ]);
      });

      expect(result.current.messages[0].content).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ type: 'text' }),
          expect.objectContaining({ type: 'image' }),
        ])
      );
    });

    test('should handle metadata in messages', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.addUserMessage('Test', {
          metadata: { customField: 'value' },
        });
      });

      expect(result.current.messages[0].metadata).toEqual({
        customField: 'value',
      });
    });

    test('should generate unique message IDs', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        result.current.addUserMessage('Message 1');
        result.current.addUserMessage('Message 2');
        result.current.addUserMessage('Message 3');
      });

      const ids = result.current.messages.map(m => m.id);
      const uniqueIds = new Set(ids);

      expect(uniqueIds.size).toBe(3);
    });

    test('should preserve message order', () => {
      const { result } = renderHook(() => useChatMessages());

      act(() => {
        for (let i = 0; i < 10; i++) {
          result.current.addUserMessage(`Message ${i}`);
        }
      });

      for (let i = 0; i < 10; i++) {
        expect(result.current.messages[i].content).toBe(`Message ${i}`);
      }
    });
  });
});
