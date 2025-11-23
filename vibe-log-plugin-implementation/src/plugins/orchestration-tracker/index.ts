/**
 * Orchestration Tracker Plugin - Main Export
 *
 * Tracks multi-agent orchestration workflows in Claude Code projects
 */

import type { VibeLogPlugin, PluginConfig } from '../core/types.js';
import { AgentDiscovery } from './agent-discovery.js';
import { HookMonitor } from './hook-monitor.js';
import { SkillTracker } from './skill-tracker.js';
import { OrchestrationStorage } from './storage.js';
import type {
  OrchestrationConfig,
  AgentData,
  HookData,
  SkillData,
} from './types.js';

/**
 * Plugin state (singleton across hooks)
 */
let agentDiscovery: AgentDiscovery;
let hookMonitor: HookMonitor;
let skillTracker: SkillTracker;
let storage: OrchestrationStorage;
let config: OrchestrationConfig;

/**
 * Current session data (in-memory cache)
 */
const sessionCache = new Map<
  string,
  {
    agents: AgentData[];
    hooks: HookData[];
    skills: SkillData[];
  }
>();

/**
 * Orchestration Tracker Plugin
 */
export const orchestrationTracker: VibeLogPlugin = {
  name: 'orchestration-tracker',
  version: '1.0.0',
  description: 'Track multi-agent orchestration workflows in Claude Code',

  author: {
    name: 'PedroGiudice',
    url: 'https://github.com/PedroGiudice',
  },

  /**
   * Initialize plugin
   */
  async init(pluginConfig: PluginConfig): Promise<void> {
    // Extract orchestration config from settings
    const settings = pluginConfig.settings || {};

    config = {
      agentsDir: (settings.agentsDir as string) || '.claude/agents',
      skillsDir: (settings.skillsDir as string) || 'skills',
      agentPatterns: (settings.agentPatterns as string[]) || ['*.md'],
      skillFormats: (settings.skillFormats as string[]) || [
        'SKILL.md',
        'skill.yaml',
        'skill.json',
      ],
      verbose: (settings.verbose as boolean) || false,
    };

    // Initialize services
    agentDiscovery = new AgentDiscovery(config);
    hookMonitor = new HookMonitor(config);
    skillTracker = new SkillTracker(config);
    storage = new OrchestrationStorage();

    // Initialize storage
    await storage.init();

    console.log('[OrchestrationTracker] Plugin initialized');
  },

  /**
   * Hook implementations
   */
  hooks: {
    /**
     * SessionStart - Discover agents, hooks, skills
     */
    SessionStart: async (session) => {
      const { sessionId, projectDir } = session;

      console.log(
        `[OrchestrationTracker] Session started: ${sessionId}`
      );

      try {
        // Discover resources in parallel
        const [agents, hooks, skills] = await Promise.all([
          agentDiscovery.discoverAgents(projectDir),
          hookMonitor.discoverHooks(projectDir),
          skillTracker.discoverSkills(projectDir),
        ]);

        // Create initial data structures
        const agentData: AgentData[] = agents.map((def) => ({
          definition: def,
          invocations: 0,
        }));

        const hookData: HookData[] = hooks.map((def) => ({
          definition: def,
          stats: {
            totalExecutions: 0,
            avgDuration: 0,
            failureRate: 0,
          },
          recentExecutions: [],
        }));

        const skillData: SkillData[] = skills.map((def) => ({
          definition: def,
          usageCount: 0,
          recentInvocations: [],
        }));

        // Cache in memory
        sessionCache.set(sessionId, {
          agents: agentData,
          hooks: hookData,
          skills: skillData,
        });

        // Store to disk
        await storage.saveAgents(sessionId, agentData);
        await storage.saveHooks(sessionId, hookData);
        await storage.saveSkills(sessionId, skillData);

        // Store in session metadata (for other plugins)
        if (!session.plugins) {
          session.plugins = {};
        }

        session.plugins.orchestration = {
          totalAgents: agents.length,
          totalHooks: hooks.length,
          totalSkills: skills.length,
        };

        console.log(
          `[OrchestrationTracker] Discovered: ${agents.length} agents, ${hooks.length} hooks, ${skills.length} skills`
        );
      } catch (error) {
        console.error(
          '[OrchestrationTracker] SessionStart error:',
          error
        );
      }
    },

    /**
     * UserPromptSubmit - Detect agent spawns and skill invocations
     */
    UserPromptSubmit: async (session, data) => {
      const { sessionId } = session;
      const prompt = data?.prompt;

      if (!prompt || typeof prompt !== 'string') {
        return;
      }

      try {
        const cached = sessionCache.get(sessionId);
        if (!cached) {
          return; // Session not initialized
        }

        // Detect skill invocation
        const skillInvocation = skillTracker.detectSkillInvocation(prompt);
        if (skillInvocation) {
          console.log(
            `[OrchestrationTracker] Skill invoked: ${skillInvocation.skill}`
          );

          // Update skill data
          const skillData = cached.skills.find(
            (s) => s.definition.name === skillInvocation.skill
          );
          if (skillData) {
            skillData.usageCount++;
            skillData.recentInvocations.push(skillInvocation);

            // Keep only last 20 invocations
            if (skillData.recentInvocations.length > 20) {
              skillData.recentInvocations.shift();
            }
          }

          // Track in skill tracker
          skillTracker.trackUsage(
            skillInvocation.skill,
            prompt,
            'success'
          );

          // Save updated data
          await storage.saveSkills(sessionId, cached.skills);
        }

        // TODO: Detect agent spawns (requires parsing prompt for agent mentions)
        // This would involve checking for patterns like:
        // - "Use agent X"
        // - "Spawn agent Y"
        // - "@agentName do something"
      } catch (error) {
        console.error(
          '[OrchestrationTracker] UserPromptSubmit error:',
          error
        );
      }
    },

    /**
     * SessionEnd - Save final orchestration data
     */
    SessionEnd: async (session) => {
      const { sessionId, startTime, projectDir } = session;

      console.log(`[OrchestrationTracker] Session ended: ${sessionId}`);

      try {
        const cached = sessionCache.get(sessionId);
        if (!cached) {
          return; // Session not initialized
        }

        // Calculate final metrics
        const metrics = storage.calculateMetrics(
          cached.agents,
          cached.hooks,
          cached.skills
        );

        // Save complete session
        await storage.saveSession({
          sessionId,
          startTime,
          endTime: Date.now(),
          projectDir,
          agents: cached.agents,
          hooks: cached.hooks,
          skills: cached.skills,
          metrics,
        });

        // Clean up cache
        sessionCache.delete(sessionId);

        console.log(
          `[OrchestrationTracker] Session saved with metrics:`,
          metrics
        );
      } catch (error) {
        console.error('[OrchestrationTracker] SessionEnd error:', error);
      }
    },
  },

  /**
   * CLI commands
   */
  commands: [
    {
      name: 'orchestration',
      description: 'View multi-agent orchestration metrics',
      options: [
        {
          flags: '-s, --session <id>',
          description: 'Session ID to analyze',
        },
        {
          flags: '--agents',
          description: 'Show agent metrics',
        },
        {
          flags: '--hooks',
          description: 'Show hook metrics',
        },
        {
          flags: '--skills',
          description: 'Show skill metrics',
        },
        {
          flags: '--latest',
          description: 'Show latest session',
          defaultValue: false,
        },
      ],
      action: async (...args: unknown[]) => {
        // Extract options (last argument)
        const options = args[args.length - 1] as Record<string, unknown>;

        try {
          // Determine session ID
          let sessionId = options.session as string | undefined;

          if (!sessionId && options.latest) {
            sessionId = (await storage.getLatestSessionId()) || undefined;
          }

          if (!sessionId) {
            console.error(
              '❌ No session specified. Use --session <id> or --latest'
            );
            return;
          }

          // Load session
          const sessionData = await storage.loadSession(sessionId);

          console.log(`\n📊 Orchestration Metrics - Session ${sessionId}\n`);

          // Show agents
          if (options.agents || !options.hooks && !options.skills) {
            console.log('👥 Agents:');
            sessionData.agents.forEach((agent) => {
              console.log(
                `   - ${agent.definition.name}: ${agent.invocations} invocations`
              );
            });
            console.log('');
          }

          // Show hooks
          if (options.hooks || !options.agents && !options.skills) {
            console.log('🪝 Hooks:');
            sessionData.hooks.forEach((hook) => {
              console.log(
                `   - ${hook.definition.name}: ${hook.stats.totalExecutions} executions (avg ${hook.stats.avgDuration}ms)`
              );
            });
            console.log('');
          }

          // Show skills
          if (options.skills || !options.agents && !options.hooks) {
            console.log('⚡ Skills:');
            sessionData.skills.forEach((skill) => {
              console.log(
                `   - ${skill.definition.name}: ${skill.usageCount} uses`
              );
            });
            console.log('');
          }

          // Show summary
          console.log('📈 Summary:');
          console.log(`   Total Agents: ${sessionData.metrics.totalAgents}`);
          console.log(`   Total Hooks: ${sessionData.metrics.totalHooks}`);
          console.log(`   Total Skills: ${sessionData.metrics.totalSkills}`);
          console.log(
            `   Agent Invocations: ${sessionData.metrics.agentInvocations}`
          );
          console.log(`   Skill Usages: ${sessionData.metrics.skillUsages}`);
          console.log(
            `   Hook Executions: ${sessionData.metrics.hookExecutions}`
          );

          if (sessionData.metrics.mostActiveAgent) {
            console.log(
              `   Most Active Agent: ${sessionData.metrics.mostActiveAgent}`
            );
          }

          if (sessionData.metrics.mostUsedSkill) {
            console.log(
              `   Most Used Skill: ${sessionData.metrics.mostUsedSkill}`
            );
          }

          console.log('');
        } catch (error) {
          console.error(
            '❌ Error loading orchestration data:',
            (error as Error).message
          );
        }
      },
    },
  ],

  /**
   * Cleanup on shutdown
   */
  cleanup: async () => {
    console.log('[OrchestrationTracker] Plugin cleanup');
    sessionCache.clear();
  },
};

// Export for external use
export { AgentDiscovery, HookMonitor, SkillTracker, OrchestrationStorage };
export * from './types.js';
