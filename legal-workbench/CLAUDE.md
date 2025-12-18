# CLAUDE.md - Legal Workbench

Regras para desenvolvimento no Legal Workbench.

---

## Arquitetura Atual (2025-12-18)

**Stack: All-React SPA + FastAPI Services**

```
Browser ──> React SPA (/) ──> FastAPI Services (/api/*)
                │
                └── Traefik reverse proxy (:80)
```

### Servicos Docker
| Servico | Rota | Porta |
|---------|------|-------|
| frontend-react | `/` | 3000 |
| api-stj | `/api/stj` | 8000 |
| api-text-extractor | `/api/text` | 8001 |
| api-doc-assembler | `/api/doc` | 8002 |
| api-trello | `/api/trello` | 8004 |
| redis | - | 6379 |

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
├── frontend/           # React SPA (Vite + TypeScript)
│   └── src/
│       ├── pages/      # HubHome, TrelloModule, DocAssembler, STJ
│       ├── components/ # Componentes React
│       ├── store/      # Zustand stores
│       └── routes.tsx  # React Router config
├── docker/             # Dockerfiles dos servicos
├── ferramentas/        # Backends Python (legado, usar docker/)
├── docs/               # Documentacao
└── _archived/          # POCs e arquiteturas antigas
```

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

*Ultima atualizacao: 2025-12-18*
