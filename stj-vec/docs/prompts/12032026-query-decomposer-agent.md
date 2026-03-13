# Retomada: Agente de Decomposicao de Query STJ

## Contexto rapido

Sessao anterior construiu a infraestrutura para decomposicao de query juridica via Claude Code headless.
O Qdrant tem 13.4M pontos com 7 payload indexes (green), pre-filtering operacional.
Modelos locais (ate 3B) descartados por qualidade insuficiente.
Plugin MCP `stj-vec-tools` criado e instalado (3 tools: search, document, filters).
Agente `query-decomposer.md` escrito com tools restritas as MCP tools. NAO TESTADO.

## Arquivos principais

- `stj-vec/agents/query-decomposer.md` -- agente de decomposicao (system prompt + tools MCP)
- `~/.claude/plugins/marketplaces/opc-plugins/plugins/stj-vec-tools/server.mjs` -- MCP server Node.js
- `stj-vec/docs/contexto/12032026-query-decomposer-agent.md` -- contexto detalhado
- `stj-vec/docs/prompts/11032026-query-improvement-metadata-enrichment.md` -- prompt retomada sessao anterior
- `stj-vec/docs/plans/query_juridica.md` -- pesquisa sobre decomposicao multi-perspectiva (referencia)

## Proximos passos (por prioridade)

### 1. Testar agente query-decomposer end-to-end
**Onde:** Terminal, CLI
**O que:** Executar `claude --agent stj-vec/agents/query-decomposer.md -p "inaplicabilidade CDC contrato de licenciamento de software pronto para uso" --output-format text --no-session-persistence --model sonnet --dangerously-skip-permissions`
**Por que:** O agente foi criado mas nunca executado. Precisa validar que as MCP tools funcionam via `--agent` e que o output JSON segue o schema
**Verificar:** Output deve ser JSON valido com campos: original_query, decomposition (intent, angles, rounds), results (array com min 10), total_results

### 2. Iterar no system prompt do agente
**Onde:** `stj-vec/agents/query-decomposer.md`
**O que:** Ajustar baseado nos resultados do teste. Possiveis melhorias: exemplos de angulos para outros temas, instrucoes mais especificas sobre vocabulario juridico, ajuste de limites
**Por que:** Primeiro teste provavelmente revelara gaps no prompt
**Verificar:** Testar com 2-3 queries diferentes alem da teste principal

### 3. Integrar no Laravel BFF
**Onde:** `stj-vec/web/app/Http/Controllers/SearchController.php`
**O que:** Adicionar rota que chama `claude --agent` via `Process::run()`, parseia JSON de resposta, retorna para frontend
**Por que:** O agente deve ser acionavel via interface web, nao so terminal
**Verificar:** `curl localhost:8082/api/search-decomposed?q=...` retorna JSON valido

### 4. Cleanup modelos Ollama
**Onde:** Terminal
**O que:** `ollama rm qwen2.5:0.5b && ollama rm qwen2.5:1.5b && ollama rm qwen2.5:3b`
**Por que:** ~3.3GB em disco sem uso. Decisao: modelos locais descartados para este caso
**Verificar:** `ollama list` mostra apenas bge-m3

### 5. Commit dos arquivos
**Onde:** repo lex-vector
**O que:** Commitar agente + documentos. Plugin MCP vive no repo opc-plugins (separado)
**Por que:** Agente e docs nao estao no git
**Verificar:** `git status` limpo para os novos arquivos

## Decisoes vigentes

- **Step 0 (engenharia pura) piorou resultados** -- expansao dilui sinal raro, descartada como abordagem principal
- **Claude Code headless e o runtime V1** -- `claude --agent`, custo zero (plano Max)
- **SDK Agent com API Key e milestone futuro** -- registrado no Linear
- **Plugin MCP para sandboxing** -- agente so acessa search/document/filters, sem Bash
- **Agente proibido de citar direito** -- restricao estrutural contra alucinacao

## Como verificar

```bash
# Qdrant operacional
curl -s localhost:6333/collections/stj | python3 -c "import json,sys; d=json.load(sys.stdin)['result']; print(f'Status: {d[\"status\"]}, Points: {d[\"points_count\"]:,}')"

# API Rust de busca
curl -s localhost:8421/api/search -X POST -H "Content-Type: application/json" \
  -d '{"query":"dano moral","limit":2,"filters":{}}' | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d[\"results\"])} resultados')"

# Plugin MCP (tools/list)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
  node ~/.claude/plugins/marketplaces/opc-plugins/plugins/stj-vec-tools/server.mjs 2>/dev/null | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d[\"result\"][\"tools\"])} tools')"

# Plugin instalado
cat ~/.claude/plugins/installed_plugins.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('stj-vec-tools' in str(d))"
```

<session_metadata>
branch: main
last_commit: 272c37c
pending_tests: agente query-decomposer (nunca executado)
qdrant_status: green, 13.4M points, 7 indexes
plugin_status: stj-vec-tools installed (project scope)
linear_milestone: SDK Agent para query decomposition
</session_metadata>
