# CLAUDE.md

**PORTUGUES BRASILEIRO COM ACENTUACAO CORRETA.** Acentos sao obrigatorios: e, a, a, c, etc.

Instrucoes operacionais para Claude Code neste repositorio.

**Arquitetura:** `ARCHITECTURE.md` (North Star)

---

## Regras deste Repositorio

### 1. Bun OBRIGATORIO para frontend (nunca npm/yarn)
```bash
cd legal-workbench/ccui-app && bun install && bun run dev
```

### 2. uv OBRIGATORIO para Python (nunca pip)
```bash
cd legal-workbench/ferramentas/legal-text-extractor && uv sync
```

### 3. Testes antes de commit
```bash
# ccui-backend
cd legal-workbench/ccui-backend && cargo test -- --test-threads=1
cargo clippy -- -W clippy::pedantic

# ferramentas (pre-commit executa ruff + pytest)
cd legal-workbench/ferramentas/legal-text-extractor && uv run pytest
```

### 4. Tauri: sincronizar versoes
Cargo.toml e tauri.conf.json DEVEM ter a mesma versao. Verificar ambos antes de build.

### 5. ZERO Emojis
PROIBIDO em qualquer output. Bug no CLI Rust causa crash em char boundaries (4 bytes).

---

## Erros Aprendidos

Adicione entrada quando: usuario corrigir erro seu, erro grosseiro, ou erro repetido.

| Data | Erro | Regra |
|------|------|-------|
| 2026-01-11 | Emoji causou crash do CLI | Regra #5: ZERO emojis |
| 2026-01-11 | Crash pode perder edits nao commitados | Commitar frequentemente |
| 2026-01-13 | Troquei modelo especificado pelo usuario | NUNCA substituir modelo indicado |
| 2026-01-17 | Build local nao atualiza Docker | Docker faz build interno, rsync nao basta |
| 2026-01-17 | Assumi deps erradas do LTE | VER CLAUDE.md do modulo antes de rodar testes |
| 2026-01-31 | Versao Cargo.toml divergia de tauri.conf.json | Regra #4: sincronizar versoes |
| 2026-03-05 | Estimativas teoricas de RAM/storage sem validar | WebSearch e WebFetch ANTES de estimar recursos |
| 2026-03-05 | Nao usei WebSearch para validar sizing de Qdrant | WebSearch e WebFetch sao ferramentas poderosas -- usar ANTES de estimar |
| 2026-03-05 | Assumi VRAM do Marker sem dados ("~4-6GB pico numa T4") | NAO assumir metricas de hardware sem medir ou pesquisar primeiro |
| 2026-03-05 | Adicionei volume_data.commit() dentro de container paralelo no Modal | NUNCA commit() dentro de containers .spawn() -- causa race condition (last-write-wins). Commit apenas via flush_volume() no final |

---

## Estrutura

```
lex-vector/
├── legal-workbench/           # Projeto principal
│   ├── ccui-app/              # [ATIVO] Desktop Tauri (React 19 + Vite 6 + Tauri 2.3)
│   ├── ccui-backend/          # [ATIVO] Backend Rust (axum 0.8 + tokio + tmux)
│   ├── frontend/              # [LEGADO] Next.js 15 (substituido por ccui-app)
│   ├── ferramentas/           # Python tools
│   │   └── legal-text-extractor/  # LTE (Marker + Gemini)
│   ├── docker/                # Docker Compose (redis, lte, ccui-backend)
│   └── docs/                  # Documentacao
├── stj-vec/                   # Busca vetorial STJ (SQLite metadados + Qdrant busca hibrida)
├── .claude/                   # Config Claude Code (agents, hooks, skills)
├── ARCHITECTURE.md            # North Star
└── CLAUDE.md                  # Este arquivo
```

---

## Hierarquia CLAUDE.md

| Nivel | Arquivo | Escopo |
|-------|---------|--------|
| Raiz | `CLAUDE.md` | Regras do repositorio |
| LW | `legal-workbench/CLAUDE.md` | Regras do projeto LW |
| Ferramentas | `legal-workbench/ferramentas/CLAUDE.md` | Regras Python |
| Modulos | `legal-workbench/ferramentas/*/CLAUDE.md` | Regras especificas |

---

## Team

- **PGR** = Pedro (dono do projeto)
- **LGP** = Leo (contribuidor ativo, socio)
