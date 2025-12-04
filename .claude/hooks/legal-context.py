#!/usr/bin/env python3
"""
legal-context.py - Provides context for legal reasoning tasks

This hook detects legal project context and provides methodology reminders
for the Legal Reasoning Lens output style.

Usage:
  Added to UserPromptSubmit hooks in settings.json when using Legal Reasoning Lens.
  Compatible with existing hook chain (runs independently, adds context).

Note:
  This hook is OPTIONAL - the Legal Reasoning Lens output style works without it.
  The hook adds contextual awareness for legal project detection.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def check_legal_files() -> list[str]:
    """Check for relevant legal context files."""
    indicators = []

    # Check for case/matter context
    for pattern in ["CASO.md", "MATTER.md", "caso_*.md", "matter_*.md"]:
        if list(Path(".").glob(pattern)):
            indicators.append("Case context file present")
            break

    # Check for legal research
    for pattern in ["PESQUISA.md", "RESEARCH.md", "jurisprudencia_*.md"]:
        if list(Path(".").glob(pattern)):
            indicators.append("Legal research file present")
            break

    # Check for document templates
    if Path("templates").exists() or Path("modelos").exists():
        indicators.append("Templates directory present")

    return indicators


def detect_legal_context() -> str | None:
    """Detect if we're in a legal project context."""
    legal_indicators = [
        "petição", "peticao", "contrato", "parecer",
        "recurso", "contestação", "contestacao",
        "legal", "juridico", "jurídico"
    ]

    cwd = Path.cwd().name.lower()
    for indicator in legal_indicators:
        if indicator in cwd:
            return f"Legal project detected: {Path.cwd().name}"

    # Check for legal files
    files = check_legal_files()
    if files:
        return " | ".join(files)

    return None


def build_context() -> str:
    """Build context string."""
    parts = []

    # Timestamp
    parts.append(f"[{datetime.now().strftime('%H:%M')}]")

    # Legal context detection
    legal = detect_legal_context()
    if legal:
        parts.append(legal)

    # Reminder about methodology
    parts.append("Legal Reasoning Lens: IRAC+ methodology active")

    return " | ".join(parts)


def main():
    try:
        json.load(sys.stdin)
    except Exception:
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
