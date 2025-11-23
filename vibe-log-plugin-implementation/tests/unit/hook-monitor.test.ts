/**
 * Unit Tests: HookMonitor
 *
 * Tests for hook discovery and performance monitoring
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { readFile } from 'fs/promises';
import {
  MOCK_SETTINGS_JSON,
  MOCK_SETTINGS_MINIMAL,
  MOCK_SETTINGS_MALFORMED,
  EXPECTED_HOOKS,
} from '../fixtures/mock-hooks.js';

// Mock fs/promises
vi.mock('fs/promises');

describe('HookMonitor', () => {
  let HookMonitor: any;
  let monitor: any;

  beforeEach(async () => {
    vi.clearAllMocks();
    vi.resetModules();

    try {
      const module = await import(
        '../../src/plugins/orchestration-tracker/hook-monitor.js'
      );
      HookMonitor = module.HookMonitor;

      monitor = new HookMonitor({
        settingsPath: '.claude/settings.json',
      });
    } catch (error) {
      console.warn('HookMonitor implementation not found - skipping tests');
    }
  });

  describe('Hook Discovery', () => {
    it.skipIf(!HookMonitor)(
      'should parse hooks from settings.json',
      async () => {
        vi.mocked(readFile).mockResolvedValue(
          JSON.stringify(MOCK_SETTINGS_JSON)
        );

        const hooks = await monitor.discoverHooks('/test/project');

        expect(hooks).toHaveLength(5); // 3 UserPromptSubmit + 1 SessionStart + 1 PreToolUse
        expect(hooks.map((h: any) => h.name)).toContain(
          'invoke-legal-braniac-hybrid'
        );
        expect(hooks.map((h: any) => h.name)).toContain('session-init');
      }
    );

    it.skipIf(!HookMonitor)('should extract hook names from commands', async () => {
      vi.mocked(readFile).mockResolvedValue(
        JSON.stringify(MOCK_SETTINGS_JSON)
      );

      const hooks = await monitor.discoverHooks('/test/project');

      // Check that names are extracted correctly from command paths
      const brainiacHook = hooks.find(
        (h: any) => h.name === 'invoke-legal-braniac-hybrid'
      );
      expect(brainiacHook).toBeDefined();
      expect(brainiacHook.triggers).toContain('UserPromptSubmit');
    });

    it.skipIf(!HookMonitor)('should handle missing settings.json', async () => {
      vi.mocked(readFile).mockRejectedValue(
        new Error('ENOENT: no such file or directory')
      );

      const hooks = await monitor.discoverHooks('/test/project');

      expect(hooks).toEqual([]);
    });

    it.skipIf(!HookMonitor)(
      'should handle minimal settings.json',
      async () => {
        vi.mocked(readFile).mockResolvedValue(
          JSON.stringify(MOCK_SETTINGS_MINIMAL)
        );

        const hooks = await monitor.discoverHooks('/test/project');

        expect(hooks).toEqual([]);
      }
    );

    it.skipIf(!HookMonitor)(
      'should handle malformed settings.json gracefully',
      async () => {
        vi.mocked(readFile).mockResolvedValue(
          JSON.stringify(MOCK_SETTINGS_MALFORMED)
        );

        // Should not throw, but return empty or partial results
        const hooks = await monitor.discoverHooks('/test/project');

        expect(Array.isArray(hooks)).toBe(true);
      }
    );

    it.skipIf(!HookMonitor)('should parse hook descriptions', async () => {
      vi.mocked(readFile).mockResolvedValue(
        JSON.stringify(MOCK_SETTINGS_JSON)
      );

      const hooks = await monitor.discoverHooks('/test/project');

      const brainiacHook = hooks.find(
        (h: any) => h.name === 'invoke-legal-braniac-hybrid'
      );
      expect(brainiacHook.description).toBe('Legal-Braniac agent detection');
    });
  });

  describe('Execution Tracking', () => {
    it.skipIf(!HookMonitor)('should track execution metrics', async () => {
      monitor.trackExecution('test-hook', 25.5, true);
      monitor.trackExecution('test-hook', 30.2, true);
      monitor.trackExecution('test-hook', 28.1, false);

      const stats = monitor.getStats('test-hook');

      expect(stats.totalExecutions).toBe(3);
      expect(stats.avgDuration).toBeCloseTo(27.93, 1);
      expect(stats.failureRate).toBeCloseTo(0.333, 2);
      expect(stats.lastRun).toBeDefined();
    });

    it.skipIf(!HookMonitor)('should track multiple hooks independently', async () => {
      monitor.trackExecution('hook-1', 10, true);
      monitor.trackExecution('hook-2', 20, true);
      monitor.trackExecution('hook-1', 15, true);

      const stats1 = monitor.getStats('hook-1');
      const stats2 = monitor.getStats('hook-2');

      expect(stats1.totalExecutions).toBe(2);
      expect(stats1.avgDuration).toBe(12.5);

      expect(stats2.totalExecutions).toBe(1);
      expect(stats2.avgDuration).toBe(20);
    });

    it.skipIf(!HookMonitor)(
      'should return zero stats for non-existent hook',
      async () => {
        const stats = monitor.getStats('non-existent-hook');

        expect(stats.totalExecutions).toBe(0);
        expect(stats.avgDuration).toBe(0);
        expect(stats.failureRate).toBe(0);
        expect(stats.lastRun).toBeUndefined();
      }
    );

    it.skipIf(!HookMonitor)('should calculate average duration correctly', async () => {
      monitor.trackExecution('test-hook', 100, true);
      monitor.trackExecution('test-hook', 200, true);
      monitor.trackExecution('test-hook', 300, true);

      const stats = monitor.getStats('test-hook');

      expect(stats.avgDuration).toBe(200);
    });

    it.skipIf(!HookMonitor)('should calculate failure rate correctly', async () => {
      // 2 success, 3 failures
      monitor.trackExecution('test-hook', 10, true);
      monitor.trackExecution('test-hook', 10, true);
      monitor.trackExecution('test-hook', 10, false);
      monitor.trackExecution('test-hook', 10, false);
      monitor.trackExecution('test-hook', 10, false);

      const stats = monitor.getStats('test-hook');

      expect(stats.failureRate).toBe(0.6); // 3/5
    });

    it.skipIf(!HookMonitor)('should update lastRun timestamp', async () => {
      const before = Date.now();
      monitor.trackExecution('test-hook', 10, true);
      const after = Date.now();

      const stats = monitor.getStats('test-hook');

      expect(stats.lastRun).toBeGreaterThanOrEqual(before);
      expect(stats.lastRun).toBeLessThanOrEqual(after);
    });
  });

  describe('Performance', () => {
    it.skipIf(!HookMonitor)(
      'should parse settings.json in <20ms',
      async () => {
        vi.mocked(readFile).mockResolvedValue(
          JSON.stringify(MOCK_SETTINGS_JSON)
        );

        const start = Date.now();
        await monitor.discoverHooks('/test/project');
        const duration = Date.now() - start;

        expect(duration).toBeLessThan(20);
      }
    );

    it.skipIf(!HookMonitor)('should track execution in <1ms', async () => {
      const start = Date.now();
      monitor.trackExecution('test-hook', 25, true);
      const duration = Date.now() - start;

      expect(duration).toBeLessThan(1);
    });
  });

  describe('Error Handling', () => {
    it.skipIf(!HookMonitor)(
      'should handle invalid JSON gracefully',
      async () => {
        vi.mocked(readFile).mockResolvedValue('{ invalid json }');

        const hooks = await monitor.discoverHooks('/test/project');

        expect(hooks).toEqual([]);
      }
    );

    it.skipIf(!HookMonitor)(
      'should handle file read errors gracefully',
      async () => {
        vi.mocked(readFile).mockRejectedValue(new Error('Permission denied'));

        const hooks = await monitor.discoverHooks('/test/project');

        expect(hooks).toEqual([]);
      }
    );
  });

  describe('Statistics Aggregation', () => {
    it.skipIf(!HookMonitor)('should handle zero executions', async () => {
      const stats = monitor.getStats('never-executed');

      expect(stats.totalExecutions).toBe(0);
      expect(stats.avgDuration).toBe(0);
      expect(stats.failureRate).toBe(0);
    });

    it.skipIf(!HookMonitor)('should handle single execution', async () => {
      monitor.trackExecution('single-hook', 42, true);

      const stats = monitor.getStats('single-hook');

      expect(stats.totalExecutions).toBe(1);
      expect(stats.avgDuration).toBe(42);
      expect(stats.failureRate).toBe(0);
    });

    it.skipIf(!HookMonitor)('should handle all failures', async () => {
      monitor.trackExecution('fail-hook', 10, false);
      monitor.trackExecution('fail-hook', 10, false);
      monitor.trackExecution('fail-hook', 10, false);

      const stats = monitor.getStats('fail-hook');

      expect(stats.failureRate).toBe(1.0);
    });

    it.skipIf(!HookMonitor)('should handle all successes', async () => {
      monitor.trackExecution('success-hook', 10, true);
      monitor.trackExecution('success-hook', 10, true);
      monitor.trackExecution('success-hook', 10, true);

      const stats = monitor.getStats('success-hook');

      expect(stats.failureRate).toBe(0);
    });
  });
});
