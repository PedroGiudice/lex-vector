# Real-Time Claude Code Context Window Monitoring in tmux

Precise real-time context window monitoring in Claude Code remains an open challenge with no perfect native solution—**the statusline JSON currently reports cumulative tokens, not actual context usage** (GitHub Issue #13783). However, combining several community tools and tmux patterns produces a highly functional monitoring setup. The most effective approach uses **ccusage's statusline mode with tmux-claude-live** for near-real-time display, supplemented by the `/context` command for precise snapshots.

## The core problem: no native real-time API

Claude Code's internal context window state is not exposed through any official API, socket, or file-based interface that updates in real-time. The `/context` slash command provides **accurate per-component token breakdowns** (system prompt, MCP tools, messages, free space), but requires manual execution. Community tools parse JSONL transcript files at `~/.claude/projects/<project-hash>/<session-id>.jsonl`, but these show **cumulative session tokens, not current context window state**—a critical distinction.

GitHub Issue #13783 documents that the `context_window` data in statusline JSON shows values like "339K/200K = 169%" because it sums all tokens ever used, not the current context after compaction. This means any monitoring solution based solely on transcript parsing will be imprecise after `/compact` operations. The most accurate approach combines multiple data sources.

## Recommended solution: ccusage + tmux-claude-live

**ccusage** is the most mature community tool for Claude Code metrics, while **tmux-claude-live** provides the tmux integration layer. Together they offer the closest approximation to real-time monitoring currently possible.

### Step 1: Install ccusage and configure statusline

```bash
# Install ccusage globally
npm install -g ccusage

# Or run via npx (no install required)
npx ccusage statusline
```

Configure Claude Code to use ccusage in its native statusline:

```json
// ~/.claude/settings.json
{
  "statusLine": {
    "type": "command",
    "command": "bun x ccusage statusline --cost-source both",
    "padding": 0
  }
}
```

### Step 2: Set up tmux-claude-live for tmux integration

```bash
# Clone and install tmux-claude-live
git clone https://github.com/worldnine/tmux-claude-live
cd tmux-claude-live
npm install

# Start the daemon (runs in background, updates tmux variables)
npm run daemon
```

Add to your `~/.tmux.conf`:

```bash
# Claude Code metrics display
set -g status-interval 2
set -g status-right-length 150
set -g status-right '#[fg=#{@ccusage_warning_color}]⚡ #{@ccusage_total_tokens_formatted}/#{@ccusage_token_limit_formatted}#[default] | %H:%M'
```

The daemon continuously polls metrics and updates tmux user variables (`@ccusage_total_tokens`, `@ccusage_warning_color`, etc.) that the status bar references. Color coding provides visual alerts: **green** under 50%, **yellow** at 50-80%, **red** above 80%.

## Alternative: Custom file-watching with status bar script

For more control, create a custom monitoring script that writes to a file, then display it in tmux:

### Metrics collector script

```bash
#!/bin/bash
# ~/.tmux/claude-metrics-collector.sh
# Run this in background: nohup ~/.tmux/claude-metrics-collector.sh &

METRICS_FILE="$HOME/.claude-code-metrics.json"
CLAUDE_DIR="$HOME/.claude/projects"

while true; do
    # Find most recent session file
    LATEST_SESSION=$(find "$CLAUDE_DIR" -name "*.jsonl" -type f -printf '%T@ %p\n' 2>/dev/null | 
                     sort -n | tail -1 | cut -d' ' -f2-)
    
    if [ -n "$LATEST_SESSION" ]; then
        # Parse token usage from JSONL (note: cumulative, not current context)
        TOKENS=$(tail -100 "$LATEST_SESSION" | 
                 jq -s '[.[] | select(.usage) | .usage] | 
                        {input: (map(.input_tokens // 0) | add),
                         output: (map(.output_tokens // 0) | add),
                         cache_read: (map(.cache_read_input_tokens // 0) | add)}' 2>/dev/null)
        
        echo "$TOKENS" | jq '. + {timestamp: now, limit: 200000}' > "$METRICS_FILE"
    fi
    
    sleep 5
done
```

### tmux status bar script

```bash
#!/bin/bash
# ~/.tmux/claude-status.sh

METRICS_FILE="$HOME/.claude-code-metrics.json"

if [ ! -f "$METRICS_FILE" ]; then
    echo "📊 N/A"
    exit 0
fi

# Check file age (stale if >60s old)
FILE_AGE=$(( $(date +%s) - $(stat -f %m "$METRICS_FILE" 2>/dev/null || stat -c %Y "$METRICS_FILE") ))
if [ "$FILE_AGE" -gt 60 ]; then
    echo "📊 stale"
    exit 0
fi

INPUT=$(jq -r '.input // 0' "$METRICS_FILE")
LIMIT=$(jq -r '.limit // 200000' "$METRICS_FILE")
PERCENT=$(echo "scale=0; $INPUT * 100 / $LIMIT" | bc)

# Color based on usage
if [ "$PERCENT" -gt 80 ]; then
    echo "#[fg=colour196]📊 ${INPUT}k/${LIMIT}k (${PERCENT}%)#[default]"
elif [ "$PERCENT" -gt 50 ]; then
    echo "#[fg=colour226]📊 ${INPUT}k/${LIMIT}k (${PERCENT}%)#[default]"
else
    echo "#[fg=colour82]📊 ${INPUT}k/${LIMIT}k (${PERCENT}%)#[default]"
fi
```

### tmux.conf configuration

```bash
# ~/.tmux.conf
set -g status on
set -g status-interval 2   # Refresh every 2 seconds
set -g status-right-length 100
set -g status-right '#(~/.tmux/claude-status.sh) | %H:%M:%S'

# Force refresh keybinding
bind-key R run-shell "~/.tmux/claude-metrics-collector.sh &; tmux refresh-client -S"

# Popup for detailed view (Prefix + C)
bind-key C display-popup -E -w 60% -h 40% "watch -n 2 -c 'npx ccusage daily'"
```

## Using OpenTelemetry for enterprise-grade monitoring

Claude Code supports full **OpenTelemetry** export, enabling integration with Prometheus, Grafana, or custom collectors. This provides the most comprehensive metrics, including `claude_code.token.usage` with input/output/cache breakdowns.

### Enable OTEL export

```bash
# ~/.bashrc or ~/.zshrc
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=prometheus
export OTEL_METRIC_EXPORT_INTERVAL=10000  # 10 seconds
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

Or configure via settings.json:

```json
{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "console",
    "OTEL_METRIC_EXPORT_INTERVAL": "5000"
  }
}
```

Available metrics include:
- **`claude_code.token.usage`** — Token consumption by type (input/output/cacheRead/cacheCreation)
- **`claude_code.cost.usage`** — Cost in USD per model
- **`claude_code.session.count`** — Sessions started
- **`claude_code.active_time.total`** — Active session time in seconds

## Hooks system for event-driven updates

Claude Code's hooks system can trigger scripts on specific events, including **PreCompact** (before `/compact` runs). This enables capturing context state before compaction:

```json
// ~/.claude/settings.json
{
  "hooks": {
    "PreCompact": [{
      "matcher": "manual",
      "hooks": [{
        "type": "command",
        "command": "echo \"$(date): Manual compact\" >> ~/.claude/compact-log.txt"
      }]
    }, {
      "matcher": "auto", 
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/log-context-before-compact.sh"
      }]
    }],
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "tmux refresh-client -S 2>/dev/null || true"
      }]
    }]
  }
}
```

Hook scripts receive JSON via stdin containing session info:

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "hook_event_name": "PreCompact",
  "trigger": "auto"
}
```

## The /context command: most accurate but manual

For **maximum precision**, the `/context` command remains unmatched. It shows exact per-component breakdowns:

```
> /context
Context Usage
  claude-sonnet-4-5-20250929 • 143k/200k tokens (72%)
  ⛁ System prompt: 3.1k tokens (1.5%)
  ⛁ System tools: 12.4k tokens (6.2%)  
  ⛝ Reserved: 45.0k tokens (22.5%) [autocompact + output tokens]
  ⛁ MCP tools: 82.0k tokens (41.0%)
  ⛁ Messages: 8 tokens (0.0%)
  ⛶ Free space: 12k (5.8%)
```

This is the **only** method that shows true current context usage post-compaction. For a hybrid approach, periodically run `/context` and parse its output, though this requires human interaction.

## Additional community tools worth considering

**cc-statusline** (`@chongdashu/cc-statusline`) offers a polished solution:

```bash
npm install -g @chongdashu/cc-statusline
cc-statusline init   # Configure ~/.claude/settings.json automatically
```

Features include context percentage with progress bar, cost tracking with burn rate ($/hour), time until rate limit reset, and git branch integration.

**Claude-Code-Usage-Monitor** for macOS provides a native menu bar app built in Swift, giving persistent visibility without terminal:

```bash
# Available at: github.com/Sapeet/claude-code-usage-monitor-macos
```

## Practical implementation summary

For immediate setup with reasonable precision and tmux integration:

1. **Install ccusage**: `npm install -g ccusage`
2. **Configure statusline**: Add the `statusLine` block to `~/.claude/settings.json`
3. **Set up tmux-claude-live**: Clone repo, run daemon, add status-right config
4. **Add tmux refresh binding**: Bind a key to force refresh when needed
5. **Use `/context` for verification**: Before important operations, manually check exact state

The fundamental limitation remains: Claude Code doesn't expose a real-time API for true context window state. All monitoring solutions are approximations based on transcript parsing or manual command execution. GitHub Issue #516 (84+ upvotes) requests native always-visible context percentage—until Anthropic implements this, the community solutions above represent the best available options.