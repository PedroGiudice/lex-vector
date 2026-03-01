# Contexto: ccui-app E2E Funcional

**Data:** 2026-02-28
**Sessao:** wrapper-legal-agents-front
**Duracao:** ~4h

---

## O que foi feito

### 1. Sincronizacao de protocolo TypeScript (ccui-app)

Executado o plano `2026-02-28-ccui-app-protocol-sync.md` completo:

- `ServerMessage` expandido com `session_id` em `chat_start/delta/end` e novo tipo `chat_init`
- `ClientMessage` com nova variante `chat_input { session_id, text }`
- `useChat` atualizado: importa `useSession`, envia `chat_input` em vez de `input` (tmux legado), trata `chat_init` como noop
- `chat-flow.test.tsx` atualizado com `session_id` nos eventos
- `tsc --noEmit` limpo apos remocao de import `MessagePart` nao usado em `useChat.ts`

### 2. Build e deploy do .deb

- `bun run tauri build --bundles deb` -- gera apenas .deb, mais rapido que `targets: "all"`
- `scp` para `cmr-auto@100.102.249.9:~/`
- Dois rebuilds nesta sessao: primeiro sem MCP bridge em release, segundo com

### 3. MCP bridge ativado em release

`src-tauri/src/lib.rs`: removido `#[cfg(debug_assertions)]` do `tauri_plugin_mcp_bridge::init()`.
Necessario para inspecao via Claude Code MCP no .deb instalado.

Tunnel reverso SSH para conectar MCP server (VM) ao app (PC):
```bash
ssh -R 9223:localhost:9223 opc@100.123.73.128 -N
```
Depois: `mcp__tauri__driver_session start host=127.0.0.1 port=9223`

### 4. Correcao de tres bugs criticos no ccui-backend (main)

Commit: `9c7b141 fix(ccui-backend): corrigir spawn do Claude`

**Bug 1: `CLAUDECODE=1` herdado do ambiente**
- Sintoma: `claude stdout EOF` imediatamente apos spawn
- Causa: backend herdava `CLAUDECODE=1` do systemd; Claude recusava iniciar ("nested session")
- Fix: `cmd.env_remove("CLAUDECODE")` em `process_proxy.rs:74`

**Bug 2: `--verbose` ausente**
- Sintoma: `Error: When using --print, --output-format=stream-json requires --verbose`
- Fix: adicionado `--verbose` ao Command em `process_proxy.rs`

**Bug 3: Formato JSON do input errado**
- Sintoma: `TypeError: undefined is not an object (evaluating '$.message.role')`
- Backend enviava: `{"type":"user","content":[...]}`
- Correto: `{"type":"user","message":{"role":"user","content":[...]}}`
- Fix: `send_input()` em `process_proxy.rs:130`

**Bug 4 (anterior, mesma sessao): binary release desatualizado**
- `CLAUDECODE unknown variant chat_input` -- binary release era pre-ProcessProxy
- Havia um processo debug `target/debug/ccui-backend` na porta 8005 bloqueando o release
- Fix: `kill 1761359` + recompilacao do release

### 5. Fluxo E2E validado

- App instalado no PC (cmr-auto)
- Sessao criada com case `teste-escritorio`
- Mensagem "Pode buscar os artigos de Lei relevantes para Acao de Rescisao de Contrato?"
- Claude respondeu, usou skill `legal-knowledge-access`, executou Bash, retornou resultado
- Modo developer: ferramentas visiveis (raw)
- Modo cliente: ferramentas ocultas (correto), mas "Processando dados..." repetido N vezes

---

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `ccui-app/src/types/protocol.ts` | Modificado -- session_id, chat_init, chat_input |
| `ccui-app/src/__tests__/protocol.test.ts` | Modificado -- 8 testes, todos passando |
| `ccui-app/src/__tests__/useChat.test.ts` | Modificado -- mock SessionContext, 6 testes |
| `ccui-app/src/__tests__/integration/chat-flow.test.tsx` | Modificado -- session_id nos eventos |
| `ccui-app/src/hooks/useChat.ts` | Modificado -- chat_input + useSession + chat_init noop |
| `ccui-app/src-tauri/src/lib.rs` | Modificado -- MCP bridge sem cfg(debug_assertions) |
| `ccui-backend/src/process_proxy.rs` | Modificado (main) -- 3 bugs corrigidos |

## Commits desta sessao

### Branch wrapper-legal-agents-front (worktree)
```
9a8f5ba feat(ccui-app): ativar MCP bridge em release build
07aeb8a fix(ccui-app): remover import nao usado MessagePart em useChat
9e76243 test(ccui-app): atualizar chat-flow integration test para protocolo ProcessProxy
106ef75 feat(ccui-app): useChat usa chat_input (ProcessProxy) + suporte a chat_init
7d6c70c feat(ccui-app): adicionar chat_input ao ClientMessage (ProcessProxy)
4e0aac6 feat(ccui-app): sincronizar ServerMessage com schema ProcessProxy (session_id + chat_init)
```

### Branch main (repo principal)
```
9c7b141 fix(ccui-backend): corrigir spawn do Claude (env_remove CLAUDECODE, --verbose, formato stream-json)
```

## Pendencias identificadas

1. **Mensagens duplicadas/triplicadas** -- ALTA PRIORIDADE
   - Causa: `--include-partial-messages` emite updates parciais de cada evento stream-json
   - Frontend acumula em vez de substituir a mensagem em progresso
   - Fix necessario: `useChat` deve atualizar (merge) a mensagem existente via `message_id`, nao adicionar nova

2. **"Processando dados..." repetido no modo cliente** -- ALTA PRIORIDADE
   - Bashes e skills sao ocultados corretamente, mas o placeholder aparece N vezes (uma por partial update)
   - Fix necessario: colapsar multiplos `Processando dados...` em um unico indicador de progresso

3. **Plano de UI dual-mode pendente** -- MEDIA PRIORIDADE
   - `docs/plans/2026-02-28-frontend-messagepart-dual-mode.md` -- plano detalhado existente
   - Nao iniciado: ChatView tipada, MessagePart[] renderer, modo cliente vs developer

4. **`TerminalPane.test.tsx` com 6 falhas pre-existentes** -- BAIXA (nao relacionado)

## Decisoes tomadas

- **MCP bridge em release**: aceitavel por ora para facilitar debug; revisar antes de distribuicao ampla
- **stderr logado em WARN**: temporario para debug, pode voltar para DEBUG depois
- **Branch mantida sem merge**: usuario quer polir antes de integrar
