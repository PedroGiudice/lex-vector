import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import ChatView from '../ChatView';

// Mock child components
jest.mock('../ChatHeader', () => {
  return function MockChatHeader({ currentModel, onModelChange, projectName }) {
    return (
      <div data-testid="chat-header">
        <span data-testid="project-name">{projectName}</span>
        <button onClick={() => onModelChange('test-model')}>Change Model</button>
      </div>
    );
  };
});

jest.mock('../ChatInput', () => {
  return function MockChatInput({ onSend, isProcessing, placeholder }) {
    return (
      <div data-testid="chat-input">
        <input
          data-testid="input-field"
          placeholder={placeholder}
          disabled={isProcessing}
          onChange={(e) => {}}
        />
        <button
          data-testid="send-button"
          onClick={() => onSend('test message')}
          disabled={isProcessing}
        >
          Send
        </button>
      </div>
    );
  };
});

jest.mock('../MessageList', () => {
  return function MockMessageList({ messages, isProcessing }) {
    return (
      <div data-testid="message-list">
        {messages.map((msg, idx) => (
          <div key={idx} data-testid={`message-${idx}`}>
            {msg.content}
          </div>
        ))}
        {isProcessing && <div data-testid="processing-indicator">Processing...</div>}
      </div>
    );
  };
});

jest.mock('../ThinkingIndicator', () => {
  return function MockThinkingIndicator() {
    return <div data-testid="thinking-indicator">Thinking...</div>;
  };
});

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock WebSocket
class MockWebSocket {
  constructor() {
    this.readyState = WebSocket.OPEN;
    this.listeners = {};
  }

  addEventListener(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  removeEventListener(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  send(data) {
    this.lastSent = data;
  }

  simulateMessage(data) {
    const event = { data: JSON.stringify(data) };
    if (this.listeners.message) {
      this.listeners.message.forEach(callback => callback(event));
    }
  }
}

global.WebSocket = MockWebSocket;
MockWebSocket.OPEN = 1;

describe('ChatView Component', () => {
  let mockProject;
  let mockSession;
  let mockWs;
  let mockSendMessage;
  let mockOnSessionActive;
  let mockOnSessionInactive;

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);

    mockProject = {
      id: 'project-1',
      name: 'Test Project',
      path: '/test/path'
    };

    mockSession = {
      id: 'session-1',
      name: 'Test Session'
    };

    mockWs = new MockWebSocket();
    mockSendMessage = jest.fn();
    mockOnSessionActive = jest.fn();
    mockOnSessionInactive = jest.fn();
  });

  describe('Rendering', () => {
    test('renders all main components', () => {
      render(
        <ChatView
          selectedProject={mockProject}
          selectedSession={mockSession}
          ws={mockWs}
        />
      );

      expect(screen.getByTestId('chat-header')).toBeInTheDocument();
      expect(screen.getByTestId('message-list')).toBeInTheDocument();
      expect(screen.getByTestId('chat-input')).toBeInTheDocument();
    });

    test('displays project name in header', () => {
      render(
        <ChatView
          selectedProject={mockProject}
          selectedSession={mockSession}
          ws={mockWs}
        />
      );

      expect(screen.getByTestId('project-name')).toHaveTextContent('Test Project');
    });

    test('shows appropriate placeholder when no project selected', () => {
      render(
        <ChatView
          selectedProject={null}
          ws={mockWs}
        />
      );

      expect(screen.getByTestId('input-field')).toHaveAttribute(
        'placeholder',
        'Select a project to start chatting...'
      );
    });

    test('does not show thinking indicator when not processing', () => {
      render(
        <ChatView
          selectedProject={mockProject}
          ws={mockWs}
        />
      );

      expect(screen.queryByTestId('thinking-indicator')).not.toBeInTheDocument();
    });
  });

  describe('Message Sending', () => {
    test('sends message via sendMessage prop when provided', async () => {
      render(
        <ChatView
          selectedProject={mockProject}
          selectedSession={mockSession}
          ws={mockWs}
          sendMessage={mockSendMessage}
        />
      );

      const sendButton = screen.getByTestId('send-button');

      await act(async () => {
        fireEvent.click(sendButton);
      });

      expect(mockSendMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          content: 'test message',
          projectName: 'Test Project'
        })
      );
    });

    test('sends message via WebSocket when sendMessage not provided', async () => {
      render(
        <ChatView
          selectedProject={mockProject}
          selectedSession={mockSession}
          ws={mockWs}
        />
      );

      const sendButton = screen.getByTestId('send-button');

      await act(async () => {
        fireEvent.click(sendButton);
      });

      expect(mockWs.lastSent).toBeDefined();
      const sentData = JSON.parse(mockWs.lastSent);
      expect(sentData.type).toBe('chat-message');
      expect(sentData.content).toBe('test message');
    });

    test('marks session as active when sending message', async () => {
      render(
        <ChatView
          selectedProject={mockProject}
          selectedSession={mockSession}
          ws={mockWs}
          onSessionActive={mockOnSessionActive}
        />
      );

      const sendButton = screen.getByTestId('send-button');

      await act(async () => {
        fireEvent.click(sendButton);
      });

      expect(mockOnSessionActive).toHaveBeenCalled();
    });

    test('disables input when processing', async () => {
      const { rerender } = render(
        <ChatView
          selectedProject={mockProject}
          ws={mockWs}
        />
      );

      // Simulate processing state by sending a message
      const sendButton = screen.getByTestId('send-button');
      await act(async () => {
        fireEvent.click(sendButton);
      });

      expect(screen.getByTestId('input-field')).toBeDisabled();
      expect(screen.getByTestId('send-button')).toBeDisabled();
    });
  });

  describe('WebSocket Message Handling', () => {
    test('handles session-created event', async () => {
      const mockOnReplaceSession = jest.fn();

      render(
        <ChatView
          selectedProject={mockProject}
          ws={mockWs}
          onReplaceTemporarySession={mockOnReplaceSession}
        />
      );

      await act(async () => {
        mockWs.simulateMessage({
          type: 'session-created',
          sessionId: 'new-session-id',
          temporaryId: 'temp-id'
        });
      });

      expect(mockOnReplaceSession).toHaveBeenCalledWith('temp-id', 'new-session-id');
    });

    test('handles incoming message', async () => {
      render(
        <ChatView
          selectedProject={mockProject}
          ws={mockWs}
        />
      );

      await act(async () => {
        mockWs.simulateMessage({
          type: 'message',
          role: 'assistant',
          content: 'Hello from Claude',
          messageId: 'msg-1'
        });
      });

      await waitFor(() => {
        expect(screen.getByText('Hello from Claude')).toBeInTheDocument();
      });
    });

    test('shows thinking indicator during processing', async () => {
      render(
        <ChatView
          selectedProject={mockProject}
          ws={mockWs}
          showThinking={true}
        />
      );

      await act(async () => {
        mockWs.simulateMessage({ type: 'processing-start' });
        mockWs.simulateMessage({ type: 'thinking' });
      });

      await waitFor(() => {
        expect(screen.getByTestId('thinking-indicator')).toBeInTheDocument();
      });
    });

    test('hides thinking indicator when complete', async () => {
      render(
        <ChatView
          selectedProject={mockProject}
          ws={mockWs}
          showThinking={true}
        />
      );

      await act(async () => {
        mockWs.simulateMessage({ type: 'processing-start' });
        mockWs.simulateMessage({ type: 'thinking' });
      });

      await waitFor(() => {
        expect(screen.getByTestId('thinking-indicator')).toBeInTheDocument();
      });

      await act(async () => {
        mockWs.simulateMessage({ type: 'claude-complete' });
      });

      await waitFor(() => {
        expect(screen.queryByTestId('thinking-indicator')).not.toBeInTheDocument();
      });
    });

    test('marks session as inactive when complete', async () => {
      render(
        <ChatView
          selectedProject={mockProject}
          selectedSession={mockSession}
          ws={mockWs}
          onSessionInactive={mockOnSessionInactive}
        />
      );

      await act(async () => {
        mockWs.simulateMessage({ type: 'claude-complete' });
      });

      expect(mockOnSessionInactive).toHaveBeenCalledWith('session-1');
    });

    test('handles error messages', async () => {
      render(
        <ChatView
          selectedProject={mockProject}
          ws={mockWs}
        />
      );

      await act(async () => {
        mockWs.simulateMessage({
          type: 'error',
          message: 'Test error message'
        });
      });

      await waitFor(() => {
        expect(screen.getByText('Test error message')).toBeInTheDocument();
      });
    });
  });

  describe('State Persistence', () => {
    test('saves model preference to localStorage', async () => {
      render(
        <ChatView
          selectedProject={mockProject}
          ws={mockWs}
        />
      );

      const changeModelButton = screen.getByText('Change Model');

      await act(async () => {
        fireEvent.click(changeModelButton);
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'chat_model_Test Project',
        'test-model'
      );
    });

    test('loads saved messages from localStorage', () => {
      const savedMessages = [
        { id: 1, content: 'Saved message', role: 'user', type: 'user' }
      ];

      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'chat_messages_Test Project') {
          return JSON.stringify(savedMessages);
        }
        return null;
      });

      render(
        <ChatView
          selectedProject={mockProject}
          ws={mockWs}
        />
      );

      expect(screen.getByText('Saved message')).toBeInTheDocument();
    });

    test('saves messages to localStorage', async () => {
      render(
        <ChatView
          selectedProject={mockProject}
          ws={mockWs}
        />
      );

      await act(async () => {
        mockWs.simulateMessage({
          type: 'message',
          role: 'assistant',
          content: 'New message',
          messageId: 'msg-1'
        });
      });

      await waitFor(() => {
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          'chat_messages_Test Project',
          expect.stringContaining('New message')
        );
      });
    });
  });

  describe('Message Deduplication', () => {
    test('prevents duplicate messages with same ID', async () => {
      render(
        <ChatView
          selectedProject={mockProject}
          ws={mockWs}
        />
      );

      await act(async () => {
        mockWs.simulateMessage({
          type: 'message',
          role: 'assistant',
          content: 'Duplicate test',
          messageId: 'same-id'
        });
        mockWs.simulateMessage({
          type: 'message',
          role: 'assistant',
          content: 'Duplicate test',
          messageId: 'same-id'
        });
      });

      await waitFor(() => {
        const messages = screen.getAllByText('Duplicate test');
        expect(messages).toHaveLength(1);
      });
    });
  });
});
