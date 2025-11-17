# Changelog

All notable changes to the Unified Statusline.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2025-11-16

### Added
- **VibbinLogging Integration** - Real-time vibe score (0-100) with contextual emojis
- **Gordon Ramsay Coaching** - Aggressive coaching suggestions from vibe-log analysis
- **Token Usage Tracking** - Display tokens used/total with percentage
- **Session Duration** - Show elapsed time since session start (e.g., "2h15m")
- **Cost Estimates** - Calculate approximate cost based on Claude Sonnet 4.5 pricing
- **Context Percentage** - Estimated context usage (0-100%) based on session duration
- **MCP Server Monitoring** - Display MCP server count and health status
- **Legal-Braniac Orchestration** - Show current task being orchestrated
- **ANSI 256 Color Palette** - Professional dark theme with WCAG AA contrast
- **4 Responsive Modes** - Minimal (< 80 cols), Compact (80-120), Comfortable (120-160), Wide (> 160)
- **Graceful Fallbacks** - Works without vibe-log, MCP, Git, or venv
- **Performance Benchmark** - `--benchmark` flag to measure execution time
- **5-Test Suite** - Automated testing with `test-unified.sh`
- **Architecture Documentation** - Comprehensive technical reference (ARCHITECTURE.md)

### Changed
- **Layout:** 2 lines → 3 lines (added coaching + context line)
- **Performance:** ~80ms → 26ms (67% improvement via optimized data fetching)
- **Color System:** Basic ANSI → ANSI 256 palette (234-254 range)
- **Data Sources:** Filesystem scans → Hybrid (filesystem + vibe-log JSON)
- **Error Handling:** Crash on missing data → Graceful fallback with defaults

### Removed
- **(none - backward compatible with professional-statusline.js)**

### Fixed
- **ANSI Length Calculation** - Strip ANSI codes before measuring string length
- **Column Alignment** - Proper padding with `visibleLength()` helper
- **Stale Data Handling** - Ignore vibe-log data > 5 minutes old
- **Git Timeout** - Added 500ms timeout to prevent hanging on slow repos

### Performance
- **Execution Time:** 26ms (74% faster than 100ms target)
- **Breakdown:**
  - Git subprocess: 10ms (38%)
  - Filesystem scans: 8ms (31%)
  - JSON parsing: 5ms (19%)
  - Formatting: 2ms (8%)
  - Output: 1ms (4%)

### Security
- **Zero Network Requests** - All data read locally (except optional MCP health checks)
- **No Secrets** - No API keys, tokens, or sensitive data in output
- **Filesystem Isolation** - Only reads from project root and `~/.vibe-log/`

---

## [1.0.0] - 2025-11-13

### Added
- **Professional Statusline** - Initial implementation for Legal-Braniac agent
- **Git Integration** - Display branch name and clean/dirty status
- **Python Venv Detection** - Show active virtual environment
- **Hooks Tracking** - Count and status of Claude Code hooks
- **Skills Tracking** - Display total and active skills count
- **Agents Detection** - List available Claude Code agents
- **Liquid Spinner Animation** - Animated loading indicator (later removed for performance)
- **Hook Wrapper System** - Universal tracking for all 7 project hooks
- **Active Agents Detector** - Detect recently executed agents (< 5 min)
- **Emoji Indicators** - Visual status indicators (🧠 🌿 📦 ⚡ ✨ 🦾)
- **ANSI Colors** - Basic color palette (cyan, yellow, green, red)

### Changed
- **(initial release)**

### Performance
- **Execution Time:** ~80ms (within 100ms target but not optimized)

---

## [Unreleased]

### Planned Features
- **JSON Output Mode** - Structured output for integration with tmux/scripts
- **Historical Metrics** - Track vibe score trends over time
- **Alert Thresholds** - Visual warnings when context > 90% or cost > $1
- **Interactive Mode** - Allow toggling sections on/off
- **Custom Themes** - User-defined color palettes
- **Session Comparison** - Compare current session vs average

---

## Version History Summary

| Version | Date       | Key Changes                               | Performance |
|---------|------------|-------------------------------------------|-------------|
| 2.0.0   | 2025-11-16 | Unified (VibbinLogging + 3 lines)         | 26ms        |
| 1.0.0   | 2025-11-13 | Professional statusline (2 lines)         | 80ms        |

---

## Migration Guide

### Upgrading from 1.0.0 to 2.0.0

**Breaking Changes:** None - fully backward compatible.

**New Dependencies (optional):**
- VibbinLogging / vibe-log-cli (for vibe score + coaching)
- MCP server configuration (for MCP monitoring)

**Configuration Changes:**

**Before (1.0.0):**
```json
{
  "statusLine": {
    "type": "command",
    "command": "node .claude/statusline/professional-statusline.js"
  }
}
```

**After (2.0.0):**
```json
{
  "statusLine": {
    "type": "command",
    "command": "node .claude/statusline/unified-statusline.js"
  }
}
```

**Optional: Install vibe-log for full features:**
```bash
npm install -g vibe-log-cli
vibe-log init
vibe-log install-hooks
```

**Behavior Changes:**
- **3 lines instead of 2** - Added coaching + context line
- **Different color scheme** - ANSI 256 instead of basic ANSI
- **More metrics** - Token usage, cost, duration, MCP status

**Rollback:**
To revert to 1.0.0 behavior:
```bash
# Use professional-statusline.js instead
node .claude/statusline/professional-statusline.js

# Or restore from backup
cp unified-statusline.js.backup unified-statusline.js
```

---

## Developer Notes

### 2.0.0 Development Process

**Design Phase (2025-11-15):**
- Analyzed VibbinLogging JSON format
- Designed 3-line layout with 70/30 split
- Created ANSI 256 color palette with WCAG AA compliance
- Defined 4 responsive breakpoints (70, 100, 140, 180 cols)

**Implementation Phase (2025-11-16):**
- Implemented `lib/color-palette-v2.js` (106 lines)
- Implemented `lib/vibe-integration.js` (294 lines)
- Refactored `unified-statusline.js` from professional-statusline.js
- Added `--benchmark` flag and performance optimizations

**Testing Phase (2025-11-16):**
- Created `test-unified.sh` with 5 test cases
- Benchmarked performance: 26ms (target < 100ms)
- Validated responsive modes: 70, 100, 140, 180 cols
- Tested graceful fallbacks: vibe-log, MCP, Git, venv

**Documentation Phase (2025-11-16):**
- Created README.md (~500 lines user documentation)
- Created ARCHITECTURE.md (~600 lines technical reference)
- Created CHANGELOG.md (this file)

**Total Effort:** ~8 hours (design 2h, implementation 3h, testing 1h, documentation 2h)

### Known Issues

**Issue #1: Git Subprocess Latency**
- **Impact:** 10ms execution time (38% of total)
- **Workaround:** Cache Git status for 30 seconds
- **Status:** Won't fix (trade-off: stale data vs performance)

**Issue #2: MCP Health Check Timeout**
- **Impact:** +3ms per server (network latency)
- **Workaround:** Skip health checks with `skipHealthCheck = true`
- **Status:** Configurable (users can disable in `lib/mcp-monitor.js`)

**Issue #3: Unicode Emoji Width Inconsistency**
- **Impact:** Alignment breaks on some terminals (e.g., Windows Terminal)
- **Workaround:** Use monospace emojis or disable emojis
- **Status:** Terminal-dependent, won't fix

### Future Considerations

**Feature Requests:**
- [ ] JSON output mode (`--json` flag)
- [ ] Historical vibe score tracking
- [ ] Configurable alert thresholds
- [ ] Custom color themes (user-defined palettes)
- [ ] Session comparison (current vs average)

**Performance Improvements:**
- [ ] Async/await for parallel data fetching (expected speedup: 50%)
- [ ] Incremental Git status updates (avoid full `git status`)
- [ ] Persistent cache with TTL (avoid filesystem scans)

**Ecosystem Integrations:**
- [ ] Tmux plugin
- [ ] Zsh/Bash prompt integration
- [ ] VS Code extension
- [ ] GitHub Actions badge

---

**Maintained by:** PedroGiudice
**Project:** Claude Code Projetos
**License:** See project root for details
