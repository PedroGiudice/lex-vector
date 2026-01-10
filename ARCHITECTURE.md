# ARCHITECTURE.md - North Star

Sistema de automacao juridica brasileira com agentes Python.

---

## Principios Fundamentais

### 1. Separacao de Camadas (Inviolavel)

| Camada | Local | Git |
|--------|-------|-----|
| **Codigo** | `~/claude-work/repos/lex-vector/` | Sim |
| **Ambiente** | `agentes/*/.venv/` | Nunca |
| **Dados** | `~/claude-code-data/` | Nunca |

**Violacao desta regra causou 3 dias de sistema inoperavel.** Ver `DISASTER_HISTORY.md`.

### 2. Ambiente Virtual Obrigatorio

Todo codigo Python executa dentro de `.venv`:
```bash
cd agentes/<nome>
source .venv/bin/activate
python main.py
```

### 3. Git Como Transporte

- Codigo sincronizado via `git push/pull`
- Nunca transportar codigo via HD externo
- Commit ao fim de cada sessao de trabalho

---

## Estrutura do Projeto

```
lex-vector/
├── legal-workbench/      # Lex-Vector (LV) - PROJETO PRINCIPAL
│   ├── frontend/         # React frontend (Next.js 15 + React 19)
│   ├── ferramentas/      # Python tools (stj-dados-abertos, legal-text-extractor)
│   ├── docker/           # Services (stj-api, trello-mcp, doc-assembler, etc)
│   └── docs/             # LV-specific documentation
├── docs/                 # Global documentation and plans
├── infra/                # Infrastructure configs (oracle)
├── _archived/            # Archived code for future reference
└── .claude/              # Config (agents, hooks, skills managed)
```

> **Nota:** Projetos experimentais (adk-agents, CCui, etc) foram migrados para
> https://github.com/PedroGiudice/claude-experiments

---

## Decisoes Arquiteturais

### ADR-001: Python + venv por Agente
Cada agente tem `.venv` isolado. `requirements.txt` obrigatorio.

### ADR-002: Dados Fora do Repositorio
Dados em `~/claude-code-data/`, nunca em Git. Usar `shared/utils/path_utils.py`.

### ADR-003: Hooks Nao-Bloqueantes
Hooks com timeout <500ms. Usar async, caching, graceful degradation.

### ADR-004: Skills Managed
Todas as skills em `.claude/skills/` (managed pelo Claude Code).

### ADR-005: Bun para Hooks JS
Hooks JS usam `bun run` em vez de `node` (~25% mais rapido). Bun 1.3.4 instalado em `~/.bun`.

---

## Restricoes (Blocking)

| Acao | Status | Referencia |
|------|--------|------------|
| Codigo em HD externo | BLOQUEADO | DISASTER_HISTORY.md |
| Python sem venv | BLOQUEADO | CLAUDE.md |
| .venv no Git | BLOQUEADO | .gitignore |
| Paths absolutos hardcoded | BLOQUEADO | CLAUDE.md |

---

## Stack

Python 3.11 | Bun 1.3.4 | Node.js v22 | Ubuntu 24.04 (WSL2) | Git | Claude Code

---

**Ultima atualizacao:** 2026-01-09
- Estrutura atualizada removendo pastas-fantasma (adk-agents, CCui, etc)
- Adicionada nota sobre migracao para claude-experiments repo
- ADR-004 atualizado: skills agora apenas em .claude/skills/
- Removida restricao obsoleta sobre skills custom
