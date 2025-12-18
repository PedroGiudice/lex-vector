#!/bin/bash
# memory-sync-gdrive.sh - Sync context memory to Google Drive on SessionEnd
#
# Runs asynchronously to not block session end

DB_FILE="$HOME/.claude/context_memory.duckdb"
REMOTE="gdrive:claude-memory/"

# Only sync if rclone is available and DB exists
if command -v rclone &> /dev/null && [ -f "$DB_FILE" ]; then
    # Run in background with timeout
    timeout 30 rclone copy "$DB_FILE" "$REMOTE" --quiet &
fi

# Always return success (non-blocking)
echo '{"continue": true}'
