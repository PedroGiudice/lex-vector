# Migration Guide: Legal-Braniac to Vibe-Log Orchestration Tracker

## Overview

This guide helps users migrate from Legal-Braniac's custom orchestration tracking to the vibe-log orchestration-tracker plugin.

**Migration Benefits:**
- ✅ Unified analytics platform (vibe-log + orchestration)
- ✅ Better long-term data persistence
- ✅ More comprehensive reporting
- ✅ Community-driven improvements
- ✅ Standard tooling (CLI, exports, etc.)

**What Stays in Legal-Braniac:**
- ❗ Orchestration engine (delegation, decision-making)
- ❗ Statusline integration (3-line hybrid statusline)
- ❗ Virtual agent factory
- ❗ Braniac-specific workflows

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Migration Steps](#migration-steps)
3. [Configuration Mapping](#configuration-mapping)
4. [Data Migration](#data-migration)
5. [Verification](#verification)
6. [Rollback Plan](#rollback-plan)
7. [FAQ](#faq)

---

## Prerequisites

### Required Versions

- **vibe-log-cli:** 0.8.0+
- **Node.js:** 18+
- **Legal-Braniac:** Any version

### Backup Existing Data

Before migrating, backup your Legal-Braniac tracking data:

```bash
# Create backup directory
mkdir -p ~/legal-braniac-backup/$(date +%Y%m%d)

# Backup session data
cp .claude/hooks/legal-braniac-session.json ~/legal-braniac-backup/$(date +%Y%m%d)/

# Backup virtual agents state
cp .claude/statusline/virtual-agents-state.json ~/legal-braniac-backup/$(date +%Y%m%d)/

# Backup hooks status
cp .claude/statusline/hooks-status.json ~/legal-braniac-backup/$(date +%Y%m%d)/

echo "✅ Backup created at ~/legal-braniac-backup/$(date +%Y%m%d)/"
```

---

## Migration Steps

### Step 1: Install vibe-log-cli

```bash
# Install globally
npm install -g vibe-log-cli

# Verify version (must be 0.8.0+)
npx vibe-log-cli --version
```

### Step 2: Enable Orchestration Tracker Plugin

```bash
# Enable plugin
npx vibe-log-cli config set plugins.orchestration-tracker.enabled true

# Configure paths (match Legal-Braniac structure)
npx vibe-log-cli config set plugins.orchestration-tracker.settings.agentsDir ".claude/agents"
npx vibe-log-cli config set plugins.orchestration-tracker.settings.skillsDir "skills"

# Verify configuration
npx vibe-log-cli config get plugins.orchestration-tracker
```

Expected output:

```json
{
  "enabled": true,
  "settings": {
    "agentsDir": ".claude/agents",
    "skillsDir": "skills",
    "agentPatterns": ["*.md"],
    "skillFormats": ["SKILL.md", "skill.yaml", "skill.json"]
  }
}
```

### Step 3: Run Migration Script

```bash
# Run automated migration
npx vibe-log-cli migrate --from legal-braniac

# If you need to specify custom paths
npx vibe-log-cli migrate --from legal-braniac \
  --source .claude/hooks/legal-braniac-session.json \
  --dest ~/.vibe-log/orchestration/
```

Expected output:

```
🔄 Starting migration from Legal-Braniac...

✅ Migrated agent data (7 agents)
✅ Migrated virtual agents state (3 virtual agents)
✅ Migrated hooks status (11 hooks)
✅ Converted session metadata

📊 Migration Summary:
   - Permanent agents: 4
   - Virtual agents: 3
   - Hooks migrated: 11
   - Skills discovered: 34

✅ Migration complete!
   Data location: ~/.vibe-log/orchestration/

Next steps:
  1. Verify migration: npx vibe-log-cli orchestration verify
  2. View metrics: npx vibe-log-cli orchestration
```

### Step 4: Verify Migration

```bash
# Verify migration
npx vibe-log-cli orchestration verify

# View migrated data
npx vibe-log-cli orchestration --agents
npx vibe-log-cli orchestration --hooks
npx vibe-log-cli orchestration --skills
```

### Step 5: Update Legal-Braniac Hooks (Optional)

If you want Legal-Braniac to write directly to vibe-log format:

```javascript
// .claude/hooks/legal-braniac-loader.js

// ADD at top:
import { OrchestrationStorage } from 'vibe-log-cli/plugins/orchestration-tracker/storage.js';

const storage = new OrchestrationStorage('~/.vibe-log/orchestration');

// REPLACE session saving logic:
async function saveSessionData(sessionData) {
  // OLD: Write to .claude/hooks/legal-braniac-session.json
  // await writeFileSync('.claude/hooks/legal-braniac-session.json', JSON.stringify(sessionData));

  // NEW: Write to vibe-log format
  await storage.saveAgents(sessionData.sessionId, sessionData.agents);
  await storage.saveHooks(sessionData.sessionId, sessionData.hooks);
  await storage.saveSkills(sessionData.sessionId, sessionData.skills);
}
```

---

## Configuration Mapping

### Legal-Braniac → Vibe-Log Orchestration Tracker

| Legal-Braniac | Vibe-Log Plugin | Notes |
|---------------|-----------------|-------|
| `.claude/agents/` | `settings.agentsDir` | Same path by default |
| `skills/` | `settings.skillsDir` | Same path by default |
| `*.md` patterns | `settings.agentPatterns` | Can add `.yaml`, `.json` |
| `SKILL.md` format | `settings.skillFormats` | Can add `skill.yaml` |
| Discovery cache (10.8x speedup) | `cache.enabled` | Same caching strategy |
| 24h virtual agent TTL | N/A | Managed by Legal-Braniac |

### Example: Custom Configuration

If your Legal-Braniac uses custom paths:

**Legal-Braniac:**
```javascript
const AGENTS_DIR = 'custom/agents';
const SKILLS_DIR = 'custom-skills';
```

**Vibe-Log Plugin:**
```bash
npx vibe-log-cli config set plugins.orchestration-tracker.settings.agentsDir "custom/agents"
npx vibe-log-cli config set plugins.orchestration-tracker.settings.skillsDir "custom-skills"
```

---

## Data Migration

### What Gets Migrated

#### 1. Agent Data

**Source:** `.claude/hooks/legal-braniac-session.json`

```json
{
  "agents": {
    "desenvolvimento": {
      "type": "permanent",
      "invocations": 12,
      "lastUsed": 1700000000000
    }
  }
}
```

**Destination:** `~/.vibe-log/orchestration/agents/{sessionId}.json`

```json
{
  "sessionId": "abc-123",
  "agents": [
    {
      "name": "desenvolvimento",
      "type": "permanent",
      "metrics": {
        "total_invocations": 12,
        "last_used": "2025-11-23T10:00:00.000Z"
      }
    }
  ]
}
```

#### 2. Virtual Agents State

**Source:** `.claude/statusline/virtual-agents-state.json`

```json
{
  "frontend-expert": {
    "createdAt": 1700000000000,
    "invocations": 3,
    "promotable": false
  }
}
```

**Destination:** `~/.vibe-log/orchestration/agents/{sessionId}.json`

```json
{
  "agents": [
    {
      "name": "frontend-expert",
      "type": "virtual",
      "spawned_at": "2025-11-23T09:00:00.000Z",
      "metrics": {
        "total_invocations": 3,
        "promotable": false
      }
    }
  ]
}
```

#### 3. Hooks Status

**Source:** `.claude/statusline/hooks-status.json`

```json
{
  "legal-braniac-loader": {
    "lastRun": 1700000000000
  },
  "vibe-analyze-prompt": {
    "lastRun": 1700000100000
  }
}
```

**Destination:** `~/.vibe-log/orchestration/hooks/{sessionId}.json`

```json
{
  "hooks": {
    "legal-braniac-loader": {
      "executions": [
        {
          "timestamp": "2025-11-23T10:00:00.000Z",
          "duration_ms": 150,
          "success": true
        }
      ]
    }
  }
}
```

### What Does NOT Get Migrated

These remain in Legal-Braniac:

- ❗ **Orchestration Engine Logic** - Delegation, decision-making, gap detection
- ❗ **Statusline Rendering** - 3-line hybrid statusline display
- ❗ **Virtual Agent Factory** - Auto-creation and promotion logic
- ❗ **Cache System** - Discovery cache (though vibe-log has its own)

**Reason:** These are core Braniac features, not data tracking.

---

## Verification

### Automated Verification

```bash
# Run verification suite
npx vibe-log-cli orchestration verify

# Expected output:
# ✅ Agent data integrity check passed
# ✅ Hook data integrity check passed
# ✅ Skill data integrity check passed
# ✅ Session metadata valid
# ✅ All timestamps converted correctly
# ✅ No data loss detected
```

### Manual Verification

#### 1. Compare Agent Counts

```bash
# Legal-Braniac count
jq '.agents | length' .claude/hooks/legal-braniac-session.json

# Vibe-log count
npx vibe-log-cli orchestration --agents --format json | jq '.agents | length'

# Should match!
```

#### 2. Verify Virtual Agents

```bash
# Legal-Braniac virtual agents
jq 'to_entries | map(select(.value.type == "virtual")) | length' \
  .claude/statusline/virtual-agents-state.json

# Vibe-log virtual agents
npx vibe-log-cli orchestration --agents --format json | \
  jq '.agents | map(select(.type == "virtual")) | length'

# Should match!
```

#### 3. Check Hook Integrity

```bash
# Legal-Braniac hooks
jq 'keys | length' .claude/statusline/hooks-status.json

# Vibe-log hooks
npx vibe-log-cli orchestration --hooks --format json | jq '.hooks | length'

# Should match!
```

---

## Rollback Plan

If you need to rollback to Legal-Braniac-only tracking:

### Option 1: Disable Plugin (Keep Data)

```bash
# Disable orchestration tracker
npx vibe-log-cli config set plugins.orchestration-tracker.enabled false

# Legal-Braniac will continue working normally
# Migrated data preserved in ~/.vibe-log/orchestration/
```

### Option 2: Full Rollback (Restore Backup)

```bash
# Restore from backup
cp ~/legal-braniac-backup/$(date +%Y%m%d)/legal-braniac-session.json \
   .claude/hooks/legal-braniac-session.json

cp ~/legal-braniac-backup/$(date +%Y%m%d)/virtual-agents-state.json \
   .claude/statusline/virtual-agents-state.json

cp ~/legal-braniac-backup/$(date +%Y%m%d)/hooks-status.json \
   .claude/statusline/hooks-status.json

# Disable plugin
npx vibe-log-cli config set plugins.orchestration-tracker.enabled false

echo "✅ Rollback complete - Legal-Braniac restored"
```

---

## Post-Migration Workflow

### Dual Tracking (Recommended)

**Best practice:** Keep both Legal-Braniac and vibe-log tracking active.

**Why?**
- Legal-Braniac: Real-time orchestration (statusline, delegation)
- Vibe-log: Long-term analytics (trends, reports)

**How?**
1. Legal-Braniac continues writing to `.claude/hooks/` (real-time)
2. Vibe-log plugin reads same data (analytics)
3. No conflicts - both read from same source

### Single Source of Truth (Advanced)

**For advanced users:** Migrate Legal-Braniac to write directly to vibe-log format.

**Pros:**
- Single data location
- Cleaner architecture
- Better long-term maintenance

**Cons:**
- Requires modifying Legal-Braniac hooks
- More complex initial setup

**Implementation:**

```javascript
// .claude/hooks/legal-braniac-loader.js

import { OrchestrationStorage } from 'vibe-log-cli/plugins/orchestration-tracker/storage.js';

const storage = new OrchestrationStorage(
  path.join(os.homedir(), '.vibe-log/orchestration')
);

// Replace all writeFileSync calls with:
await storage.saveAgents(sessionId, agents);
await storage.saveHooks(sessionId, hooks);
await storage.saveSkills(sessionId, skills);
```

---

## FAQ

### Q: Will migration affect Legal-Braniac functionality?

**A:** No. Legal-Braniac orchestration engine, statusline, and virtual agent factory continue working normally. Only the data tracking layer moves to vibe-log.

### Q: Can I use both Legal-Braniac and vibe-log tracking?

**A:** Yes! Recommended approach is dual tracking:
- Legal-Braniac: Real-time orchestration
- Vibe-log: Long-term analytics

### Q: What happens to my virtual agents?

**A:** Virtual agent state is migrated to vibe-log format, but Legal-Braniac continues managing their lifecycle (creation, promotion, TTL).

### Q: Do I need to modify Legal-Braniac code?

**A:** No, not required. Optional: You can update hooks to write directly to vibe-log format for cleaner architecture.

### Q: Will this break my statusline?

**A:** No. The hybrid-statusline.js continues reading from Legal-Braniac's `.claude/hooks/` files. No changes needed.

### Q: How do I migrate multiple projects?

**A:** Run the migration script in each project directory:

```bash
# Project 1
cd ~/projects/project1
npx vibe-log-cli migrate --from legal-braniac

# Project 2
cd ~/projects/project2
npx vibe-log-cli migrate --from legal-braniac
```

### Q: Can I customize detection patterns?

**A:** Yes! Vibe-log plugin supports custom patterns:

```bash
npx vibe-log-cli config set \
  plugins.orchestration-tracker.settings.detectionPatterns.agentSpawn \
  '["Task tool", "@agent-", "delegating to", "YOUR CUSTOM PATTERN"]'
```

### Q: Where is data stored after migration?

**A:** `~/.vibe-log/orchestration/`

```
~/.vibe-log/
├── orchestration/
│   ├── agents/
│   │   └── {sessionId}.json
│   ├── hooks/
│   │   └── {sessionId}.json
│   └── skills/
│       └── {sessionId}.json
└── config.json
```

### Q: How do I export migrated data?

**A:** Use vibe-log CLI:

```bash
# Export to JSON
npx vibe-log-cli orchestration --format json > metrics.json

# Export to CSV
npx vibe-log-cli orchestration --format csv --export metrics.csv
```

### Q: What if migration fails?

**A:** Migration is non-destructive - original files are not deleted. Simply rollback using the backup:

```bash
cp ~/legal-braniac-backup/$(date +%Y%m%d)/* .claude/hooks/
cp ~/legal-braniac-backup/$(date +%Y%m%d)/* .claude/statusline/
```

---

## Support

If you encounter issues during migration:

1. **Check logs:** `cat ~/.vibe-log/logs/migration.log`
2. **Verify backup:** Ensure backup was created successfully
3. **Report issue:** [GitHub Issues](https://github.com/vibe-log/vibe-log-cli/issues)
4. **Rollback:** Use rollback plan above

---

## Next Steps

After successful migration:

1. ✅ **Verify data integrity** - Compare counts with Legal-Braniac
2. ✅ **Test CLI commands** - `npx vibe-log-cli orchestration`
3. ✅ **Explore analytics** - View trends and patterns
4. ✅ **Customize config** - Adjust patterns and paths as needed
5. ✅ **Share feedback** - Help improve the plugin!

---

**Migration complete!** 🎉

You now have unified orchestration tracking via vibe-log while maintaining all Legal-Braniac functionality.
