# REPOSITORY CLEANUP, TOOL ANALYSIS & REORGANIZATION

## OPERATIONAL SETUP

### Step 0: Activate Gemini Agents
Before any analysis, attempt to activate **two Gemini agents** for large-context processing:
- **Agent 1**: Analyze `ferramentas/` (development tools)
- **Agent 2**: Analyze `docker/services/` (production services)

If two agents cannot be activated, proceed with a single agent processing both sequentially.

These agents will read and process the entire repository to build comprehensive context.

---

## CRITICAL PRINCIPLE (REVISED)

**⚠️ WARNING: Docker copies may be DEGRADED, not canonical.**

The original assumption that "Docker = truth" is being challenged. Many tools in `ferramentas/` were developed BEFORE Docker containerization. The Docker versions may be:
- Incomplete copies
- Missing recent development
- Simplified/stripped versions
- Out of sync with source

**NEW PRINCIPLE: Identify the MOST FUNCTIONAL version, regardless of location.**

---

## PHASE 1: IMPARTIAL FILE CLASSIFICATION

Execute a thorough, unbiased classification of ALL repository files. This classification will inform all subsequent decisions.

### Classification Schema:

For each file/directory, capture:
```yaml
path: /full/path/to/item
type: [code|config|doc|test|script|data|generated|unknown]
category: [core|tool|infrastructure|documentation|archive|experimental]
size: bytes
last_modified: date
functional_role: "Brief description of what this does"
dependencies: [list of what depends on this]
```

### Launch Parallel Classification Agents:

| Agent | Scope | Focus |
|-------|-------|-------|
| Agent A | `/legal-workbench/ferramentas/*` | Tool source code analysis |
| Agent B | `/legal-workbench/docker/*` | Docker service analysis |
| Agent C | `/legal-workbench/poc-*` | Experimental code analysis |
| Agent D | Repository root + `/docs/` + `/skills/` | Documentation & config |
| Agent E | `/_archived/` + `/adk-agents/` + `/comandos/` | Supporting infrastructure |

**Constraint**: Classification must be DESCRIPTIVE and UNBIASED. Do not make value judgments during classification—only describe what exists.

---

## PHASE 2: TOOL DISCREPANCY ANALYSIS

### Known Tool Pairs to Analyze:

| Ferramentas (Dev) | Docker (Prod) | Analysis Required |
|-------------------|---------------|-------------------|
| `legal-text-extractor/` | `docker/services/text-extractor/` | Compare completeness |
| `legal-doc-assembler/` | `docker/services/doc-assembler/` | Compare completeness |
| `stj-dados-abertos/` | `docker/services/stj-api/` | Same tool? Different? |
| `trello-mcp/` | `docker/services/trello-mcp/` | Compare completeness |
| `prompt-library/` | (none) | Orphan evaluation |

### For Each Pair, Determine:

```markdown
## Tool: [NAME]

### Ferramentas Version:
- File count: X
- LOC estimate: X
- Has tests: Yes/No (count)
- Has documentation: Yes/No
- Dependencies: [list]
- Key features: [list]
- Maturity signals: [version numbers, dates, completeness]

### Docker Version:
- File count: X
- LOC estimate: X
- Has tests: Yes/No (count)
- Dockerfile present: Yes/No
- Dependencies: [list]
- Key features: [list]
- Appears to be: [full copy | partial copy | stub | independent]

### Discrepancies Found:
- [List specific differences]

### Functional Density Score:
- Ferramentas: X/10 (features per complexity)
- Docker: X/10 (features per complexity)

### Recommendation: [ferramentas | docker | merge | archive both]
```

---

## PHASE 3: OPTIMAL TOOL SELECTION

### Selection Criteria (Priority Order):

1. **Functional Density** — Most features per unit of complexity
2. **Completeness** — Has tests, docs, examples
3. **Maintainability** — Clean code, clear structure
4. **Integration Readiness** — Works with current architecture

**NOT minimalism** — We want the BEST tools, not the fewest.

### Decision Matrix Template:

| Tool | Best Version | Location to Keep | Action for Other |
|------|--------------|------------------|------------------|
| text-extractor | ? | ? | Archive/Delete |
| doc-assembler | ? | ? | Archive/Delete |
| stj-api | ? | ? | Archive/Delete |
| trello-mcp | ? | ? | Archive/Delete |
| prompt-library | ? | ? | Integrate/Archive |

---

## PHASE 4: ROOT DIRECTORY CLEANUP

### Allowed in Repository Root (6 files only):
- `README.md`, `CLAUDE.md`, `ARCHITECTURE.md`
- `requirements.txt`, `LICENSE`, `.gitignore`

### File Disposition:

| Pattern | Action | Destination |
|---------|--------|-------------|
| `*.html` | Move | `docs/visualizations/` |
| `*.ps1` | Move | `scripts/windows/` |
| `diagnostico-*.txt` | Delete | — |
| `*:Zone.Identifier` | Delete | — |
| `gemini_context.txt` | Delete | (16MB generated) |
| `repomix-output.xml` | Delete | (32MB generated) |
| `GEMINI.md` | Move | `docs/` |
| `DISASTER_HISTORY.md` | Move | `docs/` |
| `WSL2-INSTALL-GUIDE.md` | Move | `docs/setup/` |
| `progress.json` | Archive | `_archived/` |

---

## PHASE 5: LEGAL-WORKBENCH STRUCTURE

### Target State:
```
legal-workbench/
├── docker/              ← Production services (after consolidation)
│   ├── services/
│   ├── docker-compose.yml
│   └── ...
├── src/                 ← Consolidated source (if ferramentas wins)
│   ├── text-extractor/
│   ├── doc-assembler/
│   ├── stj-api/
│   ├── trello-mcp/
│   └── prompt-library/
├── poc/                 ← Experimental (consolidated)
│   ├── fasthtml-stj/
│   ├── react-stj/
│   └── reflex-stj/
├── modules/             ← Streamlit UI wrappers
├── docs/                ← Documentation
├── app.py
├── config.yaml
└── requirements.txt
```

### Consolidation Actions:
```bash
# Consolidate POCs
mkdir -p legal-workbench/poc
mv legal-workbench/poc-fasthtml-stj legal-workbench/poc/fasthtml-stj
mv legal-workbench/poc-react-stj legal-workbench/poc/react-stj
mv legal-workbench/poc-reflex-stj legal-workbench/poc/reflex-stj

# If ferramentas/ tools are superior:
mv legal-workbench/ferramentas legal-workbench/src
# Update Docker to reference src/ instead of copying
```

---

## EXECUTION GUIDELINES

### Parallel Agent Deployment:
Use as many agents as purposeful—no fixed number. Examples:
- One agent per tool comparison
- Separate agents for doc classification vs code classification
- Dedicated agent for dependency analysis

### Preserve Git History:
```bash
git mv old_path new_path  # Always use git mv
```

### Output Requirements:

1. **Impartial Classification Report** (CSV or Markdown table)
2. **Tool Comparison Matrix** with functional density scores
3. **Recommended Actions** with justification
4. **Execution Script** (if confident in recommendations)

---

## VERIFICATION CHECKLIST

After reorganization:
- [ ] Repository root: ≤6 files
- [ ] legal-workbench root: Only essential files + directories
- [ ] No duplicate tools (one canonical location per tool)
- [ ] No Zone.Identifier files
- [ ] No generated dumps (>1MB)
- [ ] All POCs under `poc/`
- [ ] Clear documentation of tool locations

---

## CONSTRAINT REMINDER

**The classification MUST be impartial.**

Do not assume Docker is better. Do not assume ferramentas is better. Measure, compare, and let the data inform the decision. The goal is to find the **most effective and functional** version of each tool, prioritizing **functional density over minimalism**.
