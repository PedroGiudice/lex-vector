"""
Context Memory - DuckDB-based persistent memory for Claude Code sessions.

Inspired by claude-mem but simplified:
- Uses DuckDB (existing project infrastructure)
- Uses Gemini Flash for compression (existing ADK)
- Integrates with existing hook system

Storage: ~/.claude/context_memory.duckdb
"""
from __future__ import annotations

import duckdb
import hashlib
import json
import logging
import os
import subprocess
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_DB_PATH = Path.home() / ".claude" / "context_memory.duckdb"


@dataclass
class Observation:
    """A compressed observation from tool execution."""
    session_id: str
    tool_name: str
    type: str  # decision, bugfix, feature, refactor, discovery, change
    summary: str
    files: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    raw_hash: str = ""
    timestamp: Optional[datetime] = None


class ContextMemoryDB:
    """
    DuckDB-based context memory for Claude Code sessions.

    Simple, efficient storage for:
    - Sessions (start, end, goals, summary)
    - Observations (compressed tool outputs)
    - Tags and files for search
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[duckdb.DuckDBPyConnection] = None
        self._lock = threading.Lock()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        """Connect to database with minimal config."""
        if self.conn:
            return

        with self._lock:
            self.conn = duckdb.connect(str(self.db_path))
            # Basic config
            self.conn.execute("SET memory_limit = '256MB'")
            self.conn.execute("SET threads = 2")
            self._ensure_schema()

    def close(self):
        """Close database connection."""
        if self.conn:
            with self._lock:
                self.conn.close()
                self.conn = None

    def _ensure_schema(self):
        """Create tables if they don't exist."""

        # Sessions table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id VARCHAR PRIMARY KEY,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                branch VARCHAR,
                project_dir VARCHAR,
                goals TEXT,
                summary TEXT,
                files_changed INTEGER DEFAULT 0,
                commits INTEGER DEFAULT 0
            )
        """)

        # Observations table - use sequence for auto-increment
        self.conn.execute("CREATE SEQUENCE IF NOT EXISTS obs_id_seq START 1")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER DEFAULT nextval('obs_id_seq'),
                session_id VARCHAR,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tool_name VARCHAR,
                type VARCHAR,
                summary TEXT,
                files VARCHAR,
                tags VARCHAR,
                raw_hash VARCHAR,
                PRIMARY KEY (id),
                UNIQUE(session_id, raw_hash)
            )
        """)

        # Indexes
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_obs_session
            ON observations(session_id)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_obs_timestamp
            ON observations(timestamp DESC)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_obs_type
            ON observations(type)
        """)

    # =========================================================================
    # SESSION OPERATIONS
    # =========================================================================

    def start_session(
        self,
        session_id: str,
        branch: Optional[str] = None,
        project_dir: Optional[str] = None,
        goals: Optional[str] = None
    ) -> bool:
        """Record session start."""
        try:
            # Check if session exists
            existing = self.conn.execute(
                "SELECT id FROM sessions WHERE id = ?", [session_id]
            ).fetchone()

            if existing:
                self.conn.execute("""
                    UPDATE sessions SET
                        start_time = CURRENT_TIMESTAMP,
                        branch = ?,
                        project_dir = ?,
                        goals = ?
                    WHERE id = ?
                """, [branch, project_dir, goals, session_id])
            else:
                self.conn.execute("""
                    INSERT INTO sessions (id, branch, project_dir, goals)
                    VALUES (?, ?, ?, ?)
                """, [session_id, branch, project_dir, goals])
            return True
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return False

    def end_session(
        self,
        session_id: str,
        summary: Optional[str] = None,
        files_changed: int = 0,
        commits: int = 0
    ) -> bool:
        """Record session end with summary."""
        try:
            self.conn.execute("""
                UPDATE sessions
                SET end_time = CURRENT_TIMESTAMP,
                    summary = ?,
                    files_changed = ?,
                    commits = ?
                WHERE id = ?
            """, [summary, files_changed, commits, session_id])
            return True
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return False

    def get_last_session(self) -> Optional[Dict]:
        """Get the most recent session."""
        try:
            result = self.conn.execute("""
                SELECT id, start_time, end_time, branch, project_dir,
                       goals, summary, files_changed, commits
                FROM sessions
                ORDER BY start_time DESC
                LIMIT 1
            """).fetchone()

            if result:
                return {
                    'id': result[0],
                    'start_time': result[1],
                    'end_time': result[2],
                    'branch': result[3],
                    'project_dir': result[4],
                    'goals': result[5],
                    'summary': result[6],
                    'files_changed': result[7],
                    'commits': result[8]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting last session: {e}")
            return None

    # =========================================================================
    # OBSERVATION OPERATIONS
    # =========================================================================

    def add_observation(self, obs: Observation) -> bool:
        """Add a compressed observation."""
        try:
            # Generate hash if not provided
            if not obs.raw_hash:
                content = f"{obs.session_id}:{obs.tool_name}:{obs.summary}"
                obs.raw_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            self.conn.execute("""
                INSERT INTO observations
                    (session_id, tool_name, type, summary, files, tags, raw_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (session_id, raw_hash) DO NOTHING
            """, [
                obs.session_id,
                obs.tool_name,
                obs.type,
                obs.summary,
                json.dumps(obs.files),
                json.dumps(obs.tags),
                obs.raw_hash
            ])
            return True
        except Exception as e:
            logger.error(f"Error adding observation: {e}")
            return False

    def get_recent_observations(
        self,
        limit: int = 20,
        days: int = 7,
        branch: Optional[str] = None,
        types: Optional[List[str]] = None
    ) -> List[Dict]:
        """Get recent observations for context injection."""
        try:
            # DuckDB: INTERVAL must be literal, not parameterized
            query = f"""
                SELECT
                    o.type, o.summary, o.timestamp, o.tool_name,
                    o.files, o.tags, s.branch
                FROM observations o
                LEFT JOIN sessions s ON o.session_id = s.id
                WHERE o.timestamp > CURRENT_TIMESTAMP - INTERVAL '{days}' DAY
            """
            params = []

            if branch:
                query += " AND (s.branch = ? OR s.branch IS NULL)"
                params.append(branch)

            if types:
                placeholders = ','.join(['?' for _ in types])
                query += f" AND o.type IN ({placeholders})"
                params.extend(types)

            # Order by branch match first, then timestamp
            branch_val = branch or ''
            query += f"""
                ORDER BY
                    CASE WHEN s.branch = '{branch_val}' THEN 0 ELSE 1 END,
                    o.timestamp DESC
                LIMIT {limit}
            """

            results = self.conn.execute(query, params).fetchall()

            return [
                {
                    'type': r[0],
                    'summary': r[1],
                    'timestamp': r[2],
                    'tool_name': r[3],
                    'files': json.loads(r[4]) if r[4] else [],
                    'tags': json.loads(r[5]) if r[5] else [],
                    'branch': r[6]
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Error getting observations: {e}")
            return []

    def search_observations(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict]:
        """Search observations by keyword."""
        try:
            results = self.conn.execute("""
                SELECT
                    o.type, o.summary, o.timestamp, o.tool_name,
                    s.branch
                FROM observations o
                LEFT JOIN sessions s ON o.session_id = s.id
                WHERE o.summary ILIKE ?
                   OR o.tags ILIKE ?
                   OR o.files ILIKE ?
                ORDER BY o.timestamp DESC
                LIMIT ?
            """, [f'%{query}%', f'%{query}%', f'%{query}%', limit]).fetchall()

            return [
                {
                    'type': r[0],
                    'summary': r[1],
                    'timestamp': r[2],
                    'tool_name': r[3],
                    'branch': r[4]
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Error searching observations: {e}")
            return []

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_stats(self) -> Dict:
        """Get memory statistics."""
        try:
            stats = {}

            stats['total_sessions'] = self.conn.execute(
                "SELECT COUNT(*) FROM sessions"
            ).fetchone()[0]

            stats['total_observations'] = self.conn.execute(
                "SELECT COUNT(*) FROM observations"
            ).fetchone()[0]

            stats['observations_by_type'] = dict(
                self.conn.execute("""
                    SELECT type, COUNT(*)
                    FROM observations
                    GROUP BY type
                """).fetchall()
            )

            stats['recent_7_days'] = self.conn.execute("""
                SELECT COUNT(*) FROM observations
                WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '7' DAY
            """).fetchone()[0]

            stats['db_size_kb'] = self.db_path.stat().st_size / 1024

            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}


# =============================================================================
# COMPRESSION UTILITIES (using Gemini)
# =============================================================================

def compress_with_gemini(
    tool_output: str,
    tool_name: str,
    files: List[str] = None,
    timeout: int = 30
) -> Optional[Dict]:
    """
    Use Gemini Flash to compress tool output into an observation.

    Returns:
        Dict with 'type', 'summary', 'tags' or None on failure
    """
    # Truncate large outputs
    output = tool_output[:4000] if len(tool_output) > 4000 else tool_output
    files_str = ', '.join(files[:5]) if files else 'N/A'

    prompt = f"""Compress this {tool_name} output into a semantic observation.

Files involved: {files_str}

Output:
{output}

Respond ONLY with valid JSON (no markdown, no explanation):
{{"type": "decision|bugfix|feature|refactor|discovery|change", "summary": "2-3 sentences max", "tags": ["tag1", "tag2"]}}"""

    try:
        result = subprocess.run(
            ["gemini", "-m", "gemini-2.5-flash", prompt],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            # Extract JSON from response (handle potential markdown wrapping)
            response = result.stdout.strip()
            if response.startswith("```"):
                # Remove markdown code blocks
                lines = response.split('\n')
                response = '\n'.join(lines[1:-1])
            return json.loads(response)
        else:
            logger.warning(f"Gemini compression failed: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        logger.warning("Gemini compression timed out")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON from Gemini: {e}")
        return None
    except FileNotFoundError:
        logger.warning("Gemini CLI not found - using fallback compression")
        return None
    except Exception as e:
        logger.error(f"Compression error: {e}")
        return None


def fallback_compress(
    tool_output: str,
    tool_name: str,
    files: List[str] = None
) -> Dict:
    """
    Simple fallback compression without AI.

    Extracts key information heuristically.
    """
    # Determine type based on tool and content
    type_map = {
        'Write': 'feature',
        'Edit': 'change',
        'MultiEdit': 'refactor',
        'Bash': 'change',
        'Task': 'discovery'
    }
    obs_type = type_map.get(tool_name, 'change')

    # Check for bug-related keywords
    if any(kw in tool_output.lower() for kw in ['fix', 'bug', 'error', 'issue']):
        obs_type = 'bugfix'
    elif any(kw in tool_output.lower() for kw in ['decide', 'choice', 'option', 'selected']):
        obs_type = 'decision'

    # Truncate summary
    summary = tool_output[:300].replace('\n', ' ')
    if len(tool_output) > 300:
        summary += '...'

    # Extract potential tags
    tags = []
    if files:
        # Extract file extensions as tags
        exts = set(Path(f).suffix[1:] for f in files if '.' in f)
        tags.extend(list(exts)[:3])

    return {
        'type': obs_type,
        'summary': summary,
        'tags': tags
    }


# =============================================================================
# CONTEXT GENERATION
# =============================================================================

def generate_context_injection(
    db: ContextMemoryDB,
    branch: Optional[str] = None,
    max_tokens: int = 500
) -> str:
    """
    Generate context string for injection at SessionStart.

    Target: ~500 tokens (roughly 2000 chars)
    """
    parts = []

    # Last session info
    last_session = db.get_last_session()
    if last_session:
        parts.append("## Last Session")
        if last_session.get('summary'):
            parts.append(last_session['summary'][:500])
        if last_session.get('branch'):
            parts.append(f"Branch: {last_session['branch']}")
        if last_session.get('files_changed'):
            parts.append(f"Files changed: {last_session['files_changed']}")

    # Recent observations (prioritize same branch)
    observations = db.get_recent_observations(
        limit=10,
        days=7,
        branch=branch,
        types=['decision', 'bugfix', 'discovery', 'feature']  # High-value types
    )

    if observations:
        parts.append("\n## Recent Context")
        for obs in observations[:7]:  # Limit for token budget
            type_emoji = {
                'decision': 'D',
                'bugfix': 'B',
                'feature': 'F',
                'refactor': 'R',
                'discovery': 'i',
                'change': 'C'
            }.get(obs['type'], '?')

            summary = obs['summary'][:150]
            parts.append(f"[{type_emoji}] {summary}")

    context = '\n'.join(parts)

    # Ensure we don't exceed token budget (~4 chars per token)
    max_chars = max_tokens * 4
    if len(context) > max_chars:
        context = context[:max_chars] + "\n[truncated]"

    return context


# =============================================================================
# CLI FOR TESTING
# =============================================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    with ContextMemoryDB() as db:
        if len(sys.argv) > 1:
            cmd = sys.argv[1]

            if cmd == "stats":
                stats = db.get_stats()
                print(json.dumps(stats, indent=2, default=str))

            elif cmd == "recent":
                obs = db.get_recent_observations(limit=10)
                for o in obs:
                    print(f"[{o['type']}] {o['summary'][:80]}...")

            elif cmd == "search" and len(sys.argv) > 2:
                query = sys.argv[2]
                results = db.search_observations(query)
                for r in results:
                    print(f"[{r['type']}] {r['summary'][:80]}...")

            elif cmd == "context":
                branch = sys.argv[2] if len(sys.argv) > 2 else None
                context = generate_context_injection(db, branch)
                print(context)

            else:
                print("Usage: python context_memory.py [stats|recent|search <query>|context [branch]]")
        else:
            print("Context Memory DB initialized")
            print(f"Path: {db.db_path}")
            stats = db.get_stats()
            print(f"Sessions: {stats.get('total_sessions', 0)}")
            print(f"Observations: {stats.get('total_observations', 0)}")
