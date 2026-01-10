---
name: lv-no-python-in-frontend
enabled: true
event: file
action: block
conditions:
  - field: file_path
    operator: regex_match
    pattern: legal-workbench/frontend/.*\.py$
---

**BLOQUEADO: Python em Frontend**

Tentativa de criar arquivo `.py` dentro de `frontend/`.

**Regra:** O frontend do LV (Lex-Vector) é **TypeScript/Next.js only**.

**Estrutura correta:**
```
legal-workbench/
├── frontend/       ← TypeScript (.ts, .tsx, .js, .jsx)
├── ferramentas/    ← Python (.py)
└── shared/         ← Python (.py) - utils compartilhados
```

**O que fazer:**
- Se é código backend: coloque em `ferramentas/[modulo]/`
- Se é utilitário compartilhado: coloque em `shared/`
- Se é script de build/deploy: coloque em `scripts/`

> Regra: .claude/hookify.lv-no-python-in-frontend.local.md
