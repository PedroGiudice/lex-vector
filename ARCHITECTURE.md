# ARCHITECTURE.md - North Star

Sistema de automacao juridica brasileira com agentes Python.

---

## Principios Fundamentais

### 1. Separacao de Camadas (Inviolavel)

| Camada | Local | Git |
|--------|-------|-----|
| **Codigo** | `~/claude-work/repos/Claude-Code-Projetos/` | Sim |
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
Claude-Code-Projetos/
├── legal-workbench/      # Dashboard juridico (PROJETO PRINCIPAL)
│   ├── frontend/         # React frontend
│   ├── docker/           # Services (stj-api, trello-mcp, doc-assembler, etc)
│   ├── ferramentas/      # Python tools (stj-dados-abertos, legal-text-extractor)
│   └── docs/             # LW-specific documentation
├── adk-agents/           # Google ADK agents (frontend_commander, etc)
├── claudecodeui-main/    # Claude Code UI (forked original)
├── CCui/                 # CCui components development
├── BASE-UI/              # UI reference/experiments
├── shared/               # Codigo compartilhado (utils, memory)
├── skills/               # Skills custom (dashboard-creator, pdf, etc)
├── docs/                 # Global documentation and plans
├── infra/                # Infrastructure configs (oracle)
├── scripts/              # Setup and utility scripts
└── .claude/              # Config (agents, hooks, skills managed)
```

---

## Decisoes Arquiteturais

### ADR-001: Python + venv por Agente
Cada agente tem `.venv` isolado. `requirements.txt` obrigatorio.

### ADR-002: Dados Fora do Repositorio
Dados em `~/claude-code-data/`, nunca em Git. Usar `shared/utils/path_utils.py`.

### ADR-003: Hooks Nao-Bloqueantes
Hooks com timeout <500ms. Usar async, caching, graceful degradation.

### ADR-004: Skills em Duas Camadas
`skills/` = custom, `.claude/skills/` = managed. Nunca misturar.

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
| Skills custom em .claude/skills/ | BLOQUEADO | ADR-004 |

---

## Stack

Python 3.11 | Bun 1.3.4 | Node.js v22 | Ubuntu 24.04 (WSL2) | Git | Claude Code

---

**Ultima atualizacao:** 2026-01-07
- Estrutura atualizada para refletir projeto atual
- legal-workbench agora e projeto principal
- Removidos diretorios obsoletos (agentes/, mcp-servers/, legal-extractor-*)
- ADR-005: Bun 1.3.4 para hooks JS (~25% mais rapido que Node.js)
