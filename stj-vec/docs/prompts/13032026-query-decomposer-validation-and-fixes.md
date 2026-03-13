# Retomada: Integracao Laravel BFF + Redesign UI para Query-Decomposer

## Contexto rapido

Sessao anterior validou o agente query-decomposer com 5 temas juridicos distintos
(familia, penal, consumidor, tributario, CDC/software). Todos retornaram dados reais,
23-47 resultados, 6-8 angulos. A expansao de queries foi desativada (prejudicial com
BGE-M3 + decomposicao por angulos). O filtro tipo=ACORDAO foi corrigido: `normalize_tipo()`
no servidor + instrucao do plugin MCP com acentos. Ollama cleanup feito (~3.3GB liberados).

Falta: (1) integrar o agente no Laravel BFF como rota da API, (2) redesenhar a UI para
exibir resultados decompostos com angulos, scores e metadados.

## Arquivos principais

- `~/.claude/agents/query-decomposer.md` -- agente com secao de engenharia de queries
- `~/.claude/plugins/marketplaces/opc-plugins/plugins/stj-vec-tools/server.mjs` -- MCP plugin (3 tools)
- `stj-vec/web/` -- Laravel 12 BFF (PHP 8.3, porta 8082)
- `stj-vec/web/app/Http/Controllers/SearchController.php` -- controller de busca existente
- `stj-vec/crates/search/` -- API Rust de busca hibrida (porta 8421)
- `stj-vec/search-config.toml` -- config com `expand_query = false`
- `stj-vec/docs/contexto/13032026-query-decomposer-validation-and-fixes.md` -- contexto detalhado

## Proximos passos (por prioridade)

### 1. Commitar mudancas pendentes
**Onde:** repo lex-vector, branch work/query-decomposer-docs
**O que:** 4 arquivos modificados: search-config.toml, metadata.rs, storage.rs, server.mjs + docs novos
**Por que:** baseline antes de novas mudancas
**Verificar:** `git status` limpo apos commit

### 2. Integrar query-decomposer no Laravel BFF
**Onde:** `stj-vec/web/app/Http/Controllers/SearchController.php` (ou novo controller)
**O que:** Rota `POST /api/search-decomposed` que:
  - Recebe `{"query": "texto juridico"}`
  - Chama `claude --agent ~/.claude/agents/query-decomposer.md -p "{query}" --output-format json --model sonnet --dangerously-skip-permissions --no-session-persistence`
  - Parseia JSON do stdout
  - Retorna para frontend
**Por que:** O agente deve ser acionavel via interface web, nao apenas CLI
**Verificar:** `curl -s localhost:8082/api/search-decomposed -X POST -d '{"query":"dano moral banco"}' -H "Content-Type: application/json"` retorna JSON com `results`, `decomposition`

### 3. Redesenhar UI do frontend Laravel
**Onde:** `stj-vec/web/resources/views/` (Blade templates)
**O que:** A UI precisa suportar:
  - **Modo busca direta** (existente): query -> resultados simples
  - **Modo decomposicao** (novo): query -> angulos explorados -> resultados agrupados por angulo
  - Exibir: angulos com contagem, scores (dense/sparse/RRF), metadados (processo, ministro, tipo, data)
  - Filtros por tipo (ACÓRDÃO/DECISÃO), classe, ministro
  - Preview do conteudo com highlight
**Por que:** A UI atual e basica (lista plana de resultados). A decomposicao produz dados ricos que precisam de visualizacao adequada
**Verificar:** Navegar em `http://extractlab:8082` e testar ambos os modos

### 4. Decidir sobre agente global vs versionado
**Onde:** `~/.claude/agents/query-decomposer.md`
**O que:** O agente esta fora do git (global em ~/.claude/agents/). Opcoes: (a) manter global-only, (b) copiar para stj-vec/docs/agents/ como referencia, (c) mover para stj-vec/ e symlink
**Por que:** Reproducibilidade -- se o agente mudar, nao ha historico

## Decisoes vigentes

- **Sonnet como default** (`model: sonnet` no frontmatter). Opus superior mas custo maior
- **Expansao desativada** -- BGE-M3 + decomposicao por angulos torna expansao redundante
- **Vocabulario juridico assado no prompt** -- extraido da base real, nao consultado em runtime
- **Agentes sempre globais** -- `~/.claude/agents/`, nunca em diretorios locais
- **Plugin MCP para sandboxing** -- agente so acessa search/document/filters, sem Bash
- **Filtro tipo com acentos** -- `ACÓRDÃO`, `DECISÃO`. API normaliza automaticamente

## Como verificar

```bash
# Servicos operacionais
curl -s localhost:6333/collections/stj | python3 -c "import json,sys; d=json.load(sys.stdin)['result']; print(f'Qdrant: {d[\"status\"]}, {d[\"points_count\"]:,} pts')"
curl -s localhost:8421/api/search -X POST -H "Content-Type: application/json" -d '{"query":"teste","limit":1,"filters":{}}' | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Rust API: {len(d[\"results\"])} resultado(s)')"
curl -s -o /dev/null -w "Laravel BFF: %{http_code}\n" localhost:8082

# Filtro tipo normalizado (ACORDAO sem acento funciona)
curl -s localhost:8421/api/search -X POST -H "Content-Type: application/json" -d '{"query":"dano moral negativacao","limit":1,"filters":{"tipo":"ACORDAO"}}' | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Filtro tipo: {d[\"query_info\"][\"post_filter_count\"]} resultados')"

# Plugin MCP
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node ~/.claude/plugins/marketplaces/opc-plugins/plugins/stj-vec-tools/server.mjs 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Plugin: {len(d[\"result\"][\"tools\"])} tools')"

# Agente global existe
test -f ~/.claude/agents/query-decomposer.md && echo "Agente: OK" || echo "Agente: FALTA"
```

<session_metadata>
branch: work/query-decomposer-docs
last_commit: a185489
pending_changes: search-config.toml, metadata.rs, storage.rs, server.mjs, docs
qdrant_status: green, 13.4M points
services: stj-search-rust (8421), stj-search-web (8082), qdrant (6333/6334)
expand_query: false (desativado)
normalize_tipo: ativo (ACORDAO -> ACÓRDÃO)
agent_location: ~/.claude/agents/query-decomposer.md (global)
agent_model: sonnet (default)
themes_tested: 5 (familia, penal, consumidor, tributario, CDC/software)
</session_metadata>
