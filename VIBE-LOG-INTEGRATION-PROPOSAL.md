# Vibe-Log-CLI Integration Proposal: Multi-Agent Orchestration Tracking

**Proposal Type:** Feature Enhancement PR
**Target Project:** [vibe-log-cli](https://github.com/vibe-log/vibe-log-cli)
**Proposer:** PedroGiudice (Claude-Code-Projetos)
**Date:** 2025-11-23
**Status:** Draft for Review

---

## Executive Summary

This proposal introduces **Multi-Agent Orchestration Tracking** capabilities to vibe-log-cli, enabling users to monitor and analyze complex Claude Code workflows involving:

- **Agent Spawning & Lifecycle**: Track when subagents are created, their execution status, and completion
- **Hook Execution Monitoring**: Real-time visibility into which hooks are running and their performance
- **Skill Usage Analytics**: Understand which skills are most utilized and when
- **Orchestrator Metrics**: Comprehensive metrics for multi-agent coordination patterns

**Value Proposition**: Extends vibe-log's session analysis to capture the full complexity of modern Claude Code workflows where users orchestrate multiple specialized agents, not just single-session interactions.

---

## Table of Contents

1. [Investigation Summary](#1-investigation-summary)
2. [Gap Analysis](#2-gap-analysis)
3. [Proposed Architecture](#3-proposed-architecture)
4. [Feature Specifications](#4-feature-specifications)
5. [Generalization Strategy](#5-generalization-strategy)
6. [Implementation Roadmap](#6-implementation-roadmap)
7. [Integration Points](#7-integration-points)
8. [Backward Compatibility](#8-backward-compatibility)
9. [Success Metrics](#9-success-metrics)
10. [Appendices](#10-appendices)

---

## 1. Investigation Summary

### 1.1 Local Repository Analysis

**Repository:** Claude-Code-Projetos
**Key Findings:**

#### Statusline Implementations Discovered

1. **hybrid-statusline.js** (Primary Implementation)
   - 3-line multiline statusline
   - Line 1: ccstatusline integration (model, git, tokens)
   - Line 2: Legal-Braniac tracking (agents, skills, hooks)
   - Line 3: Technical status (venv, cache)
   - Cache system: 10.8x speedup (3.4s → 0.05s)
   - Blinking indicators for real-time activity (<5s)

2. **legal-braniac-loader.js** (Core Tracking Engine)
   - Auto-discovery system for agents/skills/hooks
   - VirtualAgentFactory: Creates temporary agents on-demand
   - Gap detection: Identifies missing capabilities
   - Session persistence: 24h TTL for virtual agents
   - Promotion system: Virtual → Permanent after 5+ successful invocations

3. **Multi-Agent Orchestration Features**
   - **DecisionEngine 2.0**: Multi-dimensional complexity analysis (technical, legal, temporal, interdependency)
   - **OrchestrationEngine 2.0**: Dependency graphs, parallel execution, deadlock detection
   - **DelegationEngine 2.0**: Agent ranking (performance 40%, capability match 30%, load 20%, keywords 10%)
   - **Retry Logic**: Exponential backoff (1s → 2s → 4s)

#### Tracking Capabilities

**Currently Tracked:**
- 19 permanent agents + N virtual agents
- 54 skills (with SKILL.md validation)
- 11 hooks (parsed from settings.json)
- Session metadata (sessionId, startTime, lastUpdate)
- Agent invocation counts and success rates
- Hook execution timestamps and frequency

**Data Storage:**
- `.claude/hooks/legal-braniac-session.json` (session state)
- `.claude/statusline/virtual-agents-state.json` (virtual agents persistence)
- `.claude/statusline/hooks-status.json` (last-run timestamps)

### 1.2 Vibe-Log-CLI Analysis

**Sources:**
- [GitHub Repository](https://github.com/vibe-log/vibe-log-cli)
- [Official Documentation](https://vibe-log.dev/)
- [npm Package](https://libraries.io/npm/vibe-log-cli)

#### Current Architecture

**Core Components:**

1. **Local Analysis Engine**
   - Launches Claude with instructions
   - Parallel sub-agents for session analysis
   - Aggregates results into HTML reports

2. **Coach Statusline**
   - **NOT a traditional statusline** - it's a prompt analysis system
   - Intercepts prompts via `UserPromptSubmit` hook
   - Analyzes prompt quality using Claude SDK
   - Scores prompts (0-100)
   - Saves to `~/.vibe-log/analyzed-prompts/{sessionId}.json`
   - Displays feedback in statusline (via separate statusline command)

3. **Cloud Sync (Optional)**
   - Sanitization layer: removes code, credentials, paths
   - Preserves conversation flow for pattern analysis
   - Smart truncation for 10,000+ message sessions

#### Coach Personalities

- **Gordon**: Tough love, business-focused ("Ship by FRIDAY or you're fired!")
- **Vibe-Log**: Supportive senior developer
- **Custom**: User-defined personality

#### Extension Points Identified

**Hooks:**
- `SessionStart`: Syncs previous sessions on startup
- `UserPromptSubmit`: Analyzes prompt quality
- `PreCompact`: Syncs full session before context compression

**Data Format:**
```json
{
  "score": 0-100,
  "quality": "excellent|good|fair|poor",
  "suggestion": "Gordon's feedback",
  "actionableSteps": "Specific improvements",
  "contextualEmoji": "🎯",
  "timestamp": "ISO 8601",
  "sessionId": "uuid",
  "originalPrompt": "user's prompt"
}
```

**Storage Location:** `~/.vibe-log/`

---

## 2. Gap Analysis

### 2.1 What Vibe-Log Currently Lacks

| Capability | Vibe-Log Status | Our Implementation | User Impact |
|------------|-----------------|-------------------|-------------|
| **Multi-Agent Tracking** | ❌ Not tracked | ✅ Full lifecycle tracking | Cannot see subagent orchestration |
| **Hook Monitoring** | ❌ Only prompt analysis hook | ✅ 11+ hooks with execution logs | No visibility into automation |
| **Skill Usage Analytics** | ❌ Not tracked | ✅ 54 skills with triggers | Cannot optimize skill usage |
| **Orchestrator Metrics** | ❌ No orchestration concept | ✅ Complex orchestration engine | No multi-agent workflow insights |
| **Real-time Activity Indicators** | ❌ Static scores | ✅ Blinking indicators (<5s) | No awareness of current activity |
| **Virtual Agent System** | ❌ Not applicable | ✅ Auto-creation + promotion | Cannot handle gaps dynamically |

### 2.2 User Pain Points (Current Vibe-Log Users)

**Scenario 1: Complex Multi-Agent Workflows**
```
User uses Claude Code with 5+ specialized agents working in parallel
→ Vibe-Log only sees main session prompts
→ No visibility into which agents are active
→ Cannot optimize agent selection
```

**Scenario 2: Hook-Heavy Projects**
```
User has 10+ hooks for validations, context injection, monitoring
→ Vibe-Log analyzes prompts but ignores hook activity
→ No way to debug hook failures
→ Cannot see hook performance impact
```

**Scenario 3: Skill-Intensive Development**
```
User leverages 30+ skills across project
→ Vibe-Log doesn't track skill invocations
→ Cannot identify underutilized skills
→ No skill recommendation system
```

### 2.3 Strategic Fit with Vibe-Log Vision

**Vibe-Log's Mission:** "Understand Your AI Coding Patterns"

**Our Contribution Aligns With:**
- ✅ **Pattern Recognition**: Multi-agent patterns are emerging coding practice
- ✅ **Productivity Insights**: Orchestration efficiency = productivity
- ✅ **Local-First Philosophy**: All our tracking is local (matches vibe-log)
- ✅ **Privacy-Preserving**: No code in logs, only metadata
- ✅ **Actionable Feedback**: "Use agent X instead of Y for 2x speedup"

---

## 3. Proposed Architecture

### 3.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│              VIBE-LOG-CLI (Enhanced)                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  EXISTING: Prompt Analysis (Coach)                   │   │
│  │  - Quality scoring                                    │   │
│  │  - Personality feedback                               │   │
│  │  - Actionable steps                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  NEW: Multi-Agent Orchestration Tracker              │   │
│  │  ┌────────────────┬───────────────┬────────────────┐ │   │
│  │  │ Agent Tracker  │ Hook Monitor  │ Skill Tracker  │ │   │
│  │  │ - Lifecycle    │ - Execution   │ - Usage        │ │   │
│  │  │ - Performance  │ - Timing      │ - Effectiveness│ │   │
│  │  │ - Load         │ - Failures    │ - Patterns     │ │   │
│  │  └────────────────┴───────────────┴────────────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Unified Storage Layer                               │   │
│  │  ~/.vibe-log/                                        │   │
│  │  ├── analyzed-prompts/        (existing)             │   │
│  │  ├── orchestration/            (NEW)                 │   │
│  │  │   ├── agents/{sessionId}.json                     │   │
│  │  │   ├── hooks/{sessionId}.json                      │   │
│  │  │   └── skills/{sessionId}.json                     │   │
│  │  └── cache/                    (NEW - performance)   │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Enhanced Analytics & Reports                        │   │
│  │  - Multi-agent efficiency reports                    │   │
│  │  - Hook performance dashboards                       │   │
│  │  - Skill recommendation engine                       │   │
│  │  - Orchestration pattern detection                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Plugin Architecture (Proposed)

```javascript
// vibe-log-cli plugin system
{
  "plugins": [
    {
      "name": "orchestration-tracker",
      "version": "1.0.0",
      "hooks": {
        "SessionStart": "orchestration-tracker/session-init.js",
        "UserPromptSubmit": "orchestration-tracker/detect-agents.js",
        "PreToolUse": "orchestration-tracker/detect-skills.js",
        "PostToolUse": "orchestration-tracker/track-execution.js"
      },
      "statuslineWidgets": [
        "orchestration-tracker/widgets/agents.js",
        "orchestration-tracker/widgets/skills.js",
        "orchestration-tracker/widgets/hooks.js"
      ],
      "analytics": {
        "enabled": true,
        "dashboards": ["multi-agent-efficiency", "skill-usage"]
      }
    }
  ]
}
```

**Benefits:**
- ✅ Modular: Users opt-in to orchestration tracking
- ✅ Extensible: Other developers can create plugins
- ✅ Backward Compatible: Existing vibe-log features unaffected
- ✅ Performance: Plugins load lazily

---

## 4. Feature Specifications

### 4.1 Agent Lifecycle Tracking

**Objective:** Track creation, execution, and termination of Claude Code subagents

**Data Model:**
```json
{
  "sessionId": "uuid",
  "agents": [
    {
      "agentId": "unique-id",
      "name": "desenvolvimento",
      "type": "permanent | virtual",
      "spawned_at": "2025-11-23T10:15:00Z",
      "completed_at": "2025-11-23T10:20:00Z",
      "status": "active | completed | failed",
      "parent_agent": "legal-braniac",
      "task_description": "Implement authentication",
      "metrics": {
        "execution_time_ms": 300000,
        "tokens_used": 15000,
        "success_rate": 0.95
      }
    }
  ]
}
```

**Detection Mechanism:**
- Parse transcript for agent spawn patterns (`Task tool`, `@agent-name`)
- Monitor stdout/stderr for agent lifecycle events
- Correlate with session timestamps

**User Value:**
- "Which agents are bottlenecks?"
- "What's my average agent execution time?"
- "Do I overuse general-purpose agents?"

### 4.2 Hook Execution Monitoring

**Objective:** Track all Claude Code hooks and their performance

**Data Model:**
```json
{
  "sessionId": "uuid",
  "hooks": {
    "legal-braniac-loader": {
      "trigger": "SessionStart",
      "executions": [
        {
          "timestamp": "2025-11-23T10:00:00Z",
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

**Detection Mechanism:**
- Parse `.claude/settings.json` to discover installed hooks
- Monitor hook wrapper stdout/stderr
- Track execution timestamps from hook-status files

**User Value:**
- "Which hooks are slowing down my workflow?"
- "Are my hooks failing silently?"
- "How often do hooks trigger?"

### 4.3 Skill Usage Analytics

**Objective:** Track skill invocations and effectiveness

**Data Model:**
```json
{
  "sessionId": "uuid",
  "skills": {
    "code-execution": {
      "invocations": [
        {
          "timestamp": "2025-11-23T10:30:00Z",
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

**Detection Mechanism:**
- Parse prompts for skill trigger keywords
- Monitor `skills/*/SKILL.md` for skill definitions
- Correlate skill calls with agent actions

**User Value:**
- "Which skills should I invest time learning?"
- "Are there underutilized skills?"
- "What's the ROI of each skill?"

### 4.4 Orchestrator Metrics

**Objective:** Provide high-level orchestration efficiency metrics

**Data Model:**
```json
{
  "sessionId": "uuid",
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

**User Value:**
- "Am I orchestrating efficiently?"
- "Where are the bottlenecks?"
- "Can I parallelize more?"

---

## 5. Generalization Strategy

### 5.1 From Specific → Generic

#### Current Implementation (Legal-Braniac Specific)

```javascript
// SPECIFIC: Hardcoded for Legal-Braniac
const agentsDir = path.join(projectDir, '.claude', 'agents');
const legalBraniacFile = 'legal-braniac.md';
```

#### Proposed Generic Implementation

```javascript
// GENERIC: Works for ANY orchestrator
const config = vibeLog.getConfig('orchestration-tracker');
const agentsDir = config.agentsDir || path.join(projectDir, '.claude', 'agents');
const orchestratorPattern = config.orchestratorPattern || /.*-braniac\.md/;
```

**Configuration File (`~/.vibe-log/config.json`):**
```json
{
  "plugins": {
    "orchestration-tracker": {
      "enabled": true,
      "agentsDir": ".claude/agents",
      "skillsDir": "skills",
      "orchestratorPattern": ".*-braniac\\.md",
      "detectionPatterns": {
        "agentSpawn": ["Task tool", "@agent-", "delegating to"],
        "skillInvoke": ["using skill", "invoke skill"],
        "hookExecution": ["hook success", "hook tracked"]
      }
    }
  }
}
```

### 5.2 Agent Auto-Discovery (Generic)

**Problem:** Different users have different agent structures

**Solution:** Pattern-based discovery

```javascript
// Generic agent discovery
async function discoverAgents(config) {
  const agentsDir = config.agentsDir;
  const patterns = config.agentPatterns || ['*.md'];

  const agents = {};
  for (const pattern of patterns) {
    const files = await glob(path.join(agentsDir, pattern));

    for (const file of files) {
      const content = await fs.readFile(file, 'utf8');
      const metadata = parseAgentMetadata(content); // Extract name, description, capabilities

      agents[metadata.name] = {
        path: file,
        ...metadata
      };
    }
  }

  return agents;
}

function parseAgentMetadata(content) {
  // Support multiple formats:
  // - YAML frontmatter (---\nname: foo\n---)
  // - Markdown headers (# Agent Name)
  // - Custom markers ([AGENT: name])

  // YAML frontmatter
  const yamlMatch = content.match(/^---\n([\s\S]+?)\n---/);
  if (yamlMatch) {
    return yaml.parse(yamlMatch[1]);
  }

  // Markdown header
  const headerMatch = content.match(/^#\s+(.+)/m);
  if (headerMatch) {
    return {
      name: slugify(headerMatch[1]),
      description: extractDescription(content)
    };
  }

  // Fallback
  return {
    name: path.basename(file, '.md'),
    description: 'Auto-discovered agent'
  };
}
```

### 5.3 Skill Detection (Generic)

**Problem:** Skills can be in different formats (SKILL.md, skill.yaml, etc.)

**Solution:** Multi-format parser

```javascript
async function discoverSkills(config) {
  const skillsDir = config.skillsDir;
  const formats = config.skillFormats || ['SKILL.md', 'skill.yaml', 'skill.json'];

  const skills = {};
  const dirs = await fs.readdir(skillsDir);

  for (const dir of dirs) {
    for (const format of formats) {
      const skillFile = path.join(skillsDir, dir, format);

      if (await fileExists(skillFile)) {
        const skill = await parseSkillFile(skillFile, format);
        skills[dir] = skill;
        break; // Found skill definition
      }
    }
  }

  return skills;
}

async function parseSkillFile(file, format) {
  const content = await fs.readFile(file, 'utf8');

  switch (format) {
    case 'SKILL.md':
      return parseMarkdownSkill(content);
    case 'skill.yaml':
      return yaml.parse(content);
    case 'skill.json':
      return JSON.parse(content);
    default:
      throw new Error(`Unknown skill format: ${format}`);
  }
}
```

### 5.4 Hook Monitoring (Generic)

**Problem:** Users may have hooks in different locations

**Solution:** Settings-based discovery

```javascript
async function discoverHooks(config) {
  const settingsPath = config.settingsPath || '.claude/settings.json';
  const settings = JSON.parse(await fs.readFile(settingsPath, 'utf8'));

  const hooks = {};

  if (settings.hooks) {
    for (const [triggerType, hookConfigs] of Object.entries(settings.hooks)) {
      for (const config of hookConfigs) {
        if (config.hooks && Array.isArray(config.hooks)) {
          for (const hook of config.hooks) {
            if (hook.command) {
              const hookName = extractHookName(hook.command);

              if (!hooks[hookName]) {
                hooks[hookName] = {
                  triggers: [],
                  command: hook.command,
                  description: hook._note || hook.description || ''
                };
              }

              hooks[hookName].triggers.push(triggerType);
            }
          }
        }
      }
    }
  }

  return hooks;
}

function extractHookName(command) {
  // Handle various command formats:
  // - "node .claude/hooks/foo.js"
  // - ".claude/hooks/foo.sh"
  // - "npx vibe-log-cli send"
  // - "node hook-wrapper.js actual-hook.js"

  const parts = command.split(/\s+/);

  // npx commands
  if (parts[0] === 'npx' && parts.length > 1) {
    return parts[1];
  }

  // Find last .js or .sh file
  const scriptPaths = parts.filter(p => p.includes('.js') || p.includes('.sh'));
  const scriptPath = scriptPaths[scriptPaths.length - 1];

  if (scriptPath) {
    return path.basename(scriptPath, path.extname(scriptPath));
  }

  return 'unknown-hook';
}
```

---

## 6. Implementation Roadmap

### Phase 1: Core Plugin System (Weeks 1-2)

**Deliverables:**
- [ ] Plugin loader mechanism
- [ ] Plugin configuration schema
- [ ] Plugin lifecycle (init, execute, cleanup)
- [ ] Backward compatibility tests

**Technical Debt:**
- Refactor vibe-log-cli to support plugin hooks
- Create plugin API documentation
- Setup plugin examples repository

### Phase 2: Orchestration Tracker Plugin (Weeks 3-4)

**Deliverables:**
- [ ] Agent discovery (generic)
- [ ] Skill detection (multi-format)
- [ ] Hook monitoring (settings-based)
- [ ] Data models (JSON schemas)
- [ ] Storage layer (`~/.vibe-log/orchestration/`)

**Testing:**
- Unit tests for discovery functions
- Integration tests with various project structures
- Performance benchmarks (target: <50ms overhead)

### Phase 3: Analytics & Visualization (Weeks 5-6)

**Deliverables:**
- [ ] Multi-agent efficiency dashboard
- [ ] Hook performance metrics
- [ ] Skill usage heatmaps
- [ ] Orchestration pattern detection
- [ ] PDF/HTML report generation

**UI Components:**
- Agent timeline visualization
- Hook execution waterfall
- Skill usage pie chart
- Orchestrator metrics card

### Phase 4: Integration & Documentation (Weeks 7-8)

**Deliverables:**
- [ ] Integration tests with real projects
- [ ] Plugin documentation (README, API reference)
- [ ] Migration guide (for Legal-Braniac users)
- [ ] Video tutorial
- [ ] Blog post announcement

**Community:**
- Submit PR to vibe-log-cli
- Create discussion thread
- Gather feedback from early adopters

---

## 7. Integration Points

### 7.1 Existing Vibe-Log Hooks

**Hook: `SessionStart`**
```javascript
// vibe-log-cli/dist/hooks/session-start.js (existing)
// ADD: Call orchestration-tracker plugin
const orchestrationTracker = require('vibe-log-cli/plugins/orchestration-tracker');
await orchestrationTracker.initSession(sessionId);
```

**Hook: `UserPromptSubmit`**
```javascript
// vibe-log-cli/dist/hooks/analyze-prompt.js (existing)
// ENHANCE: Detect agent spawn patterns
const prompt = input.prompt;
const agentSpawn = await orchestrationTracker.detectAgentSpawn(prompt);
if (agentSpawn) {
  await orchestrationTracker.registerAgent(agentSpawn);
}
```

**Hook: `PreCompact`**
```javascript
// vibe-log-cli/dist/hooks/pre-compact.js (existing)
// ADD: Sync orchestration data
await orchestrationTracker.syncBeforeCompact(sessionId);
```

### 7.2 Data Storage Integration

**Unified Storage Structure:**
```
~/.vibe-log/
├── analyzed-prompts/          # EXISTING: Prompt analysis
│   └── {sessionId}.json
├── orchestration/             # NEW: Orchestration tracking
│   ├── agents/
│   │   └── {sessionId}.json
│   ├── hooks/
│   │   └── {sessionId}.json
│   └── skills/
│       └── {sessionId}.json
├── cache/                     # NEW: Performance cache
│   └── statusline-cache.json
└── config.json                # EXISTING: User config
```

**Backward Compatibility:**
- Old sessions (no orchestration data) still work
- New fields optional in reports
- Gradual migration via `vibe-log migrate`

### 7.3 Statusline Integration

**Current vibe-log statusline:**
```
Gordon: 85/100 - Clear prompt 🎯
```

**Enhanced statusline (opt-in):**
```
Gordon: 85/100 - Clear prompt 🎯 | 🤖 3 agents | 🛠️ docx, git | ⚡ 6 hooks
```

**Configuration:**
```json
{
  "statusline": {
    "widgets": [
      "coach",             // EXISTING: Gordon feedback
      "orchestration"      // NEW: Agent/skill/hook tracking
    ]
  }
}
```

---

## 8. Backward Compatibility

### 8.1 Compatibility Matrix

| Vibe-Log Version | Orchestration Plugin | Coach Feature | Cloud Sync | Report Generation |
|------------------|----------------------|---------------|------------|-------------------|
| 0.7.x (current)  | ⚠️  Plugin disabled   | ✅ Works      | ✅ Works   | ✅ Works          |
| 0.8.x (proposed) | ✅ Plugin optional    | ✅ Works      | ✅ Works   | ✅ Enhanced       |
| 1.0.x (future)   | ✅ Plugin default     | ✅ Works      | ✅ Works   | ✅ Full support   |

### 8.2 Migration Path

**For Existing Vibe-Log Users:**
1. Upgrade to vibe-log-cli@0.8.0 (with plugin system)
2. Install orchestration-tracker plugin: `npx vibe-log-cli plugin install orchestration-tracker`
3. Enable in config: `npx vibe-log-cli config set plugins.orchestration-tracker.enabled true`
4. Start using: Automatic detection on next session

**For Legal-Braniac Users:**
1. Install vibe-log-cli@0.8.0
2. Run migration: `npx vibe-log-cli migrate --from legal-braniac`
3. Verify: `npx vibe-log-cli orchestration status`

**Migration Script:**
```bash
#!/bin/bash
# ~/.vibe-log/migrate-legal-braniac.sh

echo "Migrating Legal-Braniac data to vibe-log orchestration format..."

# Copy session files
cp .claude/hooks/legal-braniac-session.json ~/.vibe-log/orchestration/agents/current-session.json

# Copy virtual agents state
cp .claude/statusline/virtual-agents-state.json ~/.vibe-log/orchestration/agents/virtual-state.json

# Copy hooks status
cp .claude/statusline/hooks-status.json ~/.vibe-log/orchestration/hooks/current-session.json

echo "Migration complete! Run 'npx vibe-log-cli orchestration verify' to validate."
```

---

## 9. Success Metrics

### 9.1 Adoption Metrics

**Target (6 months post-launch):**
- ✅ 100+ installations of orchestration-tracker plugin
- ✅ 20+ projects using multi-agent tracking
- ✅ 5+ community-contributed plugins

**Measurement:**
- npm download stats
- GitHub stars/forks
- Community forum discussions

### 9.2 Performance Metrics

**Target:**
- ✅ Plugin overhead: <50ms per session
- ✅ Storage overhead: <5MB per 100 sessions
- ✅ Report generation: <3s for 1000-session analysis

**Measurement:**
- Benchmarking suite
- User feedback surveys
- Automated performance tests in CI

### 9.3 User Satisfaction

**Target:**
- ✅ 90%+ users find orchestration insights valuable
- ✅ 80%+ users enable plugin by default
- ✅ 50%+ users configure custom patterns

**Measurement:**
- In-app satisfaction survey
- GitHub issues/feedback
- Community testimonials

---

## 10. Appendices

### Appendix A: References

**Local Repository Documentation:**
- [Multi-Agent Orchestration Statusline Architecture](./multi-agent-orchestration-statusline-architecture.md)
- [Claude Code Statuslines Repositories](./claude-code-statuslines-repositories.md)
- [Legal-Braniac Agent Definition](./.claude/orchestrator/legal-braniac.md)
- [Vibe-Log Web Compatibility](./.claude/hooks/docs/vibe-log-web-compatibility.md)

**External Sources:**
- [Vibe-Log-CLI GitHub Repository](https://github.com/vibe-log/vibe-log-cli)
- [Vibe-Log Official Documentation](https://vibe-log.dev/)
- [Vibe-Log npm Package](https://libraries.io/npm/vibe-log-cli)
- [Claude Code Statusline Documentation](https://code.claude.com/docs/en/statusline)
- [ccstatusline Project](https://github.com/sirmalloc/ccstatusline)
- [Awesome Claude Code - Statuslines](https://github.com/hesreallyhim/awesome-claude-code/issues/158)

### Appendix B: Code Examples

**B.1: Generic Agent Discovery**

See Section 5.2 for full implementation.

**B.2: Plugin Configuration Schema**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "enabled": {
      "type": "boolean",
      "default": false
    },
    "agentsDir": {
      "type": "string",
      "default": ".claude/agents"
    },
    "skillsDir": {
      "type": "string",
      "default": "skills"
    },
    "agentPatterns": {
      "type": "array",
      "items": { "type": "string" },
      "default": ["*.md"]
    },
    "skillFormats": {
      "type": "array",
      "items": { "type": "string" },
      "default": ["SKILL.md", "skill.yaml", "skill.json"]
    },
    "detectionPatterns": {
      "type": "object",
      "properties": {
        "agentSpawn": {
          "type": "array",
          "items": { "type": "string" }
        },
        "skillInvoke": {
          "type": "array",
          "items": { "type": "string" }
        },
        "hookExecution": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    }
  }
}
```

**B.3: Orchestration Data JSON Schema**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["sessionId", "version"],
  "properties": {
    "sessionId": {
      "type": "string",
      "format": "uuid"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "agents": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["agentId", "name", "type", "spawned_at"],
        "properties": {
          "agentId": { "type": "string" },
          "name": { "type": "string" },
          "type": { "enum": ["permanent", "virtual"] },
          "spawned_at": { "type": "string", "format": "date-time" },
          "completed_at": { "type": "string", "format": "date-time" },
          "status": { "enum": ["active", "completed", "failed"] },
          "parent_agent": { "type": "string" },
          "task_description": { "type": "string" },
          "metrics": {
            "type": "object",
            "properties": {
              "execution_time_ms": { "type": "integer" },
              "tokens_used": { "type": "integer" },
              "success_rate": { "type": "number", "minimum": 0, "maximum": 1 }
            }
          }
        }
      }
    },
    "hooks": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "trigger": { "type": "string" },
          "executions": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "timestamp": { "type": "string", "format": "date-time" },
                "duration_ms": { "type": "integer" },
                "success": { "type": "boolean" },
                "output_summary": { "type": "string" }
              }
            }
          },
          "stats": {
            "type": "object",
            "properties": {
              "total_executions": { "type": "integer" },
              "avg_duration_ms": { "type": "number" },
              "failure_rate": { "type": "number", "minimum": 0, "maximum": 1 }
            }
          }
        }
      }
    },
    "skills": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "invocations": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "timestamp": { "type": "string", "format": "date-time" },
                "agent": { "type": "string" },
                "context": { "type": "string" },
                "outcome": { "enum": ["success", "failure", "partial"] }
              }
            }
          },
          "stats": {
            "type": "object",
            "properties": {
              "total_uses": { "type": "integer" },
              "success_rate": { "type": "number", "minimum": 0, "maximum": 1 },
              "avg_duration_ms": { "type": "number" }
            }
          }
        }
      }
    },
    "orchestration": {
      "type": "object",
      "properties": {
        "total_agents_spawned": { "type": "integer" },
        "parallel_execution_count": { "type": "integer" },
        "sequential_execution_count": { "type": "integer" },
        "avg_agent_execution_time_ms": { "type": "number" },
        "orchestrator_overhead_ms": { "type": "number" },
        "efficiency_score": { "type": "number", "minimum": 0, "maximum": 1 },
        "bottleneck_agents": {
          "type": "array",
          "items": { "type": "string" }
        },
        "recommendations": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    }
  }
}
```

### Appendix C: Frequently Asked Questions

**Q: Why should vibe-log add this instead of it being a separate tool?**

A: Orchestration tracking is a natural extension of vibe-log's mission to "understand AI coding patterns". Multi-agent workflows are becoming the norm (not exception) in Claude Code, and users already trust vibe-log for session analysis. Integrating orchestration tracking provides a **unified analytics platform** rather than fragmenting the ecosystem.

**Q: Won't this bloat vibe-log's codebase?**

A: No. The plugin architecture ensures orchestration tracking is **opt-in**. Users who don't need it won't load it. Estimated addition: ~2000 LOC in a separate plugin directory, with zero impact on core vibe-log performance.

**Q: How does this differ from ccstatusline?**

A: ccstatusline is a **visual statusline** (what you see in the terminal). This proposal adds **data collection and analytics** (what vibe-log does best). They're complementary: ccstatusline displays data, vibe-log analyzes patterns over time.

**Q: What if my project doesn't use agents/skills/hooks?**

A: The plugin gracefully detects absence of these features and reports "No orchestration detected" without errors. It's designed to be zero-overhead for traditional single-agent workflows.

**Q: Can I contribute to the plugin?**

A: Absolutely! The plugin will be open-source (MIT license) with clear contribution guidelines. We welcome enhancements like:
- New detection patterns
- Additional analytics dashboards
- Support for other orchestration frameworks (e.g., LangGraph, CrewAI)

---

## Conclusion

This proposal presents a **comprehensive, production-ready plan** to integrate Multi-Agent Orchestration Tracking into vibe-log-cli. The implementation strategy prioritizes:

✅ **Generalization**: Works for any Claude Code project structure
✅ **Backward Compatibility**: Existing vibe-log features unaffected
✅ **Performance**: <50ms overhead via aggressive caching
✅ **Modularity**: Plugin architecture for opt-in adoption
✅ **User Value**: Actionable insights into orchestration efficiency

**Next Steps:**
1. Review this proposal with vibe-log maintainers
2. Refine technical specifications based on feedback
3. Initiate Phase 1 implementation (Plugin System)
4. Submit PR to [vibe-log-cli](https://github.com/vibe-log/vibe-log-cli)

**Contact:**
- GitHub: [@PedroGiudice](https://github.com/PedroGiudice)
- Project: [Claude-Code-Projetos](https://github.com/PedroGiudice/Claude-Code-Projetos)
- Discussion: [Open an issue](https://github.com/vibe-log/vibe-log-cli/issues) to discuss this proposal

---

**Document Version:** 1.0
**Last Updated:** 2025-11-23
**Status:** Ready for Review
