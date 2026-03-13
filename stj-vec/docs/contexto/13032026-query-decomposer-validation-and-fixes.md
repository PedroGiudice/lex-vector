# Contexto: Validacao Multi-Tema do Query-Decomposer + Fix Filtro Tipo + Desativacao de Expansao

**Data:** 2026-03-13
**Sessao:** work/query-decomposer-docs (continuacao)
**Duracao:** ~1.5h

---

## O que foi feito

### 1. Teste end-to-end com 4 temas juridicos distintos

Rodados 4 agentes query-decomposer (Sonnet) em paralelo, cada um com tema diferente:

| Query | Area | Angulos | Buscas | Resultados | Tokens | Tempo |
|-------|------|---------|--------|------------|--------|-------|
| pensao alimenticia majoracao proporcionalidade | Familia | 7 | 7 | 23 | 74.7k | 132s |
| homicidio culposo transito embriaguez dolo eventual | Penal/Transito | 7 | 7 | 29 | 76.3k | 212s |
| dano moral negativacao indevida banco | Consumidor/Bancario | 6 | 6 | 40 | 85.7k | 161s |
| prescricao intercorrente execucao fiscal fazenda | Tributario | 8 | 8 | 47 | 78.4k | 456s |

Todos retornaram JSON valido, dados reais (doc_ids numericos, scores decimais, ministros reais).
Comparativo com teste anterior (CDC/software): 6 angulos, 17 resultados, 71k tokens, 151s.

**Conclusao:** agente funciona de forma robusta em temas completamente distintos.
Temas com mais ramificacoes juridicas (prescricao intercorrente: 8 sub-temas) fazem
o agente iterar mais rounds (3 vs 2), comportamento desejavel.

### 2. Diagnostico e fix do filtro tipo=ACORDAO

**Problema:** filtro `tipo: "ACORDAO"` retornava 0 resultados pos-filtro.

**Causa raiz:** valores na base (SQLite e Qdrant) usam acentos: `ACÓRDÃO`, `DECISÃO`.
O plugin MCP instruia o agente a usar `ACORDAO` (sem acento). Qdrant keyword index
e case+accent sensitive.

**Distribuicao real:**
- `DECISÃO`: 1,603,047 documentos
- `ACÓRDÃO`: 542,376 documentos

**Fix em 3 camadas:**
1. **Plugin MCP** (`~/.claude/plugins/.../stj-vec-tools/server.mjs`): description corrigida para `ACÓRDÃO, DECISÃO (com acentos obrigatórios)`
2. **API Rust** (`metadata.rs`): funcao `normalize_tipo()` converte `ACORDAO`->`ACÓRDÃO`, `DECISAO`->`DECISÃO` automaticamente
3. **Teste unitario** (`storage.rs`): corrigido `ACORDAO`->`ACÓRDÃO`

Validacao: `tipo=ACORDAO` (sem acento) agora retorna resultados corretos via normalize_tipo.

### 3. Desativacao da expansao de queries

**Decisao:** `expand_query = false` no `search-config.toml`.

**Motivo:** a expansao concatenava termos do dicionario (`expansao_juridica.json`) na query
antes do embedding, diluindo o sinal. Exemplo: "dano moral" virava
"dano moral responsabilidade civil indenizacao por danos morais". Com BGE-M3, o modelo
ja captura relacoes semanticas sem expansao explicita. Alem disso, o query-decomposer
ja faz decomposicao por angulos -- expansao na API e redundante.

**Dicionario preservado:** `config/expansao_juridica.json` continua existindo (26 entradas:
siglas de leis, termos juridicos). Reativavel via `expand_query = true`.

### 4. Cleanup da VM

- **Ollama:** removidos 3 modelos qwen2.5 (0.5b, 1.5b, 3b) -- ~3.3GB liberados. Sobrou apenas bge-m3
- **PHP orfao:** processo na porta 8082 matado, stj-search-web relancado
- **Servicos validados:** Qdrant green (13.4M pts), Rust API (8421), Laravel BFF (8082)

## Estado dos arquivos

| Arquivo | Status | Detalhe |
|---------|--------|---------|
| `stj-vec/search-config.toml` | Modificado | `expand_query = false` |
| `stj-vec/crates/search/src/metadata.rs` | Modificado | +`normalize_tipo()` para filtro accent-tolerant |
| `stj-vec/crates/core/src/storage.rs` | Modificado | Teste: `ACORDAO` -> `ACÓRDÃO` |
| `~/.claude/plugins/.../stj-vec-tools/server.mjs` | Modificado | Instrucao tipo com acentos |

## Commits desta sessao

```
(nenhum commit nesta sessao -- mudancas pendentes)
```

## Decisoes tomadas

- **Expansao desativada**: BGE-M3 captura semantica sem expansao literal. Query-decomposer ja decompoe por angulos -- expansao na API e redundante e prejudicial | Descartado: manter expansao ativa (dilui sinal, piora queries nichadas)
- **normalize_tipo() no servidor**: tolerancia a variantes sem acento no filtro tipo. Defesa em profundidade -- nao depende da instrucao do plugin | Descartado: so corrigir o plugin (fragil, qualquer cliente pode errar)
- **Ollama modelos locais removidos**: qwen2.5 descartados para decomposicao de queries (decisao da sessao anterior). Mantido apenas bge-m3 para embeddings

## Metricas

| Metrica | Valor |
|---------|-------|
| Qdrant status | green, 13,442,327 pts |
| Temas testados | 5 (CDC/software + 4 novos) |
| Media resultados/tema | 31.2 |
| Media tokens/tema (Sonnet) | 77.2k |
| Media tempo/tema (Sonnet) | 190s |
| Disco apos cleanup | 69% (400GB/581GB) |
| RAM | 35/62GB |
| Ollama | apenas bge-m3 (1.2GB) |

## Pendencias identificadas

1. **Integrar query-decomposer no Laravel BFF** (alta) -- rota `POST /api/search-decomposed` que chama `claude --agent` via Process::run(), parseia JSON, retorna para frontend. Proxima sessao
2. **Melhorar substancialmente a UI** (alta) -- frontend Laravel precisa de redesign para suportar resultados decompostos, angulos, scores
3. **Commit das mudancas** (alta) -- 4 arquivos modificados pendentes de commit
4. **test_rrf_weighted_dense_bias falha** (baixa) -- teste unitario pre-existente com bug de logica (valores muito proximos, float comparison). Nao bloqueia nada
5. **Agente global fora do git** (media) -- `~/.claude/agents/query-decomposer.md` nao esta versionado. Decidir: copiar para stj-vec/docs/ ou manter apenas global
