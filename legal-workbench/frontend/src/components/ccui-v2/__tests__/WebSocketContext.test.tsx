import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import React from 'react';
import {
  WebSocketProvider,
  useWebSocket,
} from '../contexts/WebSocketContext';
import { mockWebSocketInstances } from '../../../test/setup';

// Mock the devToken module to avoid async crypto operations
vi.mock('../utils/devToken', () => ({
  setDevAuthCookie: vi.fn().mockResolvedValue('mock-jwt-token'),
}));

// Test component that exposes context values
function TestConsumer({
  onContextValue,
}: {
  onContextValue?: (value: ReturnType<typeof useWebSocket>) => void;
}) {
  const context = useWebSocket();
  React.useEffect(() => {
    onContextValue?.(context);
  }, [context, onContextValue]);

  return (
    <div>
      <span data-testid="connection-status">{context.connectionStatus}</span>
      <span data-testid="is-connected">{String(context.isConnected)}</span>
      <span data-testid="retry-count">{context.retryCount}</span>
      <span data-testid="last-message">{JSON.stringify(context.lastMessage)}</span>
      <span data-testid="last-error">{context.lastError?.message || 'none'}</span>
      <button data-testid="send-btn" onClick={() => context.sendMessage({ test: 'message' })}>
        Send
      </button>
      <button data-testid="retry-btn" onClick={() => context.retry()}>
        Retry
      </button>
      <button data-testid="clear-error-btn" onClick={() => context.clearError()}>
        Clear Error
      </button>
    </div>
  );
}

// Wrapper to render with provider
function renderWithProvider(
  props: { wsUrl?: string; maxRetries?: number; enabled?: boolean } = {}
) {
  return render(
    <WebSocketProvider {...props}>
      <TestConsumer />
    </WebSocketProvider>
  );
}

// Helper to flush pending promises
const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0));

describe('WebSocketContext', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  describe('Initial Connection', () => {
    it('should start in connecting state when enabled', async () => {
      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws' });

      // Flush async operations
      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(screen.getByTestId('connection-status').textContent).toBe('connecting');
      });
    });

    it('should start in disabled state when not enabled', async () => {
      renderWithProvider({ enabled: false });

      await waitFor(() => {
        expect(screen.getByTestId('connection-status').textContent).toBe('disabled');
      });
    });

    it('should create WebSocket with correct URL', async () => {
      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws' });

      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(1);
        expect(mockWebSocketInstances[0].url).toBe('ws://test.com/ws');
      });
    });

    it('should transition to connected state on WebSocket open', async () => {
      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws' });

      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(1);
      });

      await act(async () => {
        mockWebSocketInstances[0].simulateOpen();
      });

      await waitFor(() => {
        expect(screen.getByTestId('connection-status').textContent).toBe('connected');
        expect(screen.getByTestId('is-connected').textContent).toBe('true');
      });
    });
  });

  describe('Connection States', () => {
    it('should handle disconnected state on clean close', async () => {
      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws' });

      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(1);
      });

      await act(async () => {
        mockWebSocketInstances[0].simulateOpen();
      });

      await waitFor(() => {
        expect(screen.getByTestId('is-connected').textContent).toBe('true');
      });

      await act(async () => {
        mockWebSocketInstances[0].simulateClose(1000, true);
      });

      await waitFor(() => {
        expect(screen.getByTestId('connection-status').textContent).toBe('disconnected');
        expect(screen.getByTestId('is-connected').textContent).toBe('false');
      });
    });

    it('should handle error state with error code', async () => {
      // Use maxRetries: 2 so we can see the transition to error state
      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws', maxRetries: 2 });

      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(1);
      });

      // First failure - should retry (retryCount becomes 1)
      await act(async () => {
        mockWebSocketInstances[0].simulateClose(1006, false);
      });

      await waitFor(() => {
        expect(screen.getByTestId('retry-count').textContent).toBe('1');
      });

      // Advance timer to trigger retry
      await act(async () => {
        vi.advanceTimersByTime(3000);
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(2);
      });

      // Second failure - retryCount becomes 2, equals maxRetries
      await act(async () => {
        mockWebSocketInstances[1].simulateClose(1006, false);
      });

      // At this point retryCount = 2, maxRetries = 2, next connect will hit error state
      await act(async () => {
        vi.advanceTimersByTime(5000);
        await flushPromises();
      });

      await waitFor(() => {
        expect(screen.getByTestId('connection-status').textContent).toBe('error');
        // Error message depends on whether it's from setError or the close event
        expect(screen.getByTestId('last-error').textContent).not.toBe('none');
      });
    });
  });

  describe('Reconnection with Backoff', () => {
    it('should attempt reconnection on unclean close', async () => {
      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws', maxRetries: 3 });

      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(1);
      });

      // Simulate unclean close
      await act(async () => {
        mockWebSocketInstances[0].simulateClose(1006, false);
      });

      await waitFor(() => {
        expect(screen.getByTestId('retry-count').textContent).toBe('1');
        expect(screen.getByTestId('connection-status').textContent).toBe('disconnected');
      });

      // Advance timer for backoff (1000ms initial + up to 1000ms jitter)
      await act(async () => {
        vi.advanceTimersByTime(3000);
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(2);
      });
    });

    it('should increment retry count on each reconnection attempt', async () => {
      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws', maxRetries: 5 });

      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(1);
      });

      // First failure
      await act(async () => {
        mockWebSocketInstances[0].simulateClose(1006, false);
      });

      await waitFor(() => {
        expect(screen.getByTestId('retry-count').textContent).toBe('1');
      });

      // Advance timer and trigger second failure
      await act(async () => {
        vi.advanceTimersByTime(3000);
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(2);
      });

      await act(async () => {
        mockWebSocketInstances[1].simulateClose(1006, false);
      });

      await waitFor(() => {
        expect(screen.getByTestId('retry-count').textContent).toBe('2');
      });
    });

    it('should stop retrying after max retries reached', async () => {
      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws', maxRetries: 2 });

      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(1);
      });

      // First failure - retry count goes to 1
      await act(async () => {
        mockWebSocketInstances[0].simulateClose(1006, false);
      });

      await act(async () => {
        vi.advanceTimersByTime(3000);
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(2);
      });

      // Second failure - retry count goes to 2
      await act(async () => {
        mockWebSocketInstances[1].simulateClose(1006, false);
      });

      await act(async () => {
        vi.advanceTimersByTime(5000);
        await flushPromises();
      });

      // At this point, retryCount (2) >= maxRetries (2), so error state
      await waitFor(() => {
        expect(screen.getByTestId('connection-status').textContent).toBe('error');
      });

      // Advance timer - should not create new connection (stays at 2)
      await act(async () => {
        vi.advanceTimersByTime(10000);
        await flushPromises();
      });

      expect(mockWebSocketInstances.length).toBe(2);
    });

    it('should reset retry count on successful connection', async () => {
      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws', maxRetries: 5 });

      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(1);
      });

      // First failure
      await act(async () => {
        mockWebSocketInstances[0].simulateClose(1006, false);
      });

      await waitFor(() => {
        expect(screen.getByTestId('retry-count').textContent).toBe('1');
      });

      // Advance timer
      await act(async () => {
        vi.advanceTimersByTime(3000);
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(2);
      });

      // Successful connection
      await act(async () => {
        mockWebSocketInstances[1].simulateOpen();
      });

      await waitFor(() => {
        expect(screen.getByTestId('retry-count').textContent).toBe('0');
        expect(screen.getByTestId('connection-status').textContent).toBe('connected');
      });
    });
  });

  describe('Message Handling', () => {
    it('should send messages when connected', async () => {
      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws' });

      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(1);
      });

      await act(async () => {
        mockWebSocketInstances[0].simulateOpen();
      });

      await waitFor(() => {
        expect(screen.getByTestId('is-connected').textContent).toBe('true');
      });

      await act(async () => {
        screen.getByTestId('send-btn').click();
      });

      expect(mockWebSocketInstances[0].send).toHaveBeenCalledWith(
        JSON.stringify({ test: 'message' })
      );
    });

    it('should not send messages when disconnected', async () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws' });

      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(1);
      });

      // Try to send without opening connection
      await act(async () => {
        screen.getByTestId('send-btn').click();
      });

      expect(mockWebSocketInstances[0].send).not.toHaveBeenCalled();
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Not connected'),
        expect.anything()
      );

      consoleSpy.mockRestore();
    });

    it('should receive and parse messages', async () => {
      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws' });

      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(1);
      });

      await act(async () => {
        mockWebSocketInstances[0].simulateOpen();
      });

      await waitFor(() => {
        expect(screen.getByTestId('is-connected').textContent).toBe('true');
      });

      await act(async () => {
        mockWebSocketInstances[0].simulateMessage({ type: 'test', data: 'hello' });
      });

      await waitFor(() => {
        const lastMessage = screen.getByTestId('last-message').textContent;
        expect(lastMessage).toContain('test');
        expect(lastMessage).toContain('hello');
      });
    });
  });

  describe('Manual Retry', () => {
    it('should allow manual retry after max retries reached', async () => {
      // Start with maxRetries: 2 so we can reach error state
      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws', maxRetries: 2 });

      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(1);
      });

      // First failure - triggers retry (retryCount becomes 1)
      await act(async () => {
        mockWebSocketInstances[0].simulateClose(1006, false);
      });

      await act(async () => {
        vi.advanceTimersByTime(3000);
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(2);
      });

      // Second failure - retryCount becomes 2
      await act(async () => {
        mockWebSocketInstances[1].simulateClose(1006, false);
      });

      await act(async () => {
        vi.advanceTimersByTime(5000);
        await flushPromises();
      });

      // retryCount (2) >= maxRetries (2), goes to error state
      await waitFor(() => {
        expect(screen.getByTestId('connection-status').textContent).toBe('error');
      });

      // Manual retry should reset retryCount and create new connection
      await act(async () => {
        screen.getByTestId('retry-btn').click();
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(3);
        expect(screen.getByTestId('retry-count').textContent).toBe('0');
      });
    });

    it('should close existing socket on manual retry', async () => {
      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws' });

      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(1);
      });

      await act(async () => {
        mockWebSocketInstances[0].simulateOpen();
      });

      await waitFor(() => {
        expect(screen.getByTestId('is-connected').textContent).toBe('true');
      });

      await act(async () => {
        screen.getByTestId('retry-btn').click();
        await flushPromises();
      });

      expect(mockWebSocketInstances[0].close).toHaveBeenCalledWith(1000, 'Manual reconnect');
    });
  });

  describe('Error Handling', () => {
    it('should set appropriate error for code 1006', async () => {
      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws', maxRetries: 3 });

      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(1);
      });

      // Simulate unclean close with code 1006
      await act(async () => {
        mockWebSocketInstances[0].simulateClose(1006, false);
      });

      // Error should be set immediately even during retry
      await waitFor(() => {
        expect(screen.getByTestId('last-error').textContent).toContain('Connection closed');
      });
    });

    it('should set appropriate error for code 1011', async () => {
      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws', maxRetries: 3 });

      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(1);
      });

      await act(async () => {
        mockWebSocketInstances[0].simulateClose(1011, false);
      });

      await waitFor(() => {
        expect(screen.getByTestId('last-error').textContent).toContain('unexpected condition');
      });
    });

    it('should clear error on clearError call', async () => {
      renderWithProvider({ enabled: true, wsUrl: 'ws://test.com/ws', maxRetries: 3 });

      await act(async () => {
        await flushPromises();
      });

      await waitFor(() => {
        expect(mockWebSocketInstances.length).toBe(1);
      });

      await act(async () => {
        mockWebSocketInstances[0].simulateClose(1006, false);
      });

      await waitFor(() => {
        expect(screen.getByTestId('last-error').textContent).not.toBe('none');
      });

      await act(async () => {
        screen.getByTestId('clear-error-btn').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('last-error').textContent).toBe('none');
      });
    });
  });

  describe('Hook Usage', () => {
    it('should throw error when used outside provider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<TestConsumer />);
      }).toThrow('useWebSocket must be used within a WebSocketProvider');

      consoleSpy.mockRestore();
    });
  });
});
