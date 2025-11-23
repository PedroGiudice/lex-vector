/**
 * Vitest Configuration
 *
 * Test runner configuration for orchestration-tracker plugin
 */

import { defineConfig } from 'vitest/config';
import { resolve } from 'path';

export default defineConfig({
  test: {
    // Test environment
    environment: 'node',

    // Setup files
    setupFiles: ['./tests/setup.ts'],

    // Global test timeout (10s for integration tests)
    testTimeout: 10000,

    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/**',
        'dist/**',
        'tests/**',
        '**/*.test.ts',
        '**/*.config.ts',
        'examples/**',
      ],
      all: true,
      lines: 95,
      functions: 95,
      branches: 90,
      statements: 95,
    },

    // Include/exclude patterns
    include: ['tests/**/*.test.ts'],
    exclude: ['node_modules', 'dist'],

    // Run tests in parallel
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false,
      },
    },

    // Reporters
    reporters: ['verbose'],

    // Globals (for easier test writing)
    globals: true,

    // Mock reset between tests
    mockReset: true,
    restoreMocks: true,
    clearMocks: true,
  },

  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@tests': resolve(__dirname, './tests'),
    },
  },
});
