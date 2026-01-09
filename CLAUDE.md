# CLAUDE.md

Instrucoes operacionais para Claude Code neste repositorio.

**Arquitetura:** `ARCHITECTURE.md` (North Star)
**Licoes:** `DISASTER_HISTORY.md`

---

## Regras Criticas

### 1. Sempre Usar venv/uv
```bash
# Backend Python
cd legal-workbench/backend && uv sync && uv run uvicorn app.main:app --reload

# Frontend
cd legal-workbench/frontend && bun install && bun run dev
```

### 2. Nunca Commitar
- `.venv/`, `__pycache__/`, `*.pdf`, `*.log`, `node_modules/`

### 3. Bun OBRIGATORIO (nunca npm/yarn)
```bash
bun install && bun run dev && bun run build
```

### 4. mgrep em vez de grep
```bash
mgrep "pattern"           # em vez de grep -r "pattern"
mgrep "pattern" src/      # busca em diretorio especifico
```

### 5. Gemini para Context Offloading
**SEMPRE** usar `gemini-assistant` (modelo: gemini-3-flash) para:
- Arquivos > 500 linhas
- Multiplos arquivos simultaneos
- Logs extensos, diffs grandes

---

## Estrutura

```
legal-workbench/       # Projeto principal (unico foco)
├── frontend/          # Next.js 15 + React 19
├── backend/           # FastAPI Python 3.12
├── lte/               # Long Text Extraction (Marker + Gemini)
├── docker/            # Servicos Docker
├── ferramentas/       # Backends legados
└── docs/              # Documentacao

.claude/               # Config Claude Code
├── agents/            # Subagentes
├── hooks/             # Hooks de automacao
└── skills/            # Skills managed
```

---

## Hierarquia CLAUDE.md

| Nivel | Arquivo | Escopo |
|-------|---------|--------|
| Raiz | `CLAUDE.md` | Regras globais |
| LW | `legal-workbench/CLAUDE.md` | Regras do projeto |
| Frontend | `legal-workbench/frontend/CLAUDE.md` | Regras React/Next |
| Backend | `legal-workbench/ferramentas/CLAUDE.md` | Regras FastAPI |
| Modulos | `legal-workbench/ferramentas/*/CLAUDE.md` | Regras especificas |

---

## Debugging

Tecnica dos 5 Porques para bugs nao-triviais:
1. Sintoma → 2. Por que? → 3. Por que? → 4. Por que? → 5. **CAUSA RAIZ**

---

## Hooks

Validar apos mudancas:
```bash
tail -50 ~/.vibe-log/hooks.log
```
Red flags: `MODULE_NOT_FOUND`, `command not found`

---

## Subagentes Discovery

Subagentes de `.claude/agents/*.md` descobertos no inicio da sessao.
Novo subagente? Reinicie a sessao.

---

## Team

- **PGR** = Pedro (dono do projeto)
- **LGP** = Leo (contribuidor ativo, socio)

---

## Terminologia

| Termo | Significado | Localização |
|-------|-------------|-------------|
| **Agentes** | ADK Agents autônomos (Gemini/Python) | Repositório externo |
| **Subagentes** | Task tools executados via Claude Code | `.claude/agents/*.md` |

> **Nota:** Arquivos de hooks usam o prefixo `subagent-` para refletir esta distinção.

---

## Projetos Experimentais

Migrados para: https://github.com/PedroGiudice/claude-experiments
