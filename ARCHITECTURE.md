# ARCHITECTURE.md - North Star

Sistema de automacao juridica brasileira.

---

## FOCO PRINCIPAL: App Tauri (Desktop)

**O produto principal e o app desktop Tauri**, nao os servicos Docker.

| Componente | Prioridade | Descricao |
|------------|------------|-----------|
| **App Tauri** | PRINCIPAL | Desktop app (Windows/Linux/Mac) |
| Docker/APIs | Suporte | Backend para funcoes avancadas (Modal GPU, etc) |
| DuckDNS/Traefik | Teste | Apenas para testes de integracao |

### Build do App Tauri
```bash
cd legal-workbench/frontend
bun install
bun run tauri build   # Gera .deb, .rpm, .AppImage
```

Artefatos em: `src-tauri/target/release/bundle/`

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
│   ├── frontend/         # React SPA (Vite + React 18 + TipTap)
│   ├── ferramentas/      # Python tools (stj-dados-abertos, legal-text-extractor)
│   ├── docker/           # Dockerized services
│   │   └── services/     # FastAPI backends + Traefik
│   └── docs/             # LV-specific documentation
├── docs/                 # Global documentation and plans
├── infra/                # Infrastructure configs
├── _archived/            # Archived code for future reference
└── .claude/              # Config (agents, hooks, skills managed)
```

> **Nota:** Projetos experimentais (adk-agents, CCui, etc) foram migrados para
> https://github.com/PedroGiudice/claude-experiments

---

## Legal Workbench - Arquitetura de Servicos

### Arquitetura de Servicos (Docker Compose local)

```
localhost (:80)
    |
    v
+------------------+
| Traefik v3.6.5   |  Reverse proxy + routing
+------------------+
    |
    +---> / ---------> frontend-react (nginx:alpine)
    +---> /api/stj --> api-stj (FastAPI)
    +---> /api/text -> api-text-extractor (FastAPI + Celery)
    +---> /api/doc --> api-doc-assembler (FastAPI)
    +---> /api/ledes -> api-ledes-converter (FastAPI)
    +---> /api/trello -> api-trello (Bun)
```

### Servicos Docker

| Servico | Porta | Stack | Health |
|---------|-------|-------|--------|
| reverse-proxy | 80, 8080 | Traefik v3.6.5 | - |
| frontend-react | 3000 | Bun + Vite + nginx | /health |
| api-stj | 8000 | Python/FastAPI | /health |
| api-text-extractor | 8001 | Python/FastAPI + Celery | /health |
| api-doc-assembler | 8002 | Python/FastAPI | /health |
| api-ledes-converter | 8003 | Python/FastAPI | /health |
| api-trello | 8004 | Bun | /health |
| redis | 6379 | Redis 7 Alpine | - |
| prometheus | 9090 | Prometheus v2.47.0 | /-/healthy |

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

| Tecnologia | Versao | Uso |
|------------|--------|-----|
| **Tauri** | 2.x | Desktop app framework (PRINCIPAL) |
| **Rust** | 1.70+ | Backend do Tauri |
| React | 18.2 | Frontend SPA |
| Bun | 1.3.4 | Frontend build, hooks JS |
| Vite | 5.0 | Build tool |
| TipTap | 3.15 | Rich text editor (Doc Assembler) |
| Python | 3.11+ | Backends FastAPI, ferramentas |
| FastAPI | 0.109+ | APIs Python |
| Modal | - | GPU serverless (Marker extraction) |
| Docker | 24+ | Containerizacao (dev/test) |
| Traefik | 3.6.5 | Reverse proxy (dev/test) |

---

**Ultima atualizacao:** 2026-01-28
- FOCO PRINCIPAL definido: App Tauri (desktop)
- Stack atualizada com Tauri, Rust, Modal
- Docker/Traefik marcados como dev/test
