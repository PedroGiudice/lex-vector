# Retomada: Enriquecimento de Metadados + Query Improvement

## Contexto rapido

O stj-vec tem 2.1M documentos e 13.5M chunks de jurisprudencia do STJ. Implementamos um query preprocessor (regex, stopwords, dicionario, RRF tuning) no Rust e atualizamos o Laravel BFF. Tudo funcionando em producao.

Uma auditoria do data-engineer revelou que temos dados ricos subutilizados na base. **48% dos documentos nao tem processo/ministro preenchidos.** O campo `classe` esta 100% vazio (mas e extraivel do campo `processo`). Os chunks tem marcacoes de secao no texto ("EMENTA", "VOTO") mas nao tem coluna `secao`. O campo `teor` tem o resultado do julgamento ("Negando", "Concedendo") mas nao e usado na busca.

O brainstorming sobre camadas superiores de query (LLM para decomposicao multi-perspectiva) esta **pausado** ate enriquecermos os metadados, porque a qualidade da busca depende diretamente do que esta disponivel na base.

## Arquivos principais

- `stj-vec/docs/contexto/11032026-query-improvement-metadata-enrichment.md` -- contexto detalhado
- `stj-vec/docs/plans/query_juridica.md` -- pesquisa sobre prompt engineering e agentes LLM para busca juridica
- `stj-vec/crates/search/src/query_preprocessor.rs` -- modulo de preprocessing implementado
- `stj-vec/crates/search/src/routes.rs` -- pipeline de busca com preprocessing integrado
- `stj-vec/config/expansao_juridica.json` -- dicionario de expansao
- `stj-vec/db/stj-vec.db` -- banco SQLite (52GB, 2.1M docs, 13.5M chunks)

## Proximos passos (por prioridade)

### 1. Enriquecer campo `classe` nos documents
**Onde:** script Python novo ou query SQL direta
**O que:** extrair classe processual do campo `processo` via regex. "REsp 2104511" -> classe = "REsp"
**Por que:** `classe` esta 0% preenchido mas e extraivel trivialmente. Habilita filtro por tipo de recurso
**Verificar:**
```sql
SELECT classe, COUNT(*) FROM documents WHERE classe != '' GROUP BY classe ORDER BY COUNT(*) DESC;
```

### 2. Adicionar coluna `secao` na tabela chunks
**Onde:** ALTER TABLE chunks + script Python para popular
**O que:** detectar marcacoes de secao ("EMENTA", "VOTO", "RELATORIO", "DECISAO") no inicio do content de cada chunk e popular a nova coluna
**Por que:** permite filtrar busca por secao -- priorizar ementa, excluir relatorio. Critico para validade juridica
**Verificar:**
```sql
SELECT secao, COUNT(*) FROM chunks WHERE secao IS NOT NULL GROUP BY secao;
```

### 3. Re-parsear 1M documents sem metadados (CMR-48)
**Onde:** script Python
**O que:** para os 1.038.171 docs com processo/ministro/tipo vazios, extrair do conteudo dos chunks associados
**Por que:** 48% da base e invisivel para filtros. NAO requer re-embedding
**Verificar:**
```sql
SELECT COUNT(*) FROM documents WHERE processo IS NULL OR processo = '';
-- Deve diminuir significativamente
```

### 4. Investigar campo `assuntos`
**Onde:** pesquisa + script
**O que:** os assuntos sao IDs numericos (ex: "10236;10496;7768"). Precisa encontrar a tabela de lookup do STJ que traduz IDs para nomes de assuntos
**Por que:** se mapearmos IDs para nomes, temos taxonomia tematica de 1.1M documentos -- filtro poderoso
**Verificar:** WebSearch por "tabela assuntos STJ" ou "taxonomia processual STJ"

### 5. Ajustar defaults do preprocessing
**Onde:** `stj-vec/search-config.toml`
**O que:**
- `sparse_weight = 0.4` (era 1.0, auditoria recomendou 0.3-0.4)
- `expand_query = false` (era true, auditoria mostrou que dilui queries especificas)
**Por que:** auditoria do data-engineer mostrou que expansao piora queries especificas e sparse alto domina sobre dense
**Verificar:** testar mesma query com/sem mudanca e comparar resultados

### 6. Continuar brainstorming de queries (apos metadados)
**Onde:** sessao de debate
**O que:** retomar design do agente de query (system prompt, formato JSON, integracao Laravel)
**Por que:** a decomposicao multi-perspectiva via Claude CLI e o proximo passo, mas depende de metadados enriquecidos para ser testavel
**Contexto:** ler `stj-vec/docs/plans/query_juridica.md` e `stj-vec/docs/contexto/11032026-*.md`

## Como verificar

```bash
# Servico Rust rodando
systemctl --user status stj-search-rust

# Laravel rodando
systemctl --user status stj-search-web

# Teste de busca com preprocessing
curl -s http://localhost:8421/api/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "dano moral contrato bancario", "limit": 3}' | python3 -m json.tool | head -30

# Laravel no browser
# https://extractlab.cormorant-alpha.ts.net (porta 8082 via Tailscale Serve)
```
