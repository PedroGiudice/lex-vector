# Unified Statusline

**Professional command center for Claude Code sessions.**

Integrates VibbinLogging metrics with system status monitoring to provide maximum situational awareness during AI-assisted development sessions. Features a precision-instrument aesthetic inspired by professional dark terminals.

![Example Output](screenchot-statusline-15-11-2025.png)

---

## Features

- **Real-time Session Metrics** - Vibe score, coaching suggestions, token usage, and cost estimates
- **System Status Monitoring** - Git status, Python venv, hooks, skills, and agents
- **Professional Dark Theme** - ANSI 256-color palette with WCAG AA contrast ratios
- **Responsive Design** - 4 adaptive layouts (minimal, compact, comfortable, wide)
- **High Performance** - Sub-100ms target (26ms achieved on reference hardware)
- **Graceful Degradation** - Works without vibe-log, MCP, or other optional dependencies

---

## Quick Start

### Installation

The unified statusline is already installed in your Claude Code project at `.claude/statusline/`.

No additional installation required - just run it:

```bash
node .claude/statusline/unified-statusline.js
```

### Example Output

```
🧠 Legal-Braniac: orchestrating  ⚡ Hooks: 10 ok      │ 📦 Python: .venv
🌿 Git: main ✓                   ✨ Skills: 34/37    │
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
🟢 Vibe: 85/100 Add more context examples           │ ⏱ 2h15m
🦾 Agents: 8 available           🔌 MCP: 2 servers ✓ │ 💰 $0.42
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
💡 Gordon: "Ship by FRIDAY or you're fired! Add tests NOW!"
🧠 Context: 68%  │  📊 Tokens: 92k/200k (46%)
```

### Usage

```bash
# Run with default terminal width
node .claude/statusline/unified-statusline.js

# Benchmark performance
node .claude/statusline/unified-statusline.js --benchmark

# Test suite (5 tests)
bash .claude/statusline/test-unified.sh
```

---

## Configuration

### Optional Dependencies

The statusline works standalone but provides enhanced features when these are installed:

#### 1. VibbinLogging (Recommended)

Enables vibe score, coaching suggestions, token tracking, and session duration.

```bash
# Install vibe-log-cli globally
npm install -g vibe-log-cli

# Initialize in Claude Code project
vibe-log init

# Install hooks (optional but recommended)
vibe-log install-hooks
```

**What you get:**
- Real-time prompt quality scoring (0-100)
- Gordon Ramsay-style aggressive coaching
- Token usage tracking (input/output split)
- Session duration and cost estimates

#### 2. MCP Servers (Optional)

Enables MCP server status monitoring.

Configure MCP servers in `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "djen-mcp-server": {
      "command": "node",
      "args": ["/path/to/djen-mcp-server/index.js"]
    }
  }
}
```

**What you get:**
- Server count and health status
- Quick detection of misconfigured servers

#### 3. Legal-Braniac Agent (Optional)

Enables orchestration tracking.

Activate Legal-Braniac agent via `.claude/agents/legal-braniac.md` to see:
- Current task being orchestrated
- Active status indicator (🧠 vs 💤)

---

## Responsive Modes

The statusline adapts to your terminal width:

| Terminal Width | Mode        | Description                                    |
|----------------|-------------|------------------------------------------------|
| < 80 cols      | **Minimal** | Single-line per section, icons only            |
| 80-120 cols    | **Compact** | 2 lines per section, abbreviated labels        |
| 120-160 cols   | **Comfortable** | Full design with 70/30 split               |
| > 160 cols     | **Wide**    | Extended coaching messages                     |

**Example: Minimal mode (70 cols)**

```
🧠: orchestrating │ 🌿: main ✓ │ 📦: ✓
🟢 85 │ 🦾: 8 │ ⏱: 2h15m
💡 Gordon: "Ship by FRIDAY or you're fired!"
```

**Example: Wide mode (180 cols)**

```
🧠 Legal-Braniac: orchestrating legal research workflow  ⚡ Hooks: 10 ok                │ 📦 Python: .venv
🌿 Git: main ✓                                          ✨ Skills: 34/37 (frontend-design, ocr-pro, ...)  │
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
🟢 Vibe: 85/100 Add more context examples for edge cases  │ ⏱ 2h15m
🦾 Agents: 8 available (legal-braniac, documentation-agent, ...)  🔌 MCP: 2 servers ✓  │ 💰 $0.42
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
💡 Gordon: "Ship by FRIDAY or you're fired! Add tests NOW and document your assumptions BEFORE submitting!"
🧠 Context: 68% (estimated based on session duration)  │  📊 Tokens: 92k/200k (46% - input: 72k, output: 20k)
```

---

## Troubleshooting

### "Vibe: not configured"

**Cause:** VibbinLogging (vibe-log-cli) is not installed or hooks are not configured.

**Solution:**
```bash
npm install -g vibe-log-cli
vibe-log init
vibe-log install-hooks
```

**Verification:**
```bash
which vibe-log  # Should return path
ls ~/.vibe-log/  # Should exist
```

### "MCP: not configured"

**Cause:** No MCP servers configured in `~/.claude/mcp.json`.

**Solution:**
1. Create `~/.claude/mcp.json` with your MCP server configuration
2. Verify servers are accessible: `which node` (or relevant command)
3. Restart statusline

**Note:** MCP is optional. Statusline works fine without it.

### "Git: unknown"

**Cause:** Not in a Git repository, or Git is not installed.

**Solution:**
```bash
# Verify Git is installed
which git

# Initialize Git repository if needed
cd /path/to/project
git init
git add .
git commit -m "Initial commit"
```

### "Python: no venv"

**Cause:** No Python virtual environment is active.

**Solution:**
```bash
# Create venv
python -m venv .venv

# Activate venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Verify
which python  # Should point to .venv
```

**Note:** This is a warning, not an error. The statusline will still work.

### Performance Issues (> 100ms)

**Cause:** Slow filesystem access, many hooks, or network MCP servers.

**Diagnosis:**
```bash
node .claude/statusline/unified-statusline.js --benchmark
```

**Solutions:**
1. **Disable MCP health checks** - Edit `lib/mcp-monitor.js` and skip `checkServerHealth()`
2. **Reduce hooks** - Move unused hooks to `.claude/hooks/disabled/`
3. **Cache vibe-log data** - Increase staleness threshold in `lib/vibe-integration.js` (line 55)

**Typical execution times:**
- Reference hardware: 26ms
- Slow HDD: 50-80ms
- Network MCP: 100-200ms (health checks)

### "Skills: none"

**Cause:** No skills directory found at `skills/`.

**Solution:**
```bash
# Verify skills directory exists
ls skills/

# If missing, create it
mkdir -p skills/
```

**Expected structure:**
```
skills/
├── ocr-pro/
│   └── SKILL.md
├── deep-parser/
│   └── SKILL.md
└── frontend-design/
    └── SKILL.md
```

**Note:** Skills without `SKILL.md` are counted but not considered functional.

---

## FAQ

### Q: What is the "Vibe Score"?

**A:** The vibe score (0-100) is a real-time assessment of your prompt quality, provided by VibbinLogging. It analyzes:
- Clarity and specificity
- Context provided
- Actionable instructions
- Example usage

Higher scores = better prompts = better AI outputs.

### Q: Who is Gordon?

**A:** Gordon is the aggressive coaching persona inspired by Gordon Ramsay. When vibe-log detects low-quality prompts, Gordon provides "aggressive coaching" like:

> "Ship by FRIDAY or you're fired! Add tests NOW!"

This is part of the VibbinLogging aesthetic and can be disabled by modifying `lib/vibe-integration.js`.

### Q: Does this send data externally?

**A:** No. All data is local:
- Vibe-log: Reads from `~/.vibe-log/analyzed-prompts/`
- Git status: Executes `git` locally
- Skills: Scans local filesystem
- MCP: Reads local config files

**Zero network requests** except for optional MCP server health checks (which you control).

### Q: Can I customize the colors?

**A:** Yes. Edit `.claude/statusline/lib/color-palette-v2.js`:

```javascript
const PALETTE = {
  // Change these ANSI 256 codes
  bg_primary:   '\x1b[48;5;234m',  // Change 234 to any 0-255
  fg_primary:   '\x1b[38;5;254m',  // Change 254 to any 0-255
  success:      '\x1b[38;5;114m',  // Change 114 to any 0-255
  // ...
};
```

**ANSI 256 color chart:** https://www.ditig.com/256-colors-cheat-sheet

**Design guidelines:**
- Use dark backgrounds (234-240 range)
- Use bright foregrounds (250-255 range)
- Maintain WCAG AA contrast ratios

### Q: How do I integrate this with my statusline?

**A:** The unified statusline is designed to be called from `.claude/hooks/` or command-line.

**Example: SessionStart hook**

```bash
#!/bin/bash
# .claude/hooks/SessionStart.sh

# Run unified statusline
node .claude/statusline/unified-statusline.js
```

**Example: UserPromptSubmit hook**

```bash
#!/bin/bash
# .claude/hooks/UserPromptSubmit.sh

# Run vibe-log analysis (updates ~/.vibe-log/analyzed-prompts/)
vibe-log analyze "$USER_PROMPT"

# Display updated statusline
node .claude/statusline/unified-statusline.js
```

### Q: What's the performance overhead?

**A:** Minimal. Reference measurements:
- **Execution time:** 26ms (74% faster than 100ms target)
- **CPU usage:** < 0.1s total CPU time
- **Memory:** ~20MB Node.js process (short-lived)
- **Disk I/O:** ~10 file reads (all cached)

**Impact on Claude Code sessions:** Negligible. The statusline completes before you finish reading the output.

### Q: Can I use this outside Claude Code?

**A:** Yes, but with limitations. The statusline is designed for Claude Code projects with:
- `.claude/` directory structure
- `skills/` directory
- `agentes/` directory (optional)

**Standalone usage:**
```bash
# Works anywhere with Node.js installed
cd /path/to/any/project
node /path/to/unified-statusline.js

# Will show minimal info without Claude Code structure
```

**Expected behavior:**
- Git status: ✓ Works
- Python venv: ✓ Works
- Vibe score: ✓ Works (if vibe-log installed)
- Skills/hooks/agents: ✗ Requires `.claude/` structure

---

## Integration Examples

### Example 1: Pre-commit Hook

Display statusline before every Git commit:

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "═══ SESSION STATUS ═══"
node .claude/statusline/unified-statusline.js
echo ""
echo "Proceeding with commit..."
```

### Example 2: Tmux Status Bar

Integrate into tmux status bar (requires JSON output mode):

```bash
# .tmux.conf
set -g status-right "#(node ~/.claude/statusline/unified-statusline.js --json | jq -r '.vibe_score')"
```

**Note:** JSON output mode not yet implemented. Feature request welcome.

### Example 3: VS Code Task

Run as VS Code task:

```json
{
  "label": "Claude Statusline",
  "type": "shell",
  "command": "node .claude/statusline/unified-statusline.js",
  "presentation": {
    "echo": true,
    "reveal": "always",
    "panel": "new"
  }
}
```

---

## Credits

**Design:** frontend-design skill (Fase 1.5 - Precision Instrument aesthetic)

**Architecture:** Unified from:
- `professional-statusline.js` (system monitoring)
- VibbinLogging integration (vibe score + coaching)

**Performance:** Optimized via test-driven development (5-test suite)

**Color Palette:** ANSI 256 with WCAG AA compliance

---

## License

Part of Claude Code Projetos repository.

See project root for license details.

---

## Support

**Issues:** Report via project repository issues tracker

**Documentation:** See `ARCHITECTURE.md` for technical details

**Contributing:** See project `CONTRIBUTING.md` for guidelines

**Quick links:**
- [Architecture Documentation](ARCHITECTURE.md)
- [Changelog](CHANGELOG.md)
- [Test Suite](test-unified.sh)
- [Color Palette Reference](lib/color-palette-v2.js)
- [Legacy README](README-LEGACY.md) - Previous statusline system documentation
