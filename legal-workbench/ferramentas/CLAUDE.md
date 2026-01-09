# CLAUDE.md - Legal Workbench Backends

Este diretorio contem os backends Python do Legal Workbench.

---

## Regras Gerais

### Stack
- Python 3.10+
- FastAPI
- Pydantic v2
- SQLAlchemy (quando aplicavel)

### Comandos
```bash
cd legal-workbench/ferramentas/<backend>
source .venv/bin/activate
python -m pytest tests/
```

### NUNCA (Todos os Backends)
- Modificar `frontend/` ao trabalhar aqui
- Commitar `.venv/`, `__pycache__/`
- Usar paths absolutos hardcoded
- Criar arquivos de backup (.old, .bak)

### Padrao de API
```python
@router.get("/endpoint")
async def endpoint() -> ResponseModel:
    # Sempre type hints
    # Sempre response model
    pass
```

---

*Herdado de: legal-workbench/CLAUDE.md*
