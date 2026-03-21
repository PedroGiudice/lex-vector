# Contexto: Channels Integration e Live Streaming

**Data:** 2026-03-22
**Sessao:** main (commits 4cab7f7..5c7bf12)
**Duracao:** ~4h (continuacao de sessao anterior sobre SDK vs local model)

---

## O que foi feito

### 1. Channel Plugin (stj-channel)

MCP channel plugin em Bun que permite empurrar queries de fora (web UI) para uma sessao Claude Code persistente. Arquitetura two-way:

- `POST /query` -- fire-and-forget, retorna `{request_id}` imediatamente
- `GET /stream/{id}` -- SSE push stream (browser abre, espera reply)
- `GET /status` -- health check
- `GET /response/{id}` -- fallback poll (quando SSE falha)

Tool `stj_channel_reply` exposta via MCP: Claude Code chama para devolver a resposta ao channel plugin, que faz push via SSE.

### 2. ChannelSessionManager (PHP)

Service singleton no Laravel que spawna/gerencia sessao Claude Code com channel. Metodos: `ensureRunning()`, `sendQuery()`, `streamUrl()`, `isAlive()`, `start()`, `stop()`.

Spawn via nohup em background. Health check via HTTP GET `/status` na porta 8790.

### 3. Driver "channel" no DecomposedSearch

Terceiro driver (alem de cli e sdk) no Livewire component. Fluxo nao-bloqueante:
1. Livewire faz POST fire-and-forget via ChannelSessionManager
2. Passa `channelStreamUrl` pro frontend
3. Alpine abre EventSource direto no channel plugin (porta 8790)
4. Quando recebe `reply`, chama `$wire.persistAnalysis(text)` para salvar no DB

### 4. Migration e Model

Coluna `session_id` (nullable, indexed) e `analysis` (longText, nullable) na `search_jobs`. Model atualizado.

### 5. CLAUDE.md com instrucoes juridicas

Instrucoes de dominio juridico para a sessao channel: processo de decomposicao, regras de citacao, vocabulario STJ.

### 6. Agente query-decomposer atualizado

Tool `mcp__stj-channel__stj_channel_reply` adicionada ao frontmatter. Config global do MCP (`~/.claude.json`) atualizada com entry do stj-channel.

## Estado dos arquivos

| Arquivo | Status | Detalhe |
|---------|--------|---------|
| `web/stj-channel/channel.ts` | Criado | MCP channel plugin, 199 linhas, com debug logging e fallback disco |
| `web/stj-channel/package.json` | Criado | @modelcontextprotocol/sdk |
| `web/app/Services/ChannelSessionManager.php` | Criado | Singleton, spawn/manage sessao CC |
| `web/app/Livewire/DecomposedSearch.php` | Modificado | +startChannelSearch, +persistAnalysis, +channelStreamUrl |
| `web/resources/views/livewire/decomposed-search.blade.php` | Modificado | +radio channel, +SSE Alpine, +analise markdown |
| `web/app/Models/SearchJob.php` | Modificado | +session_id, +analysis no $fillable |
| `web/database/migrations/2026_03_21_201407_*.php` | Criado | session_id + analysis |
| `web/config/services.php` | Modificado | +agent.channel config |
| `web/app/Providers/AppServiceProvider.php` | Modificado | +singleton ChannelSessionManager |
| `web/.mcp.json` | Modificado | +stj-channel server |
| `web/CLAUDE.md` | Modificado | +instrucoes pesquisador juridico |
| `web/tests/Feature/ChannelDriverTest.php` | Criado | 13 testes, 27 assertions |
| `~/.claude.json` | Modificado | +stj-channel MCP global |
| `~/.claude/agents/query-decomposer.md` | Modificado | +tool stj_channel_reply |

## Commits desta sessao

```
5c7bf12 fix(stj-channel): debug logging + fallback poll quando SSE desconecta
4e448b2 feat(stj-vec-web): channel plugin e ChannelSessionManager
59e79f5 test(stj-vec-web): testes para driver channel e persistAnalysis
70b78c2 feat(stj-vec-web): migration session_id/analysis + instrucoes pesquisador juridico
4cab7f7 feat(stj-vec-web): driver channel com SSE push e analise textual
```

## Decisoes tomadas

- **Channels em vez de SDK multi-turn**: Channels mantem contexto naturalmente via sessao CC persistente. SDK exigiria persistencia manual do array de messages. | Descartado: SDK com DB de messages
- **SSE push em vez de polling**: Channel plugin faz push via ReadableStream controller quando Claude responde. Zero polling. | Problema: SSE nao esta entregando (ver pendencias)
- **Agente query-decomposer como base**: Reusar agente existente (--agent query-decomposer) em vez de criar novo. Adicionada tool de reply. | Trade-off: agente e buscador puro, precisa ser expandido para pesquisador com analise
- **Config global do MCP**: stj-channel adicionado em `~/.claude.json` para funcionar de qualquer cwd. | Alternativa descartada: .mcp.json por projeto
- **Tmux para sessao persistente**: Claude Code precisa de terminal interativo. Tmux mantem a sessao viva em background.

## Teste E2E realizado

Claude Code recebeu query via channel, fez 7 buscas no STJ, gerou analise completa com precedentes citados (REsp, AREsp, turmas, ministros). Tempo: ~100s por query com Opus. Resposta textual de alta qualidade juridica.

**Problema critico:** a resposta nao chegou ao browser via SSE. O handler `CallToolRequestSchema` mostra "reply pushed via SSE" mas o `activeStreams` Map pode estar vazio quando o reply chega (stream ja desconectou ou timing issue). Fallback de disco adicionado mas nao resolve o UX.

## Pendencias identificadas

1. **SSE push nao entrega reply ao browser** (alta) -- Bug principal. O `activeStreams.get(request_id)` retorna undefined quando Claude responde. Pode ser: (a) timing -- stream abre e fecha antes do reply, (b) Bun ReadableStream issue com long-lived connections. Debug logging adicionado mas nao testado apos reinicio.

2. **Live streaming output** (alta) -- Redesign necessario. Em vez de esperar reply final, mostrar o que Claude esta fazendo em tempo real (buscando, analisando, escrevendo). Possivel abordagem: ler stdout do processo CC via pipe (como ccui-vf faz) ou usar `--output-format stream-json` com `--input-format stream-json`.

3. **Cancel nao para Claude** (media) -- `cancelSearch()` reseta estado Livewire mas nao envia Escape/Ctrl+C para a sessao tmux. Solucao: `tmux send-keys -t stj-channel Escape` ou `C-c`.

4. **Jobs ficam stuck em "running"** (media) -- Sem timeout/cleanup automatico. Se SSE falha e cancel nao funciona, SearchJob fica `status=running` indefinidamente. Precisa de cron job ou scheduled command para limpar.

5. **`/clear` apos cada resposta** (baixa) -- Decidir se quer follow-ups (contexto preservado) ou queries independentes (clear apos cada). Depende do UX desejado.

6. **Prompt do agente precisa evoluir** (media) -- O query-decomposer atual e buscador puro (output JSON). Para channel, precisa ser pesquisador com analise textual. A sessao anterior ja criou `agent/prompts/decomposer.md` com esse perfil, mas o agente CC usa o frontmatter de `~/.claude/agents/query-decomposer.md`.
