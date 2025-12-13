# Backup Configuration - Gordon Co-pilot Installation

**Date**: 2025-11-18
**Purpose**: Testing vibe-log Gordon Co-pilot statusline

## Current Configuration (BEFORE vibe-log installation)

### Statusline
```json
{
  "type": "command",
  "command": "cd \"$CLAUDE_PROJECT_DIR\" && bun run .claude/statusline/professional-statusline.js",
  "padding": 0
}
```

**Active statusline**: `professional-statusline.js`
**Hybrid statusline**: `hybrid-powerline-statusline.js` (created but not activated)

### Backups Created
- `.claude/statusline/hybrid-powerline-statusline.js.backup`
- `.claude/settings.json.backup`

### Hooks Active (UserPromptSubmit)
1. `.claude/monitoring/hooks/log_hook.sh UserPromptSubmit`
2. `.claude/monitoring/hooks/detect_agents.sh`
3. `bun run .claude/hooks/hook-wrapper.js .claude/hooks/prompt-enhancer.js`
4. `bun run .claude/hooks/hook-wrapper.js .claude/hooks/context-collector.js`
5. `bun run .claude/hooks/hook-wrapper.js .claude/hooks/vibe-analyze-prompt.js` ⚠️ (broken - calls non-existent command)
6. `.claude/monitoring/hooks/detect_skills.sh`

## What to Restore (if needed)

### Option 1: Restore professional-statusline
```bash
cp .claude/settings.json.backup .claude/settings.json
```

### Option 2: Activate hybrid-powerline (manual)
Edit `.claude/settings.json`:
```json
"command": "cd \"$CLAUDE_PROJECT_DIR\" && bun run .claude/statusline/hybrid-powerline-statusline.js"
```

## Expected Changes from vibe-log installation

1. **Statusline**: Will be replaced with vibe-log Co-pilot statusline
2. **Hooks**: May add/modify UserPromptSubmit hooks for prompt analysis
3. **Files created**: Likely in `~/.vibe-log/` or `.claude/`
4. **Analysis output**: `~/.vibe-log/analysis/` or similar

## Test Plan

1. Install via `npx vibe-log-cli` → "Configure prompt coach status line" → Gordon
2. Test with 3-5 prompts (varied quality)
3. Observe:
   - Statusline feedback (scores, messages)
   - Performance impact
   - Analysis file locations
4. **Decision**: Keep if valuable, restore if not

---

**Created by**: Claude Code (Sonnet 4.5)
**Session**: b4efbe5f-ed86-43ef-b21b-a5c695ee9647
