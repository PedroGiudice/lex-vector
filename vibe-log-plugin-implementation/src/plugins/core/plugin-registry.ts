/**
 * Plugin Registry Implementation
 *
 * Manages plugin lifecycle: registration, initialization, hook triggering
 */

import type {
  VibeLogPlugin,
  PluginConfig,
  LoadedPlugin,
  PluginRegistry as IPluginRegistry,
  HookTrigger,
  SessionMetadata,
  PluginLogger,
} from './types.js';

/**
 * Simple console-based logger for plugins
 */
class ConsoleLogger implements PluginLogger {
  constructor(private prefix: string) {}

  debug(message: string, ...args: unknown[]): void {
    console.debug(`[${this.prefix}]`, message, ...args);
  }

  info(message: string, ...args: unknown[]): void {
    console.info(`[${this.prefix}]`, message, ...args);
  }

  warn(message: string, ...args: unknown[]): void {
    console.warn(`[${this.prefix}]`, message, ...args);
  }

  error(message: string, ...args: unknown[]): void {
    console.error(`[${this.prefix}]`, message, ...args);
  }
}

/**
 * Plugin Registry - Singleton
 */
export class PluginRegistry implements IPluginRegistry {
  private static instance: PluginRegistry;
  private plugins: Map<string, LoadedPlugin> = new Map();
  private logger: PluginLogger;

  private constructor() {
    this.logger = new ConsoleLogger('PluginRegistry');
  }

  /**
   * Get singleton instance
   */
  static getInstance(): PluginRegistry {
    if (!PluginRegistry.instance) {
      PluginRegistry.instance = new PluginRegistry();
    }
    return PluginRegistry.instance;
  }

  /**
   * Register a plugin
   */
  async register(plugin: VibeLogPlugin, config: PluginConfig): Promise<void> {
    const startTime = Date.now();

    try {
      // Validate plugin
      this.validatePlugin(plugin);

      // Check if already registered
      if (this.plugins.has(plugin.name)) {
        throw new Error(`Plugin "${plugin.name}" is already registered`);
      }

      // Initialize plugin
      if (config.enabled) {
        await plugin.init(config);
        this.logger.info(`Plugin "${plugin.name}" initialized`);
      } else {
        this.logger.debug(`Plugin "${plugin.name}" registered but disabled`);
      }

      // Store in registry
      const loadTime = Date.now() - startTime;
      this.plugins.set(plugin.name, {
        plugin,
        config,
        loadTime,
      });

      this.logger.info(
        `Plugin "${plugin.name}" registered successfully (${loadTime}ms)`
      );
    } catch (error) {
      const loadTime = Date.now() - startTime;
      this.logger.error(
        `Failed to register plugin "${plugin.name}":`,
        error
      );

      // Store failed plugin for debugging
      this.plugins.set(plugin.name, {
        plugin,
        config,
        loadTime,
        error: error as Error,
      });

      throw error;
    }
  }

  /**
   * Unregister a plugin
   */
  async unregister(pluginName: string): Promise<void> {
    const loaded = this.plugins.get(pluginName);

    if (!loaded) {
      throw new Error(`Plugin "${pluginName}" is not registered`);
    }

    try {
      // Call cleanup if exists
      if (loaded.plugin.cleanup) {
        await loaded.plugin.cleanup();
      }

      this.plugins.delete(pluginName);
      this.logger.info(`Plugin "${pluginName}" unregistered`);
    } catch (error) {
      this.logger.error(
        `Error unregistering plugin "${pluginName}":`,
        error
      );
      throw error;
    }
  }

  /**
   * Get plugin by name
   */
  get(pluginName: string): LoadedPlugin | undefined {
    return this.plugins.get(pluginName);
  }

  /**
   * Get all loaded plugins
   */
  getAll(): LoadedPlugin[] {
    return Array.from(this.plugins.values());
  }

  /**
   * Check if plugin is loaded
   */
  has(pluginName: string): boolean {
    return this.plugins.has(pluginName);
  }

  /**
   * Trigger hook across all enabled plugins
   */
  async triggerHook(
    trigger: HookTrigger,
    session: SessionMetadata,
    data?: unknown
  ): Promise<void> {
    const enabledPlugins = Array.from(this.plugins.values()).filter(
      (loaded) => loaded.config.enabled && !loaded.error
    );

    if (enabledPlugins.length === 0) {
      return;
    }

    this.logger.debug(
      `Triggering hook "${trigger}" for ${enabledPlugins.length} plugin(s)`
    );

    // Execute hooks in parallel
    const promises = enabledPlugins.map(async (loaded) => {
      const { plugin } = loaded;
      const handler = plugin.hooks?.[trigger];

      if (!handler) {
        return; // Plugin doesn't implement this hook
      }

      try {
        const startTime = Date.now();
        await handler(session, data);
        const duration = Date.now() - startTime;

        this.logger.debug(
          `Hook "${trigger}" completed for plugin "${plugin.name}" (${duration}ms)`
        );
      } catch (error) {
        this.logger.error(
          `Hook "${trigger}" failed for plugin "${plugin.name}":`,
          error
        );
        // Don't throw - continue with other plugins
      }
    });

    await Promise.all(promises);
  }

  /**
   * Validate plugin structure
   */
  private validatePlugin(plugin: VibeLogPlugin): void {
    if (!plugin.name || typeof plugin.name !== 'string') {
      throw new Error('Plugin must have a valid name');
    }

    if (!plugin.version || typeof plugin.version !== 'string') {
      throw new Error('Plugin must have a valid version');
    }

    if (!plugin.init || typeof plugin.init !== 'function') {
      throw new Error('Plugin must implement init() method');
    }

    // Validate plugin name format (kebab-case)
    if (!/^[a-z0-9-]+$/.test(plugin.name)) {
      throw new Error(
        `Plugin name "${plugin.name}" must be kebab-case (lowercase, hyphens only)`
      );
    }
  }

  /**
   * Clear all plugins (for testing)
   */
  async clear(): Promise<void> {
    const pluginNames = Array.from(this.plugins.keys());

    for (const name of pluginNames) {
      await this.unregister(name);
    }

    this.logger.info('All plugins cleared');
  }
}

/**
 * Export singleton instance
 */
export const pluginRegistry = PluginRegistry.getInstance();
