#!/usr/bin/env python3
"""
context-memory-summary.py - SessionEnd hook for session summary generation

Generates a summary of the session and stores it for next session context.

Usage (in settings.json SessionEnd):
  python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/context-memory-summary.py"
"""
import json
import os
import subprocess
import sys
from pathlib import Path

# Add memory module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from memory.context_memory import ContextMemoryDB
except ImportError:
    ContextMemoryDB = None


def get_git_stats() -> dict:
    """Get git statistics for this session."""
    stats = {'files_changed': 0, 'commits': 0}
    cwd = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())

    try:
        # Count uncommitted changes
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True, timeout=5, cwd=cwd
        )
        if result.returncode == 0:
            changes = [l for l in result.stdout.strip().split('\n') if l]
            stats['files_changed'] = len(changes)

        # Count recent commits (last hour, approximately this session)
        result = subprocess.run(
            ['git', 'log', '--oneline', '--since=1.hour.ago'],
            capture_output=True, text=True, timeout=5, cwd=cwd
        )
        if result.returncode == 0:
            commits = [l for l in result.stdout.strip().split('\n') if l]
            stats['commits'] = len(commits)

    except Exception:
        pass

    return stats


def generate_summary(db: ContextMemoryDB, session_id: str) -> str:
    """Generate session summary from observations."""
    try:
        # Get observations from this session
        results = db.conn.execute("""
            SELECT type, summary
            FROM observations
            WHERE session_id = ?
            ORDER BY timestamp
        """, [session_id]).fetchall()

        if not results:
            return "No significant activity recorded."

        # Count by type
        type_counts = {}
        summaries = []
        for type_, summary in results:
            type_counts[type_] = type_counts.get(type_, 0) + 1
            if len(summaries) < 5:  # Keep top 5 summaries
                summaries.append(summary[:100])

        # Build summary
        parts = []

        # Type breakdown
        type_str = ', '.join(f"{count} {t}s" for t, count in type_counts.items())
        parts.append(f"Activity: {type_str}")

        # Key work items
        if summaries:
            parts.append("Key items:")
            for s in summaries[:3]:
                parts.append(f"  - {s}")

        return '\n'.join(parts)

    except Exception as e:
        return f"Summary generation failed: {str(e)[:50]}"


def main():
    output = {"continue": True}

    if ContextMemoryDB is None:
        print(json.dumps(output))
        return

    # Read stdin
    stdin_data = {}
    try:
        import select
        if select.select([sys.stdin], [], [], 0.1)[0]:
            stdin_data = json.load(sys.stdin)
    except Exception:
        pass

    try:
        session_id = stdin_data.get('session_id', os.environ.get('CLAUDE_SESSION_ID', 'unknown'))
        git_stats = get_git_stats()

        with ContextMemoryDB() as db:
            # Generate summary
            summary = generate_summary(db, session_id)

            # End session with summary
            db.end_session(
                session_id=session_id,
                summary=summary,
                files_changed=git_stats['files_changed'],
                commits=git_stats['commits']
            )

        # Log completion
        output['systemMessage'] = f"Session saved ({git_stats['commits']} commits, {git_stats['files_changed']} files)"

    except Exception as e:
        output['systemMessage'] = f"Session summary skipped: {str(e)[:50]}"

    print(json.dumps(output))


if __name__ == "__main__":
    main()
