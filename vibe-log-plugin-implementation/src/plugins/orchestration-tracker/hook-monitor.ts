/**
 * Hook Monitor - Hook Execution Tracking
 *
 * Monitors Claude Code hook execution performance and statistics
 */

import { readFile } from 'fs/promises';
import { join } from 'path';
import type {
  OrchestrationConfig,
  HookDefinition,
  HookStats,
} from './types.js';

/**
 * Hook execution record (internal)
 */
interface HookExecution {
  timestamp: number;
  duration: number;
  success: boolean;
  error?: string;
}

/**
 * Hook Monitor Service
 */
export class HookMonitor {
  private executions: Map<string, HookExecution[]> = new Map();

  constructor(private config: OrchestrationConfig) {}

  /**
   * Discover hooks from .claude/settings.json
   *
   * @param projectDir - Project root directory
   * @returns Array of hook definitions
   */
  async discoverHooks(projectDir: string): Promise<HookDefinition[]> {
    const settingsPath = join(projectDir, '.claude', 'settings.json');

    try {
      const content = await readFile(settingsPath, 'utf-8');
      const settings = JSON.parse(content);

      const hooks: HookDefinition[] = [];

      // Parse hooks section
      if (settings.hooks && typeof settings.hooks === 'object') {
        for (const [trigger, hookConfig] of Object.entries(settings.hooks)) {
          if (!hookConfig || typeof hookConfig !== 'object') {
            continue;
          }

          const config = hookConfig as Record<string, unknown>;

          // Handle both single and multiple hooks
          const hooksArray = Array.isArray(config.hooks)
            ? config.hooks
            : [config];

          for (const hook of hooksArray) {
            if (typeof hook !== 'object' || !hook) {
              continue;
            }

            const hookObj = hook as Record<string, unknown>;
            const command = hookObj.command as string;

            if (!command) {
              continue;
            }

            const name = this.extractHookName(command);
            const description = (hookObj.description as string) || 'No description';

            hooks.push({
              name,
              triggers: [trigger],
              command,
              description,
            });
          }
        }
      }

      this.log(`Discovered ${hooks.length} hook(s) from settings.json`);
      return hooks;
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        this.log('settings.json not found');
        return [];
      }

      if (error instanceof SyntaxError) {
        throw new Error(`Invalid JSON in settings.json: ${error.message}`);
      }

      throw error;
    }
  }

  /**
   * Track hook execution
   *
   * @param hookName - Hook identifier
   * @param duration - Execution duration (ms)
   * @param success - Whether execution succeeded
   * @param error - Optional error message
   */
  trackExecution(
    hookName: string,
    duration: number,
    success: boolean,
    error?: string
  ): void {
    const execution: HookExecution = {
      timestamp: Date.now(),
      duration,
      success,
      error,
    };

    const existing = this.executions.get(hookName) || [];
    existing.push(execution);

    // Keep only last 100 executions per hook (prevent memory bloat)
    if (existing.length > 100) {
      existing.shift();
    }

    this.executions.set(hookName, existing);

    this.log(
      `Tracked execution for "${hookName}": ${duration}ms (${success ? 'success' : 'failure'})`
    );
  }

  /**
   * Get execution statistics for a hook
   *
   * @param hookName - Hook identifier
   * @returns Aggregated statistics
   */
  getStats(hookName: string): HookStats {
    const executions = this.executions.get(hookName) || [];

    if (executions.length === 0) {
      return {
        totalExecutions: 0,
        avgDuration: 0,
        failureRate: 0,
      };
    }

    const totalExecutions = executions.length;
    const durations = executions.map((e) => e.duration);
    const failures = executions.filter((e) => !e.success).length;

    const avgDuration =
      durations.reduce((sum, d) => sum + d, 0) / totalExecutions;
    const failureRate = failures / totalExecutions;
    const lastRun = executions[executions.length - 1].timestamp;
    const minDuration = Math.min(...durations);
    const maxDuration = Math.max(...durations);

    return {
      totalExecutions,
      avgDuration: Math.round(avgDuration),
      failureRate: Math.round(failureRate * 1000) / 1000, // 3 decimal places
      lastRun,
      minDuration,
      maxDuration,
    };
  }

  /**
   * Get all tracked hooks with stats
   *
   * @returns Map of hook name to stats
   */
  getAllStats(): Map<string, HookStats> {
    const stats = new Map<string, HookStats>();

    for (const hookName of this.executions.keys()) {
      stats.set(hookName, this.getStats(hookName));
    }

    return stats;
  }

  /**
   * Get recent executions for a hook
   *
   * @param hookName - Hook identifier
   * @param limit - Maximum number of executions to return
   * @returns Recent executions (newest first)
   */
  getRecentExecutions(
    hookName: string,
    limit: number = 10
  ): HookExecution[] {
    const executions = this.executions.get(hookName) || [];
    return executions.slice(-limit).reverse();
  }

  /**
   * Clear execution history for a hook
   *
   * @param hookName - Hook identifier (or all if not specified)
   */
  clearHistory(hookName?: string): void {
    if (hookName) {
      this.executions.delete(hookName);
      this.log(`Cleared history for "${hookName}"`);
    } else {
      this.executions.clear();
      this.log('Cleared all execution history');
    }
  }

  /**
   * Extract hook name from command
   *
   * Examples:
   * - "node .claude/hooks/foo.js" -> "foo"
   * - "python .claude/hooks/bar.py" -> "bar"
   * - "/path/to/script.sh" -> "script"
   */
  private extractHookName(command: string): string {
    // Remove command prefix (node, python, bash, etc.)
    const cleaned = command
      .replace(/^(node|python3?|bash|sh)\s+/, '')
      .trim();

    // Extract filename without extension
    const match = cleaned.match(/([^/\\]+?)\.[^.]+$/);
    if (match) {
      return match[1];
    }

    // Fallback: use entire command (truncated)
    return cleaned.slice(0, 30);
  }

  /**
   * Export execution data (for storage)
   *
   * @returns Serializable execution data
   */
  exportData(): Record<string, HookExecution[]> {
    return Object.fromEntries(this.executions);
  }

  /**
   * Import execution data (from storage)
   *
   * @param data - Previously exported data
   */
  importData(data: Record<string, HookExecution[]>): void {
    this.executions = new Map(Object.entries(data));
    this.log(`Imported data for ${this.executions.size} hook(s)`);
  }

  /**
   * Log helper (respects verbose config)
   */
  private log(message: string): void {
    if (this.config.verbose) {
      console.log(`[HookMonitor] ${message}`);
    }
  }
}
