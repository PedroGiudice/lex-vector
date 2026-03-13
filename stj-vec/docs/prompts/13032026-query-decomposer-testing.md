# Retomada: Teste e Iteracao do Agente Query-Decomposer

## Contexto rapido

Sessao anterior testou o agente `query-decomposer` end-to-end com 3 modelos (Haiku/Sonnet/Opus).
Haiku fabricou todos os resultados (zero tool calls). Sonnet e Opus funcionaram, Opus superior
(32 resultados, 8 angulos vs 17/6 do Sonnet). Adicionada secao de engenharia de queries ao
prompt com vocabulario juridico real extraido da base STJ e legal-knowledge-base.
Agente movido para `~/.claude/agents/query-decomposer.md` (global).

## Arquivos principais

- `~/.claude/agents/query-decomposer.md` -- agente atualizado com secao de engenharia de queries
- `~/.claude/plugins/marketplaces/opc-plugins/plugins/stj-vec-tools/server.mjs` -- MCP server (3 tools)
- `stj-vec/docs/contexto/13032026-query-decomposer-testing.md` -- contexto detalhado
- `stj-vec/docs/contexto/12032026-query-decomposer-agent.md` -- contexto da sessao anterior

## Proximos passos (por prioridade)

### 1. Testar com queries de outros temas juridicos
**Onde:** Terminal, via `claude --agent` ou subagente
**O que:** Rodar o agente com 2-3 queries de temas diferentes para validar robustez:
- "prescricao intercorrente execucao fiscal" (tributario)
- "dano moral por negativacao indevida banco" (consumidor/bancario)
- "responsabilidade civil objetiva transporte passageiro" (civil)
**Por que:** Ate agora so testamos CDC/software. O prompt tem exemplos de vocabulario STJ mas precisa funcionar para qualquer tema juridico
**Verificar:** Cada execucao deve retornar JSON valido, min 15 resultados, dados reais (doc_ids numericos, scores com decimais)

### 2. Investigar filtro tipo=ACORDAO retornando 0 resultados
**Onde:** Qdrant API direta ou `stj-vec/src/` (Rust search)
**O que:** Verificar se o payload index `tipo` e case-sensitive. Testar: `curl localhost:6333/collections/stj/points/scroll` com filtro `tipo: "ACORDAO"` vs `tipo: "ACÓRDÃO"`
**Por que:** Na sessao, busca com filtro tipo=ACORDAO retornou pre_filter=9, post_filter=0. Todos os candidatos foram eliminados pelo filtro
**Verificar:** `curl -s localhost:6333/collections/stj/points/scroll -X POST -H "Content-Type: application/json" -d '{"limit":5,"filter":{"must":[{"key":"tipo","match":{"value":"ACORDAO"}}]}}'` deve retornar pontos

### 3. Integrar no Laravel BFF
**Onde:** `stj-vec/web/app/Http/Controllers/SearchController.php`
**O que:** Adicionar rota `POST /api/search-decomposed` que chama `claude --agent ~/.claude/agents/query-decomposer.md -p "{query}" --output-format json --model sonnet --dangerously-skip-permissions --no-session-persistence`, parseia JSON, retorna para frontend
**Por que:** O agente deve ser acionavel via interface web
**Verificar:** `curl -s localhost:8082/api/search-decomposed -X POST -d '{"query":"dano moral banco"}' -H "Content-Type: application/json"` retorna JSON valido

### 4. Cleanup modelos Ollama
**Onde:** Terminal
**O que:** `ollama rm qwen2.5:0.5b && ollama rm qwen2.5:1.5b && ollama rm qwen2.5:3b`
**Por que:** ~3.3GB em disco sem uso. Decisao: modelos locais descartados para decomposicao
**Verificar:** `ollama list` mostra apenas bge-m3

## Decisoes vigentes

- **Haiku descartado** -- fabrica resultados sem chamar tools. Problema de capacidade, nao de prompt
- **Sonnet como default** (`model: sonnet` no frontmatter). Opus e melhor mas custo/token maior
- **Vocabulario juridico assado no prompt** -- extraido da base real, nao consultado em runtime
- **Agentes sempre globais** -- `~/.claude/agents/`, nunca em `stj-vec/agents/`
- **Plugin MCP para sandboxing** -- agente so acessa search/document/filters, sem Bash

## Como verificar

```bash
# Servicos operacionais
curl -s localhost:6333/collections/stj | python3 -c "import json,sys; d=json.load(sys.stdin)['result']; print(f'Qdrant: {d[\"status\"]}, {d[\"points_count\"]:,} pts')"
curl -s localhost:8421/api/search -X POST -H "Content-Type: application/json" -d '{"query":"teste","limit":1,"filters":{}}' | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Rust API: {len(d[\"results\"])} resultado(s)')"

# Plugin MCP
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node ~/.claude/plugins/marketplaces/opc-plugins/plugins/stj-vec-tools/server.mjs 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Plugin: {len(d[\"result\"][\"tools\"])} tools')"

# Agente global existe
test -f ~/.claude/agents/query-decomposer.md && echo "Agente: OK" || echo "Agente: FALTA"
```

<session_metadata>
branch: work/query-decomposer-docs
last_commit: a185489
pending_tests: agente com queries de outros temas, filtro tipo=ACORDAO
qdrant_status: green, 13.4M points, 7 indexes
plugin_status: stj-vec-tools installed (project scope)
agent_location: ~/.claude/agents/query-decomposer.md (global)
agent_model: sonnet (default), opus (superior), haiku (DESCARTADO)
</session_metadata>
