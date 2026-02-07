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

## Context Offloading (Gemini Bridge Plugin)

Plugin `gemini-bridge@opc-plugins` invoca Gemini CLI via MCP server para exploracao
e analise pesada de codigo. Preserva a janela de contexto do Claude.

- **Plugin:** `gemini-bridge@opc-plugins` (MCP server Python, zero deps)
- **Tool:** `mcp__gemini_bridge__explore` (modes: onboarding, targeted, verify, research)
- **Subagente:** `gemini-bridge-explorer` (restrito a apenas a tool acima)
- **Skill:** `gemini-bridge:delegation` (protocolo de delegacao)
- **Hook:** PreToolUse bloqueia Task(Explore) e redireciona para o plugin
- **Regras detalhadas:** `~/.claude/rules/gemini-offloading.md`

---

## Verificacao Obrigatoria

Antes de considerar qualquer tarefa de backend concluida:

### 1. Testes Unitarios
```bash
cd legal-workbench/ferramentas/<backend>
source .venv/bin/activate
pytest tests/ -v
```

### 2. Teste de Endpoints (quando API mudou)
```bash
# Para endpoints publicos
curl -X GET http://localhost:8000/api/endpoint

# Para endpoints autenticados - usar route-tester skill
# Skill: /route-tester
```

### 3. Type Checking
```bash
mypy app/ --ignore-missing-imports
```

### 4. Checklist Pre-Commit
- [ ] pytest passa (todos os testes)
- [ ] Endpoint testado (curl ou route-tester)
- [ ] Type hints adicionados em funcoes novas
- [ ] Logs verificados (sem erros/warnings inesperados)

> **Regra**: NAO commitar sem verificar. Testes de integracao falham se unitarios nao passam.

---

*Herdado de: legal-workbench/CLAUDE.md*
