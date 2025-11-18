#!/bin/bash
# Structured logger for Claude Code monitoring hooks
# Provides JSON-formatted logging with levels: INFO, WARN, ERROR, DEBUG

# Determine log directory dynamically
if [ -n "$CLAUDE_PROJECT_DIR" ]; then
    LOG_DIR="${CLAUDE_PROJECT_DIR}/.claude/monitoring/logs"
else
    # Fallback to script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    LOG_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)/logs"
fi

LOG_FILE="${LOG_DIR}/hooks.log"

# Log levels (numeric for filtering)
declare -A LOG_LEVELS=(
    ["DEBUG"]=0
    ["INFO"]=1
    ["WARN"]=2
    ["ERROR"]=3
)

# Current log level (set via LOG_LEVEL env var, default INFO)
CURRENT_LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Check if log level is enabled
should_log() {
    local level="$1"
    local current_level_num="${LOG_LEVELS[$CURRENT_LOG_LEVEL]}"
    local check_level_num="${LOG_LEVELS[$level]}"

    [ "$check_level_num" -ge "$current_level_num" ]
}

# Main logging function
# Usage: log_event LEVEL HOOK_NAME MESSAGE [SESSION_ID] [EXTRA_JSON]
log_event() {
    local level="$1"
    local hook="$2"
    local message="$3"
    local session="${4:-unknown}"
    local extra="${5:-{}}"

    # Check if this level should be logged
    if ! should_log "$level"; then
        return 0
    fi

    # Create log directory if needed
    mkdir -p "$LOG_DIR" 2>/dev/null

    # Generate timestamp (ISO 8601)
    local timestamp=$(date -Iseconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S%z')

    # Build JSON log entry
    local json_log=$(cat <<EOF
{"timestamp":"$timestamp","level":"$level","hook":"$hook","message":"$message","session":"$session","extra":$extra}
EOF
)

    # Write to log file (append mode)
    echo "$json_log" >> "$LOG_FILE" 2>/dev/null

    # Also write to stderr for debugging (only if DEBUG level)
    if [ "$CURRENT_LOG_LEVEL" = "DEBUG" ]; then
        echo "[$(date '+%H:%M:%S')] [$level] $hook: $message" >&2
    fi
}

# Convenience functions for each log level
log_debug() {
    log_event "DEBUG" "$1" "$2" "$3" "$4"
}

log_info() {
    log_event "INFO" "$1" "$2" "$3" "$4"
}

log_warn() {
    log_event "WARN" "$1" "$2" "$3" "$4"
}

log_error() {
    log_event "ERROR" "$1" "$2" "$3" "$4"
}

# Log rotation function (called by SessionEnd hook)
# Removes logs older than N days (default 7)
rotate_logs() {
    local days="${1:-7}"

    if [ -f "$LOG_FILE" ]; then
        # Archive old logs
        local archive_file="${LOG_FILE}.$(date +%Y%m%d)"

        # Move current log to archive if not already archived today
        if [ ! -f "$archive_file" ]; then
            cp "$LOG_FILE" "$archive_file" 2>/dev/null
        fi

        # Delete archives older than N days
        find "$LOG_DIR" -name "hooks.log.*" -mtime +$days -delete 2>/dev/null

        # Truncate current log if larger than 10MB
        if [ -f "$LOG_FILE" ]; then
            local size=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
            if [ "$size" -gt 10485760 ]; then  # 10MB
                # Keep last 1000 lines
                tail -n 1000 "$LOG_FILE" > "$LOG_FILE.tmp" 2>/dev/null
                mv "$LOG_FILE.tmp" "$LOG_FILE" 2>/dev/null
            fi
        fi
    fi
}

# Query logs function (helper for debugging)
# Usage: query_logs [HOOK_NAME] [LEVEL] [LAST_N_LINES]
query_logs() {
    local hook="${1:-.*}"
    local level="${2:-.*}"
    local lines="${3:-50}"

    if [ -f "$LOG_FILE" ]; then
        tail -n "$lines" "$LOG_FILE" | grep -E "\"hook\":\"$hook\"" | grep -E "\"level\":\"$level\""
    else
        echo "No log file found at: $LOG_FILE" >&2
        return 1
    fi
}

# Export functions for use in other scripts
export -f log_event log_debug log_info log_warn log_error rotate_logs query_logs
