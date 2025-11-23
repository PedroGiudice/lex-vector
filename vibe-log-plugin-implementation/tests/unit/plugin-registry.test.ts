/**
 * Unit Tests: PluginRegistry
 *
 * Tests for plugin registration, lifecycle, and hook execution
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { PluginRegistry } from '../../src/plugins/core/plugin-registry.js';
import { HookTrigger } from '../../src/plugins/core/types.js';
import {
  createMockPlugin,
  createMockConfig,
  createMockSession,
  measureTime,
} from '../helpers.js';
import type { VibeLogPlugin } from '../../src/plugins/core/types.js';

describe('PluginRegistry', () => {
  let registry: PluginRegistry;

  beforeEach(async () => {
    // Get fresh instance and clear all plugins
    registry = PluginRegistry.getInstance();
    await registry.clear();
  });

  describe('Plugin Registration', () => {
    it('should register plugin successfully', async () => {
      const plugin = createMockPlugin();
      const config = createMockConfig();

      await registry.register(plugin, config);

      expect(registry.has('test-plugin')).toBe(true);
      expect(registry.get('test-plugin')).toBeDefined();
    });

    it('should reject invalid plugin name (not kebab-case)', async () => {
      const plugin = createMockPlugin({ name: 'TestPlugin' });
      const config = createMockConfig();

      await expect(registry.register(plugin, config)).rejects.toThrow(
        /must be kebab-case/
      );
    });

    it('should reject plugin with no name', async () => {
      const plugin = createMockPlugin({ name: '' });
      const config = createMockConfig();

      await expect(registry.register(plugin, config)).rejects.toThrow(
        /must have a valid name/
      );
    });

    it('should reject plugin with no version', async () => {
      const plugin = createMockPlugin({ version: '' });
      const config = createMockConfig();

      await expect(registry.register(plugin, config)).rejects.toThrow(
        /must have a valid version/
      );
    });

    it('should reject plugin without init method', async () => {
      const plugin = {
        name: 'bad-plugin',
        version: '1.0.0',
        description: 'Bad plugin',
        // Missing init method
      } as unknown as VibeLogPlugin;
      const config = createMockConfig();

      await expect(registry.register(plugin, config)).rejects.toThrow(
        /must implement init/
      );
    });

    it('should reject duplicate plugin registration', async () => {
      const plugin = createMockPlugin();
      const config = createMockConfig();

      await registry.register(plugin, config);

      await expect(registry.register(plugin, config)).rejects.toThrow(
        /already registered/
      );
    });

    it('should initialize plugin on register', async () => {
      const initSpy = vi.fn();
      const plugin = createMockPlugin({
        init: initSpy,
      });
      const config = createMockConfig();

      await registry.register(plugin, config);

      expect(initSpy).toHaveBeenCalledWith(config);
    });

    it('should NOT initialize disabled plugin', async () => {
      const initSpy = vi.fn();
      const plugin = createMockPlugin({
        init: initSpy,
      });
      const config = createMockConfig({ enabled: false });

      await registry.register(plugin, config);

      expect(initSpy).not.toHaveBeenCalled();
    });

    it('should track load time', async () => {
      const plugin = createMockPlugin({
        init: async () => {
          await new Promise((resolve) => setTimeout(resolve, 10));
        },
      });
      const config = createMockConfig();

      await registry.register(plugin, config);

      const loaded = registry.get('test-plugin');
      expect(loaded?.loadTime).toBeGreaterThanOrEqual(10);
    });

    it('should store failed plugin with error', async () => {
      const error = new Error('Init failed');
      const plugin = createMockPlugin({
        init: async () => {
          throw error;
        },
      });
      const config = createMockConfig();

      await expect(registry.register(plugin, config)).rejects.toThrow(
        'Init failed'
      );

      const loaded = registry.get('test-plugin');
      expect(loaded?.error).toBeDefined();
      expect(loaded?.error?.message).toBe('Init failed');
    });
  });

  describe('Plugin Unregistration', () => {
    it('should unregister plugin and call cleanup', async () => {
      const cleanupSpy = vi.fn();
      const plugin = createMockPlugin({
        cleanup: cleanupSpy,
      });
      const config = createMockConfig();

      await registry.register(plugin, config);
      await registry.unregister('test-plugin');

      expect(cleanupSpy).toHaveBeenCalled();
      expect(registry.has('test-plugin')).toBe(false);
    });

    it('should throw when unregistering non-existent plugin', async () => {
      await expect(registry.unregister('non-existent')).rejects.toThrow(
        /is not registered/
      );
    });

    it('should handle cleanup errors gracefully', async () => {
      const plugin = createMockPlugin({
        cleanup: async () => {
          throw new Error('Cleanup failed');
        },
      });
      const config = createMockConfig();

      await registry.register(plugin, config);

      await expect(registry.unregister('test-plugin')).rejects.toThrow(
        'Cleanup failed'
      );
    });
  });

  describe('Plugin Retrieval', () => {
    it('should get plugin by name', async () => {
      const plugin = createMockPlugin();
      const config = createMockConfig();

      await registry.register(plugin, config);

      const loaded = registry.get('test-plugin');
      expect(loaded?.plugin.name).toBe('test-plugin');
      expect(loaded?.config).toEqual(config);
    });

    it('should return undefined for non-existent plugin', () => {
      const loaded = registry.get('non-existent');
      expect(loaded).toBeUndefined();
    });

    it('should get all plugins', async () => {
      const plugin1 = createMockPlugin({ name: 'plugin-1' });
      const plugin2 = createMockPlugin({ name: 'plugin-2' });
      const config = createMockConfig();

      await registry.register(plugin1, config);
      await registry.register(plugin2, config);

      const all = registry.getAll();
      expect(all).toHaveLength(2);
      expect(all.map((p) => p.plugin.name)).toContain('plugin-1');
      expect(all.map((p) => p.plugin.name)).toContain('plugin-2');
    });

    it('should check if plugin exists', async () => {
      const plugin = createMockPlugin();
      const config = createMockConfig();

      expect(registry.has('test-plugin')).toBe(false);

      await registry.register(plugin, config);

      expect(registry.has('test-plugin')).toBe(true);
    });
  });

  describe('Hook Execution', () => {
    it('should trigger hooks in parallel', async () => {
      const hook1Spy = vi.fn();
      const hook2Spy = vi.fn();

      const plugin1 = createMockPlugin({
        name: 'plugin-1',
        hooks: {
          [HookTrigger.SessionStart]: hook1Spy,
        },
      });

      const plugin2 = createMockPlugin({
        name: 'plugin-2',
        hooks: {
          [HookTrigger.SessionStart]: hook2Spy,
        },
      });

      const config = createMockConfig();
      await registry.register(plugin1, config);
      await registry.register(plugin2, config);

      const session = createMockSession();
      await registry.triggerHook(HookTrigger.SessionStart, session);

      expect(hook1Spy).toHaveBeenCalledWith(session, undefined);
      expect(hook2Spy).toHaveBeenCalledWith(session, undefined);
    });

    it('should pass data to hook handlers', async () => {
      const hookSpy = vi.fn();
      const plugin = createMockPlugin({
        hooks: {
          [HookTrigger.UserPromptSubmit]: hookSpy,
        },
      });

      const config = createMockConfig();
      await registry.register(plugin, config);

      const session = createMockSession();
      const data = { prompt: 'test prompt' };

      await registry.triggerHook(HookTrigger.UserPromptSubmit, session, data);

      expect(hookSpy).toHaveBeenCalledWith(session, data);
    });

    it('should skip disabled plugins', async () => {
      const hookSpy = vi.fn();
      const plugin = createMockPlugin({
        hooks: {
          [HookTrigger.SessionStart]: hookSpy,
        },
      });

      const config = createMockConfig({ enabled: false });
      await registry.register(plugin, config);

      const session = createMockSession();
      await registry.triggerHook(HookTrigger.SessionStart, session);

      expect(hookSpy).not.toHaveBeenCalled();
    });

    it('should skip plugins with errors', async () => {
      const hookSpy = vi.fn();
      const plugin = createMockPlugin({
        init: async () => {
          throw new Error('Init failed');
        },
        hooks: {
          [HookTrigger.SessionStart]: hookSpy,
        },
      });

      const config = createMockConfig();
      await expect(registry.register(plugin, config)).rejects.toThrow();

      const session = createMockSession();
      await registry.triggerHook(HookTrigger.SessionStart, session);

      expect(hookSpy).not.toHaveBeenCalled();
    });

    it('should skip plugins without hook implementation', async () => {
      const plugin = createMockPlugin({
        hooks: {}, // No SessionStart hook
      });

      const config = createMockConfig();
      await registry.register(plugin, config);

      const session = createMockSession();

      // Should not throw
      await expect(
        registry.triggerHook(HookTrigger.SessionStart, session)
      ).resolves.not.toThrow();
    });

    it('should handle plugin errors gracefully', async () => {
      const errorHook = vi.fn().mockRejectedValue(new Error('Hook failed'));
      const successHook = vi.fn().mockResolvedValue(undefined);

      const plugin1 = createMockPlugin({
        name: 'failing-plugin',
        hooks: {
          [HookTrigger.SessionStart]: errorHook,
        },
      });

      const plugin2 = createMockPlugin({
        name: 'success-plugin',
        hooks: {
          [HookTrigger.SessionStart]: successHook,
        },
      });

      const config = createMockConfig();
      await registry.register(plugin1, config);
      await registry.register(plugin2, config);

      const session = createMockSession();

      // Should not throw, but continue with other plugins
      await registry.triggerHook(HookTrigger.SessionStart, session);

      expect(errorHook).toHaveBeenCalled();
      expect(successHook).toHaveBeenCalled();
    });

    it('should execute hooks in parallel for performance', async () => {
      // Create 3 plugins with slow hooks
      const delay = 50;
      const createSlowPlugin = (name: string) => {
        return createMockPlugin({
          name,
          hooks: {
            [HookTrigger.SessionStart]: async () => {
              await new Promise((resolve) => setTimeout(resolve, delay));
            },
          },
        });
      };

      const config = createMockConfig();
      await registry.register(createSlowPlugin('plugin-1'), config);
      await registry.register(createSlowPlugin('plugin-2'), config);
      await registry.register(createSlowPlugin('plugin-3'), config);

      const session = createMockSession();
      const { duration } = await measureTime(() =>
        registry.triggerHook(HookTrigger.SessionStart, session)
      );

      // If sequential: 150ms+, if parallel: ~50ms
      expect(duration).toBeLessThan(delay * 2);
    });

    it('should handle no plugins gracefully', async () => {
      const session = createMockSession();

      // Should not throw
      await expect(
        registry.triggerHook(HookTrigger.SessionStart, session)
      ).resolves.not.toThrow();
    });
  });

  describe('Clear Registry', () => {
    it('should clear all plugins', async () => {
      const plugin1 = createMockPlugin({ name: 'plugin-1' });
      const plugin2 = createMockPlugin({ name: 'plugin-2' });
      const config = createMockConfig();

      await registry.register(plugin1, config);
      await registry.register(plugin2, config);

      expect(registry.getAll()).toHaveLength(2);

      await registry.clear();

      expect(registry.getAll()).toHaveLength(0);
    });

    it('should call cleanup on all plugins when clearing', async () => {
      const cleanup1 = vi.fn();
      const cleanup2 = vi.fn();

      const plugin1 = createMockPlugin({
        name: 'plugin-1',
        cleanup: cleanup1,
      });

      const plugin2 = createMockPlugin({
        name: 'plugin-2',
        cleanup: cleanup2,
      });

      const config = createMockConfig();
      await registry.register(plugin1, config);
      await registry.register(plugin2, config);

      await registry.clear();

      expect(cleanup1).toHaveBeenCalled();
      expect(cleanup2).toHaveBeenCalled();
    });
  });

  describe('Singleton Pattern', () => {
    it('should return same instance', () => {
      const instance1 = PluginRegistry.getInstance();
      const instance2 = PluginRegistry.getInstance();

      expect(instance1).toBe(instance2);
    });
  });
});
