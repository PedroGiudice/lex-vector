/**
 * Plugin Loader - Dynamic Plugin Loading
 *
 * Handles plugin discovery, loading, and configuration resolution
 */

import { readFile, readdir, stat } from 'fs/promises';
import { join, resolve } from 'path';
import { pathToFileURL } from 'url';
import { homedir } from 'os';
import type { VibeLogPlugin, PluginConfig } from './types.js';

/**
 * Plugin loading errors
 */
export class PluginLoadError extends Error {
  constructor(
    message: string,
    public readonly pluginPath: string,
    public readonly cause?: Error
  ) {
    super(message);
    this.name = 'PluginLoadError';
  }
}

/**
 * Load a single plugin from path
 *
 * @param pluginPath - Absolute or relative path to plugin (file or directory)
 * @returns Loaded plugin instance
 * @throws {PluginLoadError} If plugin cannot be loaded or is invalid
 */
export async function loadPlugin(pluginPath: string): Promise<VibeLogPlugin> {
  try {
    // Resolve path (supports relative paths, node_modules, etc.)
    const resolvedPath = await resolvePluginPath(pluginPath);

    // Dynamic import (ESM)
    const fileUrl = pathToFileURL(resolvedPath).href;
    const module = await import(fileUrl);

    // Validate plugin export
    const plugin = extractPluginExport(module);
    validatePluginStructure(plugin, resolvedPath);

    return plugin;
  } catch (error) {
    if (error instanceof PluginLoadError) {
      throw error;
    }

    throw new PluginLoadError(
      `Failed to load plugin from "${pluginPath}"`,
      pluginPath,
      error as Error
    );
  }
}

/**
 * Load all plugins from a directory
 *
 * @param dir - Directory containing plugins
 * @returns Array of loaded plugins (skips invalid ones with warnings)
 */
export async function loadPluginsFromDir(
  dir: string
): Promise<VibeLogPlugin[]> {
  const plugins: VibeLogPlugin[] = [];
  const errors: PluginLoadError[] = [];

  try {
    const resolvedDir = resolve(dir);
    const entries = await readdir(resolvedDir, { withFileTypes: true });

    // Load plugins in parallel
    const loadPromises = entries.map(async (entry) => {
      // Skip non-directories and hidden folders
      if (!entry.isDirectory() || entry.name.startsWith('.')) {
        return null;
      }

      const pluginPath = join(resolvedDir, entry.name, 'index.ts');

      try {
        // Check if index.ts exists
        await stat(pluginPath);
        return await loadPlugin(pluginPath);
      } catch (error) {
        // Skip directories without index.ts (not plugins)
        if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
          return null;
        }

        // Log other errors but continue
        const loadError =
          error instanceof PluginLoadError
            ? error
            : new PluginLoadError(
                `Failed to load plugin from "${pluginPath}"`,
                pluginPath,
                error as Error
              );
        errors.push(loadError);
        return null;
      }
    });

    const results = await Promise.all(loadPromises);
    plugins.push(...results.filter((p): p is VibeLogPlugin => p !== null));

    // Log errors (non-blocking)
    if (errors.length > 0) {
      console.warn(
        `⚠️  ${errors.length} plugin(s) failed to load from "${dir}":`
      );
      errors.forEach((err) => {
        console.warn(`   - ${err.pluginPath}: ${err.message}`);
      });
    }

    return plugins;
  } catch (error) {
    throw new PluginLoadError(
      `Failed to read plugin directory "${dir}"`,
      dir,
      error as Error
    );
  }
}

/**
 * Load plugin configuration from ~/.vibe-log/config.json
 *
 * @param pluginName - Plugin name (kebab-case)
 * @returns Plugin configuration with defaults
 */
export async function loadPluginConfig(
  pluginName: string
): Promise<PluginConfig> {
  const configPath = join(homedir(), '.vibe-log', 'config.json');

  try {
    const configContent = await readFile(configPath, 'utf-8');
    const config = JSON.parse(configContent);

    // Extract plugin config (plugins.{name})
    const pluginConfig = config.plugins?.[pluginName];

    // Return defaults if not configured
    if (!pluginConfig) {
      return {
        enabled: false, // Disabled by default
        settings: {},
      };
    }

    // Merge with defaults
    return {
      enabled: pluginConfig.enabled ?? false,
      settings: pluginConfig.settings ?? {},
      cache: pluginConfig.cache ?? {
        enabled: true,
        ttlSeconds: 300, // 5 minutes default
      },
    };
  } catch (error) {
    // Config file doesn't exist or is invalid - return defaults
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      return {
        enabled: false,
        settings: {},
      };
    }

    // JSON parse error
    if (error instanceof SyntaxError) {
      console.warn(
        `⚠️  Invalid JSON in config file "${configPath}", using defaults`
      );
      return {
        enabled: false,
        settings: {},
      };
    }

    throw error;
  }
}

/**
 * Resolve plugin path (supports multiple formats)
 *
 * Priority:
 * 1. Absolute path
 * 2. Relative path (from cwd)
 * 3. node_modules lookup
 * 4. ~/.vibe-log/plugins/ lookup
 */
async function resolvePluginPath(pluginPath: string): Promise<string> {
  // 1. Try as-is (absolute or relative)
  try {
    const resolvedPath = resolve(pluginPath);
    await stat(resolvedPath);
    return resolvedPath;
  } catch (error) {
    // File doesn't exist, try other methods
  }

  // 2. Try node_modules
  try {
    const nodeModulesPath = resolve('node_modules', pluginPath);
    await stat(nodeModulesPath);
    return nodeModulesPath;
  } catch (error) {
    // Not in node_modules
  }

  // 3. Try ~/.vibe-log/plugins/
  try {
    const vibeLogPluginsPath = join(
      homedir(),
      '.vibe-log',
      'plugins',
      pluginPath
    );
    await stat(vibeLogPluginsPath);
    return vibeLogPluginsPath;
  } catch (error) {
    // Not found anywhere
  }

  throw new Error(
    `Plugin path "${pluginPath}" not found (tried: relative, node_modules, ~/.vibe-log/plugins/)`
  );
}

/**
 * Extract plugin export from module
 *
 * Supports:
 * - export default plugin
 * - export const plugin = ...
 * - export { plugin }
 */
function extractPluginExport(module: unknown): VibeLogPlugin {
  const mod = module as Record<string, unknown>;

  // Try default export first
  if (mod.default && typeof mod.default === 'object') {
    return mod.default as VibeLogPlugin;
  }

  // Try named exports (common pattern: export const orchestrationTracker = ...)
  const possibleExports = Object.values(mod).filter(
    (value) => typeof value === 'object' && value !== null
  );

  if (possibleExports.length === 1) {
    return possibleExports[0] as VibeLogPlugin;
  }

  // Multiple exports - look for one with plugin structure
  const pluginExport = possibleExports.find((value) => {
    const obj = value as Record<string, unknown>;
    return (
      typeof obj.name === 'string' &&
      typeof obj.version === 'string' &&
      typeof obj.init === 'function'
    );
  });

  if (pluginExport) {
    return pluginExport as VibeLogPlugin;
  }

  throw new Error(
    'Plugin module must export a valid VibeLogPlugin (default export or named export)'
  );
}

/**
 * Validate plugin structure
 */
function validatePluginStructure(
  plugin: unknown,
  pluginPath: string
): asserts plugin is VibeLogPlugin {
  if (!plugin || typeof plugin !== 'object') {
    throw new PluginLoadError(
      'Plugin must be an object',
      pluginPath
    );
  }

  const p = plugin as Record<string, unknown>;

  if (!p.name || typeof p.name !== 'string') {
    throw new PluginLoadError(
      'Plugin must have a valid "name" property',
      pluginPath
    );
  }

  if (!p.version || typeof p.version !== 'string') {
    throw new PluginLoadError(
      'Plugin must have a valid "version" property',
      pluginPath
    );
  }

  if (!p.init || typeof p.init !== 'function') {
    throw new PluginLoadError(
      'Plugin must implement "init()" method',
      pluginPath
    );
  }

  // Validate kebab-case name
  if (!/^[a-z0-9-]+$/.test(p.name)) {
    throw new PluginLoadError(
      `Plugin name "${p.name}" must be kebab-case (lowercase, hyphens only)`,
      pluginPath
    );
  }
}
