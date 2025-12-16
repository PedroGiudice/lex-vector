#!/usr/bin/env python3
"""
context-memory-capture.py - PostToolUse hook for observation capture

Captures high-value tool executions and compresses them into observations.

IMPORTANT: This hook must be FAST (<500ms) to avoid blocking.
- Only captures Write, Edit, MultiEdit, Bash (significant tools)
- Uses fallback compression if Gemini times out
- Runs compression in background if possible

Usage (in settings.json PostToolUse):
  python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/context-memory-capture.py"
"""
import json
import hashlib
import os
import sys
from pathlib import Path
from typing import List, Optional

# Add memory module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from memory.context_memory import (
        ContextMemoryDB, Observation,
        compress_with_gemini, fallback_compress
    )
except ImportError:
    ContextMemoryDB = None

# Tools worth capturing (high signal)
CAPTURE_TOOLS = {'Write', 'Edit', 'MultiEdit', 'Bash', 'Task'}

# Minimum output size to capture (filter noise)
MIN_OUTPUT_SIZE = 100

# Maximum output size to process (truncate large outputs)
MAX_OUTPUT_SIZE = 5000


def extract_files_from_result(tool_name: str, result: dict) -> List[str]:
    """Extract file paths from tool result."""
    files = []

    if tool_name in ('Write', 'Edit', 'MultiEdit', 'Read'):
        # Look for file_path in input or result
        if 'file_path' in result:
            files.append(result['file_path'])
        elif 'path' in result:
            files.append(result['path'])

    # For Bash, try to extract paths from output
    if tool_name == 'Bash':
        output = result.get('stdout', '') or result.get('output', '')
        # Simple heuristic: look for common file patterns
        for line in output.split('\n')[:10]:
            if '/' in line and len(line) < 200:
                # Might be a file path
                parts = line.split()
                for part in parts:
                    if part.startswith('/') or part.startswith('./'):
                        files.append(part[:100])
                        break

    return files[:5]  # Limit to 5 files


def generate_hash(session_id: str, tool_name: str, output: str) -> str:
    """Generate unique hash for deduplication."""
    content = f"{session_id}:{tool_name}:{output[:500]}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def main():
    # Always output valid JSON
    output = {"continue": True}

    # Check if module is available
    if ContextMemoryDB is None:
        print(json.dumps(output))
        return

    # Read stdin
    try:
        import select
        if not select.select([sys.stdin], [], [], 0.1)[0]:
            print(json.dumps(output))
            return
        stdin_data = json.load(sys.stdin)
    except Exception:
        print(json.dumps(output))
        return

    tool_name = stdin_data.get('tool_name', '')

    # Only capture specific tools
    if tool_name not in CAPTURE_TOOLS:
        print(json.dumps(output))
        return

    # Get tool output
    tool_result = stdin_data.get('tool_result', {})
    tool_output = ''

    if isinstance(tool_result, str):
        tool_output = tool_result
    elif isinstance(tool_result, dict):
        # Try common output fields
        tool_output = (
            tool_result.get('output', '') or
            tool_result.get('stdout', '') or
            tool_result.get('content', '') or
            tool_result.get('result', '') or
            str(tool_result)
        )

    # Skip small outputs (noise)
    if len(tool_output) < MIN_OUTPUT_SIZE:
        print(json.dumps(output))
        return

    # Truncate large outputs
    if len(tool_output) > MAX_OUTPUT_SIZE:
        tool_output = tool_output[:MAX_OUTPUT_SIZE] + '\n[truncated]'

    try:
        session_id = stdin_data.get('session_id', os.environ.get('CLAUDE_SESSION_ID', 'unknown'))
        files = extract_files_from_result(tool_name, stdin_data.get('tool_input', {}))

        # Try Gemini compression (with short timeout)
        compressed = compress_with_gemini(
            tool_output, tool_name, files, timeout=10
        )

        # Fallback if Gemini fails
        if not compressed:
            compressed = fallback_compress(tool_output, tool_name, files)

        # Create observation
        obs = Observation(
            session_id=session_id,
            tool_name=tool_name,
            type=compressed.get('type', 'change'),
            summary=compressed.get('summary', tool_output[:300]),
            files=files,
            tags=compressed.get('tags', []),
            raw_hash=generate_hash(session_id, tool_name, tool_output)
        )

        # Store in database
        with ContextMemoryDB() as db:
            db.add_observation(obs)

    except Exception as e:
        # Non-blocking: log but don't fail
        pass  # Could log to a file if needed

    print(json.dumps(output))


if __name__ == "__main__":
    main()
