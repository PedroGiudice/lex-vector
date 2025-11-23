/**
 * Plugin System Types for Vibe-Log CLI
 *
 * Defines the plugin architecture enabling extensibility while
 * maintaining backward compatibility with existing vibe-log features.
 */

/**
 * Plugin configuration schema
 */
export interface PluginConfig {
  /** Plugin enable/disable flag */
  enabled: boolean;

  /** Plugin-specific settings (flexible schema) */
  settings?: Record<string, unknown>;

  /** Cache settings */
  cache?: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

/**
 * Session metadata shared across all plugins
 */
export interface SessionMetadata {
  sessionId: string;
  startTime: number;
  endTime?: number;
  projectDir: string;

  /** Vibe-log original metadata (preserved) */
  vibeLog?: {
    messages?: number;
    tokens?: number;
    [key: string]: unknown;
  };

  /** Plugin-contributed metadata */
  plugins?: Record<string, unknown>;
}

/**
 * Hook trigger points in vibe-log lifecycle
 */
export enum HookTrigger {
  SessionStart = 'SessionStart',
  SessionEnd = 'SessionEnd',
  UserPromptSubmit = 'UserPromptSubmit',
  PreToolUse = 'PreToolUse',
  PostToolUse = 'PostToolUse',
  PreCompact = 'PreCompact',
}

/**
 * Plugin hook handler signature
 */
export type PluginHookHandler<T = unknown> = (
  session: SessionMetadata,
  data?: T
) => Promise<void> | void;

/**
 * Plugin hooks definition
 */
export interface PluginHooks {
  [HookTrigger.SessionStart]?: PluginHookHandler;
  [HookTrigger.SessionEnd]?: PluginHookHandler;
  [HookTrigger.UserPromptSubmit]?: PluginHookHandler<{ prompt: string }>;
  [HookTrigger.PreToolUse]?: PluginHookHandler<{ tool: string }>;
  [HookTrigger.PostToolUse]?: PluginHookHandler<{ tool: string; result: unknown }>;
  [HookTrigger.PreCompact]?: PluginHookHandler;
}

/**
 * CLI command contributed by plugin
 */
export interface PluginCommand {
  /** Command name (e.g., 'orchestration') */
  name: string;

  /** Command description for help text */
  description: string;

  /** Command handler */
  action: (...args: unknown[]) => Promise<void> | void;

  /** Options/flags for command */
  options?: Array<{
    flags: string;
    description: string;
    defaultValue?: unknown;
  }>;
}

/**
 * Main plugin interface
 */
export interface VibeLogPlugin {
  /** Unique plugin identifier (kebab-case) */
  name: string;

  /** Semantic version */
  version: string;

  /** Human-readable description */
  description: string;

  /** Author info */
  author?: {
    name: string;
    email?: string;
    url?: string;
  };

  /** Hook implementations */
  hooks?: PluginHooks;

  /** CLI commands */
  commands?: PluginCommand[];

  /** Plugin initialization (called once on load) */
  init(config: PluginConfig): Promise<void> | void;

  /** Plugin cleanup (called on shutdown) */
  cleanup?(): Promise<void> | void;
}

/**
 * Plugin loader result
 */
export interface LoadedPlugin {
  plugin: VibeLogPlugin;
  config: PluginConfig;
  loadTime: number;
  error?: Error;
}

/**
 * Plugin registry interface
 */
export interface PluginRegistry {
  /** Register a plugin */
  register(plugin: VibeLogPlugin, config: PluginConfig): Promise<void>;

  /** Unregister a plugin */
  unregister(pluginName: string): Promise<void>;

  /** Get plugin by name */
  get(pluginName: string): LoadedPlugin | undefined;

  /** Get all loaded plugins */
  getAll(): LoadedPlugin[];

  /** Check if plugin is loaded */
  has(pluginName: string): boolean;

  /** Trigger hook across all plugins */
  triggerHook(
    trigger: HookTrigger,
    session: SessionMetadata,
    data?: unknown
  ): Promise<void>;
}

/**
 * Storage interface for plugin data
 */
export interface PluginStorage {
  /** Get item from storage */
  get<T>(key: string): Promise<T | undefined>;

  /** Set item in storage */
  set<T>(key: string, value: T): Promise<void>;

  /** Delete item from storage */
  delete(key: string): Promise<void>;

  /** Check if key exists */
  has(key: string): Promise<boolean>;

  /** Clear all plugin data */
  clear(): Promise<void>;
}

/**
 * Logger interface for plugins
 */
export interface PluginLogger {
  debug(message: string, ...args: unknown[]): void;
  info(message: string, ...args: unknown[]): void;
  warn(message: string, ...args: unknown[]): void;
  error(message: string, ...args: unknown[]): void;
}
