# CLAUDE.md

**PORTUGUÊS BRASILEIRO COM ACENTUAÇÃO CORRETA.** Usar "eh" em vez de "é" é inaceitável. Acentos são obrigatórios: é, á, ã, ç, etc.

Instruções operacionais para Claude Code neste repositório.

**Arquitetura:** `ARCHITECTURE.md` (North Star)
**Lições:** `DISASTER_HISTORY.md`

---

## Regras Críticas

### 1. Sempre Usar venv/uv
```bash
# Backend Python
cd legal-workbench/backend && uv sync && uv run uvicorn app.main:app --reload

# Frontend
cd legal-workbench/frontend && bun install && bun run dev
```

### 2. Nunca Commitar
- `.venv/`, `__pycache__/`, `*.pdf`, `*.log`, `node_modules/`

### 3. Bun OBRIGATÓRIO (nunca npm/yarn/node)
```bash
bun install && bun run dev && bun run build
```

**Para scripts JS:** Sempre `bun run script.js`, nunca `node script.js`

### 4. mgrep em vez de grep
```bash
mgrep "pattern"           # em vez de grep -r "pattern"
mgrep "pattern" src/      # busca em diretório específico
```

### 5. Gemini Bridge para Context Offloading
**SEMPRE** usar `gemini-bridge-explorer` plugin para:
- Arquivos > 500 linhas
- Múltiplos arquivos simultâneos
- Logs extensos, diffs grandes

### 6. ZERO Emojis
**PROIBIDO** usar emojis em qualquer output: respostas, código, commits, comentários.
Motivo: Bug no CLI Rust causa crash em char boundaries de emojis (4 bytes).

### 7. Testes Obrigatórios (Backend)
Pre-commit executa **ruff + pytest** automaticamente para arquivos Python em `ferramentas/`.

### 8. Docker Compose
```bash
docker compose ps                  # listar containers
docker compose logs <container>    # ver logs
docker compose up -d               # subir serviços
```
- Commit bloqueado se testes falharem
- Bypass (emergência): `git commit --no-verify`
- CI também bloqueia merge se testes falharem

---

## Erros Aprendidos

**INSTRUÇÃO PARA CLAUDE:** Adicione uma entrada aqui quando:
- O usuário corrigir um erro seu
- Você cometer erro grosseiro (syntax error, import errado)
- Um erro acontecer mais de uma vez
- Erro "fatal" (mudança em um layer quebra outro — ex: backend quebra frontend)

Não crie hooks para cada erro — documente aqui primeiro. Esta seção cresce orgânicamente.

| Data | Erro | Regra |
|------|------|-------|
| 2026-01-11 | Emoji causou crash do CLI (panic em char boundary) | Regra #6: ZERO emojis |
| 2026-01-11 | Crash do CLI pode perder edits não commitados | **Commitar frequentemente durante sessão** |
| 2026-01-13 | Feedback loop só roda no commit, não proativamente | Commitar após cada mudança lógica para validar cedo |
| 2026-01-13 | Troquei modelo especificado pelo usuário (gemini-3-pro-preview) | **NUNCA substituir modelo indicado pelo usuário - usar EXATAMENTE o especificado** |
| 2026-01-17 | Build local (bun) nao atualiza Docker - fiz rsync do dist mas container usa build interno | **SEMPRE usar cicd-operator para deploy no LW** - Docker faz build interno, rsync nao basta |
| 2026-01-17 | Assumi que testes falhando = deps faltando. Na verdade, LTE usa Marker (não pytesseract/pdf2image/anthropic) | **VER CLAUDE.md DO MÓDULO antes de rodar testes** - código legado tem imports obsoletos |
| 2026-01-31 | Versão no Cargo.toml (0.1.0) divergia do tauri.conf.json (0.1.3) - build ia regredir versão | **Tauri: SEMPRE sincronizar versão em Cargo.toml E tauri.conf.json antes de build** |

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

Técnica dos 5 Porquês para bugs não-triviais:
1. Sintoma → 2. Por quê? → 3. Por quê? → 4. Por quê? → 5. **CAUSA RAIZ**

---

## Hooks

Validar após mudanças:
```bash
tail -50 ~/.vibe-log/hooks.log
```
Red flags: `MODULE_NOT_FOUND`, `command not found`

---

## Subagentes Discovery

Subagentes de `.claude/agents/*.md` descobertos no início da sessão.
Novo subagente? Reinicie a sessão.

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
