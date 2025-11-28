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

## Working Directory Management (Critical)

**CRITICAL:** When executing Bash commands via tools, the `pwd` (working directory) **persists across commands** and affects hook execution on subsequent user prompts.

### The Problem

User hooks (UserPromptSubmit, SessionStart, etc.) execute with paths relative to the **current `pwd`**. If Claude leaves `pwd` in a subdirectory, the next user prompt triggers hooks with the wrong working directory, causing failures:

```bash
# Claude executes:
cd skills  # pwd changes to .../skills/

# User submits next prompt
# Hooks try to execute:
.claude/hooks/hook-wrapper.js
# → Expands to: .../skills/.claude/hooks/hook-wrapper.js ❌ NOT FOUND
```

**Real incident (2025-11-19):** After `cd skills` to list skills, hooks failed with:
- `.claude/monitoring/hooks/*.sh: not found`
- `Cannot find module '.../skills/.claude/hooks/hook-wrapper.js'`

### Mandatory Practices

When executing Bash commands that change directories:

1. **PREFER relative paths** (avoid `cd` entirely):
   ```bash
   # ✅ GOOD
   ls skills/
   find skills -name "SKILL.md"
   cat agentes/oab-watcher/main.py

   # ❌ AVOID
   cd skills
   ls
   # ← pwd stays in skills/
   ```

2. **If `cd` is necessary**, use **subshells** for single operations:
   ```bash
   # ✅ GOOD - pwd returns to original automatically
   (cd skills && ls -la)

   # ❌ AVOID - pwd stays changed
   cd skills && ls -la
   ```

3. **For multiple operations**, return to root explicitly:
   ```bash
   # ✅ GOOD
   cd skills && ls && cat pdf/SKILL.md && cd ..

   # ✅ BETTER - guaranteed return even if commands fail
   cd skills; ls; cat pdf/SKILL.md; cd ..
   ```

4. **VERIFY `pwd` before complex operations**:
   ```bash
   pwd  # Should show: /home/cmr-auto/claude-work/repos/Claude-Code-Projetos
   ```

5. **After ANY directory change**, confirm return to root:
   ```bash
   cd agentes/oab-watcher
   # ... perform operations ...
   cd ~/claude-work/repos/Claude-Code-Projetos  # Return to absolute root path
   pwd  # Verify
   ```

### Why This Matters

**Hooks are non-blocking** - they fail silently with warnings. This means:
- User prompts still execute (Claude continues working)
- Hook failures may go unnoticed
- Context collection, monitoring, and automation break silently

**Always assume the next user prompt depends on clean `pwd` state.**

---

## Hook Validation Protocol

**CRITICAL:** After impactful codebase changes (hooks, dependencies, configs), verify hook execution logs.

### When to Validate

- After modifying hook files (.claude/hooks/*)
- After changing hook dependencies (node_modules, Python packages)
- After updating settings.json hook configuration
- After removing/renaming files referenced by hooks

### Validation Checklist

```bash
# 1. Check hook execution logs
tail -50 ~/.vibe-log/hooks.log  # Vibe-log hooks
cat .claude/monitoring/logs/hooks.log  # Monitoring hooks
cat .claude/hooks/lib/skill-tracking.log  # Skill detection

# 2. Verify all hook files exist
cat .claude/settings.json | jq -r '.hooks[][] | .hooks[] | .command'

# 3. Test critical hooks manually
python3 .claude/hooks/improve-prompt.py < test-input.json
node .claude/hooks/context-collector.js

# 4. Check system-reminders in next prompt
# Look for "hook success" or "hook error" messages
```

### Red Flags

- `MODULE_NOT_FOUND` errors → Missing dependency or wrong path
- `Another hook execution is already in progress` → Vibe-log concurrency (benign)
- `command not found` → Script not executable or missing shebang
- Silent failures → Hook returns non-zero exit but marked as "Success"

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
# Standard workflow
git pull  # Start of work session
# ... make changes ...
git add .
git commit -m "feat: adiciona <feature/correção/refatoração>"
git push  # End of work session
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
├── skills/            # Claude Code skills (PROJECT-SPECIFIC, CUSTOM)
│   ├── ocr-pro/       # Advanced OCR for documents
│   ├── deep-parser/   # Deep parsing of complex structures
│   ├── frontend-design/ # Frontend design system skill
│   └── ... (37 total) # Each MUST have SKILL.md to be functional
│
├── .claude/           # Claude Code configuration (MANAGED, SETTINGS)
│   ├── skills/        # Managed/official skills (DO NOT add custom skills here)
│   │   ├── anthropic-skills/  # Official Anthropic skills collection
│   │   └── superpowers/       # Advanced Claude Code capabilities
│   ├── hooks/         # Execution hooks (UserPromptSubmit, SessionStart, etc)
│   ├── agents/        # Agent definitions (.md files)
│   └── statusline/    # Statusline UI configuration
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

### ❌ Custom Skills in .claude/skills/
```bash
# BLOCKED - Custom skills MUST go in skills/, NOT .claude/skills/
mv my-custom-skill .claude/skills/  # ❌ WRONG

# CORRECT - Custom skills in skills/ root
mv my-custom-skill skills/  # ✅ CORRECT
```

**Why this is blocked:**
- `.claude/skills/` = Managed/official skills (anthropic-skills, superpowers)
- `skills/` = Project-specific custom skills
- Mixing them causes count confusion and breaks statusline tracking
- Each skill in `skills/` MUST have `SKILL.md` to be functional

**Detection:**
```bash
# Check for misplaced skills
find .claude/skills -maxdepth 1 -type d -name "*" | while read dir; do
  [ -f "$dir/SKILL.md" ] && echo "⚠️  MISPLACED: $dir should be in skills/"
done
```

**Correct structure:**
- `skills/` → 37 custom skills (34 functional with SKILL.md, 3 placeholders)
- `.claude/skills/anthropic-skills/` → 13 official sub-skills
- `.claude/skills/superpowers/` → 20 official sub-skills

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

Virtual environments are **mandatory**, not optional. Historical evidence shows that global Python installations cause version conflicts and dependency contamination.

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

## Non-Negotiable Git Discipline

This project requires strict Git workflow discipline to maintain code quality and enable reliable collaboration.

### Commit Frequently

**Rule:** Commit and push changes **at minimum** at the end of each work session. Ideally, commit after completing each logical unit of work.

```bash
# After completing a feature/fix
git add .
git commit -m "feat: implementa parser de publicações OAB"
git push

# Don't let uncommitted changes accumulate
# If you have to stop work, commit what you have
```

**Why:**
- Prevents loss of work
- Creates clear development history
- Enables easy rollback if needed
- Keeps codebase synchronized

### Branch Strategy for Complex Features

**Rule:** Features that will take **more than 2 sprints** to complete MUST be developed in separate branches.

```bash
# Create feature branch
git checkout -b feature/sistema-busca-jurisprudencia

# Work on feature (multiple commits)
git add .
git commit -m "feat: adiciona crawler de tribunais"
git push origin feature/sistema-busca-jurisprudencia

# Continue working...
git commit -m "feat: adiciona parser de acórdãos"
git push

# When feature is complete and tested
git checkout main
git pull
git merge feature/sistema-busca-jurisprudencia
git push
git branch -d feature/sistema-busca-jurisprudencia
```

**Why:**
- Keeps `main` branch stable and deployable
- Allows experimental work without breaking production
- Enables parallel development of multiple features
- Provides clear feature boundaries in history

### What Gets Synchronized via Git

- ✅ **Committed:** Source code (.py), configuration (config.json), documentation (.md), dependencies (requirements.txt)
- ❌ **NOT committed:** Virtual environments (.venv/), data files, logs, downloads, outputs (all in .gitignore)

---

## Claude Code Marketplace Plugins

Project plugins must be installed via the Marketplace.

**Required plugins:**
- (List will be populated as plugins are adopted)

**Important:** Plugin binaries (node_modules/, superpowers_cache/, etc.) are **not committed to Git**. Only code that *uses* plugins is version-controlled.

---

## When Making Architectural Changes

Before proposing or implementing any architectural change:

1. **Read DISASTER_HISTORY.md** to understand what went wrong before
2. **Validate against three-layer separation** (Code/Environment/Data)
3. **Test thoroughly** in clean environment (fresh clone + venv setup)
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
- Python 3.12.3 + 5 venvs (agentes) + 1 venv global (root)
- npm packages (340) - mcp-servers/djen-mcp-server
- 10 hooks validated

Directory structure: `~/claude-work/repos/Claude-Code-Projetos`

See `WSL_SETUP.md`, `QUICK-REFERENCE.md`, and `CHANGELOG.md` for details.

---

## WSL2 Quick Start

**Comandos essenciais para desenvolvimento diário no WSL2:**

### Navegação Básica
```bash
# Ir para projeto
cd ~/claude-work/repos/Claude-Code-Projetos

# Verificar status
git status
```

### Ativar venv de um Agente
```bash
# Exemplo: oab-watcher
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/oab-watcher
source .venv/bin/activate  # ⚠️ Linux: bin/activate (não Scripts\activate)

# Verificar ativação
which python  # Deve apontar para .venv/bin/python
```

### Ativar venv Global (Shared)
```bash
cd ~/claude-work/repos/Claude-Code-Projetos
source .venv/bin/activate

# Usar para: testes compartilhados, linting, type checking
pytest
ruff check .
mypy .
```

### Executar Agente
```bash
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/<agent-name>
source .venv/bin/activate
python main.py
```

### Git Workflow
```bash
# Commit e push
git add .
git commit -m "feat: implementa feature X"
git push

# Pull changes (outra máquina)
git pull
```

### Hooks - Validar Manualmente
```bash
cd ~/claude-work/repos/Claude-Code-Projetos

# Testar Legal-Braniac
node .claude/hooks/invoke-legal-braniac-hybrid.js

# Testar session context
node .claude/hooks/session-context-hybrid.js
```

**Diferenças Windows vs WSL:**
| Ação | Windows | WSL |
|------|---------|-----|
| Ativar venv | `.venv\Scripts\activate` | `source .venv/bin/activate` |
| Path separator | `\` (backslash) | `/` (forward slash) |
| Line endings | CRLF | LF |

---

---

## vibe-log Gordon Co-pilot Integration

**Status**: ✅ Installed and tested (2025-11-18)
**Personality**: Gordon (tough love, business-focused)

### Architecture

**Prompt Analysis Flow**:
```
User prompt → UserPromptSubmit hook → vibe-analyze-prompt.js
           → npx vibe-log-cli analyze-prompt --stdin
           → Claude SDK analysis (local)
           → ~/.vibe-log/analyzed-prompts/{sessionId}.json
```

**Analysis Output Format**:
```json
{
  "score": 0-100,
  "quality": "excellent|good|fair|poor",
  "suggestion": "Gordon's feedback",
  "actionableSteps": "Specific improvements",
  "contextualEmoji": "🎯",
  "timestamp": "ISO 8601",
  "sessionId": "uuid",
  "originalPrompt": "user's prompt"
}
```

### Installation

```bash
npx vibe-log-cli
# Select: "Status Line - Strategic Co-pilot"
# Choose personality: Gordon
# Enable usage metrics: Yes (powered by ccusage)
```

**What gets installed**:
- ✅ Hook: `npx vibe-log-cli analyze-prompt` (via UserPromptSubmit)
- ✅ Analysis engine: Local Claude SDK
- ✅ Storage: `~/.vibe-log/analyzed-prompts/`
- ⚠️ Statusline: Requires **disabling** existing statusline in `.claude/settings.json`

### Critical Discovery

**Problem**: vibe-log statusline does NOT auto-activate when existing statusline is configured.

**Solution**: Temporarily disable statusline in settings.json:
```json
"_statusLine_DISABLED_FOR_VIBE_LOG": {
  "_comment": "Renamed to test vibe-log Gordon Co-pilot",
  // ... original config
}
```

**Restore**: Rename back to `"statusLine"` to revert.

### Files

- **Backups**: `.claude/settings.json.backup`, `BACKUP_INFO.md`
- **Analyses**: `~/.vibe-log/analyzed-prompts/{sessionId}.json`
- **Debug logs**: `~/.vibe-log/hook-debug.log`, `statusline-debug.log`

### Performance

- **Analysis time**: <2s (background, non-blocking)
- **Storage**: ~5KB per analysis
- **Impact**: Minimal (spawns detached process)

### Examples

**Good prompt** (score 85+):
```
"Implement user authentication with JWT tokens in the auth/ directory.
Use bcrypt for password hashing. Include login, register, and logout endpoints."
```

**Poor prompt** (score <40):
```
"teste"
→ Gordon: "Your message is just one word - we need to understand what you're building."
```

### Integration with Legal-Braniac

**Current state**:
- vibe-log Gordon: Prompt quality analysis
- Legal-Braniac: Agent/skill orchestration

**Decision**: Keep SEPARATE (see "Rejected Architectural Decisions" below).

---

## Rejected Architectural Decisions

### ❌ Unified Statusline (Gordon + Legal-Braniac)

**Date:** 2025-11-19
**Status:** REJECTED - "Enxugando Gelo"

#### What Was Proposed

Criar statusline unificada combinando:
1. **vibe-log Gordon Co-pilot** - Análise de qualidade de prompts (score, suggestion)
2. **Legal-Braniac tracking** - Contagem de agentes/skills/hooks
3. **Powerline visual design** - Design profissional com arrows ANSI 256

**Formato proposto:**
```
🎯 Gordon: 85/100 - Clear prompt │ Legal-Braniac ● │ 7ag 34sk 6h │ git main* │ venv ●
```

#### Why It Seemed Like a Good Idea

- ✅ Informação útil em tempo real
- ✅ Design visual profissional
- ✅ "Melhor dos dois mundos" (Gordon + Braniac)
- ✅ Tecnicamente viável (~130-150 linhas código)

#### Why It Was Actually "Enxugar Gelo"

**1. Duplicação de Informação**
- Gordon analysis: Já disponível via vibe-log terminal output
- Legal-Braniac status: Já disponível via logs/session files
- **Benefício:** Ver em formato "mais bonito"
- **Custo:** 130-150 linhas código + manutenção contínua

**2. Dependência de Sistemas Externos**
- **vibe-log:** Sistema externo - se mudar estrutura JSON, quebra
- **sessionId matching:** Frágil - se sessionIds divergirem, falha silenciosamente
- **Comparação:** "Construir ponte entre duas ilhas que estão se movendo"

**3. ROI Negativo**
```
Ganho:  Ver info na statusline (visual)
Custo:  - 130-150 linhas código
        - Manutenção contínua
        - Ponto de falha adicional
        - Acoplamento a sistemas externos
        - Debugging quando quebrar

ROI: NEGATIVO
```

**4. Alternativas Mais Simples Existem**
```bash
# Aliases bash (30 segundos de setup)
alias gordon='cat ~/.vibe-log/analyzed-prompts/$(cat .claude/hooks/legal-braniac-session.json | jq -r .sessionId).json | jq -r "Gordon: \(.score)/100 - \(.suggestion)"'

alias braniac='test -f .claude/hooks/legal-braniac-session.json && echo "Braniac ●" || echo "Braniac ○"'
```

#### Key Lessons Learned

**1. "Tecnicamente Viável" ≠ "Vale a Pena"**
- Código pode ser simples (~100 linhas)
- Mas manutenção + acoplamento + duplicação = enxugar gelo

**2. Perguntar "Por Que Isso Não Existe Já?"**
- Se vibe-log não tem plugin system, há razão
- Se Legal-Braniac não tem statusline nativa, há razão
- Tentar forçar integração = nadar contra a corrente

**3. Informação Duplicada = Sinal de Problema**
- Se informação JÁ existe em outro lugar
- E você quer apenas "formato diferente"
- Provavelmente é enxugar gelo

**4. Questionar o Benefício Real**
- "Mais bonito" não é benefício técnico
- "Mais conveniente" raramente justifica manutenção contínua
- "Gostaria de ter" ≠ "Necessário para produtividade"

#### Decision

**KEEP SEPARATE:**
- ✅ CLI: vibe-log nativo (Gordon analysis)
- ✅ Legal-Braniac: Logs/session files (quando necessário)
- ✅ Aliases bash: Se precisar acesso rápido

**RATIONALE:**
- Zero código custom = zero manutenção
- Informação já disponível = não duplicar
- Sistemas independentes = menos acoplamento
- Simplicidade > "visual bonito"

#### References

- Prompt detalhado: `.claude/statusline/CLAUDE-CODE-WEB-PROMPT.md` (780 linhas)
- Análise técnica: Session 2025-11-19 (conversação completa)
- Limitações Claude Code Web: `README.md` - "Limitações Conhecidas"

---

## TUI Template Implementation (2025-11-27)

### Overview

Implementacao completa de template maximalista para TUIs com Textual/Python.

**Localizacao:** `tui-template/`
**Versao:** v0.1.0
**Commit:** `5eb0e41`

### Estatisticas

| Metrica | Valor |
|---------|-------|
| Arquivos Python | 39 |
| Linhas de codigo | 9,335 |
| Temas | 5 |
| Widgets | 12+ |
| Spinners customizados | 11 |

### Componentes Implementados

**Temas:**
- `vibe-neon` - Dracula/Cyberpunk (padrao)
- `vibe-matrix` - Matrix verde
- `vibe-synthwave` - Rosa/roxo
- `minimal-dark` - Minimalista escuro
- `minimal-light` - Minimalista claro

**Widgets Base:**
- Header, Sidebar, LogPanel, ProgressPanel
- StatusBar, FileBrowser, ResultViewer

**Widgets Avancados (Powerline/Spinners):**
- SpinnerWidget (11 spinners: claude, thinking, pulse_bar, neon, wave, matrix, processing, orbital, dna, minimal, cyber)
- Blinker, InputCursor
- PowerlineBar, PowerlineHeader, PowerlineFooter, PowerlineBreadcrumb

**Arquitetura:**
- Workers assincronos com cancelamento
- Sistema de mensagens Textual
- Models Pydantic para validacao
- Testes pytest

### Agentes Utilizados na Implementacao

| Agente | Uso |
|--------|-----|
| `desenvolvimento` | Fases 1-13 (estrutura, widgets, workers, screens) |
| `gemini-assistant` | Geracao de spinners, powerline widgets, review |
| `frontend-developer` | Validacao de widgets e CSS |
| `code-architecture-reviewer` | Review de arquitetura completa |
| `frontend-error-fixer` | Correcao de 7 bugs criticos |

### Bugs Criticos Corrigidos

1. CSS Variable `$text-muted` nao definida
2. Message attributes incorretos (7 mensagens)
3. TUIApp constructor sem parametros
4. Timer leak em PowerlineHeader
5. CSS transform nao suportado pelo Textual
6. RGBA background incompativel

### Como Usar

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/tui-template
pip install -e ".[dev]"
python -m tui_app
# Ou: ./scripts/run_dev.sh
```

### Documentacao Gerada

- `tui-template/README.md` - Documentacao principal
- `tui-template/CHANGELOG.md` - Historico v0.1.0
- `tui-template/BUG_FIXES_APPLIED.md` - Correcoes aplicadas
- `tui-template/MESSAGE_CONTRACT_FIXES.md` - Contratos de mensagens

### Licoes Aprendidas

1. **Gemini CLI como segunda opiniao** - Util para gerar codigo repetitivo (spinners, widgets) e review de arquitetura
2. **Frontend agents essenciais** - Identificaram 7 bugs criticos antes dos testes
3. **Message contracts** - Importante validar consistencia entre emissor/receptor
4. **CSS Textual** - Nao suporta todas propriedades CSS web (transform, rgba)

---

## Gemini CLI Integration (2025-11-27)

### Setup

Agente `gemini-assistant` adicionado para integracao com Gemini CLI:

**Localizacao:** `.claude/agents/gemini-assistant.md`

### Casos de Uso

1. **Segunda opiniao** em arquitetura/codigo
2. **Analise de contexto grande** (1M+ tokens)
3. **Geracao de codigo repetitivo** (spinners, widgets)
4. **Review de especificacoes**

### Comandos

```bash
# Query simples
gemini "Sua pergunta aqui"

# Analise de arquivo
cat arquivo.py | gemini "Analise este codigo"

# Output JSON
gemini "Liste melhorias" --output-format json
```

### Limitacoes

- Requer autenticacao Google OAuth
- Rate limits da API Gemini
- Sem contexto persistente entre chamadas

---

## Custom Agents - Descoberta e Registro (2025-11-27)

### CRÍTICO: Agentes só ficam disponíveis após reiniciar sessão

O Claude Code descobre agentes automaticamente dos arquivos `.md` em:
- `.claude/agents/` (project-level)
- `~/.claude/agents/` (user-level global)

**PORÉM**: A descoberta acontece **NO INÍCIO DA SESSÃO**.

Se você criar um agente DURANTE a sessão, ele **NÃO estará disponível** até reiniciar o Claude Code.

### Sintoma
```
Task(subagent_type='meu-novo-agente')
# Erro: "Agent type 'meu-novo-agente' not found"
```

### Solução
1. Criar o arquivo `.claude/agents/meu-novo-agente.md`
2. **Reiniciar a sessão do Claude Code** (fechar e abrir novamente)
3. O agente estará disponível

### Verificação
Para confirmar quais agentes estão disponíveis na sessão atual, a lista aparece na mensagem de erro quando um agente não é encontrado.

### Arquivos Relevantes
- `.claude/hooks/lib/agent-auto-discovery.js` - Script de auto-discovery (para Legal-Braniac)
- `.claude/hooks/agent-tools-mapping.json` - Mapeamento gerado (orquestração interna)

### Agente TUI-Master
Criado agente especialista em Textual TUI:
- **Arquivo:** `.claude/agents/tui-master.md` (666 linhas)
- **Global:** `~/.claude/agents/tui-master.md`
- **Uso:** `Task(subagent_type='tui-master', prompt='...')` (após reiniciar sessão)

---

## Legal Extractor TUI - Refactoring CSS (2025-11-27)

### Problema Identificado

O `legal-extractor-tui` tinha **17 widgets com DEFAULT_CSS** que sobrescreviam os estilos do `widgets.tcss`, impedindo que temas funcionassem corretamente.

### Correções Aplicadas

**1. Timer Leak em PowerlineHeader (CRÍTICO)**
```python
# ANTES (bug)
def __init__(self, ...):
    self.timer = self.set_interval(1, self._update_time)  # LEAK!

# DEPOIS (correto)
def __init__(self, ...):
    self.timer = None

def on_mount(self) -> None:
    self.timer = self.set_interval(1, self._update_time)
```

**2. DEFAULT_CSS Removido de 17 Widgets:**
- config_panel, extraction_progress, StageIndicator
- file_selector, file_browser, header
- powerline_breadcrumb, PowerlineBar, PowerlineHeader, PowerlineFooter
- StageProgress, PipelineProgress, result_viewer
- results_panel, sidebar, status_bar, system_selector

**3. ~300 linhas CSS adicionadas ao widgets.tcss**

### Como Executar

```bash
cd legal-extractor-tui
./run.sh          # Modo normal
./run.sh --dev    # Modo dev (Textual DevTools)
```

**Nota:** O script usa `legal_extractor_tui.app:LegalExtractorApp` (module path), não file path.

### Resultado

- ✅ Temas funcionam corretamente
- ✅ ~726 linhas de CSS duplicado removidas
- ✅ Single source of truth para estilos (widgets.tcss)
- ✅ Timer leak corrigido

### Commits

- `d981fd1` - refactor: remove DEFAULT_CSS from widgets
- `e6a3e49` - fix: use module path in textual run command

---

## TUI Elite Squad - Specialized Agents (2025-11-28)

### Arquitetura Implementada

Criada squad de 4 agentes especializados + 1 generalista com shared knowledge base.

**Problema Resolvido:**
- `tui-master.md` original tinha ~600 linhas de conhecimento embutido
- Conhecimento duplicava/conflitava com outras fontes
- Risco de inconsistencias entre agentes

**Solucao:** Single Source of Truth em `skills/tui-core/`

### Knowledge Base (`skills/tui-core/`)

| Arquivo | Linhas | Conteudo |
|---------|--------|----------|
| `KNOWLEDGE_INDEX.md` | ~100 | Indice central |
| `rules.md` | ~200 | Anti-alucinacao TCSS |
| `tcss-reference.md` | ~340 | Referencia CSS completa |
| `patterns.md` | ~460 | Padroes de codigo |
| `theme-guide.md` | ~265 | Sistema de temas |
| `widget-catalog.md` | ~380 | Catalogo de widgets |
| `bug-patterns.md` | ~340 | Bugs criticos e solucoes |
| `debugging-guide.md` | ~230 | Workflow de debug |

### Agentes Especializados (`.claude/agents/`)

| Agente | Role | Tools | Restricoes |
|--------|------|-------|------------|
| `tui-architect` | Planejamento | Read, Grep, Glob | NAO escreve codigo |
| `tui-designer` | TCSS/Temas | Read, Write, Edit, Glob, Grep | NAO escreve Python |
| `tui-developer` | Python | All | NAO escreve TCSS visual |
| `tui-debugger` | Diagnostico | Read, Bash, Grep, Glob | NAO modifica codigo |
| `tui-master` | Generalista | All | Refatorado para usar KB |

### Workflow

```
Claude Principal (orquestrador)
       |
   ┌───┴───┐
   |       |
tui-architect ──> tui-designer ──> tui-developer
                       |               |
                       └───────┬───────┘
                               |
                         tui-debugger

tui-master = fallback para tarefas simples
```

### Invocacao

```python
Task(subagent_type='tui-architect', prompt='...')
Task(subagent_type='tui-designer', prompt='...')
Task(subagent_type='tui-developer', prompt='...')
Task(subagent_type='tui-debugger', prompt='...')
Task(subagent_type='tui-master', prompt='...')
```

### IMPORTANTE: Orquestracao de Agentes

**O Claude Code NAO possui orquestracao nativa de agentes.**

Cada agente e independente. O workflow e documentado no `SQUAD_MANIFEST.md` e seguido pelo Claude principal.

### Fontes Primarias Usadas

1. `legal-extractor-tui/Guia-completo-de-CSS-TCSS-Textual-0.80.0.md` (500 linhas)
2. `legal-extractor-tui/Research-templates-guidance-TUI-TEXTUAL.md` (228 linhas)
3. `tui-template/BUG_FIXES_APPLIED.md` (322 linhas)
4. `tui-template/MESSAGE_CONTRACT_FIXES.md` (475 linhas)

### Commit

- `5405fe6` - feat(agents): implement TUI Elite Squad with shared knowledge base

---

**Last updated:** 2025-11-28
**Maintained by:** PedroGiudice
**For Claude Code instances operating in:** `~/claude-work/repos/Claude-Code-Projetos` (WSL2)
- add explíto e curto que podem aparecer mensagens de erro, mas que não são VERDADEIROS erros de hook.
- add Desativei autocompact
- add to all memoories
- add focando em adicionar as implementações feitas, as descobertas e o que ainda falta do roadmap
- add
- add
- add
- add
- add
- Use descriptive names and be thorough documenting test, results and next steps