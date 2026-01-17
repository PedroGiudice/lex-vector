# CLAUDE.md - Legal Workbench

Regras para desenvolvimento no Legal Workbench.

---

## Arquitetura Atual (2026-01-17)

**Stack: React SPA (Vite) + FastAPI Services + Traefik**

```
Browser ──> Traefik (:80) ──> React SPA (/)
                │
                └──> FastAPI Services (/api/*)
```

### Servicos Docker
| Servico | Rota | Porta | Stack |
|---------|------|-------|-------|
| reverse-proxy | - | 80, 8080 | Traefik v3.6.5 |
| frontend-react | `/` | 3000 | Vite + React 18 + nginx |
| api-stj | `/api/stj` | 8000 | FastAPI |
| api-text-extractor | `/api/text` | 8001 | FastAPI + Celery |
| api-doc-assembler | `/api/doc` | 8002 | FastAPI |
| api-ledes-converter | `/api/ledes` | 8003 | FastAPI |
| api-trello | `/api/trello` | 8004 | Bun |
| redis | - | 6379 | Redis 7 Alpine |
| prometheus | - | 9090 | Prometheus v2.47.0 |

### Producao
- **Servidor:** Oracle Cloud (64.181.162.38)
- **Deploy:** rsync + docker compose build + up -d
- **SSH:** `opc@64.181.162.38` com chave `~/.ssh/oci_lw`

---

## RULE 0: UMA UNICA ARQUITETURA

**NUNCA manter duas arquiteturas concomitantemente.**

- Um `docker-compose.yml`
- Um frontend (React)
- Uma fonte de verdade

> Arquiteturas antigas estao em `_archived/`

---

## Estrutura do Projeto

```
legal-workbench/
├── frontend/                # React SPA (Vite + TypeScript)
│   └── src/
│       ├── pages/           # HubHome, TrelloModule, DocAssembler, STJ
│       ├── components/      # Componentes React
│       │   ├── document/    # TipTapDocumentViewer, FieldList, FieldEditorPanel
│       │   ├── templates/   # TemplateList
│       │   ├── upload/      # DropZone
│       │   └── ui/          # Button, Modal, Input, CollapsibleSection
│       ├── extensions/      # TipTap extensions (FieldAnnotationMark)
│       ├── store/           # Zustand stores (documentStore)
│       ├── services/        # API clients
│       └── types/           # TypeScript types
├── docker/                  # Configuracao Docker
│   ├── services/            # Backends (doc-assembler, stj-api, etc)
│   ├── scripts/             # deploy.sh, health-check.sh
│   └── docker-compose.yml
├── ferramentas/             # Python tools standalone
│   ├── stj-dados-abertos/   # STJ data pipeline
│   └── legal-text-extractor/# OCR + AI extraction
├── docs/                    # Documentacao
└── _archived/               # POCs e arquiteturas antigas
```

---

## VEDACOES CRITICAS (NUNCA)

### Arquivos de Backup
**NUNCA criar arquivos de backup no repositorio:**
- `.old`, `.bak`, `.backup`, `.orig`, `.tmp`
- `*_antigo`, `*_backup`, `*_old`
- Copias de arquivos para "preservar"

> Use branches Git para preservar codigo. Hook PreToolUse bloqueia automaticamente.

### Separacao Front-Back
**NUNCA modificar frontend ao trabalhar em backend:**
- Tarefas de backend = APENAS arquivos em `ferramentas/` ou `docker/`
- Tarefas de frontend = APENAS arquivos em `frontend/`
- Excecao: alteracoes coordenadas explicitas no prompt

### Granularidade de Tarefas
**NUNCA trabalhar em multiplos modulos simultaneamente:**
- UM modulo por tarefa
- UM commit por mudanca logica
- Se prompt pede multiplos modulos: dividir em tarefas sequenciais

### Regressoes
**NUNCA usar codigo de versoes anteriores:**
- Se precisar de referencia, consulte Git history
- NAO copiar codigo de `_archived/`
- NAO "restaurar" versoes antigas de componentes

---

## Comandos

```bash
# Subir ambiente completo
cd legal-workbench
docker compose up -d

# Ver logs
docker compose logs -f frontend-react

# Rebuild apos mudancas
docker compose build frontend-react && docker compose up -d

# Acessar
http://localhost/           # Hub Home
http://localhost/trello     # Trello Command Center
http://localhost/doc-assembler
http://localhost/stj
```

---

## Definition of Done

1. Backend funcionando (teste via curl ou E2E)
2. Frontend renderiza corretamente
3. Testes E2E com `qa_commander` passam
4. Build Docker funciona

---

## Regras de Frontend

### Sempre Usar Subagente Especializado

| Tarefa | Subagente |
|--------|-----------|
| React/TypeScript | `frontend-developer` |
| UI/Design | `ui-designer` |
| E2E Testing | `qa_commander` |
| Review | `code-reviewer-superpowers` |

### Antes de Implementar

1. Confirmar expectativa de UI
2. Identificar endpoints necessarios
3. Definir estados de erro/loading

---

*Ultima atualizacao: 2026-01-17*
