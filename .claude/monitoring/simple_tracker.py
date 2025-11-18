#!/usr/bin/env python3
"""
Sistema simplificado de tracking para Claude Code
Monitora: agentes, hooks, skills
"""

import json
import sqlite3
import sys
import os
from datetime import datetime
from pathlib import Path
import re

def get_safe_project_dir():
    """
    Get project directory with path traversal protection.
    Only allows directories within Claude-Code-Projetos.
    """
    project_dir = Path(os.getenv('CLAUDE_PROJECT_DIR', os.getcwd())).resolve()

    # Define allowed root directories
    allowed_roots = [
        Path.home() / "claude-work" / "repos" / "Claude-Code-Projetos",  # WSL2 structure
        Path.home() / "Claude-Code-Projetos",  # Legacy structure
    ]

    # Check if project_dir is within allowed roots
    for allowed_root in allowed_roots:
        try:
            project_dir.relative_to(allowed_root)
            return project_dir
        except ValueError:
            continue

    # Fallback to current directory if not within allowed roots
    return Path.cwd()

# Dynamic path with path traversal protection
PROJECT_DIR = get_safe_project_dir()
DB_PATH = PROJECT_DIR / ".claude" / "monitoring" / "tracking.db"

class SimpleTracker:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(
            str(DB_PATH),
            timeout=10.0,  # Wait up to 10s for database lock
            isolation_level='DEFERRED'  # Better concurrency
        )
        # Enable WAL mode for concurrent reads/writes
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.init_db()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection is always closed"""
        self.close()
        return False  # Don't suppress exceptions

    def init_db(self):
        # Tabela unificada
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                type TEXT CHECK(type IN ('agent', 'hook', 'skill')),
                name TEXT NOT NULL,
                status TEXT,
                session_id TEXT,
                metadata JSON
            )
        """)

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_recent
            ON events(type, timestamp DESC)
        """)

        self.conn.commit()

    def track_agent(self, name, status, session_id, metadata=None):
        self.conn.execute("""
            INSERT INTO events (type, name, status, session_id, metadata)
            VALUES ('agent', ?, ?, ?, ?)
        """, (name, status, session_id, json.dumps(metadata)))
        self.conn.commit()

    def track_hook(self, name, session_id):
        self.conn.execute("""
            INSERT INTO events (type, name, session_id)
            VALUES ('hook', ?, ?)
        """, (name, session_id))
        self.conn.commit()

    def track_skill(self, name, session_id):
        self.conn.execute("""
            INSERT INTO events (type, name, session_id)
            VALUES ('skill', ?, ?)
        """, (name, session_id))
        self.conn.commit()

    def get_recent(self, event_type, minutes=5):
        cursor = self.conn.execute("""
            SELECT name, status, COUNT(*) as count, MAX(timestamp) as last_seen
            FROM events
            WHERE type = ?
            AND timestamp > datetime('now', '-' || ? || ' minutes')
            GROUP BY name, status
            ORDER BY last_seen DESC
        """, (event_type, minutes))

        return [dict(zip(['name', 'status', 'count', 'last_seen'], row))
                for row in cursor.fetchall()]

    def cleanup_old(self, days=7):
        self.conn.execute("""
            DELETE FROM events
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        """, (days,))
        self.conn.commit()

    def close(self):
        self.conn.close()


# === CLI Commands ===

def cmd_agent(args):
    with SimpleTracker() as tracker:
        name, status, session = args[0], args[1], args[2]
        tracker.track_agent(name, status, session)
        print(f"✓ Agent tracked: {name} ({status})")

def cmd_hook(args):
    with SimpleTracker() as tracker:
        name, session = args[0], args[1]
        tracker.track_hook(name, session)
        print(f"✓ Hook tracked: {name}")

def cmd_skill(args):
    with SimpleTracker() as tracker:
        name, session = args[0], args[1]
        tracker.track_skill(name, session)
        print(f"✓ Skill tracked: {name}")

def cmd_status(args):
    with SimpleTracker() as tracker:
        print("📊 Status (last 5 minutes)\n")

        # Agentes
        agents = tracker.get_recent('agent', 5)
        print(f"🤖 Agents ({len(agents)})")
        for a in agents:
            print(f"  • {a['name']:<20} {a['status']:<10} ({a['count']}x)")

        # Hooks
        hooks = tracker.get_recent('hook', 5)
        print(f"\n⚡ Hooks ({len(hooks)})")
        for h in hooks:
            print(f"  • {h['name']:<20} ({h['count']}x)")

        # Skills
        skills = tracker.get_recent('skill', 5)
        print(f"\n🛠️  Skills ({len(skills)})")
        for s in skills:
            print(f"  • {s['name']:<20} ({s['count']}x)")

def cmd_statusline(args):
    """Gera output para statusline"""
    with SimpleTracker() as tracker:
        agents = tracker.get_recent('agent', 2)
        active_agents = [a for a in agents if a['status'] == 'active']

        hooks = tracker.get_recent('hook', 1)
        skills = tracker.get_recent('skill', 2)

        # Formato compacto
        agent_str = f"{len(active_agents)}/{len(agents)}" if agents else "0/0"
        hook_str = f"{len(hooks)}" if hooks else "0"
        skill_names = [s['name'] for s in skills[:3]]
        skill_str = ", ".join(skill_names) if skill_names else "-"

        print(f"🤖 {agent_str} │ ⚡ {hook_str} │ 🛠️ {skill_str}")

def cmd_cleanup(args):
    with SimpleTracker() as tracker:
        days = int(args[0]) if args else 7
        tracker.cleanup_old(days)
        print(f"✓ Cleaned up events older than {days} days")


# === Main ===

COMMANDS = {
    'agent': cmd_agent,
    'hook': cmd_hook,
    'skill': cmd_skill,
    'status': cmd_status,
    'statusline': cmd_statusline,
    'cleanup': cmd_cleanup,
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
Simple Tracker - Monitor Claude Code multi-agent systems

Usage:
  simple_tracker.py agent <name> <status> <session_id>
  simple_tracker.py hook <name> <session_id>
  simple_tracker.py skill <name> <session_id>
  simple_tracker.py status
  simple_tracker.py statusline
  simple_tracker.py cleanup [days]

Examples:
  simple_tracker.py agent backend-dev active abc123
  simple_tracker.py hook PostResponse abc123
  simple_tracker.py skill docx abc123
  simple_tracker.py status
""")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

    try:
        COMMANDS[cmd](sys.argv[2:])
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
