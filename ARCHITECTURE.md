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
├── agentes/              # Agentes Python autonomos
│   ├── oab-watcher/      # Monitora Diario OAB
│   ├── djen-tracker/     # Monitora DJEN
│   └── legal-lens/       # Analise NLP
├── comandos/             # Utilitarios single-purpose
├── mcp-servers/          # Servidores MCP (trello-mcp)
├── legal-extractor-cli/  # CLI extracao de PDFs
├── legal-extractor-tui/  # TUI extracao de PDFs
├── shared/               # Codigo compartilhado
├── skills/               # Skills custom do projeto
└── .claude/              # Config Claude Code
    ├── agents/           # Definicoes de agentes
    ├── hooks/            # Hooks de execucao
    └── skills/           # Skills managed
```

---

## Decisoes Arquiteturais

### ADR-001: Python + venv por Agente
- **Decisao:** Cada agente tem seu proprio `.venv`
- **Razao:** Isolamento de dependencias, evita conflitos de versao
- **Consequencia:** `requirements.txt` obrigatorio por agente

### ADR-002: Dados Fora do Repositorio
- **Decisao:** Dados em `~/claude-code-data/`, nunca em Git
- **Razao:** Logs e downloads podem ser grandes e sensiveis
- **Consequencia:** Usar `shared/utils/path_utils.py` para paths

### ADR-003: Hooks Nao-Bloqueantes
- **Decisao:** Hooks devem ter timeout <500ms
- **Razao:** Hooks lentos travam a sessao Claude Code
- **Consequencia:** Usar async, caching, graceful degradation

### ADR-004: Skills em Duas Camadas
- **Decisao:** `skills/` = custom, `.claude/skills/` = managed
- **Razao:** Separar skills do projeto de skills oficiais
- **Consequencia:** Nunca colocar skills custom em `.claude/skills/`

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

Python 3.11 | Node.js v22 | Ubuntu 24.04 (WSL2) | Git | Claude Code
