# Contexto: Fix CLI MCP + JSONL Extraction + Historico Clicavel

**Data:** 2026-03-19 (sessao 2)
**Branch:** main
**Duracao:** ~3h

---

## O que foi feito

### 1. Diagnostico do "fetch failed"

O MCP plugin `stj-vec-tools` falhava intermitentemente com `fetch failed` quando o CLI era spawado como subprocesso pelo PHP (via systemd). Causa: o CLI carregava 22+ plugins MCP simultaneamente, causando contencao no startup. O `stj-vec-tools` tentava `fetch("http://localhost:8421")` antes de estar pronto.

### 2. --strict-mcp-config

Flag `--strict-mcp-config` + `--mcp-config` inline no `AgentRunner::start()`. O CLI agora carrega apenas 1 MCP server (`stj-vec-tools`) em vez de 22+ plugins. Startup instantaneo, sem contencao.

Tool names mudaram: `mcp__stj-vec-tools__search` (antes: `mcp__plugin_stj-vec-tools_stj-vec-tools__search`).

### 3. Extracao de resultados via JSONL

`AgentRunner::getResult()` agora tem 3 estrategias em cascata:

1. **JSONL extraction** (imposto): le o session log do CLI (`~/.claude/projects/-home-opc-lex-vector/{session_id}.jsonl`), extrai `tool_result` das chamadas `search`, dedup por `doc_id`. Independe do output textual do agente.
2. **JSON parsing**: se o agente retornou JSON `{results: [...]}`
3. **Narrative fallback**: aceita texto como `{narrative: "..."}`

### 4. Instrucao de formato JSON no -p

O system prompt do agente (via --agent) compete com o system prompt base do CLI. Nenhum modelo (Sonnet, Opus) obedece a instrucao de retornar JSON puro. Solucao: injetar instrucao de formato diretamente no `-p` (user message). O agente passa a retornar JSON na maioria dos casos. JSONL extraction garante robustez quando nao retorna.

### 5. nohup spawn

`Process::run` trocado por `shell_exec` com `nohup`. O `artisan serve` e single-threaded -- `Process::run` bloqueava todo o app ate o bash retornar. Com `nohup` + `&`, o bash retorna o PID imediatamente.

### 6. Retry no MCP plugin

`server.mjs` atualizado: `localhost` -> `127.0.0.1`, retry com 3 tentativas e backoff (500ms, 1.5s, 3s), versao 0.2.0.

### 7. Historico clicavel

`loadHistoryJob()` corrigido para receber `array $data` (Livewire 4 dispatch passa array como primeiro argumento). Jobs antigos com `results: null` corrigidos via tinker.

### 8. Blade: narrative fallback

Template `decomposed-search.blade.php` renderiza texto narrativo quando `$decomposition['narrative']` esta presente.

## Commits desta sessao

```
41916a7 fix(stj-vec-web): strict-mcp-config, nohup spawn e historico clicavel
f4a9913 feat(stj-vec-web): extracao de resultados via JSONL + fallback narrativo
43d46dd feat(stj-vec-web): SSE streaming, search_jobs table e SDK output parser
5c5b8cb docs(stj-vec): adiciona contextos e prompts das sessoes 16-19/03
```

## Decisoes tomadas

- **JSONL extraction como primary**: imposta, nao depende do agente seguir instrucoes de formato. Os dados vem direto dos tool calls.
- **--strict-mcp-config**: elimina 22+ plugins do startup. Custo zero, ganho enorme em estabilidade.
- **nohup em vez de Process::run**: artisan serve e single-threaded, nao pode bloquear.
- **Instrucao no -p, nao no system prompt**: user message tem mais peso que system prompt para formato de resposta.
- **Opus no agente**: modelo trocado de sonnet para opus no frontmatter do query-decomposer.md. Mais caro mas melhor decomposicao.

## Estado atual

- **CLI driver**: funciona end-to-end. 30 resultados em ~45-60s. JSONL extraction garante dados estruturados.
- **SDK driver**: funciona (sessao anterior). Mais rapido (~30s) mas usa API key.
- **Historico**: clicavel, carrega resultados do DB.
- **55 testes passando**, Pint clean.

## Pendencias

1. **Analise de qualidade** (proxima sessao): comparar resultados CLI vs SDK, avaliar cobertura, iterar prompts
2. **Performance CLI**: 45-60s e aceitavel mas poderia ser melhor. Opus e mais lento que Sonnet.
3. **Theming TOML**: bug nao resolvido (CSS variables nao aplicadas)
4. **Testes de auth**: ausentes
5. **Push para origin**: 48+ commits locais
