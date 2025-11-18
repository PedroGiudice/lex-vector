#!/bin/bash

# Get script directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRACKER="${SCRIPT_DIR}/../simple_tracker.py"

# Load logger library
source "${SCRIPT_DIR}/lib/logger.sh"

INPUT=$(cat)
# Sanitize SESSION_ID - remove all chars except alphanumeric, underscore, hyphen
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' | tr -cd 'a-zA-Z0-9_-')
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""')

log_debug "detect_skills" "Starting skill detection" "$SESSION_ID"

if [ -z "$TRANSCRIPT" ] || [ "$TRANSCRIPT" = "null" ]; then
    log_debug "detect_skills" "No transcript, skipping" "$SESSION_ID"
    echo "$INPUT"
    exit 0
fi

if [ ! -f "$TRANSCRIPT" ]; then
    log_warn "detect_skills" "Transcript not found: $TRANSCRIPT" "$SESSION_ID"
    echo "$INPUT"
    exit 0
fi

# Última mensagem
RECENT=$(tail -n 3 "$TRANSCRIPT" 2>/dev/null | jq -r 'select(.role=="assistant") | .content' 2>/dev/null || echo "")

# Detecta skills por palavras-chave
declare -A SKILLS=(
    ["docx"]="(\.docx|word document|creating.*document)"
    ["pdf"]="(\.pdf|pdf document)"
    ["pptx"]="(\.pptx|powerpoint|presentation)"
    ["xlsx"]="(\.xlsx|spreadsheet|excel)"
    ["git"]="(git (add|commit|push|pull|branch)|repository)"
    ["bash"]="(bash_tool|executing command|running.*command)"
    ["web_search"]="(searching|web_search|brave)"
    ["analysis"]="(analyz|review|assess)"
)

DETECTED_COUNT=0
for SKILL in "${!SKILLS[@]}"; do
    PATTERN="${SKILLS[$SKILL]}"
    if echo "$RECENT" | grep -qiE "$PATTERN"; then
        log_info "detect_skills" "Detected skill: $SKILL (pattern: $PATTERN)" "$SESSION_ID"
        if "$TRACKER" skill "$SKILL" "$SESSION_ID" 2>&1; then
            log_info "detect_skills" "Tracked skill: $SKILL" "$SESSION_ID"
            ((DETECTED_COUNT++))
        else
            log_error "detect_skills" "Failed to track skill: $SKILL" "$SESSION_ID"
        fi
    fi
done

if [ $DETECTED_COUNT -gt 0 ]; then
    log_info "detect_skills" "Detection complete: $DETECTED_COUNT skills found" "$SESSION_ID"
else
    log_debug "detect_skills" "No skills detected" "$SESSION_ID"
fi

echo "$INPUT"
