/**
 * Test Helpers and Utilities
 *
 * Common functions used across test suites
 */

import type {
  VibeLogPlugin,
  PluginConfig,
  SessionMetadata,
  HookTrigger,
} from '../src/plugins/core/types.js';

/**
 * Create a mock plugin for testing
 */
export function createMockPlugin(
  overrides?: Partial<VibeLogPlugin>
): VibeLogPlugin {
  return {
    name: 'test-plugin',
    version: '1.0.0',
    description: 'Test plugin',
    init: async () => {},
    cleanup: async () => {},
    hooks: {},
    commands: [],
    ...overrides,
  };
}

/**
 * Create a default plugin config
 */
export function createMockConfig(
  overrides?: Partial<PluginConfig>
): PluginConfig {
  return {
    enabled: true,
    settings: {},
    cache: {
      enabled: false,
      ttlSeconds: 300,
    },
    ...overrides,
  };
}

/**
 * Create a mock session metadata
 */
export function createMockSession(
  overrides?: Partial<SessionMetadata>
): SessionMetadata {
  return {
    sessionId: 'test-session-123',
    startTime: Date.now(),
    projectDir: '/test/project',
    vibeLog: {
      messages: 0,
      tokens: 0,
    },
    plugins: {},
    ...overrides,
  };
}

/**
 * Create a spy that tracks async function calls
 */
export function createAsyncSpy<T = unknown>(): jest.Mock<Promise<T>> {
  return async (...args: unknown[]) => {
    return Promise.resolve(args as unknown as T);
  };
}

/**
 * Wait for all promises to resolve
 */
export async function flushPromises(): Promise<void> {
  return new Promise((resolve) => setImmediate(resolve));
}

/**
 * Measure execution time of async function
 */
export async function measureTime<T>(
  fn: () => Promise<T>
): Promise<{ result: T; duration: number }> {
  const start = Date.now();
  const result = await fn();
  const duration = Date.now() - start;
  return { result, duration };
}

/**
 * Create a mock file system structure
 */
export interface MockFileSystem {
  [path: string]: string | MockFileSystem;
}

/**
 * Convert mock file system to readdir/readFile compatible structure
 */
export function setupMockFS(fs: MockFileSystem): Map<string, string> {
  const files = new Map<string, string>();

  function traverse(obj: MockFileSystem, prefix = ''): void {
    for (const [key, value] of Object.entries(obj)) {
      const path = prefix ? `${prefix}/${key}` : key;

      if (typeof value === 'string') {
        files.set(path, value);
      } else {
        traverse(value, path);
      }
    }
  }

  traverse(fs);
  return files;
}

/**
 * Assert that function throws specific error
 */
export async function expectThrowsAsync(
  fn: () => Promise<unknown>,
  errorMessage: string | RegExp
): Promise<void> {
  let error: Error | undefined;

  try {
    await fn();
  } catch (e) {
    error = e as Error;
  }

  if (!error) {
    throw new Error('Expected function to throw, but it did not');
  }

  if (typeof errorMessage === 'string') {
    if (!error.message.includes(errorMessage)) {
      throw new Error(
        `Expected error message to include "${errorMessage}", but got "${error.message}"`
      );
    }
  } else {
    if (!errorMessage.test(error.message)) {
      throw new Error(
        `Expected error message to match ${errorMessage}, but got "${error.message}"`
      );
    }
  }
}

/**
 * Create a mock timer for performance testing
 */
export class MockTimer {
  private startTime = 0;

  start(): void {
    this.startTime = Date.now();
  }

  elapsed(): number {
    return Date.now() - this.startTime;
  }

  assertLessThan(ms: number): void {
    const elapsed = this.elapsed();
    if (elapsed >= ms) {
      throw new Error(
        `Expected execution time to be less than ${ms}ms, but got ${elapsed}ms`
      );
    }
  }
}

/**
 * Create a mock logger that tracks calls
 */
export function createMockLogger() {
  return {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  };
}

/**
 * Assert hook was called with correct parameters
 */
export function assertHookCalled(
  hookSpy: jest.Mock,
  trigger: HookTrigger,
  session: SessionMetadata,
  data?: unknown
): void {
  const calls = hookSpy.mock.calls;

  if (calls.length === 0) {
    throw new Error(`Expected hook to be called, but it was not`);
  }

  const lastCall = calls[calls.length - 1];
  const [actualSession, actualData] = lastCall;

  if (actualSession.sessionId !== session.sessionId) {
    throw new Error(
      `Expected session ID "${session.sessionId}", but got "${actualSession.sessionId}"`
    );
  }

  if (data !== undefined && JSON.stringify(actualData) !== JSON.stringify(data)) {
    throw new Error(
      `Expected hook data to match, but got different data`
    );
  }
}
