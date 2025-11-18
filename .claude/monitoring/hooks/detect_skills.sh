#!/bin/bash

# Get script directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRACKER="${SCRIPT_DIR}/../simple_tracker.py"

INPUT=$(cat)
# Sanitize SESSION_ID - remove all chars except alphanumeric, underscore, hyphen
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' | tr -cd 'a-zA-Z0-9_-')
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""')

[ -z "$TRANSCRIPT" ] || [ "$TRANSCRIPT" = "null" ] && echo "$INPUT" && exit 0
[ ! -f "$TRANSCRIPT" ] && echo "$INPUT" && exit 0

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

for SKILL in "${!SKILLS[@]}"; do
    PATTERN="${SKILLS[$SKILL]}"
    if echo "$RECENT" | grep -qiE "$PATTERN"; then
        "$TRACKER" skill "$SKILL" "$SESSION_ID" 2>/dev/null || true
    fi
done

echo "$INPUT"
