# Contexto: SSE Push + Streaming de Progresso -- Busca Decomposta

**Data:** 2026-03-17
**Branch:** main (mudancas nao commitadas)

---

## O que foi feito

### 1. decompose.ts -- eventos NDJSON no stderr
Helper `emitEvent()` emite JSON+newline no stderr. Eventos: `search_started`, `search_completed`, `completed`, `error`. Stdout (result.json) nao e afetado.

### 2. SearchStreamController -- endpoint SSE
Controller le `stderr.log` via fseek/fread, retransmite cada linha NDJSON como SSE (`event: {name}\ndata: {json}\n\n`). Heartbeat a cada 500ms. Detecta processo morto. Timeout server-side 600s. Ao receber `completed` do stderr, espera ate 2s pelo result.json (race condition Bun stdout/stderr).

### 3. DecomposedSearch.php -- novos metodos
- `loadResult()` -- le resultado com retry (5x 300ms)
- `markError(?string $message)` -- seta status + mensagem
- `markTimeout()` -- seta status timeout
- `streamUrl` -- public property setada em `startSearch()`
- `extractErrorFromStderr()` -- le stderr.log e result.json, traduz erros da API
- `humanizeApiError()` -- traduz mensagens comuns (usage limits, auth, rate limit)

### 4. Blade template -- Alpine EventSource
`wire:poll.3s` substituido por `x-data` com EventSource. Chips de angulos em tempo real (SDK). Spinner de angulo atual com animate-pulse. Timeout client-side 600s. Fallback: `onerror` chama `loadResult()`.

### 5. ANTHROPIC_API_KEY removida
Key estava no `.env` do Laravel e vazava para o subprocesso CLI, forcando o CLI a usar billing de API em vez da subscription OAuth. Removida do `.env`, `config/services.php`, e `SdkAgentRunner`.

### 6. Systemd service -- PATH injetado
`stj-search-web.service` nao tinha PATH. Subprocessos CLI nao encontravam `node` para lancar MCP servers. Adicionado PATH completo e HOME.

### 7. query-decomposer.md -- restricao de tools
Frontmatter `tools` lista apenas as 3 tools MCP do stj-vec-tools. **Porem o allowlist nao e enforced pelo CLI `--agent`** -- o agente continua tendo acesso a Bash, Skill, etc.

## Estado dos arquivos (nao commitados)

| Arquivo | Status | Detalhe |
|---------|--------|---------|
| `stj-vec/agent/src/decompose.ts` | Modificado | +emitEvent helper, 5 pontos de emissao |
| `stj-vec/web/app/Http/Controllers/SearchStreamController.php` | Criado | Endpoint SSE |
| `stj-vec/web/app/Livewire/DecomposedSearch.php` | Modificado | +loadResult, markError, markTimeout, streamUrl, extractErrorFromStderr |
| `stj-vec/web/app/Services/SdkAgentRunner.php` | Modificado | Removida injecao de ANTHROPIC_API_KEY |
| `stj-vec/web/config/services.php` | Modificado | Removida referencia anthropic_api_key |
| `stj-vec/web/resources/views/livewire/decomposed-search.blade.php` | Modificado | Alpine EventSource + chips tempo real |
| `stj-vec/web/routes/web.php` | Modificado | +rota SSE |
| `stj-vec/web/tests/Feature/DecomposedSearchTest.php` | Modificado | +5 testes (loadResult, markError, markTimeout, streamUrl) |
| `stj-vec/web/tests/Feature/SearchStreamControllerTest.php` | Criado | 4 testes SSE |
| `.claude/settings.json` | Modificado | +stj-vec-tools plugin |
| `~/.claude/agents/query-decomposer.md` | Modificado | tools allowlist (nao enforced) |
| `~/.config/systemd/user/stj-search-web.service` | Modificado | +PATH, +HOME |
| `stj-vec/web/.env` | Modificado | Removida ANTHROPIC_API_KEY |

## Decisoes tomadas

- **SSE em vez de wire:poll**: push e correto, polling causa race conditions e requests desnecessarios
- **Remover ANTHROPIC_API_KEY**: vazava para CLI via env, forcando billing de API. CLI usa subscription OAuth
- **Public property vs computed**: `getStreamUrlProperty()` retornava proxy callable do Livewire no Alpine. Trocado por public property `$streamUrl`
- **Retry no loadResult**: Bun faz flush do stderr antes do stdout. SSE emite `completed` mas result.json pode estar vazio por ~200ms

## Problemas nao resolvidos

1. **CLI `tools` allowlist nao enforced** (CRITICO) -- o frontmatter `tools` no agente lista so as 3 MCP tools, mas o CLI `--agent` ignora e da acesso a tudo (Bash, Skill, Glob, etc). O agente chamou `Skill('jurisprudence-search')` em vez de usar as tools MCP
2. **Parsing do resultado CLI** -- `AgentRunner::getResult()` espera JSON com chave `results` no top-level ou dentro de envelope `{type: "result", result: "<json>"}`. O CLI com `--output-format json` retorna array de mensagens, e o `result` do ultimo elemento e texto narrativo, nao JSON estruturado. O agente nao seguiu o prompt de output JSON
3. **SDK driver sem API key** -- removida intencionalmente. Precisa ser reconfigurada de forma segura (`.env` e ok, mas precisa garantir que nao vaza para CLI)
4. **Tailscale Serve porta 8443** -- configurado para expor o app, mas nao testado end-to-end

## Testes

52 testes passando, Pint clean. Testes cobrem: SSE content-type, 404, eventos stderr, loadResult, markError, markTimeout, streamUrl.
