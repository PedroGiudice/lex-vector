# CLAUDE.md - LEDES Converter

Conversor de invoices DOCX para formato LEDES 1998B (Salesforce LegalOps).

## Stack
- Python 3.10+ / FastAPI
- SQLite (stdlib sqlite3) para persistencia de Matters
- python-docx para parsing DOCX

## Estrutura
```
api/
  main.py              # Rotas FastAPI
  models.py            # Pydantic models
  ledes_generator.py   # Geracao LEDES pura
  ledes_validator.py   # Validacao do output
  task_codes.py        # Mapeamento UTBMS
  matter_store.py      # CRUD SQLite de Matters
templates/
  CMR-LEDES-TEMPLATE.txt  # Template de referencia
tests/
data/                  # SQLite runtime (gitignored)
```

## Comandos
```bash
cd ferramentas/ledes-converter
uv sync
uv run pytest -v
uv run uvicorn api.main:app --port 8003 --reload
```

## Regras
- Formato LEDES 1998B: ASCII-only, pipe-delimited, 24 campos exatos
- Toda linha termina com `[]`
- Campos de moeda: max 14 digitos + 2 decimais
- Datas: YYYYMMDD
- Task codes: UTBMS (L210, L510, L160, L250, A103, A106)
