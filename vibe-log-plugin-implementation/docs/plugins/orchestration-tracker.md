# Orchestration Tracker Plugin

## Overview

The **Orchestration Tracker** plugin extends vibe-log-cli with multi-agent workflow monitoring capabilities. It provides comprehensive tracking and analytics for Claude Code projects that use:

- **Multi-agent orchestration** - Coordinate multiple specialized agents
- **Custom skills** - Extend Claude's capabilities with domain-specific skills
- **Lifecycle hooks** - Automate workflows with hook-based triggers

### Why Use This Plugin?

Modern Claude Code workflows involve complex orchestration patterns. Understanding how agents interact, which skills are most effective, and where hooks might be slowing down your workflow is critical for optimization.

**Key Benefits:**

- 📊 **Visibility** - See all agents, skills, and hooks in one place
- ⚡ **Performance** - Identify bottlenecks in orchestration workflows
- 🎯 **Optimization** - Data-driven insights for improving agent selection
- 🔍 **Debugging** - Track hook execution and failure patterns
- 📈 **Analytics** - Historical trends and usage patterns

---

## Installation

### Prerequisites

- vibe-log-cli 0.8.0+ (with plugin system support)
- Claude Code project with `.claude/` configuration
- Node.js 18+ or compatible runtime

### Enable the Plugin

```bash
# Install vibe-log-cli (if not already installed)
npm install -g vibe-log-cli

# Enable orchestration tracking
npx vibe-log-cli config set plugins.orchestration-tracker.enabled true

# Verify installation
npx vibe-log-cli orchestration --version
```

### First Run

On your next Claude Code session, the plugin will automatically:

1. Discover agents in `.claude/agents/`
2. Detect skills in `skills/` directory
3. Parse hooks from `.claude/settings.json`
4. Start tracking orchestration metrics

---

## Configuration

### Default Configuration

The plugin works out-of-the-box with standard Claude Code project structures:

```json
{
  "plugins": {
    "orchestration-tracker": {
      "enabled": true,
      "settings": {
        "agentsDir": ".claude/agents",
        "skillsDir": "skills",
        "agentPatterns": ["*.md"],
        "skillFormats": ["SKILL.md", "skill.yaml", "skill.json"],
        "detectionPatterns": {
          "agentSpawn": ["Task tool", "@agent-", "delegating to"],
          "skillInvoke": ["using skill", "invoke skill"],
          "hookExecution": ["hook success", "hook tracked"]
        }
      },
      "cache": {
        "enabled": true,
        "ttlSeconds": 300
      }
    }
  }
}
```

### Configuration Options

#### Core Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable/disable the plugin |
| `agentsDir` | string | `.claude/agents` | Directory containing agent definitions |
| `skillsDir` | string | `skills` | Directory containing skill definitions |
| `agentPatterns` | string[] | `["*.md"]` | File patterns for agent discovery |
| `skillFormats` | string[] | `["SKILL.md", "skill.yaml", "skill.json"]` | Supported skill file formats |

#### Detection Patterns

Customize how the plugin detects agent spawning, skill invocations, and hook executions:

```json
{
  "detectionPatterns": {
    "agentSpawn": [
      "Task tool",
      "@agent-",
      "delegating to",
      "spawning agent"
    ],
    "skillInvoke": [
      "using skill",
      "invoke skill",
      "skill:",
      "Skill:"
    ],
    "hookExecution": [
      "hook success",
      "hook tracked",
      "Hook executed"
    ]
  }
}
```

#### Cache Settings

Control performance caching:

```json
{
  "cache": {
    "enabled": true,
    "ttlSeconds": 300
  }
}
```

- `enabled`: Enable in-memory caching of discovered resources
- `ttlSeconds`: Cache time-to-live (300 = 5 minutes)

### Custom Configuration Example

For non-standard project structures:

```json
{
  "plugins": {
    "orchestration-tracker": {
      "enabled": true,
      "settings": {
        "agentsDir": "custom/agents",
        "skillsDir": "custom-skills",
        "agentPatterns": ["*.yaml", "*.json"],
        "skillFormats": ["skill.config.json"]
      }
    }
  }
}
```

---

## Data Models

### Agent Data Schema

```json
{
  "sessionId": "uuid-v4",
  "agents": [
    {
      "agentId": "unique-agent-id",
      "name": "desenvolvimento",
      "type": "permanent",
      "spawned_at": "2025-11-23T10:15:00.000Z",
      "completed_at": "2025-11-23T10:20:00.000Z",
      "status": "completed",
      "parent_agent": "legal-braniac",
      "task_description": "Implement authentication module",
      "metrics": {
        "execution_time_ms": 300000,
        "tokens_used": 15000,
        "success_rate": 0.95
      }
    }
  ]
}
```

#### Agent Fields

- `agentId` (string): Unique identifier for agent instance
- `name` (string): Agent name (from definition file)
- `type` (enum): `permanent` or `virtual`
  - **permanent**: Defined in `.claude/agents/`
  - **virtual**: Created on-demand by orchestrator
- `spawned_at` (ISO 8601): Agent creation timestamp
- `completed_at` (ISO 8601, optional): Agent completion timestamp
- `status` (enum): `active`, `completed`, `failed`
- `parent_agent` (string, optional): Parent orchestrator name
- `task_description` (string): Task assigned to agent
- `metrics` (object): Performance metrics

### Hook Data Schema

```json
{
  "sessionId": "uuid-v4",
  "hooks": {
    "legal-braniac-loader": {
      "trigger": "SessionStart",
      "executions": [
        {
          "timestamp": "2025-11-23T10:00:00.000Z",
          "duration_ms": 150,
          "success": true,
          "output_summary": "6 agents, 34 skills discovered"
        }
      ],
      "stats": {
        "total_executions": 1,
        "avg_duration_ms": 150,
        "failure_rate": 0.0
      }
    }
  }
}
```

#### Hook Fields

- `trigger` (string): Hook trigger type (SessionStart, UserPromptSubmit, etc.)
- `executions` (array): Individual execution records
- `stats` (object): Aggregated statistics

### Skill Data Schema

```json
{
  "sessionId": "uuid-v4",
  "skills": {
    "code-execution": {
      "invocations": [
        {
          "timestamp": "2025-11-23T10:30:00.000Z",
          "agent": "desenvolvimento",
          "context": "Running pytest",
          "outcome": "success"
        }
      ],
      "stats": {
        "total_uses": 15,
        "success_rate": 0.93,
        "avg_duration_ms": 2000
      }
    }
  }
}
```

#### Skill Fields

- `invocations` (array): Individual skill usage records
- `stats` (object): Aggregated usage statistics
- `outcome` (enum): `success`, `failure`, `partial`

### Orchestration Metrics Schema

```json
{
  "sessionId": "uuid-v4",
  "orchestration": {
    "total_agents_spawned": 7,
    "parallel_execution_count": 3,
    "sequential_execution_count": 4,
    "avg_agent_execution_time_ms": 180000,
    "orchestrator_overhead_ms": 5000,
    "efficiency_score": 0.85,
    "bottleneck_agents": ["qualidade-codigo"],
    "recommendations": [
      "Consider parallelizing qualidade-codigo and documentacao tasks"
    ]
  }
}
```

---

## CLI Commands

### `orchestration` - View Orchestration Metrics

Display comprehensive metrics for multi-agent workflows.

#### Basic Usage

```bash
# Show all metrics for current session
npx vibe-log-cli orchestration

# Show metrics for specific session
npx vibe-log-cli orchestration --session abc-123-def

# Show only agent metrics
npx vibe-log-cli orchestration --agents

# Show only hook metrics
npx vibe-log-cli orchestration --hooks

# Show only skill metrics
npx vibe-log-cli orchestration --skills
```

#### Options

| Flag | Short | Description |
|------|-------|-------------|
| `--session <id>` | `-s` | Session ID to analyze |
| `--agents` | `-a` | Show agent metrics only |
| `--hooks` | `-h` | Show hook metrics only |
| `--skills` | `-k` | Show skill metrics only |
| `--format <type>` | `-f` | Output format: `table`, `json`, `csv` |
| `--export <file>` | `-e` | Export to file |

#### Output Examples

**Agent Metrics:**

```
╔══════════════════════════════════════════════════════════════╗
║                     AGENT METRICS                            ║
╠══════════════════════════════════════════════════════════════╣
║ Agent              │ Type      │ Invocations │ Avg Time      ║
╠══════════════════════════════════════════════════════════════╣
║ desenvolvimento    │ Permanent │ 12          │ 3m 45s        ║
║ qualidade-codigo   │ Permanent │ 8           │ 5m 12s        ║
║ documentacao       │ Virtual   │ 3           │ 2m 30s        ║
║ frontend-expert    │ Virtual   │ 2           │ 4m 15s        ║
╚══════════════════════════════════════════════════════════════╝

Bottleneck: qualidade-codigo (longest avg execution time)
Recommendation: Consider parallel testing strategies
```

**Hook Metrics:**

```
╔══════════════════════════════════════════════════════════════╗
║                     HOOK METRICS                             ║
╠══════════════════════════════════════════════════════════════╣
║ Hook                    │ Executions │ Avg Duration │ Failures ║
╠══════════════════════════════════════════════════════════════╣
║ legal-braniac-loader    │ 1          │ 150ms        │ 0        ║
║ vibe-analyze-prompt     │ 15         │ 45ms         │ 0        ║
║ context-collector       │ 15         │ 120ms        │ 1 (6.7%) ║
║ improve-prompt          │ 8          │ 80ms         │ 0        ║
╚══════════════════════════════════════════════════════════════╝

Warning: context-collector has 6.7% failure rate
```

**Skill Metrics:**

```
╔══════════════════════════════════════════════════════════════╗
║                     SKILL METRICS                            ║
╠══════════════════════════════════════════════════════════════╣
║ Skill              │ Uses │ Success Rate │ Avg Duration       ║
╠══════════════════════════════════════════════════════════════╣
║ code-execution     │ 25   │ 96%          │ 1.2s               ║
║ git                │ 18   │ 100%         │ 0.8s               ║
║ docx               │ 12   │ 92%          │ 2.5s               ║
║ deep-parser        │ 8    │ 88%          │ 3.1s               ║
╚══════════════════════════════════════════════════════════════╝

Most used: code-execution (25 invocations)
Least reliable: deep-parser (88% success rate)
```

---

## Real-World Examples

### Example 1: Multi-Agent Web Development Workflow

**Scenario:** Building a full-stack web application with separate agents for frontend, backend, and testing.

**Session Data:**

```json
{
  "agents": [
    {
      "name": "frontend-expert",
      "type": "virtual",
      "task_description": "Build React components with TypeScript",
      "metrics": {
        "execution_time_ms": 240000,
        "tokens_used": 12000
      }
    },
    {
      "name": "backend-expert",
      "type": "virtual",
      "task_description": "Implement REST API with Express",
      "metrics": {
        "execution_time_ms": 180000,
        "tokens_used": 9000
      }
    },
    {
      "name": "qualidade-codigo",
      "type": "permanent",
      "task_description": "Run integration tests",
      "metrics": {
        "execution_time_ms": 120000,
        "tokens_used": 6000
      }
    }
  ]
}
```

**Insights:**

- Frontend work took longest (4 minutes)
- Backend was most efficient (3 minutes)
- Testing was quick (2 minutes)
- **Recommendation:** Consider parallelizing frontend and backend development

### Example 2: Legal Document Processing Pipeline

**Scenario:** Processing legal documents with specialized agents for OCR, parsing, and analysis.

**Skills Used:**

```json
{
  "skills": {
    "ocr-pro": {
      "total_uses": 45,
      "success_rate": 0.93,
      "avg_duration_ms": 3500
    },
    "deep-parser": {
      "total_uses": 45,
      "success_rate": 0.89,
      "avg_duration_ms": 2200
    },
    "legal-lens": {
      "total_uses": 38,
      "success_rate": 0.95,
      "avg_duration_ms": 1800
    }
  }
}
```

**Insights:**

- OCR is bottleneck (3.5s average)
- Deep-parser has lowest success rate (89%)
- Legal-lens is fastest and most reliable
- **Recommendation:** Pre-process with OCR in batch, optimize deep-parser error handling

### Example 3: Hook Performance Debugging

**Scenario:** Identifying slow hooks affecting session startup time.

**Hook Metrics:**

```json
{
  "hooks": {
    "session-context-hybrid": {
      "avg_duration_ms": 450,
      "failure_rate": 0.0
    },
    "legal-braniac-loader": {
      "avg_duration_ms": 150,
      "failure_rate": 0.0
    },
    "vibe-analyze-prompt": {
      "avg_duration_ms": 45,
      "failure_rate": 0.0
    }
  }
}
```

**Insights:**

- session-context-hybrid is slowest (450ms)
- Total startup overhead: ~645ms
- All hooks reliable (0% failure)
- **Recommendation:** Enable caching for session-context-hybrid

---

## Troubleshooting

### Plugin Not Loading

**Symptom:** No orchestration data collected

**Causes & Solutions:**

1. **Plugin disabled in config**
   ```bash
   # Check config
   npx vibe-log-cli config get plugins.orchestration-tracker.enabled

   # Enable if false
   npx vibe-log-cli config set plugins.orchestration-tracker.enabled true
   ```

2. **Incompatible vibe-log version**
   ```bash
   # Check version
   npx vibe-log-cli --version

   # Should be 0.8.0+
   # Upgrade if needed
   npm update -g vibe-log-cli
   ```

3. **Plugin initialization failed**
   ```bash
   # Check logs
   cat ~/.vibe-log/logs/plugin-errors.log
   ```

### No Agents Discovered

**Symptom:** `orchestration --agents` shows no agents

**Causes & Solutions:**

1. **Incorrect agentsDir path**
   ```bash
   # Verify directory exists
   ls -la .claude/agents/

   # Update config if different location
   npx vibe-log-cli config set plugins.orchestration-tracker.settings.agentsDir "custom/path"
   ```

2. **Agent files don't match patterns**
   ```bash
   # Check patterns
   npx vibe-log-cli config get plugins.orchestration-tracker.settings.agentPatterns

   # Add custom patterns (e.g., for .yaml files)
   npx vibe-log-cli config set plugins.orchestration-tracker.settings.agentPatterns '["*.md", "*.yaml"]'
   ```

3. **Invalid agent file format**
   ```bash
   # Test agent parsing manually
   npx vibe-log-cli orchestration validate-agent .claude/agents/my-agent.md
   ```

### Skills Not Tracked

**Symptom:** `orchestration --skills` shows no skills

**Causes & Solutions:**

1. **Missing SKILL.md files**
   ```bash
   # Verify each skill has definition file
   find skills/ -name "SKILL.md"

   # Skills without SKILL.md won't be tracked
   ```

2. **Incorrect skillsDir**
   ```bash
   # Check config
   npx vibe-log-cli config get plugins.orchestration-tracker.settings.skillsDir

   # Update if needed
   npx vibe-log-cli config set plugins.orchestration-tracker.settings.skillsDir "custom-skills"
   ```

### Hook Execution Not Monitored

**Symptom:** `orchestration --hooks` shows empty results

**Causes & Solutions:**

1. **Hooks not in settings.json**
   ```bash
   # Verify hooks configuration
   cat .claude/settings.json | jq '.hooks'

   # Plugin reads hooks from settings.json
   ```

2. **Hook execution not detected**
   ```bash
   # Check detection patterns
   npx vibe-log-cli config get plugins.orchestration-tracker.settings.detectionPatterns.hookExecution

   # Add custom patterns for your hook output format
   ```

### Performance Issues

**Symptom:** Slow session startup or high CPU usage

**Solutions:**

1. **Enable caching**
   ```json
   {
     "cache": {
       "enabled": true,
       "ttlSeconds": 600
     }
   }
   ```

2. **Reduce discovery scope**
   ```json
   {
     "settings": {
       "agentPatterns": ["legal-*.md"],
       "skillFormats": ["SKILL.md"]
     }
   }
   ```

3. **Disable plugin temporarily**
   ```bash
   npx vibe-log-cli config set plugins.orchestration-tracker.enabled false
   ```

---

## API Reference

### TypeScript Interfaces

#### OrchestrationConfig

```typescript
interface OrchestrationConfig {
  agentsDir: string;
  skillsDir: string;
  agentPatterns: string[];
  skillFormats: string[];
  detectionPatterns: {
    agentSpawn: string[];
    skillInvoke: string[];
    hookExecution: string[];
  };
}
```

#### AgentDefinition

```typescript
interface AgentDefinition {
  name: string;
  path: string;
  description: string;
  capabilities: string[];
  type: 'permanent' | 'virtual';
}
```

#### AgentMetadata

```typescript
interface AgentMetadata {
  name: string;
  description: string;
  capabilities?: string[];
  triggers?: string[];
  dependencies?: string[];
}
```

#### HookDefinition

```typescript
interface HookDefinition {
  name: string;
  triggers: string[];
  command: string;
  description: string;
}
```

#### HookStats

```typescript
interface HookStats {
  totalExecutions: number;
  avgDuration: number;
  failureRate: number;
  lastRun?: number;
}
```

#### SkillDefinition

```typescript
interface SkillDefinition {
  name: string;
  path: string;
  triggers: string[];
  description: string;
}
```

#### SkillInvocation

```typescript
interface SkillInvocation {
  skill: string;
  timestamp: number;
  context: string;
  agent?: string;
  outcome: 'success' | 'failure' | 'partial';
}
```

#### OrchestrationSession

```typescript
interface OrchestrationSession {
  sessionId: string;
  agents: AgentData[];
  hooks: HookData[];
  skills: SkillData[];
  metrics: OrchestrationMetrics;
}
```

#### OrchestrationMetrics

```typescript
interface OrchestrationMetrics {
  total_agents_spawned: number;
  parallel_execution_count: number;
  sequential_execution_count: number;
  avg_agent_execution_time_ms: number;
  orchestrator_overhead_ms: number;
  efficiency_score: number;
  bottleneck_agents: string[];
  recommendations: string[];
}
```

### Plugin Methods

#### AgentDiscovery

```typescript
class AgentDiscovery {
  constructor(config: OrchestrationConfig);

  async discoverAgents(projectDir: string): Promise<AgentDefinition[]>;
  parseAgentMetadata(content: string): AgentMetadata;
}
```

#### HookMonitor

```typescript
class HookMonitor {
  constructor(config: OrchestrationConfig);

  async discoverHooks(projectDir: string): Promise<HookDefinition[]>;
  trackExecution(hookName: string, duration: number, success: boolean): void;
  getStats(hookName: string): HookStats;
}
```

#### SkillTracker

```typescript
class SkillTracker {
  constructor(config: OrchestrationConfig);

  async discoverSkills(projectDir: string): Promise<SkillDefinition[]>;
  detectSkillInvocation(prompt: string): SkillInvocation | null;
  trackUsage(skillName: string, context: string, outcome: 'success' | 'failure'): void;
}
```

#### OrchestrationStorage

```typescript
class OrchestrationStorage {
  constructor(baseDir: string);

  async saveAgents(sessionId: string, agents: AgentData[]): Promise<void>;
  async saveHooks(sessionId: string, hooks: HookData[]): Promise<void>;
  async saveSkills(sessionId: string, skills: SkillData[]): Promise<void>;
  async loadSession(sessionId: string): Promise<OrchestrationSession>;
}
```

---

## Storage Locations

All orchestration data is stored locally in `~/.vibe-log/orchestration/`:

```
~/.vibe-log/
├── orchestration/
│   ├── agents/
│   │   └── {sessionId}.json
│   ├── hooks/
│   │   └── {sessionId}.json
│   ├── skills/
│   │   └── {sessionId}.json
│   └── cache/
│       └── discovery-cache.json
├── config.json
└── logs/
    └── plugin-errors.log
```

**Privacy Note:** Only metadata is stored (agent names, execution times, etc.). No code or prompt content is saved.

---

## Performance Considerations

### Caching Strategy

The plugin uses intelligent caching to minimize overhead:

- **Discovery Cache:** Agent/skill/hook discovery results cached for 5 minutes (default)
- **Session Cache:** Current session data cached in memory
- **Lazy Loading:** Resources loaded only when needed

### Benchmarks

Target performance (measured on standard laptop):

- Agent discovery: <50ms (for 20 agents)
- Hook parsing: <20ms (from settings.json)
- Skill discovery: <100ms (for 50 skills)
- Full plugin cycle: <150ms total

**Actual overhead per session:** ~100-150ms on SessionStart, <10ms on other hooks

### Optimization Tips

1. **Reduce patterns:** Only match files you actually use
2. **Enable caching:** Set ttlSeconds to 600+ for stable projects
3. **Limit discovery:** Use specific patterns instead of wildcards
4. **Monitor logs:** Check for repeated discovery calls

---

## Contributing

We welcome contributions to improve the orchestration-tracker plugin!

### Development Setup

```bash
# Clone vibe-log-cli
git clone https://github.com/vibe-log/vibe-log-cli.git
cd vibe-log-cli

# Install dependencies
npm install

# Link plugin for development
cd src/plugins/orchestration-tracker
npm link

# Run tests
npm test
```

### Adding New Detection Patterns

To support custom orchestration frameworks:

```typescript
// src/plugins/orchestration-tracker/patterns.ts
export const PATTERNS = {
  agentSpawn: [
    // Existing patterns
    'Task tool',
    '@agent-',

    // Add your patterns
    'CrewAI spawn',
    'LangGraph invoke'
  ]
};
```

### Submitting Changes

1. Fork vibe-log-cli
2. Create feature branch
3. Add tests for new functionality
4. Submit PR with clear description

---

## License

MIT License (same as vibe-log-cli)

---

## Support

- **Issues:** [GitHub Issues](https://github.com/vibe-log/vibe-log-cli/issues)
- **Discussions:** [GitHub Discussions](https://github.com/vibe-log/vibe-log-cli/discussions)
- **Documentation:** [vibe-log.dev](https://vibe-log.dev/)

---

**Version:** 1.0.0
**Last Updated:** 2025-11-23
**Maintainer:** PedroGiudice (@PedroGiudice)
