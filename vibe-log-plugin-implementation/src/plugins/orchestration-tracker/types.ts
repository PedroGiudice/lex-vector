/**
 * Orchestration Tracker - Type Definitions
 *
 * Domain-specific types for multi-agent orchestration tracking
 */

/**
 * Plugin configuration
 */
export interface OrchestrationConfig {
  /** Directory containing agent definitions */
  agentsDir: string;

  /** Directory containing skills */
  skillsDir: string;

  /** Patterns to match agent files (e.g., ['*.md', '*.yaml']) */
  agentPatterns: string[];

  /** Formats to support for skill files */
  skillFormats: string[];

  /** Enable verbose logging */
  verbose?: boolean;
}

/**
 * Agent definition
 */
export interface AgentDefinition {
  /** Agent name */
  name: string;

  /** File path */
  path: string;

  /** Description */
  description: string;

  /** Capabilities/skills */
  capabilities: string[];

  /** Agent type */
  type: 'permanent' | 'virtual';

  /** Optional metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Agent metadata (parsed from files)
 */
export interface AgentMetadata {
  name?: string;
  description?: string;
  capabilities?: string[];
  type?: 'permanent' | 'virtual';
  [key: string]: unknown;
}

/**
 * Hook definition
 */
export interface HookDefinition {
  /** Hook name */
  name: string;

  /** Triggers (events that activate hook) */
  triggers: string[];

  /** Command to execute */
  command: string;

  /** Description */
  description: string;
}

/**
 * Hook execution statistics
 */
export interface HookStats {
  /** Total executions */
  totalExecutions: number;

  /** Average duration (ms) */
  avgDuration: number;

  /** Failure rate (0-1) */
  failureRate: number;

  /** Last run timestamp */
  lastRun?: number;

  /** Min duration */
  minDuration?: number;

  /** Max duration */
  maxDuration?: number;
}

/**
 * Skill definition
 */
export interface SkillDefinition {
  /** Skill name */
  name: string;

  /** File path */
  path: string;

  /** Triggers/keywords */
  triggers: string[];

  /** Description */
  description: string;

  /** Optional metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Skill invocation record
 */
export interface SkillInvocation {
  /** Skill name */
  skill: string;

  /** Timestamp */
  timestamp: number;

  /** Context/prompt that triggered */
  context: string;

  /** Outcome */
  outcome?: 'success' | 'failure';
}

/**
 * Agent runtime data
 */
export interface AgentData {
  /** Agent definition */
  definition: AgentDefinition;

  /** Number of invocations */
  invocations: number;

  /** Last invocation timestamp */
  lastInvoked?: number;

  /** Success rate (0-1) */
  successRate?: number;
}

/**
 * Hook runtime data
 */
export interface HookData {
  /** Hook definition */
  definition: HookDefinition;

  /** Execution statistics */
  stats: HookStats;

  /** Recent executions */
  recentExecutions: Array<{
    timestamp: number;
    duration: number;
    success: boolean;
    error?: string;
  }>;
}

/**
 * Skill runtime data
 */
export interface SkillData {
  /** Skill definition */
  definition: SkillDefinition;

  /** Usage count */
  usageCount: number;

  /** Recent invocations */
  recentInvocations: SkillInvocation[];

  /** Effectiveness score (0-1) */
  effectiveness?: number;
}

/**
 * Orchestration metrics
 */
export interface OrchestrationMetrics {
  /** Total agents discovered */
  totalAgents: number;

  /** Total hooks active */
  totalHooks: number;

  /** Total skills available */
  totalSkills: number;

  /** Agent invocation count */
  agentInvocations: number;

  /** Skill usage count */
  skillUsages: number;

  /** Hook execution count */
  hookExecutions: number;

  /** Average hook duration */
  avgHookDuration: number;

  /** Most active agent */
  mostActiveAgent?: string;

  /** Most used skill */
  mostUsedSkill?: string;
}

/**
 * Complete orchestration session
 */
export interface OrchestrationSession {
  /** Session ID */
  sessionId: string;

  /** Session start time */
  startTime: number;

  /** Session end time */
  endTime?: number;

  /** Project directory */
  projectDir: string;

  /** Agents data */
  agents: AgentData[];

  /** Hooks data */
  hooks: HookData[];

  /** Skills data */
  skills: SkillData[];

  /** Aggregated metrics */
  metrics: OrchestrationMetrics;
}
