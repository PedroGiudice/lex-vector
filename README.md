# Legal Workbench

Plataforma de automacao juridica brasileira. Extracao de documentos PDF, analise com LLM, e organizacao de dados juridicos.

## Stack

| Camada | Tecnologia |
|--------|------------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind, Shadcn/UI |
| Backend | Python 3.12, FastAPI |
| PDF Extraction | Marker (deep learning), pdfplumber (fallback) |
| LLM | Google Gemini |
| Database | PostgreSQL (Supabase) |
| Package Managers | Bun (frontend), uv (backend) |
| Containers | Docker, Docker Compose |

## Estrutura

```
legal-workbench/
├── frontend/        # Next.js SPA
├── backend/         # FastAPI principal
├── lte/             # Long Text Extraction (Marker + Gemini)
├── docker/          # Servicos Docker legados
├── ferramentas/     # Backends Python (legado)
└── docs/            # Documentacao
```

## Servicos

| Servico | Porta | Proposito |
|---------|-------|-----------|
| legal-frontend | 3000 | Interface Next.js |
| legal-api | 8000 | API principal |
| lte-api | 8002 | Extracao de texto (OCR+LLM) |

## Comandos

```bash
# Subir ambiente
cd legal-workbench && docker compose up -d

# Frontend dev
cd legal-workbench/frontend && bun install && bun run dev

# Backend dev
cd legal-workbench/backend && uv sync && uv run uvicorn app.main:app --reload
```

## Documentacao

| Arquivo | Conteudo |
|---------|----------|
| `CLAUDE.md` | Regras operacionais para Claude Code |
| `ARCHITECTURE.md` | North Star (principios inviolaveis) |
| `legal-workbench/CLAUDE.md` | Regras especificas do LW |

## Task Execution Patterns

- **Swarm**: Tarefas medio-complexas com subagentes paralelos
- **Breakdown**: Decompor tarefas grandes em unidades atomicas antes da execucao

> **Terminologia:** "Subagentes" sao Task tools (`.claude/agents/*.md`) executados via Claude Code. "Agentes" ADK autonomos estao em repositorio separado.

## Git

**OBRIGATORIO:**

1. **Branch para alteracoes significativas** — >3 arquivos OU mudanca estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho nao commitado
4. **Deletar branch apos merge** — Local e remota

## Experimental Projects

Projetos experimentais foram migrados para [claude-experiments](https://github.com/PedroGiudice/claude-experiments).
