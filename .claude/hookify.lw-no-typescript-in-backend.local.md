---
name: lw-no-typescript-in-backend
enabled: true
event: file
action: block
conditions:
  - field: file_path
    operator: regex_match
    pattern: legal-workbench/ferramentas/.*\.(ts|tsx)$
---

**BLOQUEADO: TypeScript em Backend**

Tentativa de criar arquivo `.ts` ou `.tsx` dentro de `ferramentas/`.

**Regra:** Os backends do LW são **Python/FastAPI only**.

**Estrutura correta:**
```
legal-workbench/
├── frontend/       ← TypeScript (.ts, .tsx)
├── ferramentas/    ← Python (.py)
│   ├── legal-doc-assembler/
│   ├── legal-text-extractor/
│   ├── prompt-library/
│   ├── stj-dados-abertos/
│   └── trello-mcp/
└── shared/         ← Python (.py)
```

**O que fazer:**
- Se é código frontend: coloque em `frontend/src/`
- Se é script Node para tooling: coloque em `scripts/` ou `docker/`

> Regra: .claude/hookify.lw-no-typescript-in-backend.local.md
