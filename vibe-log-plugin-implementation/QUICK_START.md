# Quick Start - Orchestration Tracker Plugin

This guide shows how to integrate the orchestration-tracker plugin into vibe-log-cli.

---

## 1. Copy Files to vibe-log-cli

Assuming you have a vibe-log-cli fork:

```bash
# Navigate to your vibe-log-cli fork
cd /path/to/vibe-log-cli

# Copy plugin files
cp -r /home/user/Claude-Code-Projetos/vibe-log-plugin-implementation/src/plugins/orchestration-tracker ./src/plugins/
cp /home/user/Claude-Code-Projetos/vibe-log-plugin-implementation/src/plugins/core/plugin-loader.ts ./src/plugins/core/
cp /home/user/Claude-Code-Projetos/vibe-log-plugin-implementation/src/cli/commands/orchestration.ts ./src/cli/commands/
```

---

## 2. Update Main CLI File

**File:** `src/cli/index.ts` (or wherever your main CLI is)

```typescript
import { Command } from 'commander';
import { createOrchestrationCommand } from './commands/orchestration.js';
import { pluginRegistry } from '../plugins/core/plugin-registry.js';
import { orchestrationTracker } from '../plugins/orchestration-tracker/index.js';

const program = new Command();

// ... existing commands ...

// Add orchestration command
program.addCommand(createOrchestrationCommand());

// Register orchestration plugin
async function initializePlugins() {
  await pluginRegistry.register(orchestrationTracker, {
    enabled: true,
    settings: {
      agentsDir: '.claude/agents',
      skillsDir: 'skills',
      agentPatterns: ['*.md'],
      skillFormats: ['SKILL.md', 'skill.yaml', 'skill.json'],
      verbose: false,
    },
  });
}

// Initialize before parsing commands
await initializePlugins();

program.parse();
```

---

## 3. Hook Integration

**File:** Your session/hook management code

```typescript
import { pluginRegistry } from './plugins/core/plugin-registry.js';
import { HookTrigger } from './plugins/core/types.js';

// On session start
async function handleSessionStart(sessionId: string, projectDir: string) {
  const session = {
    sessionId,
    projectDir,
    startTime: Date.now(),
    plugins: {},
  };

  await pluginRegistry.triggerHook(HookTrigger.SessionStart, session);

  return session;
}

// On user prompt
async function handleUserPrompt(session, prompt: string) {
  await pluginRegistry.triggerHook(
    HookTrigger.UserPromptSubmit,
    session,
    { prompt }
  );
}

// On session end
async function handleSessionEnd(session) {
  await pluginRegistry.triggerHook(HookTrigger.SessionEnd, session);
}
```

---

## 4. Configuration (Optional)

**File:** `~/.vibe-log/config.json`

```json
{
  "plugins": {
    "orchestration-tracker": {
      "enabled": true,
      "settings": {
        "agentsDir": ".claude/agents",
        "skillsDir": "skills",
        "agentPatterns": ["*.md", "*.yaml"],
        "skillFormats": ["SKILL.md", "skill.yaml", "skill.json"],
        "verbose": false
      },
      "cache": {
        "enabled": true,
        "ttlSeconds": 300
      }
    }
  }
}
```

---

## 5. Test the Plugin

### Basic Test

```bash
# Navigate to a Claude Code project
cd /path/to/claude-code-project

# Run a session (this should trigger SessionStart)
npx vibe-log-cli [your-existing-command]

# View metrics
npx vibe-log-cli orchestration --latest
```

### Expected Output

```
📊 Orchestration Metrics
────────────────────────────────────────────────────────────

Session Info:
  ID:       abc123-def456-ghi789
  Started:  11/23/2025, 10:30:00 AM
  ...

👥 Agents
────────────────────────────────────────────────────────────
  1. [P] desenvolvimento 0×
     Implementação técnica hands-on
  ...

📈 Summary
────────────────────────────────────────────────────────────
  Total Agents: 7
  Total Hooks: 6
  Total Skills: 34
  ...
```

---

## 6. Debugging

### Enable Verbose Logging

```json
{
  "plugins": {
    "orchestration-tracker": {
      "settings": {
        "verbose": true
      }
    }
  }
}
```

**Output:**
```
[AgentDiscovery] Discovered 7 agent(s) from .claude/agents
[HookMonitor] Discovered 6 hook(s) from settings.json
[SkillTracker] Discovered 34 skill(s) from skills
[OrchestrationTracker] Session started: abc123
```

### Check Storage

```bash
# List sessions
npx vibe-log-cli orchestration --list

# Show storage stats
npx vibe-log-cli orchestration --stats

# Manually inspect storage
ls -la ~/.vibe-log/orchestration/
cat ~/.vibe-log/orchestration/sessions/latest.json | jq
```

---

## 7. Common Issues

### Issue: "Plugin not found"

**Solution:**
- Ensure plugin files copied correctly
- Check import paths (`.js` extensions required for ESM)
- Verify `orchestrationTracker` export exists

### Issue: "No sessions found"

**Solution:**
- Ensure hooks are triggered (SessionStart, SessionEnd)
- Check `~/.vibe-log/orchestration/` directory exists
- Enable verbose logging to see what's happening

### Issue: "No agents/hooks/skills discovered"

**Solution:**
- Check `agentsDir`, `skillsDir` in config
- Verify file patterns match actual files
- Enable verbose logging to see parsing errors

---

## 8. Development Workflow

### Run Tests (after implementing test suite)

```bash
npm run test:orchestration
```

### Lint and Type Check

```bash
npm run lint
npm run typecheck
```

### Build

```bash
npm run build
```

---

## 9. CLI Usage Examples

### View Latest Session

```bash
npx vibe-log-cli orchestration --latest
```

### View Specific Session

```bash
npx vibe-log-cli orchestration --session abc123-def456
```

### Filter by Category

```bash
# Agents only
npx vibe-log-cli orchestration --latest --agents

# Hooks only
npx vibe-log-cli orchestration --latest --hooks

# Skills only
npx vibe-log-cli orchestration --latest --skills
```

### List All Sessions

```bash
npx vibe-log-cli orchestration --list
```

### Storage Statistics

```bash
npx vibe-log-cli orchestration --stats
```

---

## 10. Next Steps

- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Add API documentation
- [ ] Create usage examples
- [ ] Submit PR to vibe-log-cli

---

## Support

**Implementation Spec:** `IMPLEMENTATION_SPEC.md`
**Full Summary:** `IMPLEMENTATION_SUMMARY.md`
**Source Code:** `src/plugins/orchestration-tracker/`

**Questions?** Check the implementation summary for detailed architecture notes.
