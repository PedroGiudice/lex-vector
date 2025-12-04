#!/usr/bin/env python3
"""
project-context.py - Provides Technical Director with project state awareness
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime


def get_git_state() -> dict | None:
    """Get repository state."""
    try:
        branch = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True, text=True, timeout=5
        )
        if branch.returncode != 0:
            return None

        status = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True, timeout=5
        )
        changes = [l for l in status.stdout.strip().split('\n') if l]

        return {
            "branch": branch.stdout.strip(),
            "uncommitted": len(changes)
        }
    except:
        return None


def check_north_star() -> str:
    """Check ARCHITECTURE.md status - critical for North Star guardianship."""
    path = Path("ARCHITECTURE.md")
    if path.exists():
        try:
            content = path.read_text()
            lines = [l for l in content.split('\n') if l.strip() and not l.startswith('#')]
            if lines:
                return "ARCHITECTURE.md: Present (North Star defined)"
        except:
            pass
        return "ARCHITECTURE.md: Present but may be empty"
    return "ARCHITECTURE.md: ABSENT — No North Star defined"


def check_deviation_log() -> str | None:
    """Check for documented deviations."""
    for path in [Path("DEVIATIONS.md"), Path("docs/deviations.md"), Path("ARCHITECTURE.md")]:
        if path.exists():
            try:
                content = path.read_text().lower()
                if "deviation" in content:
                    return "Deviation log exists"
            except:
                pass
    return None


def build_context() -> str:
    """Assemble context string."""
    parts = []

    # Timestamp
    parts.append(f"[{datetime.now().strftime('%H:%M')}]")

    # Git
    git = get_git_state()
    if git:
        git_str = f"git:{git['branch']}"
        if git['uncommitted']:
            git_str += f" ({git['uncommitted']} uncommitted)"
        parts.append(git_str)

    # North Star status (critical)
    parts.append(check_north_star())

    # Deviations
    dev = check_deviation_log()
    if dev:
        parts.append(dev)

    return " | ".join(parts)


def main():
    try:
        json.load(sys.stdin)
    except:
        pass

    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": build_context()
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
