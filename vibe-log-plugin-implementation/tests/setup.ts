/**
 * Vitest Setup File
 *
 * Global test configuration, mocks, and utilities
 */

import { beforeEach, afterEach, vi } from 'vitest';

/**
 * Global beforeEach - Reset mocks and state
 */
beforeEach(() => {
  // Reset all mocks before each test
  vi.clearAllMocks();

  // Reset timers
  vi.useFakeTimers();
});

/**
 * Global afterEach - Cleanup
 */
afterEach(() => {
  // Restore real timers
  vi.useRealTimers();

  // Clear all intervals/timeouts
  vi.clearAllTimers();
});

/**
 * Mock console to reduce test noise
 * Individual tests can override with vi.spyOn()
 */
global.console = {
  ...console,
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
};

/**
 * Mock fs/promises for file system operations
 */
vi.mock('fs/promises', () => ({
  readFile: vi.fn(),
  writeFile: vi.fn(),
  readdir: vi.fn(),
  stat: vi.fn(),
  mkdir: vi.fn(),
  access: vi.fn(),
  unlink: vi.fn(),
}));

/**
 * Mock path module (real implementation is fine, but can be overridden)
 */
vi.mock('path', async () => {
  const actual = await vi.importActual<typeof import('path')>('path');
  return actual;
});
