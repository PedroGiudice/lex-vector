# PreToolUse Hook: Tool Injection for Task Agents

## 📋 Overview

**Hook Name**: `inject-tools-to-agents.js`
**Trigger**: PreToolUse (when `tool_name === "Task"`)
**Purpose**: Automatically inject tool availability instructions into Task agent prompts
**Version**: 1.0.0
**Date**: 2025-11-20

## 🎯 Problem Solved

**Before this hook:**
- Agents like "Plan" would say "I can't access the web" even though WebFetch/WebSearch were available
- Each agent .md file listed tools, but no runtime enforcement
- No single source of truth for agent→tools mapping

**After this hook:**
- Agent prompts automatically include `[SYSTEM: Available tools: WebFetch, WebSearch]`
- Centralized mapping in `agent-tools-mapping.json`
- Critical instructions (e.g., "MUST use WebFetch") injected when needed

## 🏗️ Architecture

```
User: "Plan jurisprudence system"
  ↓
[UserPromptSubmit] → Legal-Braniac suggests "Plan" agent
  ↓
Claude decides: Use Task tool
  ↓
[PreToolUse hook] → inject-tools-to-agents.js
  ├─ Reads agent-tools-mapping.json
  ├─ Detects subagent_type="Plan"
  ├─ Injects: "\n[SYSTEM: Available: WebFetch, WebSearch]\nIMPORTANT: ..."
  └─ Returns { updatedInput: { prompt: "..." } }
  ↓
Agent "Plan" executes with modified prompt
  └─ Sees WebFetch/WebSearch in system instruction
  └─ Uses tools when needed (no more "I can't access web")
```

## 📁 Files

### Core Implementation
- **`.claude/hooks/inject-tools-to-agents.js`** - Main hook (250 lines)
- **`.claude/hooks/agent-tools-mapping.json`** - Tool mappings (100 lines)
- **`.claude/hooks/lib/agent-mapping-loader.js`** - Shared helper (170 lines)

### Integration
- **`.claude/hooks/lib/agent-orchestrator.js`** - Legal-Braniac uses mapping for suggestions

### Tests
- **`.claude/hooks/test-pretool-simple.sh`** - 5 core tests
- **`.claude/hooks/test-pretool-hook.sh`** - Comprehensive tests (10 scenarios)

## 🔧 Configuration

### agent-tools-mapping.json Structure

```json
{
  "agents": {
    "Plan": {
      "tools": ["Glob", "Grep", "Read", "WebFetch", "WebSearch"],
      "description": "Planning agent with web research capabilities",
      "critical_instruction": "IMPORTANT: You have WebFetch and WebSearch tools available..."
    },

    "desenvolvimento": {
      "tools": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
      "description": "Development agent for code implementation",
      "critical_instruction": null
    }
  }
}
```

**Fields:**
- `tools`: Array of tool names (use `"*"` for all tools)
- `description`: Human-readable description (for documentation)
- `critical_instruction`: Text injected at end of prompt (or `null`)

## ✅ Tests

Run tests before any modifications:

```bash
# Quick validation (5 tests)
.claude/hooks/test-pretool-simple.sh

# Comprehensive (10 scenarios)
.claude/hooks/test-pretool-hook.sh
```

**Test Coverage:**
1. ✓ Plan agent → WebFetch/WebSearch injected
2. ✓ Bash tool → Pass through (not modified)
3. ✓ Unknown agent → Pass through
4. ✓ desenvolvimento → Multiple tools injected
5. ✓ claude-code-guide → Critical instruction injected

## 🔍 Debugging

### Enable Debug Logging

```bash
export PRETOOL_DEBUG=1
echo '{"tool_name":"Task","tool_input":{"subagent_type":"Plan","prompt":"Test"},"hook_event_name":"PreToolUse"}' | \
  node .claude/hooks/inject-tools-to-agents.js
```

**Debug log location**: `.claude/hooks/lib/pretool-debug.log`

### Common Issues

**Issue**: Hook not modifying prompt
**Cause**: Agent not in mapping
**Solution**: Add agent to `agent-tools-mapping.json`

**Issue**: Wrong tools injected
**Cause**: Cache stale (60s TTL)
**Solution**: Wait 60s or restart Claude Code session

**Issue**: JSON parse error
**Cause**: Invalid mapping syntax
**Solution**: Validate JSON: `python3 -m json.tool agent-tools-mapping.json`

## 📊 Performance

**Execution time**: <5ms (cold start), <0.01ms (cache hit)
**Memory footprint**: ~2KB (mapping file)
**Cache TTL**: 60 seconds (in-memory)

## 🔐 Safety Features

1. **Pass-through on error**: Never blocks tool calls (exit 0 always)
2. **Try/catch everywhere**: All JSON parsing, file I/O wrapped
3. **Validation**: Checks for required fields before modification
4. **Backwards compatible**: Agents not in mapping → unchanged

## 🎓 Adding New Agents

1. **Add to mapping**:
```json
{
  "agents": {
    "my-new-agent": {
      "tools": ["Read", "WebFetch"],
      "description": "My custom agent",
      "critical_instruction": null
    }
  }
}
```

2. **Test it**:
```bash
echo '{"tool_name":"Task","tool_input":{"subagent_type":"my-new-agent","prompt":"Test"},"hook_event_name":"PreToolUse"}' | \
  node .claude/hooks/inject-tools-to-agents.js
```

3. **Expected output**:
```json
{
  "updatedInput": {
    "prompt": "Test\n\n---\n[SYSTEM: Available tools for this task: Read, WebFetch]\n---\n"
  }
}
```

## 🔗 Integration with Legal-Braniac

**Legal-Braniac now reads the same mapping** to enrich agent suggestions:

```javascript
// Before:
"Use Plan agent for this task"

// After (with mapping integration):
"Use Plan agent for this task (tools: WebFetch, WebSearch)"
```

**File**: `.claude/hooks/lib/agent-orchestrator.js`

## 📝 Maintenance Checklist

- [ ] Run tests before committing changes
- [ ] Update mapping when creating new agents
- [ ] Document critical_instruction rationale
- [ ] Clear cache (restart session) after mapping changes
- [ ] Validate JSON syntax after edits

## 🚨 Troubleshooting

### Symptom: "Agent says 'I can't access web'"

1. Check if agent is in mapping:
```bash
cat .claude/hooks/agent-tools-mapping.json | grep -A 3 "Plan"
```

2. Verify hook is enabled:
```bash
cat .claude/settings.json | grep -A 5 "PreToolUse"
```

3. Test hook directly:
```bash
.claude/hooks/test-pretool-simple.sh
```

4. Check debug logs (if enabled):
```bash
tail -20 .claude/hooks/lib/pretool-debug.log
```

## 📚 References

- **Official Docs**: https://docs.anthropic.com/en/docs/claude-code/hooks
- **PreToolUse Spec**: Search "PreToolUse hook modify tool parameters Claude Code"
- **Example**: https://gist.github.com/na0x2c6/32cc9edfc10d505f27a2a12f850029bd (WebFetch validation)

---

**Author**: Claude Code (Sonnet 4.5)
**Maintainer**: PedroGiudice
**Last Updated**: 2025-11-20
