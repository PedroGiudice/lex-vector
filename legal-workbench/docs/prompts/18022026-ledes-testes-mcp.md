# Retomada: Batch de Testes do LEDES Converter via MCP

## Contexto rapido

O modulo LEDES Converter esta funcional com 12 endpoints, 128 testes backend,
4 matters persistidos em SQLite, e AppImage gerado. Todos os issues Linear
(CMR-23 a CMR-29) estao fechados. A API roda na porta 8003.

O objetivo desta retomada e executar um batch de testes end-to-end via MCP
para validar que todos os endpoints respondem corretamente, os matters estao
acessiveis, e as conversoes produzem output LEDES 1998B valido.

## Arquivos principais

- `ferramentas/ledes-converter/api/main.py` -- FastAPI app, todos os endpoints
- `ferramentas/ledes-converter/api/models.py` -- Pydantic models
- `ferramentas/ledes-converter/api/ledes_generator.py` -- geracao LEDES 1998B
- `ferramentas/ledes-converter/api/ledes_validator.py` -- validacao de output
- `ferramentas/ledes-converter/api/matter_store.py` -- CRUD SQLite
- `ferramentas/ledes-converter/api/task_codes.py` -- classificacao UTBMS
- `ferramentas/ledes-converter/tests/` -- 128 testes em 5 arquivos
- `docs/contexto/18022026-ledes-estado-e-testes-mcp.md` -- contexto desta sessao

## Proximos passos (por prioridade)

### 1. Testar health e matters via HTTP
**Onde:** API porta 8003
**O que:** `GET /health`, `GET /matters`, `GET /matters/{name}`
**Por que:** validar que API e dados estao acessiveis
**Verificar:**
```bash
curl -s localhost:8003/health
curl -s localhost:8003/matters | python3 -m json.tool
curl -s "localhost:8003/matters/CMR%20General%20Litigation%20Matters" | python3 -m json.tool
```

### 2. Testar conversao text-to-ledes
**Onde:** `POST /convert/text-to-ledes`
**O que:** enviar texto com line items e config, verificar output LEDES
**Por que:** endpoint mais simples para validar pipeline completa
**Verificar:**
```bash
curl -s -X POST localhost:8003/convert/text-to-ledes \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Legal services rendered:\nDraft and file Special Appeal to STJ - US $1,200.00\nPrepare defense motion - US $900.00",
    "config": {
      "matter_name": "CMR General Litigation Matters",
      "billing_start_date": "2026-02-01",
      "billing_end_date": "2026-02-28"
    }
  }' | python3 -m json.tool
```

### 3. Testar validacao do output
**Onde:** `POST /validate`
**O que:** pegar output LEDES do passo 2 e validar
**Por que:** confirmar que o validador detecta erros/warnings
**Verificar:**
```bash
# Usar o ledes_content do passo anterior como input
curl -s -X POST localhost:8003/validate \
  -H "Content-Type: application/json" \
  -d '{"ledes_content": "<output do passo 2>"}' | python3 -m json.tool
```

### 4. Testar conversao structured
**Onde:** `POST /convert/structured`
**O que:** enviar JSON com line items estruturados
**Por que:** endpoint usado pelo frontend para conversao programatica
**Verificar:**
```bash
curl -s -X POST localhost:8003/convert/structured \
  -H "Content-Type: application/json" \
  -d '{
    "line_items": [
      {"description": "Draft appeal brief", "amount": 1200.00},
      {"description": "Court hearing attendance", "amount": 900.00}
    ],
    "config": {
      "matter_name": "CMR General Litigation Matters",
      "billing_start_date": "2026-02-01",
      "billing_end_date": "2026-02-28"
    }
  }' | python3 -m json.tool
```

### 5. Rodar suite de testes backend
**Onde:** dentro do container ou venv
**O que:** executar os 128 testes
**Por que:** regressao apos periodo sem tocar no codigo
**Verificar:**
```bash
# Via Docker
docker exec -it <container_id> pytest tests/ -v --tb=short

# Ou via venv local
cd ferramentas/ledes-converter && source venv/bin/activate && pytest tests/ -v
```

### 6. Testar CRUD de matters
**Onde:** `POST/PUT/DELETE /matters`
**O que:** criar matter de teste, atualizar, deletar
**Por que:** validar persistencia SQLite end-to-end
**Verificar:**
```bash
# Criar
curl -s -X POST localhost:8003/matters \
  -H "Content-Type: application/json" \
  -d '{"matter_name": "TEST-MATTER", "matter_id": "TEST-001", "client_id": "Test Client"}' | python3 -m json.tool

# Verificar
curl -s "localhost:8003/matters/TEST-MATTER" | python3 -m json.tool

# Deletar
curl -s -X DELETE "localhost:8003/matters/TEST-MATTER"
```

## Como verificar (smoke test rapido)

```bash
# Health
curl -s localhost:8003/health

# Matters existem
curl -s localhost:8003/matters | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d)} matters')"

# Conversao funciona
curl -s -X POST localhost:8003/convert/text-to-ledes \
  -H "Content-Type: application/json" \
  -d '{"text": "Legal advice - US $500.00", "config": {"matter_name": "CMR General Litigation Matters"}}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('LEDES OK' if 'ledes_content' in d else f'FAIL: {d}')"
```
