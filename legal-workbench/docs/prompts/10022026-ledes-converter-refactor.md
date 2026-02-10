# Retomada: LEDES Converter -- Novos Endpoints e Frontend Tauri

## Contexto rapido

O backend do LEDES Converter foi completamente refatorado em `ferramentas/ledes-converter/`. Agora tem 6 modulos (main, generator, validator, task_codes, matter_store, models), 108 testes passando, e endpoints para conversao DOCX, matters CRUD, validacao e batch.

A proxima etapa e adicionar dois novos endpoints de entrada (structured e text-to-ledes) e implementar o frontend no Tauri usando APIs nativas. A decisao arquitetural e que o formulario editavel e o centro -- DOCX, texto colado e entrada manual sao modos diferentes de alimentar o mesmo formulario.

A branch `work/session-20260210-123818` tem 6 commits sobre main. Ainda nao foi mergeada.

## Arquivos principais

- `ferramentas/ledes-converter/api/main.py` -- endpoints FastAPI (conversao, matters, validate, batch)
- `ferramentas/ledes-converter/api/ledes_generator.py` -- logica pura de geracao LEDES (sem FastAPI)
- `ferramentas/ledes-converter/api/ledes_validator.py` -- validacao LEDES 1998B
- `ferramentas/ledes-converter/api/task_codes.py` -- classificacao UTBMS
- `ferramentas/ledes-converter/api/matter_store.py` -- CRUD SQLite
- `ferramentas/ledes-converter/api/models.py` -- todos os Pydantic models
- `docs/contexto/10022026-ledes-converter-refactor.md` -- contexto detalhado

## Proximos passos (por prioridade)

### 1. Adicionar endpoint POST /convert/structured

**Onde:** `ferramentas/ledes-converter/api/main.py`
**O que:** Endpoint que recebe JSON com dados estruturados (invoice_number, invoice_date, billing_start/end, line_items[]) + matter_name. Pula a etapa de extracao -- vai direto para `generate_ledes_1998b()`. Task codes sao classificados automaticamente pelas descricoes dos line items.
**Por que:** Modo de entrada "formulario" -- o mais pratico para o dia a dia.
**Verificar:**
```bash
cd ferramentas/ledes-converter
uv run python -m pytest tests/ -v
```

### 2. Adicionar endpoint POST /convert/text-to-ledes

**Onde:** `ferramentas/ledes-converter/api/main.py`
**O que:** Aceita campo `text` (conteudo colado) + `matter_name`. Roda `extract_ledes_data()` no texto, merge com matter config, gera LEDES. Retorna tanto os dados extraidos quanto o LEDES para o frontend mostrar no formulario editavel.
**Por que:** Modo "colar texto" -- rapido quando o usuario tem o conteudo do invoice mas nao o .docx.
**Verificar:** Mesmo comando acima.

### 3. Atualizar issues no Linear

**Onde:** Linear (workspace cmr-auto)
**O que:** Fechar CMR-23 a CMR-27 e CMR-29. Criar milestone para "LEDES Converter - Tauri Native" no projeto lex-vector.
**Por que:** Issues resolvidos nesta sessao.

### 4. Implementar frontend LEDES no Tauri

**Onde:** `frontend/src/` (novo componente ou refactor do LedesConverterModule.tsx existente)
**O que:** Interface com 3 abas (Upload DOCX / Colar Texto / Manual), dropdown de matters, formulario editavel com line items, preview LEDES com highlighting do validador, save direto no filesystem via Tauri.
**Por que:** O frontend atual e basico -- precisa dos novos modos de entrada e integracao Tauri nativa.
**Importante:** Usar APIs nativas do Tauri: `dialog.open()` para selecao de arquivo, `fs.writeTextFile()` para salvar output, `tauri-plugin-http` para chamadas ao backend (nao fetch nativo).

### 5. Merge para main

**Onde:** Branch `work/session-20260210-123818`
**O que:** Criar PR, revisar, mergear.
**Por que:** 6 commits pendentes.

## Como verificar

```bash
# Testes do backend
cd legal-workbench/ferramentas/ledes-converter
uv run python -m pytest tests/ -v --tb=short

# Esperado: 108 passed, 8 skipped

# Verificar estrutura
find ferramentas/ledes-converter -name "*.py" | sort

# Git log
git log --oneline work/session-20260210-123818 --not main
```
