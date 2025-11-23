# Implementation Specification - Orchestration Tracker Plugin

**Status:** Ready for parallel implementation by specialized agents
**Deadline:** Production-ready PR

---

## Phase 1: Core Plugin Implementation (Agent: desenvolvimento)

### Files to Implement

#### 1. `src/plugins/core/plugin-loader.ts`

**Purpose:** Load and instantiate plugins from filesystem or registry

**Functions:**
```typescript
export async function loadPlugin(pluginPath: string): Promise<VibeLogPlugin>
export async function loadPluginsFromDir(dir: string): Promise<VibeLogPlugin[]>
export async function loadPluginConfig(pluginName: string): Promise<PluginConfig>
```

**Logic:**
- Resolve plugin path (local file or node_modules)
- Dynamic import (ESM)
- Validate plugin exports
- Load config from ~/.vibe-log/config.json
- Error handling with fallbacks

---

#### 2. `src/plugins/orchestration-tracker/index.ts`

**Purpose:** Main plugin export

**Structure:**
```typescript
import type { VibeLogPlugin } from '../core/types.js';
import { AgentDiscovery } from './agent-discovery.js';
import { HookMonitor } from './hook-monitor.js';
import { SkillTracker } from './skill-tracker.js';

export const orchestrationTracker: VibeLogPlugin = {
  name: 'orchestration-tracker',
  version: '1.0.0',
  description: 'Track multi-agent orchestration workflows in Claude Code',
  author: {
    name: 'PedroGiudice',
    url: 'https://github.com/PedroGiudice'
  },

  async init(config) {
    // Initialize agent discovery
    // Initialize hook monitor
    // Initialize skill tracker
    // Setup storage
  },

  hooks: {
    SessionStart: async (session) => {
      // Discover agents, hooks, skills
      // Store in session.plugins.orchestration
    },

    UserPromptSubmit: async (session, data) => {
      // Detect agent spawns
      // Track skill invocations
    },

    SessionEnd: async (session) => {
      // Save orchestration data
      // Generate analytics
    }
  },

  commands: [
    {
      name: 'orchestration',
      description: 'View orchestration metrics',
      action: async (options) => {
        // CLI command implementation
      }
    }
  ]
};
```

---

#### 3. `src/plugins/orchestration-tracker/agent-discovery.ts`

**Purpose:** Discover agents in Claude Code project

**Interface:**
```typescript
export class AgentDiscovery {
  constructor(private config: OrchestrationConfig) {}

  async discoverAgents(projectDir: string): Promise<AgentDefinition[]> {
    // GENERIC implementation:
    // 1. Read config.agentsDir (default: .claude/agents)
    // 2. Find files matching config.agentPatterns (default: ['*.md'])
    // 3. Parse metadata (YAML frontmatter or Markdown headers)
    // 4. Return AgentDefinition[]
  }

  parseAgentMetadata(content: string): AgentMetadata {
    // Support:
    // - YAML frontmatter (---\nname: foo\n---)
    // - Markdown headers (# Agent Name)
    // - Custom markers ([AGENT: name])
  }
}

export interface AgentDefinition {
  name: string;
  path: string;
  description: string;
  capabilities: string[];
  type: 'permanent' | 'virtual';
}
```

**Requirements:**
- ✅ GENERIC (works with any agent structure)
- ✅ Configurable paths and patterns
- ✅ Multi-format parsing
- ✅ Error handling (skip invalid files)

---

#### 4. `src/plugins/orchestration-tracker/hook-monitor.ts`

**Purpose:** Monitor hook execution performance

**Interface:**
```typescript
export class HookMonitor {
  constructor(private config: OrchestrationConfig) {}

  async discoverHooks(projectDir: string): Promise<HookDefinition[]> {
    // 1. Read .claude/settings.json
    // 2. Parse hooks.* sections
    // 3. Extract hook names from commands
    // 4. Return HookDefinition[]
  }

  trackExecution(hookName: string, duration: number, success: boolean): void {
    // Store execution metrics
  }

  getStats(hookName: string): HookStats {
    // Return aggregated stats
  }
}

export interface HookDefinition {
  name: string;
  triggers: string[];
  command: string;
  description: string;
}

export interface HookStats {
  totalExecutions: number;
  avgDuration: number;
  failureRate: number;
  lastRun?: number;
}
```

---

#### 5. `src/plugins/orchestration-tracker/skill-tracker.ts`

**Purpose:** Track skill usage and effectiveness

**Interface:**
```typescript
export class SkillTracker {
  constructor(private config: OrchestrationConfig) {}

  async discoverSkills(projectDir: string): Promise<SkillDefinition[]> {
    // GENERIC implementation:
    // 1. Read config.skillsDir (default: skills/)
    // 2. Support multiple formats (SKILL.md, skill.yaml, skill.json)
    // 3. Parse triggers/keywords
    // 4. Return SkillDefinition[]
  }

  detectSkillInvocation(prompt: string): SkillInvocation | null {
    // Pattern matching against triggers
  }

  trackUsage(skillName: string, context: string, outcome: 'success' | 'failure'): void {
    // Store usage data
  }
}

export interface SkillDefinition {
  name: string;
  path: string;
  triggers: string[];
  description: string;
}

export interface SkillInvocation {
  skill: string;
  timestamp: number;
  context: string;
}
```

---

#### 6. `src/plugins/orchestration-tracker/storage.ts`

**Purpose:** Persist orchestration data

**Interface:**
```typescript
export class OrchestrationStorage {
  constructor(private baseDir: string) {
    // baseDir = ~/.vibe-log/orchestration/
  }

  async saveAgents(sessionId: string, agents: AgentData[]): Promise<void> {
    // Write to orchestration/agents/{sessionId}.json
  }

  async saveHooks(sessionId: string, hooks: HookData[]): Promise<void> {
    // Write to orchestration/hooks/{sessionId}.json
  }

  async saveSkills(sessionId: string, skills: SkillData[]): Promise<void> {
    // Write to orchestration/skills/{sessionId}.json
  }

  async loadSession(sessionId: string): Promise<OrchestrationSession> {
    // Load all data for session
  }
}

export interface OrchestrationSession {
  sessionId: string;
  agents: AgentData[];
  hooks: HookData[];
  skills: SkillData[];
  metrics: OrchestrationMetrics;
}
```

---

#### 7. `src/cli/commands/orchestration.ts`

**Purpose:** CLI command for viewing orchestration metrics

**Implementation:**
```typescript
import { Command } from 'commander';
import { OrchestrationStorage } from '../../plugins/orchestration-tracker/storage.js';

export function createOrchestrationCommand(): Command {
  const command = new Command('orchestration');

  command
    .description('View multi-agent orchestration metrics')
    .option('-s, --session <id>', 'Session ID to analyze')
    .option('--agents', 'Show agent metrics')
    .option('--hooks', 'Show hook metrics')
    .option('--skills', 'Show skill metrics')
    .action(async (options) => {
      // Implementation:
      // 1. Load orchestration data
      // 2. Format metrics (tables with ora/chalk)
      // 3. Display insights
    });

  return command;
}
```

---

## Phase 2: Test Suite (Agent: qualidade-codigo)

### Files to Implement

#### 1. `tests/unit/plugin-registry.test.ts`

**Tests:**
```typescript
describe('PluginRegistry', () => {
  it('should register plugin successfully')
  it('should reject invalid plugin name')
  it('should initialize plugin on register')
  it('should trigger hooks in parallel')
  it('should handle plugin errors gracefully')
  it('should unregister plugin and call cleanup')
})
```

---

#### 2. `tests/unit/agent-discovery.test.ts`

**Tests:**
```typescript
describe('AgentDiscovery', () => {
  it('should discover agents from .claude/agents')
  it('should parse YAML frontmatter')
  it('should parse Markdown headers')
  it('should handle custom markers')
  it('should skip invalid files')
  it('should support custom agent directories')
  it('should support multiple patterns')
})
```

---

#### 3. `tests/unit/hook-monitor.test.ts`

**Tests:**
```typescript
describe('HookMonitor', () => {
  it('should parse hooks from settings.json')
  it('should extract hook names from commands')
  it('should track execution metrics')
  it('should calculate statistics correctly')
  it('should handle missing settings.json')
})
```

---

#### 4. `tests/unit/skill-tracker.test.ts`

**Tests:**
```typescript
describe('SkillTracker', () => {
  it('should discover skills from skills/')
  it('should support SKILL.md format')
  it('should support skill.yaml format')
  it('should support skill.json format')
  it('should detect skill invocations from prompts')
  it('should track usage statistics')
})
```

---

#### 5. `tests/integration/orchestration-full-cycle.test.ts`

**Tests:**
```typescript
describe('Orchestration Full Cycle', () => {
  it('should complete full session lifecycle')
  it('should discover all resources correctly')
  it('should save data to correct locations')
  it('should handle concurrent sessions')
  it('should cleanup on session end')
})
```

---

#### 6. `tests/integration/performance.test.ts`

**Benchmarks:**
```typescript
describe('Performance', () => {
  it('should complete agent discovery in <50ms', async () => {
    const start = Date.now();
    await agentDiscovery.discoverAgents(projectDir);
    expect(Date.now() - start).toBeLessThan(50);
  })

  it('should complete hook parsing in <20ms')
  it('should complete full plugin cycle in <100ms')
})
```

**Target:**
- ✅ >95% code coverage
- ✅ All tests passing
- ✅ Performance benchmarks met

---

## Phase 3: Documentation (Agent: documentacao)

### Files to Implement

#### 1. `docs/plugins/orchestration-tracker.md`

**Sections:**
```markdown
# Orchestration Tracker Plugin

## Overview
[What it does, why it's useful]

## Installation
[How to enable the plugin]

## Configuration
[All config options with examples]

## Data Models
[JSON schemas for agents, hooks, skills]

## CLI Commands
[How to use npx vibe-log-cli orchestration]

## Examples
[Real-world usage scenarios]

## Troubleshooting
[Common issues and solutions]

## API Reference
[TypeScript interfaces and types]
```

---

#### 2. `examples/basic-usage.ts`

**Code example:**
```typescript
// Example: Enable orchestration tracking

import { pluginRegistry } from 'vibe-log-cli/plugins/core';
import { orchestrationTracker } from 'vibe-log-cli/plugins/orchestration-tracker';

// Register plugin
await pluginRegistry.register(orchestrationTracker, {
  enabled: true,
  settings: {
    agentsDir: '.claude/agents',
    skillsDir: 'skills',
    agentPatterns: ['*.md'],
    skillFormats: ['SKILL.md', 'skill.yaml']
  }
});

// View metrics
npx vibe-log-cli orchestration --agents
```

---

#### 3. `PR_DESCRIPTION.md`

**Full PR description ready to paste on GitHub:**
```markdown
## Multi-Agent Orchestration Tracking Plugin

[Complete PR description following the template from earlier]

## Screenshots
[Placeholder for screenshots - to be added]

## Checklist
- [x] Implementation complete
- [x] Tests passing (>95% coverage)
- [x] Documentation complete
- [x] Performance benchmarks met
- [x] Backward compatible
- [x] CI passing
```

---

## Success Criteria

✅ **Code Quality:**
- TypeScript strict mode passing
- ESLint passing (no warnings)
- 100% type coverage
- No any types (except where necessary)

✅ **Testing:**
- >95% code coverage
- All unit tests passing
- Integration tests passing
- Performance benchmarks met (<50ms overhead)

✅ **Documentation:**
- Complete plugin guide
- API reference
- Usage examples
- Migration guide

✅ **Backward Compatibility:**
- Zero breaking changes
- Existing vibe-log features unaffected
- Opt-in only

---

## Timeline

**Parallel execution** (agents working simultaneously):
- desenvolvimento: 2-3h (core implementation)
- qualidade-codigo: 1-2h (tests)
- documentacao: 1h (docs)

**Total:** ~3h wall time (if parallelized)

---

## Deliverables

After completion, you should have:

```
vibe-log-plugin-implementation/
├── src/
│   ├── plugins/
│   │   ├── core/
│   │   │   ├── types.ts ✅
│   │   │   ├── plugin-registry.ts ✅
│   │   │   └── plugin-loader.ts [TODO]
│   │   └── orchestration-tracker/
│   │       ├── index.ts [TODO]
│   │       ├── agent-discovery.ts [TODO]
│   │       ├── hook-monitor.ts [TODO]
│   │       ├── skill-tracker.ts [TODO]
│   │       └── storage.ts [TODO]
│   └── cli/
│       └── commands/
│           └── orchestration.ts [TODO]
├── tests/
│   ├── unit/ [TODO - 5 files]
│   ├── integration/ [TODO - 2 files]
│   └── fixtures/ [TODO - test data]
├── docs/
│   └── plugins/
│       └── orchestration-tracker.md [TODO]
├── examples/
│   └── basic-usage.ts [TODO]
└── PR_DESCRIPTION.md [TODO]
```

**Ready to copy to vibe-log-cli fork and submit PR!**
