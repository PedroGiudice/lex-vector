import { renderHook, act, waitFor } from '@testing-library/react';
import { useChatWebSocket } from './useChatWebSocket';

// Mock WebSocket
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    this.onopen = null;
    this.onmessage = null;
    this.onclose = null;
    this.onerror = null;

    // Simulate connection after a short delay
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  send(data) {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
    // Store sent message for testing
    this.lastSentMessage = data;
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code: 1000 }));
    }
  }

  // Helper to simulate receiving a message
  simulateMessage(data) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }));
    }
  }

  // Helper to simulate error
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
}

// WebSocket constants
MockWebSocket.CONNECTING = 0;
MockWebSocket.OPEN = 1;
MockWebSocket.CLOSING = 2;
MockWebSocket.CLOSED = 3;

global.WebSocket = MockWebSocket;

// Mock timers
jest.useFakeTimers();

describe('useChatWebSocket', () => {
  let mockWebSocket;

  beforeEach(() => {
    mockWebSocket = null;
    jest.clearAllMocks();
    jest.clearAllTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
  });

  describe('Connection Management', () => {
    test('should connect on mount', async () => {
      const { result } = renderHook(() =>
        useChatWebSocket({
          url: 'ws://localhost:3000/ws'
        })
      );

      expect(result.current.connectionStatus).toBe('connecting');
      expect(result.current.isConnected).toBe(false);

      // Wait for connection
      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      expect(result.current.connectionStatus).toBe('connected');
    });

    test('should call onConnect callback when connected', async () => {
      const onConnect = jest.fn();

      renderHook(() =>
        useChatWebSocket({
          url: 'ws://localhost:3000/ws',
          onConnect
        })
      );

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(onConnect).toHaveBeenCalledTimes(1);
      });
    });

    test('should construct URL with token for OSS mode', () => {
      const { result } = renderHook(() =>
        useChatWebSocket({
          url: '/ws',
          token: 'test-token-123',
          isPlatform: false
        })
      );

      // The URL should be constructed with the token parameter
      expect(result.current.connectionStatus).toBe('connecting');
    });

    test('should not append token in platform mode', () => {
      const { result } = renderHook(() =>
        useChatWebSocket({
          url: '/ws',
          token: 'test-token-123',
          isPlatform: true
        })
      );

      expect(result.current.connectionStatus).toBe('connecting');
    });
  });

  describe('Message Handling', () => {
    test('should receive and parse messages', async () => {
      const onMessage = jest.fn();
      let wsInstance;

      const originalWebSocket = global.WebSocket;
      global.WebSocket = function(url) {
        wsInstance = new MockWebSocket(url);
        return wsInstance;
      };

      const { result } = renderHook(() =>
        useChatWebSocket({
          url: 'ws://localhost:3000/ws',
          onMessage
        })
      );

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      // Simulate receiving a message
      const testMessage = {
        type: 'claude-response',
        data: { content: 'Hello, world!' }
      };

      act(() => {
        wsInstance.simulateMessage(testMessage);
      });

      expect(onMessage).toHaveBeenCalledWith(testMessage);
      expect(result.current.lastMessage).toEqual(testMessage);

      global.WebSocket = originalWebSocket;
    });

    test('should send messages when connected', async () => {
      let wsInstance;

      const originalWebSocket = global.WebSocket;
      global.WebSocket = function(url) {
        wsInstance = new MockWebSocket(url);
        return wsInstance;
      };

      const { result } = renderHook(() =>
        useChatWebSocket({
          url: 'ws://localhost:3000/ws'
        })
      );

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      const testMessage = { type: 'user-message', content: 'Test' };

      act(() => {
        result.current.sendMessage(testMessage);
      });

      expect(wsInstance.lastSentMessage).toBe(JSON.stringify(testMessage));

      global.WebSocket = originalWebSocket;
    });

    test('should buffer messages when not connected', async () => {
      let wsInstance;

      const originalWebSocket = global.WebSocket;
      global.WebSocket = function(url) {
        wsInstance = new MockWebSocket(url);
        return wsInstance;
      };

      const { result } = renderHook(() =>
        useChatWebSocket({
          url: 'ws://localhost:3000/ws'
        })
      );

      // Send message before connection is established
      const testMessage = { type: 'user-message', content: 'Test' };

      act(() => {
        result.current.sendMessage(testMessage);
      });

      // Message should be buffered, not sent yet
      expect(wsInstance.lastSentMessage).toBeUndefined();

      // Now connect
      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      // Buffered message should be sent on connection
      expect(wsInstance.lastSentMessage).toBe(JSON.stringify(testMessage));

      global.WebSocket = originalWebSocket;
    });
  });

  describe('Reconnection Logic', () => {
    test('should auto-reconnect on disconnect', async () => {
      let wsInstance;
      let connectionCount = 0;

      const originalWebSocket = global.WebSocket;
      global.WebSocket = function(url) {
        connectionCount++;
        wsInstance = new MockWebSocket(url);
        return wsInstance;
      };

      const { result } = renderHook(() =>
        useChatWebSocket({
          url: 'ws://localhost:3000/ws',
          autoReconnect: true,
          reconnectDelay: 1000
        })
      );

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      expect(connectionCount).toBe(1);

      // Simulate disconnect
      act(() => {
        wsInstance.close();
      });

      expect(result.current.isConnected).toBe(false);
      expect(result.current.connectionStatus).toBe('disconnected');

      // Wait for reconnect delay
      await act(async () => {
        jest.advanceTimersByTime(1100);
      });

      // Should have attempted to reconnect
      expect(connectionCount).toBeGreaterThan(1);

      global.WebSocket = originalWebSocket;
    });

    test('should not reconnect when autoReconnect is false', async () => {
      let wsInstance;
      let connectionCount = 0;

      const originalWebSocket = global.WebSocket;
      global.WebSocket = function(url) {
        connectionCount++;
        wsInstance = new MockWebSocket(url);
        return wsInstance;
      };

      const { result } = renderHook(() =>
        useChatWebSocket({
          url: 'ws://localhost:3000/ws',
          autoReconnect: false
        })
      );

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      const initialConnectionCount = connectionCount;

      // Simulate disconnect
      act(() => {
        wsInstance.close();
      });

      // Wait for what would be the reconnect delay
      await act(async () => {
        jest.advanceTimersByTime(5000);
      });

      // Should not have reconnected
      expect(connectionCount).toBe(initialConnectionCount);

      global.WebSocket = originalWebSocket;
    });

    test('should respect maxReconnectAttempts', async () => {
      let wsInstance;
      let connectionCount = 0;

      const originalWebSocket = global.WebSocket;
      global.WebSocket = function(url) {
        connectionCount++;
        wsInstance = new MockWebSocket(url);
        // Simulate connection failure
        setTimeout(() => {
          if (wsInstance.onclose) {
            wsInstance.readyState = WebSocket.CLOSED;
            wsInstance.onclose(new CloseEvent('close', { code: 1006 }));
          }
        }, 20);
        return wsInstance;
      };

      const { result } = renderHook(() =>
        useChatWebSocket({
          url: 'ws://localhost:3000/ws',
          autoReconnect: true,
          reconnectDelay: 100,
          maxReconnectAttempts: 3
        })
      );

      // Let initial connection attempt complete and fail
      await act(async () => {
        jest.advanceTimersByTime(50);
      });

      // Trigger reconnection attempts
      for (let i = 0; i < 5; i++) {
        await act(async () => {
          jest.advanceTimersByTime(200);
        });
      }

      // Should have attempted initial + 3 reconnects = 4 total
      expect(connectionCount).toBeLessThanOrEqual(4);

      global.WebSocket = originalWebSocket;
    });

    test('should manually reconnect', async () => {
      let wsInstance;
      let connectionCount = 0;

      const originalWebSocket = global.WebSocket;
      global.WebSocket = function(url) {
        connectionCount++;
        wsInstance = new MockWebSocket(url);
        return wsInstance;
      };

      const { result } = renderHook(() =>
        useChatWebSocket({
          url: 'ws://localhost:3000/ws',
          autoReconnect: false
        })
      );

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      const initialConnectionCount = connectionCount;

      // Manually trigger reconnect
      act(() => {
        result.current.reconnect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Should have created a new connection
      expect(connectionCount).toBeGreaterThan(initialConnectionCount);

      global.WebSocket = originalWebSocket;
    });
  });

  describe('Error Handling', () => {
    test('should call onError callback on error', async () => {
      const onError = jest.fn();
      let wsInstance;

      const originalWebSocket = global.WebSocket;
      global.WebSocket = function(url) {
        wsInstance = new MockWebSocket(url);
        return wsInstance;
      };

      const { result } = renderHook(() =>
        useChatWebSocket({
          url: 'ws://localhost:3000/ws',
          onError
        })
      );

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      // Simulate error
      act(() => {
        wsInstance.simulateError();
      });

      expect(onError).toHaveBeenCalled();
      expect(result.current.connectionStatus).toBe('error');

      global.WebSocket = originalWebSocket;
    });

    test('should handle JSON parse errors gracefully', async () => {
      let wsInstance;
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      const originalWebSocket = global.WebSocket;
      global.WebSocket = function(url) {
        wsInstance = new MockWebSocket(url);
        return wsInstance;
      };

      const { result } = renderHook(() =>
        useChatWebSocket({
          url: 'ws://localhost:3000/ws'
        })
      );

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      // Send invalid JSON
      act(() => {
        if (wsInstance.onmessage) {
          wsInstance.onmessage(new MessageEvent('message', { data: 'invalid json' }));
        }
      });

      expect(consoleError).toHaveBeenCalled();

      consoleError.mockRestore();
      global.WebSocket = originalWebSocket;
    });
  });

  describe('Cleanup', () => {
    test('should cleanup on unmount', async () => {
      let wsInstance;

      const originalWebSocket = global.WebSocket;
      global.WebSocket = function(url) {
        wsInstance = new MockWebSocket(url);
        return wsInstance;
      };

      const { unmount } = renderHook(() =>
        useChatWebSocket({
          url: 'ws://localhost:3000/ws'
        })
      );

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      const closeSpy = jest.spyOn(wsInstance, 'close');

      unmount();

      expect(closeSpy).toHaveBeenCalled();

      global.WebSocket = originalWebSocket;
    });

    test('should clear reconnect timeout on unmount', async () => {
      let wsInstance;

      const originalWebSocket = global.WebSocket;
      global.WebSocket = function(url) {
        wsInstance = new MockWebSocket(url);
        return wsInstance;
      };

      const { unmount } = renderHook(() =>
        useChatWebSocket({
          url: 'ws://localhost:3000/ws',
          autoReconnect: true,
          reconnectDelay: 5000
        })
      );

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Trigger disconnect to start reconnect timer
      act(() => {
        wsInstance.close();
      });

      // Unmount before reconnect happens
      unmount();

      // Advance time past reconnect delay
      await act(async () => {
        jest.advanceTimersByTime(6000);
      });

      // No error should occur from attempting to reconnect after unmount

      global.WebSocket = originalWebSocket;
    });

    test('should call onDisconnect when manually disconnecting', async () => {
      const onDisconnect = jest.fn();
      let wsInstance;

      const originalWebSocket = global.WebSocket;
      global.WebSocket = function(url) {
        wsInstance = new MockWebSocket(url);
        return wsInstance;
      };

      const { result } = renderHook(() =>
        useChatWebSocket({
          url: 'ws://localhost:3000/ws',
          onDisconnect
        })
      );

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      act(() => {
        result.current.disconnect();
      });

      expect(onDisconnect).toHaveBeenCalled();
      expect(result.current.isConnected).toBe(false);

      global.WebSocket = originalWebSocket;
    });
  });
});
