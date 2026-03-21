# Retomada: Channel Streaming e Live Output

## Contexto rapido

Implementamos integracao de Claude Code Channels no BFF Laravel do stj-vec. Uma sessao Claude Code roda persistente no tmux (`stj-channel`) com o agente `query-decomposer` e acesso ao MCP `stj-vec-tools`. Queries chegam via HTTP ao channel plugin (porta 8790), que empurra para a sessao CC. Claude busca no STJ, gera analise, e responde via tool `stj_channel_reply`.

O fluxo funciona end-to-end: Claude recebe query, busca, e gera resposta juridica de alta qualidade. Problema: a resposta nao chega ao browser. O SSE push entre channel plugin e browser esta falhando -- o `activeStreams` Map esta vazio quando o reply chega (~100s depois). Precisa de redesign para live streaming.

## Arquivos principais

- `web/stj-channel/channel.ts` -- MCP channel plugin (HTTP + SSE + fallback disco)
- `web/app/Services/ChannelSessionManager.php` -- spawn/manage sessao CC
- `web/app/Livewire/DecomposedSearch.php` -- componente com 3 drivers (cli/sdk/channel)
- `web/resources/views/livewire/decomposed-search.blade.php` -- UI com Alpine SSE
- `~/.claude/agents/query-decomposer.md` -- agente CC com tools STJ + reply
- `~/.claude.json` -- config global MCP com stj-channel
- `docs/contexto/22032026-channels-integration-e-live-streaming.md` -- contexto detalhado
- `/home/opc/.claude/plans/dreamy-dancing-peacock.md` -- plano original (6 tasks, todas concluidas mas com bugs)

## Proximos passos (por prioridade)

### 1. Diagnosticar e corrigir SSE push
**Onde:** `web/stj-channel/channel.ts`, handler `CallToolRequestSchema`
**O que:** Debug logging ja adicionado (linhas 70, 73, 149). Reiniciar sessao tmux com codigo atualizado, enviar query, verificar stderr do channel plugin para entender se `activeStreams` esta populado quando o reply chega. Hipotese principal: Bun ReadableStream pode estar fechando a conexao HTTP antes do reply (keep-alive nao funciona como esperado).
**Por que:** Sem isso, o channel e inutilizavel -- resposta existe mas nao chega ao browser
**Verificar:** `curl -sN http://localhost:8790/stream/test-1 &` + POST query + verificar se SSE recebe `data: {"type":"reply",...}`

### 2. Redesenhar para live streaming output
**Onde:** `web/stj-channel/channel.ts` (redesign) + `decomposed-search.blade.php` (display)
**O que:** Em vez de reply unico no final, streaming incremental do que Claude esta fazendo. Duas abordagens possiveis:
  - (A) **stdout pipe**: Ler output do CC via `--output-format stream-json` (como ccui-vf faz com ProcessProxy). Channel plugin vira bridge entre stdout CC e SSE browser.
  - (B) **Multi-reply tool**: Claude chama `stj_channel_reply` multiplas vezes com `type: "progress"` (buscando...), `type: "partial"` (texto parcial), `type: "done"` (final). Requer ajuste no prompt do agente.
  Recomendacao: abordagem (B) e mais simples e nao requer mudar como CC e spawnado.
**Por que:** Sem live output, o usuario ve uma caixa preta por 2 minutos -- UX inaceitavel
**Verificar:** Browser mostra progresso em tempo real (sub-queries sendo executadas, texto aparecendo)

### 3. Implementar cancel real
**Onde:** `web/app/Livewire/DecomposedSearch.php` metodo `cancelSearch()`, + possivelmente endpoint no channel plugin
**O que:** Quando driver=channel, enviar `tmux send-keys -t stj-channel Escape` (ou Ctrl+C) para interromper o turn do Claude. Alternativa: endpoint `POST /cancel/{request_id}` no channel plugin que envia Escape via process signal.
**Por que:** Cancel no BFF so reseta estado local, Claude continua processando e consumindo tokens
**Verificar:** Clicar cancel no browser -> Claude para de buscar no tmux

### 4. Cleanup de jobs stuck
**Onde:** Criar artisan command ou scheduled task
**O que:** `SearchJob::where('status', 'running')->where('created_at', '<', now()->subMinutes(15))->update(['status' => 'timeout'])`. Rodar a cada 5 minutos via scheduler.
**Por que:** Jobs ficam stuck se SSE falha e cancel nao funciona
**Verificar:** `php artisan schedule:list` mostra o job, `php artisan tinker` nao tem jobs running antigos

### 5. Evoluir agente de buscador para pesquisador
**Onde:** `~/.claude/agents/query-decomposer.md`
**O que:** O agente atual e buscador puro (output JSON). Para channel, precisa gerar analise textual com citacoes de precedentes. O prompt ja existe em `stj-vec/agent/prompts/decomposer.md` (sessao anterior, branch `feature/agent-pesquisa-juridica`) mas nao esta no agente CC. Mergear as instrucoes de pesquisa + analise no frontmatter/body do agente.
**Por que:** O channel espera resposta textual via `stj_channel_reply`, nao JSON puro
**Verificar:** Claude responde com analise markdown citando REsp/AREsp reais

## Como verificar

```bash
# Servicos
systemctl --user status stj-search-rust   # API Rust (8421)
systemctl --user status stj-search-web    # Laravel BFF (8082)
tmux list-sessions | grep stj-channel     # Sessao CC com channel

# Channel health
curl -s http://localhost:8790/status       # {"ok":true,"active_streams":0}

# Testes Laravel
cd ~/lex-vector/stj-vec/web && php artisan test --compact  # 68 passed

# Iniciar sessao channel (se nao existir)
cd ~/lex-vector/stj-vec/web
tmux new-session -d -s stj-channel
tmux send-keys -t stj-channel 'claude --dangerously-skip-permissions --agent query-decomposer --dangerously-load-development-channels server:stj-channel' Enter
# Confirmar prompt de development channels (Enter)

# Web UI
# https://extractlab.cormorant-alpha.ts.net:8443
# Login: pgr@stj-vec.local / stj2026
```

<session_metadata>
branch: main
last_commit: 5c7bf12
pending_tests: 0 (68/68 passing)
channel_port: 8790
bff_port: 8082
rust_api_port: 8421
tmux_session: stj-channel
agent: query-decomposer
</session_metadata>
