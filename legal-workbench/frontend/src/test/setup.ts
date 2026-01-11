import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock window.getSelection (required by some components)
Object.defineProperty(window, 'getSelection', {
  writable: true,
  value: vi.fn(() => ({
    toString: vi.fn(() => ''),
    removeAllRanges: vi.fn(),
    addRange: vi.fn(),
    getRangeAt: vi.fn(),
    rangeCount: 0,
    isCollapsed: true,
  })),
});

// Mock URL.createObjectURL and URL.revokeObjectURL for file handling tests
Object.defineProperty(URL, 'createObjectURL', {
  writable: true,
  value: vi.fn(() => 'blob:mock-url'),
});

Object.defineProperty(URL, 'revokeObjectURL', {
  writable: true,
  value: vi.fn(),
});

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
    get length() {
      return Object.keys(store).length;
    },
    key: vi.fn((index: number) => Object.keys(store)[index] || null),
    // Internal helper to reset store for tests
    _reset: () => {
      store = {};
    },
    // Internal helper to set data directly for tests
    _setStore: (data: Record<string, string>) => {
      store = { ...data };
    },
    _getStore: () => store,
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

export { localStorageMock };

// Mock WebSocket class
export class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    mockWebSocketInstances.push(this);
  }

  send = vi.fn();
  close = vi.fn((code?: number, reason?: string) => {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      const event = new CloseEvent('close', {
        wasClean: code === 1000,
        code: code || 1000,
        reason: reason || '',
      });
      this.onclose(event);
    }
  });

  // Test helpers
  simulateOpen() {
    this.readyState = MockWebSocket.OPEN;
    if (this.onopen) {
      this.onopen(new Event('open'));
    }
  }

  simulateClose(code: number = 1000, wasClean: boolean = true) {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      const event = new CloseEvent('close', { wasClean, code, reason: '' });
      this.onclose(event);
    }
  }

  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }

  simulateMessage(data: unknown) {
    if (this.onmessage) {
      const event = new MessageEvent('message', {
        data: JSON.stringify(data),
      });
      this.onmessage(event);
    }
  }
}

// Store reference to mock instances for testing
export const mockWebSocketInstances: MockWebSocket[] = [];

// Global WebSocket mock
vi.stubGlobal('WebSocket', MockWebSocket);

// Mock crypto.subtle for JWT generation in devToken
Object.defineProperty(globalThis, 'crypto', {
  value: {
    subtle: {
      importKey: vi.fn().mockResolvedValue({}),
      sign: vi.fn().mockResolvedValue(new ArrayBuffer(32)),
    },
    getRandomValues: vi.fn((arr: Uint8Array) => {
      for (let i = 0; i < arr.length; i++) {
        arr[i] = Math.floor(Math.random() * 256);
      }
      return arr;
    }),
  },
});

// Mock document.cookie
let cookieStore = '';
Object.defineProperty(document, 'cookie', {
  get: () => cookieStore,
  set: (value: string) => {
    // Append cookies like real browser behavior
    const parts = value.split(';')[0];
    const existing = cookieStore.split('; ').filter((c) => c && !c.startsWith(parts.split('=')[0]));
    existing.push(parts);
    cookieStore = existing.filter(Boolean).join('; ');
  },
  configurable: true,
});

export const resetCookieStore = () => {
  cookieStore = '';
};

// Reset mocks before each test
beforeEach(() => {
  localStorageMock._reset();
  vi.clearAllMocks();
  mockWebSocketInstances.length = 0;
  resetCookieStore();
});
