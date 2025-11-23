/**
 * Orchestration Storage - Data Persistence
 *
 * Persists orchestration data to ~/.vibe-log/orchestration/
 */

import { mkdir, writeFile, readFile, readdir, stat } from 'fs/promises';
import { join } from 'path';
import { homedir } from 'os';
import type {
  AgentData,
  HookData,
  SkillData,
  OrchestrationSession,
  OrchestrationMetrics,
} from './types.js';

/**
 * Orchestration Storage Service
 */
export class OrchestrationStorage {
  private baseDir: string;

  /**
   * @param baseDir - Base directory for storage (default: ~/.vibe-log/orchestration/)
   */
  constructor(baseDir?: string) {
    this.baseDir =
      baseDir || join(homedir(), '.vibe-log', 'orchestration');
  }

  /**
   * Initialize storage (create directories)
   */
  async init(): Promise<void> {
    await mkdir(this.baseDir, { recursive: true });
    await mkdir(join(this.baseDir, 'agents'), { recursive: true });
    await mkdir(join(this.baseDir, 'hooks'), { recursive: true });
    await mkdir(join(this.baseDir, 'skills'), { recursive: true });
    await mkdir(join(this.baseDir, 'sessions'), { recursive: true });
  }

  /**
   * Save agents data for session
   *
   * @param sessionId - Session ID
   * @param agents - Agents data
   */
  async saveAgents(sessionId: string, agents: AgentData[]): Promise<void> {
    const filePath = join(this.baseDir, 'agents', `${sessionId}.json`);
    await this.writeJSON(filePath, agents);
  }

  /**
   * Load agents data for session
   *
   * @param sessionId - Session ID
   * @returns Agents data (empty array if not found)
   */
  async loadAgents(sessionId: string): Promise<AgentData[]> {
    const filePath = join(this.baseDir, 'agents', `${sessionId}.json`);
    return await this.readJSON<AgentData[]>(filePath, []);
  }

  /**
   * Save hooks data for session
   *
   * @param sessionId - Session ID
   * @param hooks - Hooks data
   */
  async saveHooks(sessionId: string, hooks: HookData[]): Promise<void> {
    const filePath = join(this.baseDir, 'hooks', `${sessionId}.json`);
    await this.writeJSON(filePath, hooks);
  }

  /**
   * Load hooks data for session
   *
   * @param sessionId - Session ID
   * @returns Hooks data (empty array if not found)
   */
  async loadHooks(sessionId: string): Promise<HookData[]> {
    const filePath = join(this.baseDir, 'hooks', `${sessionId}.json`);
    return await this.readJSON<HookData[]>(filePath, []);
  }

  /**
   * Save skills data for session
   *
   * @param sessionId - Session ID
   * @param skills - Skills data
   */
  async saveSkills(sessionId: string, skills: SkillData[]): Promise<void> {
    const filePath = join(this.baseDir, 'skills', `${sessionId}.json`);
    await this.writeJSON(filePath, skills);
  }

  /**
   * Load skills data for session
   *
   * @param sessionId - Session ID
   * @returns Skills data (empty array if not found)
   */
  async loadSkills(sessionId: string): Promise<SkillData[]> {
    const filePath = join(this.baseDir, 'skills', `${sessionId}.json`);
    return await this.readJSON<SkillData[]>(filePath, []);
  }

  /**
   * Save complete session data
   *
   * @param session - Complete orchestration session
   */
  async saveSession(session: OrchestrationSession): Promise<void> {
    const filePath = join(
      this.baseDir,
      'sessions',
      `${session.sessionId}.json`
    );
    await this.writeJSON(filePath, session);

    // Also save individual components
    await this.saveAgents(session.sessionId, session.agents);
    await this.saveHooks(session.sessionId, session.hooks);
    await this.saveSkills(session.sessionId, session.skills);
  }

  /**
   * Load complete session data
   *
   * @param sessionId - Session ID
   * @returns Complete orchestration session
   * @throws {Error} If session not found
   */
  async loadSession(sessionId: string): Promise<OrchestrationSession> {
    const filePath = join(this.baseDir, 'sessions', `${sessionId}.json`);

    try {
      return await this.readJSON<OrchestrationSession>(filePath);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        throw new Error(`Session "${sessionId}" not found`);
      }
      throw error;
    }
  }

  /**
   * List all session IDs
   *
   * @returns Array of session IDs (sorted by date, newest first)
   */
  async listSessions(): Promise<string[]> {
    const sessionsDir = join(this.baseDir, 'sessions');

    try {
      const files = await readdir(sessionsDir);

      const sessionFiles = files.filter((f) => f.endsWith('.json'));

      // Get file stats for sorting by modification time
      const fileStats = await Promise.all(
        sessionFiles.map(async (file) => {
          const filePath = join(sessionsDir, file);
          const stats = await stat(filePath);
          return {
            sessionId: file.replace('.json', ''),
            mtime: stats.mtime.getTime(),
          };
        })
      );

      // Sort by modification time (newest first)
      fileStats.sort((a, b) => b.mtime - a.mtime);

      return fileStats.map((f) => f.sessionId);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        return [];
      }
      throw error;
    }
  }

  /**
   * Get latest session ID
   *
   * @returns Latest session ID (or null if no sessions)
   */
  async getLatestSessionId(): Promise<string | null> {
    const sessions = await this.listSessions();
    return sessions.length > 0 ? sessions[0] : null;
  }

  /**
   * Delete session data
   *
   * @param sessionId - Session ID
   */
  async deleteSession(sessionId: string): Promise<void> {
    const paths = [
      join(this.baseDir, 'sessions', `${sessionId}.json`),
      join(this.baseDir, 'agents', `${sessionId}.json`),
      join(this.baseDir, 'hooks', `${sessionId}.json`),
      join(this.baseDir, 'skills', `${sessionId}.json`),
    ];

    await Promise.all(
      paths.map(async (path) => {
        try {
          const fs = await import('fs/promises');
          await fs.unlink(path);
        } catch (error) {
          // Ignore if file doesn't exist
          if ((error as NodeJS.ErrnoException).code !== 'ENOENT') {
            throw error;
          }
        }
      })
    );
  }

  /**
   * Calculate metrics from session data
   *
   * @param agents - Agents data
   * @param hooks - Hooks data
   * @param skills - Skills data
   * @returns Aggregated metrics
   */
  calculateMetrics(
    agents: AgentData[],
    hooks: HookData[],
    skills: SkillData[]
  ): OrchestrationMetrics {
    const agentInvocations = agents.reduce(
      (sum, a) => sum + a.invocations,
      0
    );
    const skillUsages = skills.reduce((sum, s) => sum + s.usageCount, 0);
    const hookExecutions = hooks.reduce(
      (sum, h) => sum + h.stats.totalExecutions,
      0
    );
    const avgHookDuration =
      hooks.length > 0
        ? Math.round(
            hooks.reduce((sum, h) => sum + h.stats.avgDuration, 0) /
              hooks.length
          )
        : 0;

    // Find most active agent
    const mostActiveAgent =
      agents.length > 0
        ? agents.reduce((max, a) =>
            a.invocations > max.invocations ? a : max
          ).definition.name
        : undefined;

    // Find most used skill
    const mostUsedSkill =
      skills.length > 0
        ? skills.reduce((max, s) => (s.usageCount > max.usageCount ? s : max))
            .definition.name
        : undefined;

    return {
      totalAgents: agents.length,
      totalHooks: hooks.length,
      totalSkills: skills.length,
      agentInvocations,
      skillUsages,
      hookExecutions,
      avgHookDuration,
      mostActiveAgent,
      mostUsedSkill,
    };
  }

  /**
   * Write JSON to file
   */
  private async writeJSON(filePath: string, data: unknown): Promise<void> {
    const json = JSON.stringify(data, null, 2);
    await writeFile(filePath, json, 'utf-8');
  }

  /**
   * Read JSON from file
   */
  private async readJSON<T>(
    filePath: string,
    defaultValue?: T
  ): Promise<T> {
    try {
      const content = await readFile(filePath, 'utf-8');
      return JSON.parse(content) as T;
    } catch (error) {
      if (
        (error as NodeJS.ErrnoException).code === 'ENOENT' &&
        defaultValue !== undefined
      ) {
        return defaultValue;
      }
      throw error;
    }
  }

  /**
   * Get storage statistics
   *
   * @returns Storage stats (sessions count, total size)
   */
  async getStats(): Promise<{
    totalSessions: number;
    latestSession?: string;
    storageDir: string;
  }> {
    const sessions = await this.listSessions();

    return {
      totalSessions: sessions.length,
      latestSession: sessions[0],
      storageDir: this.baseDir,
    };
  }
}
