# Contexto: Query Improvement + Metadata Enrichment

**Data:** 2026-03-11
**Branch:** main (trabalho direto, sem branch separado)

---

## O que foi feito

### 1. Query Preprocessing (Step 0) -- IMPLEMENTADO

Modulo `query_preprocessor.rs` no crate search. Pipeline: extracao de metadados por regex -> stopwords juridicas -> expansao por dicionario -> embedding.

**Arquivos criados:**
- `stj-vec/crates/search/src/query_preprocessor.rs` -- modulo principal
- `stj-vec/config/expansao_juridica.json` -- dicionario com 22 entradas

**Arquivos modificados:**
- `routes.rs` -- chamada ao preprocessor antes do embedding, merge de filtros
- `searcher.rs` -- `fuse_rrf()` com pesos dense/sparse configuraveis
- `config.rs` -- `PreprocessingConfig` com feature flags
- `types.rs` -- novos campos opcionais em SearchRequest e QueryInfo
- `metadata.rs` -- suporte a filtro `processo_like`
- `main.rs` -- carrega dicionario no startup
- `search-config.toml` -- secoes `[preprocessing]` e pesos RRF

**Build release feito, servico restartado, funcionando em producao.**

### 2. Laravel UI Updates -- IMPLEMENTADO

- Fundo `bg-gray-200` (era branco)
- Cards com `shadow-sm` e `hover:shadow-md`
- Bloco de preprocessing (filtros detectados, termos expandidos) aparece quando API retorna novos campos

### 3. Brainstorming de Camadas Superiores -- EM ANDAMENTO

Debate extenso sobre opcoes de melhoria de queries:

**Opcoes mapeadas para transformacao de query (intercambiaveis):**
- LLM online via Claude CLI (decomposicao multi-perspectiva)
- Modelo pequeno fine-tuned (mT5/BART, requer dados de treino)
- LLM local via Ollama/vLLM

**Decisoes tomadas:**
- Claude CLI e o caminho para decomposicao (padrao ELCO-machina: subprocess Python, captura stdout)
- Laravel orquestra (N buscas paralelas), Claude so decompoe
- Sistema calibravel: busca direta (sem LLM) + busca profunda (com LLM)
- Estagio 2 (modelo pequeno substituindo LLM) descartado por ora

**Decisao pendente:** brainstorming pausado porque dependemos primeiro de enriquecer metadados da base.

### 4. Auditoria do data-engineer -- CONCLUIDA

Auditoria critica do step 0 e do plano LLM. Pontos principais:

**Criticas ao step 0:**
- Expansao dilui queries especificas (CDC expande para tokens frequentes, perde sinal raro como "licenciamento de software"). Recomenda desligar por default
- Filtros sao pos-busca (SQLite) em vez de pre-busca (Qdrant payload filters)
- Stopwords estaticas podem ser perigosas em certas queries

**Sobre RRF:**
- Sparse com peso alto gera massa de matches lexicais genericos
- Recomenda default: dense_weight=1.0, sparse_weight=0.3-0.4

**Pontos cegos identificados:**
- Sem metadado de secao nos chunks (ementa vs relatorio vs voto)
- Sem eval set para medir impacto de mudancas
- Contextual Retrieval nao aplicado (re-embedding necessario)
- RRF e client-side (Rust), nao server-side (Qdrant nativo)

### 5. Descoberta: Metadados Subutilizados -- PRIORIDADE IMEDIATA

Censo completo da base revelou dados ricos nao explorados:

| Campo | Preenchido | Vazio | Cobertura |
|-------|-----------|-------|-----------|
| processo | 1.108.844 | 1.038.171 | 51.6% |
| ministro | 1.108.844 | 1.038.171 | 51.6% |
| classe | 0 | 2.147.015 | 0% |
| orgao_julgador | 0 | 2.147.015 | 0% |
| data_publicacao | 2.146.974 | 41 | 99.998% |
| data_julgamento | 0 | 2.147.015 | 0% |
| assuntos | 1.108.844 | 1.038.171 | 51.6% |
| teor | 1.102.518 | 1.044.497 | 51.3% |
| tipo | 1.108.844 | 1.038.171 | 51.6% |
| source_file | 2.147.015 | 0 | 100% |

**Campo `teor` -- resultado do julgamento:**
```
Negando          554.648
Nao Conhecendo   382.030
Concedendo       122.566
Outros            36.581
...
```

**Campo `assuntos` -- codigos numericos (IDs de taxonomia STJ):**
```
10236;10236
10496;10496;7768;7779;7780
```
Formato: IDs separados por `;`. Significado dos IDs precisa ser investigado (provavelmente tabela de assuntos do STJ).

**Marcacoes de secao nos chunks:** chunks de acordaos comecam com "EMENTA", "VOTO", etc. Extraivel por regex para popular nova coluna `secao` na tabela chunks.

**Schema atual de chunks (sem secao):**
```sql
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    chunk_index INTEGER,
    content TEXT NOT NULL,
    token_count INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);
```

**Campo `classe` -- extraivel do processo:**
"REsp 2104511" -> classe = "REsp". Regex simples sobre campo existente.

## Issues Linear

- **CMR-48**: Re-parsear metadados (processo/ministro) de 1M documents sem metadados (High, tech-debt)

## Decisoes tomadas

1. **Step 0 e base, sempre ativo** -- regex, stopwords, dicionario, RRF tuning
2. **LLM via Claude CLI para decomposicao** -- padrao ELCO-machina (subprocess, stdout)
3. **Laravel orquestra, Claude so decompoe** -- separacao clara de responsabilidades
4. **Sistema calibravel** -- busca direta vs busca profunda (com LLM)
5. **Enriquecimento de metadados e prioridade** antes de continuar brainstorming de queries
6. **Expansao deve ser desligada por default** -- auditoria mostrou que dilui queries especificas
7. **sparse_weight default deve ser 0.3-0.4** -- nao 1.0

## Pendencias

1. **PRIORIDADE: Enriquecer metadados da base** -- classe (extrair de processo), secao (extrair de chunks), teor ja esta la mas nao e usado na busca
2. **Re-parsear 1M docs sem metadados** (CMR-48)
3. **Investigar campo assuntos** -- IDs numericos, precisa de tabela de lookup do STJ
4. **Eval set** -- 20-30 queries com ground truth para medir impacto
5. **Ajustar defaults** -- sparse_weight para 0.3-0.4, expansao off por default
6. **Continuar brainstorming** -- design do system prompt do agente de query, integracao Laravel
7. **Payload filters no Qdrant** -- mover filtros de pos-busca (SQLite) para pre-busca (Qdrant)
