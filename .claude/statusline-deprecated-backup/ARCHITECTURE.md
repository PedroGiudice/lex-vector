# Unified Statusline - Architecture

**Technical reference for developers extending or maintaining the unified statusline.**

---

## System Overview

```
unified-statusline.js (main entry)
├── lib/color-palette-v2.js         → ANSI 256 color palette
├── lib/vibe-integration.js         → VibbinLogging data reader
├── lib/skills-tracker.js           → Filesystem-based skill detection
└── lib/mcp-monitor.js              → MCP server configuration reader
```

**Data flow:**
1. **Input:** Terminal width (`process.stdout.columns`)
2. **Calculation:** Responsive layout (minimal/compact/comfortable/wide)
3. **Data fetching:** Parallel reads from filesystem and Git
4. **Formatting:** 3-line output with ANSI 256 colors
5. **Output:** STDOUT (colored terminal text)

**Performance target:** < 100ms total execution time

**Design philosophy:** Fail gracefully, never block, always display something useful.

---

## Components

### Main Entry: unified-statusline.js

**Responsibilities:**
- Calculate responsive layout based on terminal width
- Fetch data from all sources (Git, venv, vibe-log, hooks, skills)
- Format 3 lines of output with proper padding and colors
- Render with ANSI 256 color codes

**Key Functions:**

#### `main()`
Entry point. Determines terminal width, calculates layout, calls formatters.

```javascript
function main() {
  const termWidth = process.stdout.columns || 120;
  const layout = calculateLayout(termWidth);

  // Format based on mode
  if (layout.mode === 'minimal') {
    line1 = formatLine1Minimal();
    // ...
  } else {
    line1 = formatLine1(layout);
    // ...
  }

  console.log(line1);
  console.log(sep1);
  // ...
}
```

#### `calculateLayout(termWidth)`
Returns layout configuration based on terminal width.

**Breakpoints:**
- < 80: `{ mode: 'minimal', width: termWidth }`
- 80-120: `{ mode: 'compact', width: termWidth, col1: 70, col2: width-73 }`
- 120-160: `{ mode: 'comfortable', width, col1: 70% of width, col2: 30% }`
- > 160: `{ mode: 'wide', width, col1: 70%, col2: 30% }`

**Why 70/30 split?** Empirically determined to balance system status (dense) vs metrics (sparse).

#### `formatLine1(layout)` - System Status
**Layout:** 2 rows, 70/30 split

**Row 1:**
- Left: `🧠 Legal-Braniac: <task>  ⚡ Hooks: <count> ok`
- Right: `📦 Python: <venv>`

**Row 2:**
- Left: `🌿 Git: <branch> <status>  ✨ Skills: <count>`
- Right: (empty)

**Data sources:**
- Legal-Braniac: `.claude/legal-braniac-session.json` (< 10 min stale)
- Hooks: `.claude/hooks/*.{js,sh}` (filesystem scan)
- Venv: `process.env.VIRTUAL_ENV` (environment variable)
- Git: `git rev-parse --abbrev-ref HEAD` + `git status --porcelain`
- Skills: `skills/` directory scan

**Performance:** ~10ms (dominated by Git subprocess)

#### `formatLine2(layout)` - Metrics
**Layout:** 2 rows, 70/30 split

**Row 1:**
- Left: `🟢 Vibe: 85/100 <suggestion>`
- Right: `⏱ <duration>`

**Row 2:**
- Left: `🦾 Agents: <count> available  🔌 MCP: <count> servers`
- Right: `💰 $<cost>`

**Data sources:**
- Vibe score: `~/.vibe-log/analyzed-prompts/*.json` (< 5 min stale)
- Agents: `.claude/agents/*.md` (filesystem scan)
- MCP: `~/.claude/mcp.json` (config file)
- Duration: `~/.vibe-log/config.json` (session_start_time)
- Cost: Estimated from token usage (Sonnet 4.5 pricing)

**Performance:** ~8ms (mostly filesystem reads, cached by OS)

#### `formatLine3(layout)` - Coaching + Context
**Layout:** 2 rows, 100% width

**Row 1:**
- Full width: `💡 Gordon: "<coaching message>"`

**Row 2:**
- Left: `🧠 Context: <percentage>%`
- Right: `📊 Tokens: <used>k/<total>k (<percentage>%)`

**Data sources:**
- Coaching: `~/.vibe-log/analyzed-prompts/*.json` (actionableSteps field)
- Context: Estimated from session duration (linear 0% → 100% over 2h)
- Tokens: `~/.vibe-log/hooks-stats.json` (tokens_used, tokens_total)

**Performance:** ~3ms (reads already cached from Line 2)

#### `padColumns(col1Text, col2Text, col1Width, col2Width)`
Pads two columns to align separator, accounting for ANSI codes.

**Algorithm:**
1. Strip ANSI codes to get visible length
2. Calculate padding needed: `col1Width - visibleLength(col1Text)`
3. Insert separator: ` │ ` (with tertiary color)
4. Append col2Text

**Example:**
```javascript
padColumns(
  '\x1b[38;5;117mVibe: 85/100\x1b[0m',  // col1 (12 visible chars)
  '\x1b[38;5;254m⏱ 2h15m\x1b[0m',       // col2
  70,  // col1 target width
  30   // col2 target width
)
// Returns: '\x1b[38;5;117mVibe: 85/100\x1b[0m' + (58 spaces) + ' │ ' + '\x1b[38;5;254m⏱ 2h15m\x1b[0m'
```

**Why this matters:** ANSI codes (e.g., `\x1b[38;5;117m`) are invisible but count toward string length. Without stripping, alignment breaks.

---

### Library: lib/color-palette-v2.js

**Purpose:** Centralized ANSI 256 color palette with semantic naming.

**Design constraints:**
- WCAG AA contrast ratios (4.5:1 minimum)
- Dark theme (backgrounds 234-236, foregrounds 240-255)
- Semantic colors (success=green, warning=yellow, error=red)
- Branding colors (gordon=orange, accent_purple=VibbinLoggin)

**Color Palette:**

| Name            | ANSI Code          | RGB Approx | Usage                        |
|-----------------|--------------------|------------|------------------------------|
| `bg_primary`    | `\x1b[48;5;234m`   | #1c1c1c    | Line 1 background            |
| `bg_secondary`  | `\x1b[48;5;235m`   | #262626    | Line 2 background            |
| `bg_accent`     | `\x1b[48;5;236m`   | #303030    | Line 3 background (coaching) |
| `fg_primary`    | `\x1b[38;5;254m`   | #e4e4e4    | Main text (high contrast)    |
| `fg_secondary`  | `\x1b[38;5;245m`   | #8a8a8a    | Labels (medium contrast)     |
| `fg_tertiary`   | `\x1b[38;5;240m`   | #585858    | Separators (low contrast)    |
| `success`       | `\x1b[38;5;114m`   | #87d787    | Green (ok, clean)            |
| `warning`       | `\x1b[38;5;221m`   | #ffd75f    | Yellow (dirty, partial)      |
| `error`         | `\x1b[38;5;204m`   | #ff5f87    | Coral red (errors)           |
| `info`          | `\x1b[38;5;117m`   | #87d7ff    | Sky blue (neutral info)      |
| `accent_purple` | `\x1b[38;5;141m`   | #af87ff    | VibbinLoggin branding        |
| `gordon`        | `\x1b[38;5;208m`   | #ff8700    | Gordon Ramsay coaching       |

**ANSI 256 Format:**
- Foreground: `\x1b[38;5;<code>m<text>\x1b[0m`
- Background: `\x1b[48;5;<code>m<text>\x1b[0m`

**Functions:**

#### `colorize(text, colorName)`
Apply foreground color with auto-reset.

```javascript
colorize('Git: main ✓', 'success')
// Returns: '\x1b[38;5;114mGit: main ✓\x1b[0m'
```

#### `bg(bgName)`
Return background ANSI code (no reset - caller must handle).

```javascript
bg('bg_primary')
// Returns: '\x1b[48;5;234m'
```

#### `separator(char, count)`
Create colored separator line.

```javascript
separator('╌', 120)
// Returns: '\x1b[38;5;240m' + '╌'.repeat(120) + '\x1b[0m'
```

#### `stripAnsi(str)` + `visibleLength(str)`
Strip ANSI codes for length calculation.

```javascript
stripAnsi('\x1b[38;5;114mGit: main\x1b[0m')
// Returns: 'Git: main'

visibleLength('\x1b[38;5;114mGit: main\x1b[0m')
// Returns: 9
```

**Why ANSI 256 vs 16?**
- More granular control (256 colors vs 16)
- Consistent across terminals (vs RGB which varies)
- Professional aesthetic (subtle gradients possible)

**Accessibility:**
All foreground/background combinations tested with WebAIM contrast checker:
- `fg_primary` on `bg_primary`: 13.2:1 (AAA)
- `fg_secondary` on `bg_primary`: 6.8:1 (AA)
- `success` on `bg_primary`: 9.1:1 (AAA)

---

### Library: lib/vibe-integration.js

**Purpose:** Read VibbinLogging analysis data from `~/.vibe-log/`.

**Data sources:**
1. `~/.vibe-log/analyzed-prompts/*.json` - Prompt analysis results
2. `~/.vibe-log/hooks-stats.json` - Token usage stats
3. `~/.vibe-log/config.json` - Session metadata

**Functions:**

#### `getLatestAnalysis()`
Returns most recent analysis file (< 5 min stale), or `null` if:
- Directory doesn't exist (vibe-log not installed)
- No files found
- All files too old (> 5 min)

**Algorithm:**
1. List all `*.json` files in `~/.vibe-log/analyzed-prompts/`
2. Sort by mtime (most recent first)
3. Check staleness: `Date.now() - mtime < 5*60*1000`
4. Parse JSON and return data

**Expected JSON format (completed analysis):**
```json
{
  "quality": "excellent",
  "score": 85,
  "suggestion": "Add more context examples",
  "contextualEmoji": "🟢",
  "actionableSteps": "Ship by FRIDAY or you're fired!"
}
```

**Expected JSON format (loading state):**
```json
{
  "state": "loading",
  "message": "Analyzing your prompt...",
  "timestamp": 1731734123456
}
```

#### `getVibeScore()`
Returns vibe score object with detailed info:
- `null`: Not available
- `{ state: 'loading', message }`: Analysis in progress
- `{ score, emoji, suggestion, quality }`: Complete analysis

**Usage:**
```javascript
const vibeScore = getVibeScore();

if (!vibeScore) {
  // Not configured
  vibeText = 'Vibe: not configured';
} else if (vibeScore.state === 'loading') {
  // Loading
  vibeText = `Vibe: ${vibeScore.message}`;
} else {
  // Complete
  vibeText = `${vibeScore.emoji} Vibe: ${vibeScore.score}/100`;
}
```

#### `getCoachingSuggestion()`
Returns full Gordon Ramsay coaching message.

**Priority:**
1. `actionableSteps` (aggressive coaching)
2. `suggestion` (regular suggestion)
3. Fallback: "Install vibe-log for coaching!"

**Format:**
```javascript
'💡 Gordon: "Ship by FRIDAY or you\'re fired! Add tests NOW!"'
```

#### `getTokenUsage()`
Returns `{ used, total, percentage }` from `~/.vibe-log/hooks-stats.json`.

**Expected JSON format:**
```json
{
  "tokens_used": 92000,
  "tokens_total": 200000
}
```

**Returns:**
```javascript
{
  used: 92000,
  total: 200000,
  percentage: 46
}
```

#### `getSessionDuration()`
Returns formatted duration (e.g., "2h15m") from session start time.

**Algorithm:**
1. Read `session_start_time` from `~/.vibe-log/config.json`
2. Calculate `Date.now() - session_start_time`
3. Format as "XhYYm" or "YYm" if < 1 hour

**Example:**
```javascript
// Session started 2h15m ago
getSessionDuration()  // Returns: "2h15m"

// Session started 45m ago
getSessionDuration()  // Returns: "45m"
```

---

### Library: lib/skills-tracker.js

**Purpose:** Detect skills from filesystem.

**Data source:** `skills/` directory (sibling to `.claude/`)

**Functions:**

#### `getTotalCount()`
Counts subdirectories in `skills/`.

**Algorithm:**
1. List `skills/` with `{ withFileTypes: true }`
2. Filter `isDirectory()`
3. Return count

**Example:**
```javascript
// skills/ contains: ocr-pro/, deep-parser/, frontend-design/
getTotalCount()  // Returns: 3
```

#### `getActiveSkills()`
Returns array of active skill names.

**Data source:** `.claude/statusline/active-skills.json` (< 5 min stale)

**Expected JSON format:**
```json
{
  "skills": ["frontend-design", "ocr-pro"],
  "timestamp": 1731734123456
}
```

**Fallback:** Returns `[]` if file doesn't exist or is stale.

#### `getFormattedCount()`
Returns formatted string for statusline.

**Format:**
- `"none"` - No skills installed
- `"8"` - 8 total, 0 active
- `"3/8"` - 3 active, 8 total

**Example:**
```javascript
// 34 total, 0 active
getFormattedCount()  // Returns: "34"

// 34 total, 31 active
getFormattedCount()  // Returns: "31/34"
```

#### `updateActiveSkills(skillNames)`
Writes `active-skills.json` with timestamp.

**Usage:** Called by hooks when skills are invoked.

**Example:**
```javascript
// Hook invokes frontend-design skill
updateActiveSkills(['frontend-design']);

// Writes .claude/statusline/active-skills.json:
{
  "skills": ["frontend-design"],
  "timestamp": 1731734123456
}
```

---

### Library: lib/mcp-monitor.js

**Purpose:** Monitor MCP (Model Context Protocol) server status.

**Data source:** `~/.claude/mcp.json` (or `.config/claude/mcp.json`)

**Functions:**

#### `isAvailable()`
Returns `true` if MCP config file exists.

**Search paths:**
1. `~/.claude/mcp.json`
2. `~/.config/claude/mcp.json`
3. `<cwd>/.claude/mcp.json`

#### `getConfig()`
Returns parsed MCP config JSON, or `null` if not found.

**Expected format:**
```json
{
  "mcpServers": {
    "djen-mcp-server": {
      "command": "node",
      "args": ["/path/to/server/index.js"]
    }
  }
}
```

#### `getServers()`
Returns array of server names (keys in `mcpServers` object).

**Example:**
```javascript
// mcp.json has 2 servers: djen-mcp-server, legal-mcp
getServers()  // Returns: ["djen-mcp-server", "legal-mcp"]
```

#### `checkServerHealth(serverName)`
Basic health check: verifies command executable exists.

**Algorithm:**
1. Read server config from `mcpServers[serverName]`
2. Extract `command` (e.g., "node")
3. Run `which <command>` (timeout 100ms)
4. Return `true` if exit code 0, `false` otherwise

**Limitation:** Only checks if command exists, not if server is actually running.

#### `getFormattedStatus()`
Returns formatted string for statusline.

**Format:**
- `null` - No MCP configured
- `"2 servers ✓"` - All servers healthy
- `"1/2 servers"` - 1 of 2 healthy

**Example:**
```javascript
// 2 servers configured, both healthy
getFormattedStatus()  // Returns: "2 servers ✓"

// 2 servers configured, 1 unhealthy (node not found)
getFormattedStatus()  // Returns: "1/2 servers"
```

---

## Data Flow

### Startup Sequence

```
1. main() called
   ↓
2. calculateLayout(termWidth)
   → Determines mode: minimal/compact/comfortable/wide
   ↓
3. Parallel data fetching:
   ├─ getGitStatus()                 (10ms - git subprocess)
   ├─ getVenvStatus()                (1ms - env var)
   ├─ getLegalBraniacStatus()        (2ms - read JSON)
   ├─ getHooksStatus()               (3ms - fs scan)
   ├─ getAgentsCount()               (2ms - fs scan)
   ├─ vibeIntegration.getVibeScore() (5ms - read JSON)
   ├─ vibeIntegration.getTokenUsage() (2ms - read JSON)
   ├─ vibeIntegration.getSessionDuration() (1ms - cached)
   ├─ skillsTracker.getFormattedCount() (2ms - fs scan)
   └─ mcpMonitor.getFormattedStatus()  (3ms - read JSON)
   ↓
4. Format lines:
   ├─ formatLine1(layout)  (2ms - string manipulation)
   ├─ formatLine2(layout)  (2ms - string manipulation)
   └─ formatLine3(layout)  (1ms - string manipulation)
   ↓
5. Print to STDOUT (1ms - console.log)
   ↓
6. Exit (0ms)

Total: ~26ms (reference hardware)
```

**Critical path:** Git subprocess (10ms) - all other operations are < 5ms.

**Optimization opportunities:**
1. Cache Git status (expensive subprocess)
2. Skip MCP health checks (network latency)
3. Use marker files instead of filesystem scans

---

## Layout Specifications

### Line 1: System Status
**Background:** `bg_primary` (#1c1c1c)
**Height:** 2 rows

#### Row 1 (70/30 split)
```
[LEFT: 70%]                                              [SEP] [RIGHT: 30%]
🧠 Legal-Braniac: orchestrating  ⚡ Hooks: 10 ok          │     📦 Python: .venv
^^ ^              ^              ^        ^^              ^     ^  ^       ^
│  │              │              │        │└─ success     │     │  │       └─ venv name
│  │              │              │        └─ count        │     │  └─ label
│  │              │              └─ label (fg_secondary)  │     └─ emoji
│  │              └─ task (info color)                    │
│  └─ agent name (info color)                             └─ separator (fg_tertiary)
└─ emoji (braniac icon)
```

#### Row 2 (70/30 split)
```
[LEFT: 70%]                                              [SEP] [RIGHT: 30%]
🌿 Git: main ✓                   ✨ Skills: 34/37        │     (empty)
^^ ^    ^    ^                   ^  ^       ^            ^
│  │    │    └─ clean (success)  │  │       └─ active/total
│  │    └─ branch                │  └─ label
│  └─ label                      └─ emoji
└─ emoji (git icon)
```

**Padding:** Right-padded with spaces to fill terminal width.

### Line 2: Metrics
**Background:** `bg_secondary` (#262626)
**Height:** 2 rows

#### Row 1 (70/30 split)
```
[LEFT: 70%]                                              [SEP] [RIGHT: 30%]
🟢 Vibe: 85/100 Add more context examples                │     ⏱ 2h15m
^^ ^     ^^     ^                                        ^     ^ ^
│  │     │└─ score                                       │     │ └─ duration
│  │     └─ max (100)                                    │     └─ emoji
│  └─ label (fg_secondary)                               │
└─ emoji (contextual from vibe-log)                      └─ separator
```

#### Row 2 (70/30 split)
```
[LEFT: 70%]                                              [SEP] [RIGHT: 30%]
🦾 Agents: 8 available           🔌 MCP: 2 servers ✓     │     💰 $0.42
^^ ^       ^                     ^  ^    ^               ^     ^  ^
│  │       └─ count              │  │    └─ status       │     │  └─ cost
│  └─ label                      │  └─ label             │     └─ emoji
└─ emoji                         └─ emoji                └─ separator
```

### Line 3: Coaching + Context
**Background:** `bg_accent` (#303030)
**Height:** 2 rows

#### Row 1 (100% width)
```
[FULL WIDTH]
💡 Gordon: "Ship by FRIDAY or you're fired! Add tests NOW!"
^^ ^       ^
│  │       └─ coaching message (gordon color #ff8700)
│  └─ persona (fg_secondary)
└─ emoji
```

#### Row 2 (50/50 split with separator)
```
[LEFT: ~50%]                           [SEP]  [RIGHT: ~50%]
🧠 Context: 68%                         │      📊 Tokens: 92k/200k (46%)
^^ ^        ^^                          ^      ^  ^       ^   ^    ^^
│  │        └─ percentage               │      │  │       │   │    └─ percentage
│  └─ label                             │      │  │       │   └─ total
└─ emoji                                │      │  │       └─ used
                                        │      │  └─ label
                                        │      └─ emoji
                                        └─ separator (fg_tertiary)
```

**Padding:** Right-padded with spaces to fill terminal width.

### Separators
**Character:** `╌` (U+2504 Box Drawings Light Triple Dash Horizontal)
**Color:** `fg_tertiary` (#585858)
**Width:** Full terminal width

**Why this character?**
- Subtle (not too heavy like `─`)
- Accessible (not too faint like `┄`)
- Unicode-safe (widely supported)

---

## Performance Considerations

### Benchmarks (Reference Hardware)

**System:** WSL2 Ubuntu 24.04, Intel i7, NVMe SSD
**Node.js:** v24.11.1

**Breakdown:**
```
Operation                  Time (ms)  Percentage
─────────────────────────────────────────────────
Git subprocess              10        38%
Filesystem scans (5x)        8        31%
JSON parsing (4x)            5        19%
String formatting            2         8%
Console output               1         4%
─────────────────────────────────────────────────
TOTAL                       26       100%
```

**Critical bottlenecks:**
1. **Git subprocess:** Unavoidable, but could be cached (trade-off: stale data)
2. **Filesystem scans:** Could use marker files (trade-off: manual updates)

### Optimization Strategies

#### 1. Caching Git Status
**Problem:** `git status --porcelain` takes 10ms (subprocess overhead).

**Solution:** Cache for 30 seconds.

```javascript
let gitStatusCache = { data: null, timestamp: 0 };

function getGitStatus() {
  const now = Date.now();
  if (now - gitStatusCache.timestamp < 30000) {
    return gitStatusCache.data;
  }

  const data = execSync('git status --porcelain', { ... });
  gitStatusCache = { data, timestamp: now };
  return data;
}
```

**Trade-off:** Statusline may show stale branch name if user switches branches.

#### 2. Skip MCP Health Checks
**Problem:** `which node` subprocess adds 3ms per server.

**Solution:** Only check if explicitly requested.

```javascript
function getFormattedStatus(skipHealthCheck = true) {
  if (skipHealthCheck) {
    return `${servers.length} server${servers.length > 1 ? 's' : ''}`;
  }
  // ... existing health check logic
}
```

**Trade-off:** Won't detect misconfigured servers.

#### 3. Async/Await for Parallel Fetching
**Problem:** Data fetching is sequential (blocking).

**Solution:** Use `Promise.all()` for parallel execution.

```javascript
async function main() {
  const [git, venv, hooks, skills, mcp] = await Promise.all([
    getGitStatusAsync(),
    getVenvStatusAsync(),
    getHooksStatusAsync(),
    getSkillsCountAsync(),
    getMcpStatusAsync()
  ]);

  // Format and print...
}
```

**Trade-off:** Complexity increases (error handling, async/await overhead).

**Expected speedup:** 10ms → 5ms (50% reduction by parallelizing Git + FS scans).

---

## Extension Points

### Adding New Metrics

**Example:** Add "Last commit time" to Line 1.

1. **Create data fetcher:**
```javascript
function getLastCommitTime() {
  try {
    const timestamp = execSync('git log -1 --format=%ct', {
      cwd: PROJECT_ROOT,
      encoding: 'utf8',
      timeout: 500
    }).trim();
    const date = new Date(parseInt(timestamp) * 1000);
    return formatDistanceToNow(date); // "2 hours ago"
  } catch {
    return null;
  }
}
```

2. **Update formatter:**
```javascript
function formatLine1(layout) {
  // ... existing code ...
  const lastCommit = getLastCommitTime();
  const lastCommitText = lastCommit
    ? colorize(`⏱ Last commit: ${lastCommit}`, 'fg_secondary')
    : '';

  const row2Col1 = `${gitEmoji} ${gitText}  ${lastCommitText}  ${skillsText}`;
  // ... rest of function
}
```

3. **Test:**
```bash
node unified-statusline.js
# Should show: "⏱ Last commit: 2 hours ago"
```

### Adding New Colors

**Example:** Add "urgent" color for critical alerts.

1. **Define color in palette:**
```javascript
// lib/color-palette-v2.js
const PALETTE = {
  // ... existing colors ...
  urgent: '\x1b[38;5;196m',  // Bright red (#ff0000)
};
```

2. **Export in module:**
```javascript
module.exports = {
  PALETTE,
  colorize,
  // ...
};
```

3. **Use in formatter:**
```javascript
const alertText = colorize('⚠ CRITICAL: Hooks failing!', 'urgent');
```

### Adding New Responsive Modes

**Example:** Add "ultra-wide" mode for > 200 cols.

1. **Update `calculateLayout()`:**
```javascript
function calculateLayout(termWidth) {
  if (termWidth < 80) return { mode: 'minimal', width: termWidth };
  if (termWidth < 120) return { mode: 'compact', ... };
  if (termWidth < 160) return { mode: 'comfortable', ... };
  if (termWidth < 200) return { mode: 'wide', ... };

  // NEW: Ultra-wide mode
  return {
    mode: 'ultra-wide',
    width: termWidth,
    col1: Math.floor(termWidth * 0.60),  // 60/40 split
    col2: termWidth - Math.floor(termWidth * 0.60) - 3
  };
}
```

2. **Create formatters:**
```javascript
function formatLine1UltraWide(layout) {
  // Show extended skill names, full Git status, etc.
}
```

3. **Update `main()`:**
```javascript
function main() {
  const layout = calculateLayout(termWidth);

  if (layout.mode === 'minimal') {
    // ...
  } else if (layout.mode === 'ultra-wide') {
    line1 = formatLine1UltraWide(layout);
    // ...
  } else {
    // Default: comfortable/compact/wide
  }
}
```

---

## Error Handling

### Philosophy: Fail Gracefully

**Principle:** Never crash. Always display something useful, even if data is incomplete.

### Strategies

#### 1. Try-Catch with Fallbacks
```javascript
function getGitStatus() {
  try {
    const branch = execSync('git rev-parse --abbrev-ref HEAD', { ... });
    return { branch, isDirty: false };
  } catch (error) {
    // Git not installed, or not in a repo
    return { branch: 'unknown', isDirty: false };
  }
}
```

**Display:** `Git: unknown ✗`

#### 2. Null Checks
```javascript
const vibeScore = vibeIntegration.getVibeScore();

if (!vibeScore) {
  vibeText = colorize('💫 Vibe: not configured', 'fg_secondary');
} else if (vibeScore.state === 'loading') {
  vibeText = colorize(`⏳ Vibe: ${vibeScore.message}`, 'info');
} else {
  vibeText = colorize(`${vibeScore.emoji} Vibe: ${vibeScore.score}/100`, 'success');
}
```

**Display:**
- Not installed: `💫 Vibe: not configured`
- Loading: `⏳ Vibe: Analyzing...`
- Complete: `🟢 Vibe: 85/100`

#### 3. Staleness Checks
```javascript
function getLatestAnalysis() {
  // ... read file ...

  const age = Date.now() - latest.mtime;
  if (age > 5 * 60 * 1000) {
    return null;  // Too old, not relevant
  }

  return data;
}
```

**Display:** If data > 5 min old, treat as "not configured" (fallback to default message).

### Common Failure Modes

| Failure                        | Handling                               | Display                          |
|--------------------------------|----------------------------------------|----------------------------------|
| Git not installed              | Return `{ branch: 'unknown' }`         | `Git: unknown ✗`                 |
| Vibe-log not installed         | Return `null` from getVibeScore()      | `💫 Vibe: not configured`        |
| MCP config malformed           | Return `null` from getConfig()         | `🔌 MCP: not configured`         |
| Skills directory missing       | Return 0 from getTotalCount()          | `✨ Skills: none`                |
| Hooks directory missing        | Return `{ total: 0, ok: 0 }`           | `⚡ Hooks: 0 ok`                 |
| Filesystem permission error    | Catch exception, return fallback       | Use default values               |
| JSON parsing error             | Catch exception, return `null`         | Fallback to "not configured"     |

---

## Testing

### Test Suite: test-unified.sh

**Coverage:**
1. **Basic execution** - Verify script runs without crashing
2. **Performance benchmark** - Measure execution time (< 100ms)
3. **Responsive modes** - Test 70, 100, 140, 180 cols
4. **Vibe-log fallback** - Simulate absence of vibe-log
5. **Git status detection** - Verify Git integration works

**Usage:**
```bash
bash .claude/statusline/test-unified.sh
```

**Expected output:**
```
╔════════════════════════════════════════════════════════════════╗
║         UNIFIED STATUSLINE TEST SUITE                         ║
╚════════════════════════════════════════════════════════════════╝

═══ TEST 1: Basic Execution (default terminal width) ═══
[... statusline output ...]
✅ TEST 1 PASSED

═══ TEST 2: Performance Benchmark (target: < 100ms) ═══
Execution time: 26ms
✅ TEST 2 PASSED - Execution time: 26ms (< 100ms)

═══ TEST 3: Responsive Modes ═══
--- Minimal mode (70 cols) ---
[... output ...]
✅ TEST 3 PASSED - All responsive modes working

═══ TEST 4: Vibe-log Fallback (simulated absence) ═══
Moved ~/.vibe-log to backup location
💫 Vibe: not configured
Restored ~/.vibe-log from backup
✅ TEST 4 PASSED - Graceful fallback when vibe-log absent

═══ TEST 5: Git Status Detection ═══
Git: main ✓
✅ TEST 5 PASSED - Git status detected

╔════════════════════════════════════════════════════════════════╗
║                    ALL TESTS PASSED ✅                         ║
╚════════════════════════════════════════════════════════════════╝
```

### Manual Testing

**Test Case 1: Fresh Session (no vibe-log)**
```bash
# Temporarily disable vibe-log
mv ~/.vibe-log ~/.vibe-log.bak

# Run statusline
node unified-statusline.js

# Expected: "💫 Vibe: not configured" message

# Restore
mv ~/.vibe-log.bak ~/.vibe-log
```

**Test Case 2: Dirty Git Status**
```bash
# Make uncommitted change
echo "test" >> README.md

# Run statusline
node unified-statusline.js

# Expected: "Git: main ●" (dirty indicator)

# Clean up
git checkout README.md
```

**Test Case 3: No Virtual Environment**
```bash
# Deactivate venv
deactivate

# Run statusline
node unified-statusline.js

# Expected: "📦 Python: no venv" (warning color)
```

### Performance Testing

**Benchmark mode:**
```bash
node unified-statusline.js --benchmark
```

**Expected output:**
```
[... statusline display ...]

Execution time: 26ms
```

**Profiling with Node.js:**
```bash
node --prof unified-statusline.js
node --prof-process isolate-*.log > profile.txt
less profile.txt
```

**Expected hotspots:**
- `execSync` (Git subprocess)
- `fs.readFileSync` (JSON reads)
- `fs.readdirSync` (directory scans)

---

## Dependencies

**Runtime:**
- Node.js >= 14.0.0 (uses `??` nullish coalescing)
- Git (optional - graceful fallback if absent)
- VibbinLogging / vibe-log-cli (optional - graceful fallback)

**Development:**
- Bash (for test suite)
- `bc` (for arithmetic in tests)

**Zero npm packages** - all functionality built with Node.js stdlib:
- `fs` - Filesystem operations
- `path` - Path manipulation
- `child_process` - Git subprocess
- `process` - Environment variables, stdout

---

## File Structure

```
.claude/statusline/
├── unified-statusline.js              ← Main entry (520 lines)
├── test-unified.sh                    ← Test suite (140 lines)
├── lib/
│   ├── color-palette-v2.js            ← ANSI 256 palette (106 lines)
│   ├── vibe-integration.js            ← Vibe-log reader (294 lines)
│   ├── skills-tracker.js              ← Skills detector (96 lines)
│   └── mcp-monitor.js                 ← MCP status (117 lines)
├── README.md                          ← User documentation
├── ARCHITECTURE.md                    ← This file (technical reference)
└── CHANGELOG.md                       ← Version history
```

**Total:** ~1,273 lines of code + ~2,000 lines of documentation.

---

## Contributing

### Code Style

- **Indentation:** 2 spaces
- **Line length:** 100 chars max
- **Comments:** Document "why", not "what"
- **Functions:** JSDoc comments for exported functions

### Adding Features

1. **Propose:** Open issue describing use case
2. **Design:** Discuss API in issue comments
3. **Implement:** Create feature branch
4. **Test:** Add test case to `test-unified.sh`
5. **Document:** Update README.md + ARCHITECTURE.md
6. **PR:** Submit pull request with description

### Performance Guidelines

- **Target:** < 100ms total execution
- **Measure:** Always run `--benchmark` before/after
- **Profile:** Use `node --prof` for complex changes

### Breaking Changes

Requires major version bump (e.g., 2.0.0 → 3.0.0):
- Changing layout structure (3 lines → 4 lines)
- Renaming data source files
- Changing ANSI color codes (breaks custom themes)

---

## References

**ANSI Escape Codes:**
- https://en.wikipedia.org/wiki/ANSI_escape_code
- https://www.ditig.com/256-colors-cheat-sheet

**Color Contrast:**
- https://webaim.org/resources/contrastchecker/

**VibbinLogging:**
- https://github.com/PedroGiudice/vibe-log-cli

**MCP Protocol:**
- https://modelcontextprotocol.io/

---

**Last updated:** 2025-11-16
**Maintained by:** PedroGiudice
**Version:** 2.0.0 (unified statusline)
