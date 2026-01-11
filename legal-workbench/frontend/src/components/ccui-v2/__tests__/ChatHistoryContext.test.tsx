import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import React from 'react';
import {
  ChatHistoryProvider,
  useChatHistory,
  Message,
  Conversation,
} from '../contexts/ChatHistoryContext';
import { localStorageMock } from '../../../test/setup';

const STORAGE_KEY = 'ccui-chat-history';
const MAX_CONVERSATIONS = 50;

// Test component that exposes context values
function TestConsumer({
  onContextValue,
}: {
  onContextValue?: (value: ReturnType<typeof useChatHistory>) => void;
}) {
  const context = useChatHistory();
  React.useEffect(() => {
    onContextValue?.(context);
  }, [context, onContextValue]);

  return (
    <div>
      <span data-testid="conversation-count">{context.conversations.length}</span>
      <span data-testid="current-id">{context.currentConversationId || 'none'}</span>
      <button
        data-testid="save-btn"
        onClick={() => {
          const messages: Message[] = [
            { id: '1', role: 'user', content: 'Hello' },
            { id: '2', role: 'assistant', content: 'Hi there!' },
          ];
          context.saveConversation(messages);
        }}
      >
        Save
      </button>
      <button
        data-testid="save-long-btn"
        onClick={() => {
          const messages: Message[] = [
            { id: '1', role: 'user', content: 'This is a very long message that exceeds fifty characters in length' },
            { id: '2', role: 'assistant', content: 'Response' },
          ];
          context.saveConversation(messages);
        }}
      >
        Save Long
      </button>
      <button data-testid="new-conv-btn" onClick={() => context.startNewConversation()}>
        New
      </button>
      <ul data-testid="conversation-list">
        {context.conversations.map((c) => (
          <li key={c.id} data-testid={`conv-${c.id}`}>
            {c.title}
          </li>
        ))}
      </ul>
    </div>
  );
}

// Helper to render with provider
function renderWithProvider() {
  return render(
    <ChatHistoryProvider>
      <TestConsumer />
    </ChatHistoryProvider>
  );
}

// Helper to create mock messages
function createMessages(count: number, prefix: string = 'msg'): Message[] {
  const messages: Message[] = [];
  for (let i = 0; i < count; i++) {
    messages.push({
      id: `${prefix}-${i}`,
      role: i % 2 === 0 ? 'user' : 'assistant',
      content: `Message ${i} from ${prefix}`,
    });
  }
  return messages;
}

// Helper to create mock conversations for localStorage
function createStoredConversations(count: number): Conversation[] {
  const conversations: Conversation[] = [];
  for (let i = 0; i < count; i++) {
    conversations.push({
      id: `conv-${Date.now()}-${i}`,
      title: `Conversation ${i}`,
      messages: createMessages(2, `conv${i}`),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    });
  }
  return conversations;
}

describe('ChatHistoryContext', () => {
  beforeEach(() => {
    localStorageMock._reset();
  });

  describe('Initial State', () => {
    it('should start with empty conversations', () => {
      renderWithProvider();
      expect(screen.getByTestId('conversation-count').textContent).toBe('0');
      expect(screen.getByTestId('current-id').textContent).toBe('none');
    });

    it('should load conversations from localStorage on mount', async () => {
      const storedConversations = createStoredConversations(3);
      localStorageMock._setStore({
        [STORAGE_KEY]: JSON.stringify(storedConversations),
      });

      renderWithProvider();

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe('3');
      });
    });

    it('should handle invalid localStorage data gracefully', async () => {
      localStorageMock._setStore({
        [STORAGE_KEY]: 'invalid json {{{',
      });

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      renderWithProvider();

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe('0');
      });

      consoleSpy.mockRestore();
    });

    it('should handle non-array localStorage data gracefully', async () => {
      localStorageMock._setStore({
        [STORAGE_KEY]: JSON.stringify({ notAnArray: true }),
      });

      renderWithProvider();

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe('0');
      });
    });
  });

  describe('saveConversation', () => {
    it('should save a new conversation', async () => {
      renderWithProvider();

      act(() => {
        screen.getByTestId('save-btn').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe('1');
      });
    });

    it('should generate title from first user message', async () => {
      renderWithProvider();

      act(() => {
        screen.getByTestId('save-btn').click();
      });

      await waitFor(() => {
        const listItems = screen.getByTestId('conversation-list').querySelectorAll('li');
        expect(listItems[0].textContent).toBe('Hello');
      });
    });

    it('should truncate long titles with ellipsis', async () => {
      renderWithProvider();

      act(() => {
        screen.getByTestId('save-long-btn').click();
      });

      await waitFor(() => {
        const listItems = screen.getByTestId('conversation-list').querySelectorAll('li');
        const title = listItems[0].textContent || '';
        expect(title.length).toBeLessThanOrEqual(50);
        expect(title).toContain('...');
      });
    });

    it('should persist to localStorage', async () => {
      renderWithProvider();

      act(() => {
        screen.getByTestId('save-btn').click();
      });

      await waitFor(() => {
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          STORAGE_KEY,
          expect.any(String)
        );
      });

      const stored = JSON.parse(localStorageMock._getStore()[STORAGE_KEY]);
      expect(stored).toHaveLength(1);
      expect(stored[0].title).toBe('Hello');
    });

    it('should not save empty messages', async () => {
      let contextRef: ReturnType<typeof useChatHistory> | null = null;

      render(
        <ChatHistoryProvider>
          <TestConsumer onContextValue={(ctx) => (contextRef = ctx)} />
        </ChatHistoryProvider>
      );

      await waitFor(() => {
        expect(contextRef).not.toBeNull();
      });

      act(() => {
        contextRef!.saveConversation([]);
      });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe('0');
      });
    });

    it('should filter out system messages before saving', async () => {
      let contextRef: ReturnType<typeof useChatHistory> | null = null;

      render(
        <ChatHistoryProvider>
          <TestConsumer onContextValue={(ctx) => (contextRef = ctx)} />
        </ChatHistoryProvider>
      );

      await waitFor(() => {
        expect(contextRef).not.toBeNull();
      });

      const messages: Message[] = [
        { id: '1', role: 'system', content: 'System message', isSystem: true },
        { id: '2', role: 'user', content: 'User message' },
        { id: '3', role: 'assistant', content: 'Assistant response' },
      ];

      act(() => {
        contextRef!.saveConversation(messages);
      });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe('1');
      });

      const stored = JSON.parse(localStorageMock._getStore()[STORAGE_KEY]);
      expect(stored[0].messages).toHaveLength(2);
      expect(stored[0].messages.every((m: Message) => !m.isSystem)).toBe(true);
    });

    it('should clear streaming state before saving', async () => {
      let contextRef: ReturnType<typeof useChatHistory> | null = null;

      render(
        <ChatHistoryProvider>
          <TestConsumer onContextValue={(ctx) => (contextRef = ctx)} />
        </ChatHistoryProvider>
      );

      await waitFor(() => {
        expect(contextRef).not.toBeNull();
      });

      const messages: Message[] = [
        { id: '1', role: 'user', content: 'Hello' },
        { id: '2', role: 'assistant', content: 'Still typing...', isStreaming: true },
      ];

      act(() => {
        contextRef!.saveConversation(messages);
      });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe('1');
      });

      const stored = JSON.parse(localStorageMock._getStore()[STORAGE_KEY]);
      expect(stored[0].messages.every((m: Message) => m.isStreaming === false)).toBe(true);
    });

    it('should update existing conversation when ID provided', async () => {
      let contextRef: ReturnType<typeof useChatHistory> | null = null;

      render(
        <ChatHistoryProvider>
          <TestConsumer onContextValue={(ctx) => (contextRef = ctx)} />
        </ChatHistoryProvider>
      );

      await waitFor(() => {
        expect(contextRef).not.toBeNull();
      });

      // Save first conversation
      const messages1: Message[] = [
        { id: '1', role: 'user', content: 'First message' },
      ];

      act(() => {
        contextRef!.saveConversation(messages1);
      });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe('1');
      });

      // Get the conversation ID from state after save
      const convId = contextRef!.currentConversationId!;
      expect(convId).toBeTruthy();

      // Update the conversation
      const messages2: Message[] = [
        { id: '1', role: 'user', content: 'Updated message' },
        { id: '2', role: 'assistant', content: 'Response' },
      ];

      act(() => {
        contextRef!.saveConversation(messages2, convId);
      });

      await waitFor(() => {
        // Still only 1 conversation (updated, not new)
        expect(screen.getByTestId('conversation-count').textContent).toBe('1');
      });

      const stored = JSON.parse(localStorageMock._getStore()[STORAGE_KEY]);
      expect(stored[0].messages).toHaveLength(2);
      expect(stored[0].title).toBe('Updated message');
    });
  });

  describe('loadConversation', () => {
    it('should return conversation by ID', async () => {
      let contextRef: ReturnType<typeof useChatHistory> | null = null;

      render(
        <ChatHistoryProvider>
          <TestConsumer onContextValue={(ctx) => (contextRef = ctx)} />
        </ChatHistoryProvider>
      );

      await waitFor(() => {
        expect(contextRef).not.toBeNull();
      });

      // Save a conversation
      const messages: Message[] = [
        { id: '1', role: 'user', content: 'Test message' },
      ];

      act(() => {
        contextRef!.saveConversation(messages);
      });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe('1');
      });

      // Get the ID from state after save
      const convId = contextRef!.currentConversationId!;
      expect(convId).toBeTruthy();

      // Load it back
      const loaded = contextRef!.loadConversation(convId);

      expect(loaded).not.toBeNull();
      expect(loaded!.messages).toHaveLength(1);
      expect(loaded!.messages[0].content).toBe('Test message');
    });

    it('should return null for non-existent ID', async () => {
      let contextRef: ReturnType<typeof useChatHistory> | null = null;

      render(
        <ChatHistoryProvider>
          <TestConsumer onContextValue={(ctx) => (contextRef = ctx)} />
        </ChatHistoryProvider>
      );

      await waitFor(() => {
        expect(contextRef).not.toBeNull();
      });

      let loaded: Conversation | null = null;
      act(() => {
        loaded = contextRef!.loadConversation('non-existent-id');
      });

      expect(loaded).toBeNull();
    });
  });

  describe('deleteConversation', () => {
    it('should remove conversation by ID', async () => {
      let contextRef: ReturnType<typeof useChatHistory> | null = null;

      render(
        <ChatHistoryProvider>
          <TestConsumer onContextValue={(ctx) => (contextRef = ctx)} />
        </ChatHistoryProvider>
      );

      await waitFor(() => {
        expect(contextRef).not.toBeNull();
      });

      // Save first conversation
      const messages: Message[] = [{ id: '1', role: 'user', content: 'Test' }];
      act(() => {
        contextRef!.saveConversation(messages);
      });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe('1');
      });

      // Get first conversation ID
      const convId1 = contextRef!.currentConversationId!;
      expect(convId1).toBeTruthy();

      // Start new conversation before saving second one
      act(() => {
        contextRef!.startNewConversation();
      });

      act(() => {
        contextRef!.saveConversation([{ id: '2', role: 'user', content: 'Test 2' }]);
      });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe('2');
      });

      // Delete first conversation
      act(() => {
        contextRef!.deleteConversation(convId1);
      });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe('1');
      });

      // Verify localStorage was updated
      const stored = JSON.parse(localStorageMock._getStore()[STORAGE_KEY]);
      expect(stored).toHaveLength(1);
      expect(stored[0].id).not.toBe(convId1);
    });

    it('should clear currentConversationId if deleted conversation was current', async () => {
      let contextRef: ReturnType<typeof useChatHistory> | null = null;

      render(
        <ChatHistoryProvider>
          <TestConsumer onContextValue={(ctx) => (contextRef = ctx)} />
        </ChatHistoryProvider>
      );

      await waitFor(() => {
        expect(contextRef).not.toBeNull();
      });

      // Save and verify current ID is set
      const messages: Message[] = [{ id: '1', role: 'user', content: 'Test' }];
      act(() => {
        contextRef!.saveConversation(messages);
      });

      await waitFor(() => {
        expect(screen.getByTestId('current-id').textContent).not.toBe('none');
      });

      // Get the current conversation ID
      const convId = contextRef!.currentConversationId!;
      expect(convId).toBeTruthy();

      // Delete it
      act(() => {
        contextRef!.deleteConversation(convId);
      });

      await waitFor(() => {
        expect(screen.getByTestId('current-id').textContent).toBe('none');
      });
    });
  });

  describe('listConversations', () => {
    it('should return all conversations', async () => {
      let contextRef: ReturnType<typeof useChatHistory> | null = null;

      render(
        <ChatHistoryProvider>
          <TestConsumer onContextValue={(ctx) => (contextRef = ctx)} />
        </ChatHistoryProvider>
      );

      await waitFor(() => {
        expect(contextRef).not.toBeNull();
      });

      // Save 3 conversations, starting new conversation each time
      for (let i = 0; i < 3; i++) {
        act(() => {
          contextRef!.startNewConversation();
        });
        act(() => {
          contextRef!.saveConversation([
            { id: `${i}`, role: 'user', content: `Message ${i}` },
          ]);
        });
      }

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe('3');
      });

      const list = contextRef!.listConversations();
      expect(list).toHaveLength(3);
    });
  });

  describe('FIFO Limit (50 conversations)', () => {
    it('should enforce maximum of 50 conversations', async () => {
      let contextRef: ReturnType<typeof useChatHistory> | null = null;

      render(
        <ChatHistoryProvider>
          <TestConsumer onContextValue={(ctx) => (contextRef = ctx)} />
        </ChatHistoryProvider>
      );

      await waitFor(() => {
        expect(contextRef).not.toBeNull();
      });

      // Save 52 conversations (exceeds limit), starting new each time
      for (let i = 0; i < 52; i++) {
        act(() => {
          contextRef!.startNewConversation();
        });
        act(() => {
          contextRef!.saveConversation([
            { id: `${i}`, role: 'user', content: `Message ${i}` },
          ]);
        });
      }

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe(
          String(MAX_CONVERSATIONS)
        );
      });
    });

    it('should remove oldest conversations when limit exceeded (FIFO)', async () => {
      let contextRef: ReturnType<typeof useChatHistory> | null = null;

      render(
        <ChatHistoryProvider>
          <TestConsumer onContextValue={(ctx) => (contextRef = ctx)} />
        </ChatHistoryProvider>
      );

      await waitFor(() => {
        expect(contextRef).not.toBeNull();
      });

      // Save exactly 50 conversations, starting new conversation each time
      for (let i = 0; i < 50; i++) {
        act(() => {
          contextRef!.startNewConversation();
        });
        act(() => {
          contextRef!.saveConversation([
            { id: `${i}`, role: 'user', content: `Message ${i}` },
          ]);
        });
      }

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe('50');
      });

      // Save one more - should evict the oldest
      act(() => {
        contextRef!.startNewConversation();
      });
      act(() => {
        contextRef!.saveConversation([
          { id: 'new', role: 'user', content: 'New message' },
        ]);
      });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe('50');
      });

      // Verify the newest is at front
      const list = contextRef!.listConversations();
      expect(list[0].title).toBe('New message'); // Newest at front
    });
  });

  describe('startNewConversation', () => {
    it('should clear currentConversationId', async () => {
      let contextRef: ReturnType<typeof useChatHistory> | null = null;

      render(
        <ChatHistoryProvider>
          <TestConsumer onContextValue={(ctx) => (contextRef = ctx)} />
        </ChatHistoryProvider>
      );

      await waitFor(() => {
        expect(contextRef).not.toBeNull();
      });

      // Save a conversation
      act(() => {
        contextRef!.saveConversation([
          { id: '1', role: 'user', content: 'Test' },
        ]);
      });

      await waitFor(() => {
        expect(screen.getByTestId('current-id').textContent).not.toBe('none');
      });

      // Start new conversation
      act(() => {
        screen.getByTestId('new-conv-btn').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('current-id').textContent).toBe('none');
      });
    });
  });

  describe('getCurrentConversation', () => {
    it('should return current conversation when set', async () => {
      let contextRef: ReturnType<typeof useChatHistory> | null = null;

      render(
        <ChatHistoryProvider>
          <TestConsumer onContextValue={(ctx) => (contextRef = ctx)} />
        </ChatHistoryProvider>
      );

      await waitFor(() => {
        expect(contextRef).not.toBeNull();
      });

      // Save a conversation
      act(() => {
        contextRef!.saveConversation([
          { id: '1', role: 'user', content: 'Test message' },
        ]);
      });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-count').textContent).toBe('1');
      });

      let current: Conversation | null = null;
      act(() => {
        current = contextRef!.getCurrentConversation();
      });

      expect(current).not.toBeNull();
      expect(current!.title).toBe('Test message');
    });

    it('should return null when no current conversation', async () => {
      let contextRef: ReturnType<typeof useChatHistory> | null = null;

      render(
        <ChatHistoryProvider>
          <TestConsumer onContextValue={(ctx) => (contextRef = ctx)} />
        </ChatHistoryProvider>
      );

      await waitFor(() => {
        expect(contextRef).not.toBeNull();
      });

      let current: Conversation | null = null;
      act(() => {
        current = contextRef!.getCurrentConversation();
      });

      expect(current).toBeNull();
    });
  });

  describe('Hook Usage', () => {
    it('should throw error when used outside provider', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<TestConsumer />);
      }).toThrow('useChatHistory must be used within a ChatHistoryProvider');

      consoleSpy.mockRestore();
    });
  });
});
