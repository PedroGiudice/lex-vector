# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Critical Architectural Decisions

### Three-Layer Separation (Inviolable)

This project enforces strict separation between three layers. **Violating this separation previously caused 3 days of system failure** (see DISASTER_HISTORY.md).

**LAYER 1: CODE (C:\claude-work\repos\Claude-Code-Projetos\)**
- Location: `C:\claude-work\repos\Claude-Code-Projetos\`
- Contents: Python source files, configuration files, documentation
- Version control: Git (mandatory)
- Portability: Synchronized via `git push`/`git pull`

**LAYER 2: ENVIRONMENT (C:\claude-work\repos\Claude-Code-Projetos\agentes\*\.venv\)**
- Location: Within each agent directory (e.g., `agentes/oab-watcher/.venv/`)
- Contents: Python interpreter, installed packages (pip)
- Version control: NEVER (must be in .gitignore)
- Portability: Recreated via `requirements.txt` on each machine

**LAYER 3: DATA (E:\claude-code-data\)**
- Location: `E:\claude-code-data\` (external drive)
- Contents: Downloads, logs, outputs, processed data
- Version control: NEVER
- Portability: Physical transport only (external drive)

**BLOCKING RULE:** Code MUST NEVER be placed on E:\. Data MUST NEVER be committed to Git.

---

## Common Development Commands

### Setting Up a New Agent

```powershell
# Always start from repository root
cd C:\claude-work\repos\Claude-Code-Projetos

# Navigate to agent directory
cd agentes\<agent-name>

# Create virtual environment
python -m venv .venv

# Activate virtual environment (PowerShell)
.venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify setup
where python  # Should point to .venv\Scripts\python.exe
pip list      # Should show only project dependencies, not global packages
```

### Running an Agent

```powershell
# Via PowerShell script (recommended)
cd agentes\<agent-name>
.\run_agent.ps1

# Via manual activation
cd agentes\<agent-name>
.venv\Scripts\activate
python main.py
```

### Testing an Agent

```powershell
cd agentes\<agent-name>
.venv\Scripts\activate
pytest tests\           # If tests exist
python -m unittest      # Alternative test framework
```

### Git Workflow

```bash
# End of work session
git add .
git commit -m "Adiciona <feature/correção/refatoração>"
git push

# Start of work session on different machine
git pull
```

### Adding New Dependencies

```powershell
# ALWAYS activate venv first
cd agentes\<agent-name>
.venv\Scripts\activate

# Install new package
pip install <package-name>

# Update requirements.txt
pip freeze > requirements.txt

# Commit the updated requirements.txt
git add requirements.txt
git commit -m "Adiciona dependência <package-name>"
git push
```

---

## Project Structure

### Code Organization

```
Claude-Code-Projetos/
├── agentes/           # Autonomous monitoring agents (long-running)
│   ├── oab-watcher/   # Monitors OAB (Brazilian Bar Association) daily journal
│   ├── djen-tracker/  # Monitors Electronic Justice Daily
│   └── legal-lens/    # Analyzes legal publications
│
├── comandos/          # Reusable utility commands (single-purpose tools)
│   ├── fetch-doc/     # Downloads documents from specific sources
│   ├── extract-core/  # Extracts core information from documents
│   ├── validate-id/   # Validates identifiers (CPF, CNPJ, OAB, etc)
│   ├── parse-legal/   # Parses legal texts
│   └── send-alert/    # Sends alerts via email/webhook
│
├── skills/            # Claude Code skills (specialized capabilities)
│   ├── ocr-pro/       # Advanced OCR for documents
│   ├── deep-parser/   # Deep parsing of complex structures
│   └── sign-recognition/  # Signature recognition
│
├── shared/            # Shared code between projects
│   ├── utils/         # Utility functions (logging, path management)
│   └── models/        # Data models (publicacao.py, etc)
│
└── docs/              # Additional documentation
    ├── architecture.md
    └── setup.md
```

### Data Organization (External Drive)

```
E:\claude-code-data/
├── agentes/
│   ├── oab-watcher/
│   │   ├── downloads/  # Downloaded PDFs
│   │   ├── logs/       # Execution logs
│   │   └── outputs/    # Processed results
│   ├── djen-tracker/
│   └── legal-lens/
└── shared/
    ├── cache/          # Shared cache
    └── temp/           # Temporary files
```

---

## Path Management

### Accessing Data from Code

Code in `C:\claude-work\repos\Claude-Code-Projetos\` must access data in `E:\claude-code-data\` using:

1. **Relative paths** (when appropriate)
2. **Environment variables** (for cross-machine compatibility)
3. **shared/utils/path_utils.py** (centralized path management)

**NEVER use hardcoded absolute paths** like `E:\claude-code-data\agentes\oab-watcher\downloads\`.

Example from `shared/utils/path_utils.py`:

```python
import os
from pathlib import Path

def get_data_dir(agent_name: str, subdir: str = "") -> Path:
    """
    Returns path to data directory for given agent.

    Args:
        agent_name: Name of agent (e.g., 'oab-watcher')
        subdir: Subdirectory within agent data (e.g., 'downloads', 'logs')

    Returns:
        Path object to data directory
    """
    data_root = Path(os.getenv('CLAUDE_DATA_ROOT', 'E:/claude-code-data'))
    agent_data = data_root / 'agentes' / agent_name

    if subdir:
        return agent_data / subdir
    return agent_data
```

Usage:

```python
from shared.utils.path_utils import get_data_dir

# Get downloads directory for oab-watcher
downloads_dir = get_data_dir('oab-watcher', 'downloads')

# Save file
output_file = downloads_dir / 'publicacao_2025-11-07.pdf'
```

---

## Prohibited Actions (BLOCKING)

These actions **must be refused** with reference to DISASTER_HISTORY.md:

### ❌ Code to External Drive
```powershell
# BLOCKED - Caused 3-day disaster (see DISASTER_HISTORY.md)
cp *.py E:\
mv <projeto> E:\projetos\
```

### ❌ Symlinks with Absolute User Paths
```powershell
# BLOCKED - Not portable across machines (Day 1 of disaster)
mklink /D <dest> C:\Users\pedro\<src>
```

### ❌ PATH with Entire User Directory
```powershell
# BLOCKED - Caused Claude Code crash (Day 2 of disaster)
setx PATH "%PATH%;C:\Users\pedro"

# CORRECT - Only add bin directory
setx PATH "%PATH%;C:\Users\pedro\.local\bin"
```

### ❌ Python Execution Without venv
```powershell
# BLOCKED - Causes version conflicts between machines
pip install <library>  # without .venv activated
python main.py         # without .venv activated

# CORRECT
cd agentes\<agent-name>
.venv\Scripts\activate
pip install <library>
python main.py
```

### ❌ Hardcoded Paths in Configuration/Hooks
```python
# BLOCKED - Breaks when moving between machines (Day 3 of disaster)
LOG_DIR = "C:\\Users\\CMR\\projetos\\logs"

# CORRECT - Use environment variables or path_utils
from shared.utils.path_utils import get_data_dir
LOG_DIR = get_data_dir('oab-watcher', 'logs')
```

### ❌ Committing .venv to Git
```bash
# BLOCKED - Environment is machine-specific
git add .venv/

# CORRECT - Ensure .gitignore includes:
# .venv/
# venv/
# __pycache__/
```

### ❌ Creating 'nul' Files on Windows
```powershell
# BLOCKED - 'nul' is a special device on Windows (like /dev/null on Linux)
# Claude Code may accidentally create these files when confusing Windows/Linux environments

# PROBLEM: Files named 'nul' in directories
agentes\oab-watcher\nul

# DETECTION: Check git status for untracked 'nul' files
git status | grep nul

# IMMEDIATE REMOVAL:
cd agentes\<agent-name>
rm nul  # or: del nul (PowerShell)

# WHY THIS HAPPENS:
# - Redirecting to /dev/null in Linux becomes "nul" on Windows
# - Windows treats 'nul' as special device, but file creation still succeeds
# - Results in empty files that pollute the repository
```

**CRITICAL:** If Claude Code creates a file named `nul` anywhere in the repository:
1. **Immediately delete it** using `rm nul` or `del nul`
2. **Do NOT commit it** to Git
3. **Report the command that created it** so the mistake can be corrected

This typically occurs when using redirections like `> nul` (Windows) instead of `> /dev/null` (Linux), or when accidentally creating files with this reserved name.

---

## Debugging Methodology

**Historical Context:** 3 days were spent debugging symptoms (PATH corruption, broken hooks, wrong npm packages) without identifying the root cause (code on external drive). See DISASTER_HISTORY.md for details.

### Mandatory Approach: 5 Whys

When encountering a non-trivial bug:

1. **Symptom:** [Describe observed behavior]
2. **Why 1?** → [Immediate cause]
3. **Why 2?** → [Deeper cause]
4. **Why 3?** → [Even deeper]
5. **Why 4?** → [Almost at root]
6. **Why 5?** → **[ROOT CAUSE]**

**Only address the root cause.** Fixing symptoms leads to infinite iterations.

Example from disaster:
- **Symptom:** Claude Code freezes on startup
- **Why 1?** PATH is corrupted
- **Why 2?** PATH was modified incorrectly
- **Why 3?** Claude Code instructed adding wrong directory
- **Why 4?** No validation of which subdirectory to add
- **Why 5 (ROOT CAUSE):** System lacked environment isolation, depended on global PATH

**Solution:** Implement virtual environments (venv), not fixing PATH band-aids.

---

## Virtual Environment (venv) Requirements

Virtual environments are **mandatory**, not optional. Historical evidence shows that global Python installations caused invisible version conflicts between machines.

### Creation

```powershell
cd agentes\<agent-name>
python -m venv .venv
```

### Activation Verification

Before executing ANY Python command:

```powershell
# Activate
.venv\Scripts\activate  # PowerShell
# or
.venv\Scripts\activate.bat  # CMD

# Verify
where python  # MUST show path containing .venv
pip list      # MUST show only project dependencies, not global packages
```

### Execution Pattern (Enforced)

```powershell
# Step 1: Navigate to project
cd C:\claude-work\repos\Claude-Code-Projetos\agentes\<agent-name>

# Step 2: Activate venv
.venv\Scripts\activate

# Step 3: Verify activation
(venv) appears in prompt

# Step 4: Install dependencies if needed
pip install -r requirements.txt

# Step 5: Execute script
python main.py
```

---

## Cross-Machine Workflow

This project is designed to work seamlessly across multiple machines (e.g., work and home computers).

### Machine A (Work)

```powershell
# Make changes
cd C:\claude-work\repos\Claude-Code-Projetos
# ... edit code ...

# Commit and push
git add .
git commit -m "Implementa parser de publicações OAB"
git push
```

### Machine B (Home)

```powershell
# Pull latest changes
cd C:\claude-work\repos\Claude-Code-Projetos
git pull

# Environment is independent - recreate if needed
cd agentes\oab-watcher
python -m venv .venv  # Only if .venv doesn't exist
.venv\Scripts\activate
pip install -r requirements.txt

# Execute
python main.py
```

### What Gets Synchronized

- ✅ **Via Git:** Source code (.py), configuration (config.json), documentation (.md), dependencies list (requirements.txt)
- ❌ **NOT synchronized:** Virtual environments (.venv/), data files (E:\claude-code-data\), logs, downloads, outputs

---

## Claude Code Marketplace Plugins

If this project uses Claude Code plugins, they must be **installed manually on each machine** via the Marketplace.

**Required plugins:**
- (List will be populated as plugins are adopted)

**Important:** Plugin binaries (node_modules/, superpowers_cache/, etc.) are **not committed to Git**. Only code that *uses* plugins is version-controlled.

---

## When Making Architectural Changes

Before proposing or implementing any architectural change:

1. **Read DISASTER_HISTORY.md** to understand what went wrong before
2. **Validate against three-layer separation** (Code/Environment/Data)
3. **Test on BOTH machines** (work and home) before considering it "done"
4. **Document the decision** in this file (CLAUDE.md)
5. **Update README.md** if user-facing

---

## References

- **README.md** - User-facing setup instructions and project overview
- **DISASTER_HISTORY.md** - Detailed account of 3-day architectural disaster and lessons learned
- **docs/architecture.md** - In-depth architectural documentation (when created)
- **docs/setup.md** - Step-by-step setup guide (when created)

---

## WSL2 Migration Status

**Sprint 1-2: Complete** ✅

Infrastructure deployed:
- Ubuntu 24.04 LTS
- Node.js v24.11.1 (nvm)
- Claude Code 2.0.42
- Python 3.12.3 + 5 venvs (all agentes)
- npm packages (340) - mcp-servers/djen-mcp-server
- 10 hooks validated

Directory structure: `~/claude-work/repos/Claude-Code-Projetos`

See `WSL_SETUP.md` and `CHANGELOG.md` for details.

---

**Last updated:** 2025-11-15
**Maintained by:** PedroGiudice
**For Claude Code instances operating in:** `~/claude-work/repos/Claude-Code-Projetos` (WSL2)
- add to memory
- add
- add to session-context and episodic-memory