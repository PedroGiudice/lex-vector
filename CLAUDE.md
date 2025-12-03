# CLAUDE.md

This file provides operational guidance to Claude Code when working with code in this repository.

---

## Critical Architectural Rules

### Three-Layer Separation (Inviolable)

This project enforces strict separation between three layers. Violating this separation caused 3 days of system failure (see DISASTER_HISTORY.md).

**LAYER 1: CODE**
- Location: `~/claude-work/repos/Claude-Code-Projetos`
- Contents: Python source files, configuration files, documentation
- Version control: Git (mandatory)
- Portability: Synchronized via `git push`/`git pull`

**LAYER 2: ENVIRONMENT**
- Location: Within each agent directory (e.g., `agentes/oab-watcher/.venv/`)
- Contents: Python interpreter, installed packages (pip)
- Version control: NEVER (must be in .gitignore)
- Portability: Recreated via `requirements.txt` on each machine

**LAYER 3: DATA**
- Location: `~/claude-code-data` or external storage
- Contents: Downloads, logs, outputs, processed data
- Version control: NEVER
- Portability: Physical transport or environment variables

**BLOCKING RULE:** Code MUST NEVER be placed in data directories. Data MUST NEVER be committed to Git.

---

## Hook Validation Protocol

After impactful codebase changes (hooks, dependencies, configs), verify hook execution logs.

### Validation Commands

```bash
# Check hook execution logs
tail -50 ~/.vibe-log/hooks.log
cat .claude/monitoring/logs/hooks.log
cat .claude/hooks/lib/skill-tracking.log

# Verify all hook files exist
cat .claude/settings.json | jq -r '.hooks[][] | .hooks[] | .command'

# Test critical hooks manually
python3 .claude/hooks/improve-prompt.py < test-input.json
node .claude/hooks/context-collector.js
```

### Red Flags

- `MODULE_NOT_FOUND` errors: Missing dependency or wrong path
- `Another hook execution is already in progress`: Vibe-log concurrency (benign)
- `command not found`: Script not executable or missing shebang
- Silent failures: Hook returns non-zero exit but marked as "Success"

---

## Project Structure

```
Claude-Code-Projetos/
├── agentes/           # Autonomous monitoring agents (long-running)
│   ├── oab-watcher/   # Monitors OAB daily journal
│   ├── djen-tracker/  # Monitors Electronic Justice Daily
│   └── legal-lens/    # Analyzes legal publications
│
├── comandos/          # Reusable utility commands (single-purpose tools)
│   ├── fetch-doc/     # Downloads documents from specific sources
│   ├── extract-core/  # Extracts core information from documents
│   ├── validate-id/   # Validates identifiers (CPF, CNPJ, OAB)
│   ├── parse-legal/   # Parses legal texts
│   └── send-alert/    # Sends alerts via email/webhook
│
├── skills/            # Claude Code skills (PROJECT-SPECIFIC, CUSTOM)
│   └── ...            # Each MUST have SKILL.md to be functional
│
├── .claude/           # Claude Code configuration (MANAGED, SETTINGS)
│   ├── skills/        # Managed/official skills (DO NOT add custom skills here)
│   │   ├── anthropic-skills/  # Official Anthropic skills collection
│   │   └── superpowers/       # Advanced Claude Code capabilities
│   ├── hooks/         # Execution hooks
│   ├── agents/        # Agent definitions (.md files)
│   └── statusline/    # Statusline UI configuration
│
└── shared/            # Shared code between projects
    ├── utils/         # Utility functions (logging, path management)
    └── models/        # Data models
```

---

## Path Management

Code must access data directories using:

1. **Environment variables** (for cross-machine compatibility)
2. **shared/utils/path_utils.py** (centralized path management)
3. **Relative paths** (when appropriate)

**NEVER use hardcoded absolute paths.**

Example from `shared/utils/path_utils.py`:

```python
import os
from pathlib import Path

def get_data_dir(agent_name: str, subdir: str = "") -> Path:
    """Returns path to data directory for given agent."""
    data_root = Path(os.getenv('CLAUDE_DATA_ROOT', '~/claude-code-data'))
    agent_data = data_root / 'agentes' / agent_name

    if subdir:
        return agent_data / subdir
    return agent_data
```

Usage:

```python
from shared.utils.path_utils import get_data_dir

downloads_dir = get_data_dir('oab-watcher', 'downloads')
output_file = downloads_dir / 'publicacao_2025-11-07.pdf'
```

---

## Prohibited Actions (BLOCKING)

These actions must be refused with reference to DISASTER_HISTORY.md:

### Custom Skills in .claude/skills/

```bash
# BLOCKED - Custom skills MUST go in skills/, NOT .claude/skills/
mv my-custom-skill .claude/skills/  # WRONG

# CORRECT - Custom skills in skills/ root
mv my-custom-skill skills/  # CORRECT
```

**Why this is blocked:**
- `.claude/skills/` = Managed/official skills (anthropic-skills, superpowers)
- `skills/` = Project-specific custom skills
- Mixing them causes count confusion and breaks statusline tracking
- Each skill in `skills/` MUST have `SKILL.md` to be functional

### Code to Data Directories

```bash
# BLOCKED - Caused 3-day disaster (see DISASTER_HISTORY.md)
cp *.py ~/claude-code-data/
mv projeto ~/claude-code-data/projetos/
```

### Python Execution Without venv

```bash
# BLOCKED - Causes version conflicts between machines
pip install library  # without .venv activated
python main.py       # without .venv activated

# CORRECT
cd agentes/agent-name
source .venv/bin/activate
pip install library
python main.py
```

### Hardcoded Paths in Configuration/Hooks

```python
# BLOCKED - Breaks when moving between machines
LOG_DIR = "/home/user/projetos/logs"

# CORRECT - Use environment variables or path_utils
from shared.utils.path_utils import get_data_dir
LOG_DIR = get_data_dir('oab-watcher', 'logs')
```

### Committing .venv to Git

```bash
# BLOCKED - Environment is machine-specific
git add .venv/

# CORRECT - Ensure .gitignore includes:
# .venv/
# venv/
# __pycache__/
```

---

## Debugging Methodology

**Historical Context:** 3 days were spent debugging symptoms without identifying the root cause. See DISASTER_HISTORY.md for details.

### Mandatory Approach: 5 Whys

When encountering a non-trivial bug:

1. **Symptom:** [Describe observed behavior]
2. **Why 1?** [Immediate cause]
3. **Why 2?** [Deeper cause]
4. **Why 3?** [Even deeper]
5. **Why 4?** [Almost at root]
6. **Why 5?** **[ROOT CAUSE]**

**Only address the root cause.** Fixing symptoms leads to infinite iterations.

---

## Virtual Environment Requirements

Virtual environments are mandatory, not optional. Historical evidence shows that global Python installations cause version conflicts and dependency contamination.

### Creation

```bash
cd agentes/agent-name
python -m venv .venv
```

### Activation Verification

```bash
# Activate
source .venv/bin/activate  # Linux/WSL2

# Verify
which python  # MUST show path containing .venv
pip list      # MUST show only project dependencies, not global packages
```

### Execution Pattern

```bash
# Step 1: Navigate to project
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/agent-name

# Step 2: Activate venv
source .venv/bin/activate

# Step 3: Verify activation
# (venv) appears in prompt

# Step 4: Install dependencies if needed
pip install -r requirements.txt

# Step 5: Execute script
python main.py
```

---

## When Making Architectural Changes

Before proposing or implementing any architectural change:

1. **Read DISASTER_HISTORY.md** to understand what went wrong before
2. **Validate against three-layer separation** (Code/Environment/Data)
3. **Test thoroughly** in clean environment (fresh clone + venv setup)
4. **Document the decision** in this file (CLAUDE.md)
5. **Update README.md** if user-facing

---

## WSL2 Environment

**Current Platform:** Ubuntu 24.04 LTS (WSL2)

### Directory Structure

- Repository: `~/claude-work/repos/Claude-Code-Projetos`
- Data: `~/claude-code-data` (or external storage)

### Essential Commands

```bash
# Navigate to project
cd ~/claude-work/repos/Claude-Code-Projetos

# Activate agent venv
cd agentes/agent-name
source .venv/bin/activate

# Activate global venv (for linting, type checking)
cd ~/claude-work/repos/Claude-Code-Projetos
source .venv/bin/activate
pytest
ruff check .
mypy .

# Validate hooks manually
node .claude/hooks/invoke-legal-braniac-hybrid.js
node .claude/hooks/session-context-hybrid.js
```

### Platform Differences

| Action | Windows | WSL2 |
|--------|---------|------|
| Activate venv | `.venv\Scripts\activate` | `source .venv/bin/activate` |
| Path separator | `\` (backslash) | `/` (forward slash) |
| Line endings | CRLF | LF |

---

## Custom Agents Discovery

The Claude Code discovers agents automatically from `.md` files in:
- `.claude/agents/` (project-level)
- `~/.claude/agents/` (user-level global)

**CRITICAL:** Discovery happens at session start. If you create an agent during a session, it will NOT be available until you restart Claude Code.

### Workflow

1. Create the file `.claude/agents/agent-name.md`
2. **Restart the Claude Code session** (close and reopen)
3. The agent will be available

---

## References

- **README.md** - User-facing setup instructions and project overview
- **DISASTER_HISTORY.md** - Detailed account of 3-day architectural disaster and lessons learned
- **WSL_SETUP.md** - WSL2 migration documentation
- **QUICK-REFERENCE.md** - Quick reference for WSL2 development
- **CHANGELOG.md** - Change history

---

**Last updated:** 2025-12-02
**Maintained by:** PedroGiudice
**For Claude Code instances operating in:** `~/claude-work/repos/Claude-Code-Projetos` (WSL2)
