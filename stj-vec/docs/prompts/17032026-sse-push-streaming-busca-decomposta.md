# Retomada: SSE Push + Busca Decomposta -- Corrigir CLI e Parsing

## Contexto rapido

Sessao anterior implementou SSE push para a busca decomposta do stj-vec: decompose.ts emite eventos NDJSON no stderr, SearchStreamController retransmite via SSE, Alpine consome com EventSource. O SDK driver funciona (eventos, chips tempo real). O CLI driver tem dois problemas bloqueantes: (1) o `tools` allowlist no frontmatter do agente nao e enforced pelo `claude --agent`, entao o agente usa Bash/Skill em vez das tools MCP; (2) o parsing do resultado CLI nao extrai o JSON estruturado do output do agente.

ANTHROPIC_API_KEY foi removida do .env para impedir vazamento para o CLI. Precisa ser reconfigurada para o SDK driver de forma isolada.

Mudancas nao commitadas. 52 testes passando.

## Arquivos principais

- `stj-vec/agent/src/decompose.ts` -- SDK agent com eventos NDJSON
- `stj-vec/web/app/Http/Controllers/SearchStreamController.php` -- endpoint SSE
- `stj-vec/web/app/Livewire/DecomposedSearch.php` -- Livewire com loadResult, markError, streamUrl
- `stj-vec/web/resources/views/livewire/decomposed-search.blade.php` -- Alpine EventSource
- `stj-vec/web/app/Services/AgentRunner.php` -- CLI driver (parsing precisa de fix)
- `~/.claude/agents/query-decomposer.md` -- agente decompositor (tools allowlist nao enforced)
- `docs/contexto/17032026-sse-push-streaming-busca-decomposta.md` -- contexto detalhado

## Proximos passos (por prioridade)

### 1. Corrigir parsing do resultado CLI no AgentRunner
**Onde:** `stj-vec/web/app/Services/AgentRunner.php`, metodo `getResult()`
**O que:** O CLI com `--output-format json` retorna um array JSON de mensagens. O ultimo elemento tem `type: "result"` e `result: "<string>"`. Esse string pode ser: (a) JSON valido com chave `results` (quando o agente segue o prompt), ou (b) texto narrativo (quando nao segue). O parser precisa: iterar o array, encontrar o ultimo `type: "result"`, tentar parsear `result` como JSON, e se tiver `results`, retornar. Se for texto, retornar null com erro descritivo.
**Por que:** Sem isso, resultados validos do CLI sao descartados
**Verificar:** `php artisan test --filter=test_poll_returns_results_when_complete`

### 2. Resolver tools allowlist do agente CLI
**Onde:** `~/.claude/agents/query-decomposer.md`
**O que:** O campo `tools` no frontmatter nao restringe quando o agente roda via `--agent` (main thread). Opcoes: (a) investigar se `disallowedTools` funciona para main thread; (b) usar hook PreToolUse para bloquear tools indesejadas; (c) aceitar que o agente vai ter acesso a tudo e confiar no prompt. A opcao (c) e fragil -- o agente chamou `Skill('jurisprudence-search')` em vez de usar MCP tools.
**Por que:** Sem restricao, o agente improvisa e ignora as tools corretas
**Verificar:** Rodar busca no browser com CLI, verificar que so usa `stj_search`/`stj_document`/`stj_filters`

### 3. Reconfigurar ANTHROPIC_API_KEY para SDK driver
**Onde:** `stj-vec/web/.env` e `stj-vec/web/app/Services/SdkAgentRunner.php`
**O que:** Colocar key no `.env`, SdkAgentRunner le e injeta APENAS no subprocesso do SDK (nao no CLI). O AgentRunner do CLI deve garantir que `ANTHROPIC_API_KEY` e removida do env do subprocesso (`env -u ANTHROPIC_API_KEY` no wrapper bash).
**Por que:** SDK precisa da key, CLI nao pode ve-la
**Verificar:** Busca SDK funciona, busca CLI nao usa API key

### 4. Commitar mudancas
**Onde:** stj-vec/
**O que:** Mudancas estao todas nao commitadas. Commitar em 2-3 commits atomicos: (1) SSE + streaming, (2) remocao API key + systemd fix, (3) fixes de parsing
**Verificar:** `php artisan test --compact` (52 testes)

## Como verificar

```bash
cd ~/lex-vector/stj-vec/web
php artisan test --compact           # 52 testes passando
vendor/bin/pint --dirty              # Pint clean
systemctl --user status stj-search-web  # Servico rodando
systemctl --user status stj-search-rust # Backend Rust rodando
curl -s http://localhost:8421/api/filters | head -1  # API Rust respondendo
```
