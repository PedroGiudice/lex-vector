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

### 3. Bun OBRIGATORIO (nunca npm/yarn/node)
```bash
bun install && bun run dev && bun run build
```

**Para scripts JS:** Sempre `bun run script.js`, nunca `node script.js`

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

### 6. ZERO Emojis
**PROIBIDO** usar emojis em qualquer output: respostas, codigo, commits, comentarios.
Motivo: Bug no CLI Rust causa crash em char boundaries de emojis (4 bytes).

### 7. Testes Obrigatorios (Backend)
Pre-commit executa **ruff + pytest** automaticamente para arquivos Python em `ferramentas/`.
- Commit bloqueado se testes falharem
- Bypass (emergencia): `git commit --no-verify`
- CI tambem bloqueia merge se testes falharem

---

## Erros Aprendidos

**INSTRUÇÃO PARA CLAUDE:** Adicione uma entrada aqui quando:
- O usuário corrigir um erro seu
- Você cometer erro grosseiro (syntax error, import errado)
- Um erro acontecer mais de uma vez
- Erro "fatal" (mudança em um layer quebra outro — ex: backend quebra frontend)

Não crie hooks para cada erro — documente aqui primeiro. Esta seção cresce organicamente.

| Data | Erro | Regra |
|------|------|-------|
| 2026-01-11 | Emoji causou crash do CLI (panic em char boundary) | Regra #6: ZERO emojis |
| 2026-01-11 | Crash do CLI pode perder edits nao commitados | **Commitar frequentemente durante sessao** |
| 2026-01-13 | Feedback loop so roda no commit, nao proativamente | Commitar apos cada mudanca logica para validar cedo |
| 2026-01-13 | Troquei modelo especificado pelo usuario (gemini-3-pro-preview) | **NUNCA substituir modelo indicado pelo usuario - usar EXATAMENTE o especificado** |

<!--
Formato para adicionar:
| YYYY-MM-DD | Descrição breve do erro | O que evitar/fazer diferente |
-->

---

## Estrutura

```
legal-workbench/       # Lex-Vector (LV) - Projeto principal
├── frontend/          # Next.js 15 + React 19
├── ferramentas/       # Python backends e tools
│   └── legal-text-extractor/  # LTE (Marker + Gemini)
├── docker/            # Servicos Docker
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
| LV | `legal-workbench/CLAUDE.md` | Regras do projeto |
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
