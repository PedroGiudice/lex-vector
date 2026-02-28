# Retomada: ccui-app Polimento -- Duplicatas e UI Cliente

## Contexto rapido

O ccui-app (cliente Tauri para ccui-backend) esta funcionando E2E: usuario manda mensagem, Claude responde usando skills e tools, resultado aparece no app. O fluxo completo foi validado no case `teste-escritorio` no PC do usuario (cmr-auto).

Dois problemas visuais criticos a resolver:

1. **Mensagens duplicadas/triplicadas**: o backend usa `--include-partial-messages` que emite atualizacoes parciais de cada evento stream-json. O `useChat` trata cada update como mensagem nova em vez de atualizar a existente pelo `message_id`. Resultado: a mesma resposta aparece 3-4x.

2. **"Processando dados..." repetido no modo cliente**: tools e Bash sao ocultados corretamente, mas o placeholder de progresso aparece N vezes (uma por partial update). Precisa colapsar em um unico indicador.

O plano de UI dual-mode completo esta em `legal-workbench/docs/plans/2026-02-28-frontend-messagepart-dual-mode.md`.

## Arquivos principais

- `legal-workbench/ccui-app/src/hooks/useChat.ts` -- acumula mensagens (bug das duplicatas aqui)
- `legal-workbench/ccui-app/src/types/protocol.ts` -- tipos ServerMessage (session_id ja ok)
- `legal-workbench/ccui-app/src/components/` -- ChatView e renderizacao (ver plano)
- `legal-workbench/docs/plans/2026-02-28-frontend-messagepart-dual-mode.md` -- plano completo de UI
- `legal-workbench/docs/contexto/28022026-ccui-app-e2e-funcional.md` -- contexto desta sessao

## Proximos passos (por prioridade)

### 1. Corrigir duplicatas em useChat

**Onde:** `ccui-app/src/hooks/useChat.ts`

**O que:** O hook recebe `chat_start`, depois varios `chat_delta` (com partial updates) e `chat_end`. Com `--include-partial-messages`, o backend emite o mesmo `message_id` em multiplos eventos `chat_start`. O hook precisa verificar se uma mensagem com aquele `message_id` ja existe antes de criar uma nova.

Logica atual em `chat_start`:
```typescript
// Adiciona sempre uma nova mensagem -- ERRADO com partial updates
setMessages(prev => [...prev, { id: msg.message_id, ... }])
```

Logica correta:
```typescript
// So adiciona se ainda nao existe
setMessages(prev => {
  if (prev.find(m => m.id === msg.message_id)) return prev;
  return [...prev, { id: msg.message_id, role: 'assistant', parts: [], ... }];
})
```

**Por que:** `--include-partial-messages` re-emite `chat_start` a cada update do processo Claude.

**Verificar:**
```bash
cd legal-workbench/ccui-app && bun run test src/__tests__/useChat.test.ts
```

### 2. Colapsar "Processando dados..." no modo cliente

**Onde:** Componente que renderiza `tool_use`/`tool_result`/`thinking` em modo cliente

**O que:** Em vez de mostrar um "Processando dados..." por partial update, mostrar um unico indicador de progresso que some quando o Claude termina (`chat_end`). Pode ser um spinner ou pill.

**Por que:** Cada partial update gera um novo `chat_delta` com `type: "tool_use"`, que o modo cliente converte em placeholder. Com 4-5 updates parciais, aparecem 4-5 placeholders identicos.

**Verificar:** Mandar uma mensagem que usa skill no modo cliente e confirmar que aparece um unico indicador.

### 3. Executar plano de UI dual-mode

**Onde:** `legal-workbench/docs/plans/2026-02-28-frontend-messagepart-dual-mode.md`

**O que:** Plano completo com ChatView tipada, MessagePart[] renderer, modo cliente vs developer com `getClientIntent()`. Usar `superpowers:executing-plans`.

**Verificar:**
```bash
cd legal-workbench/ccui-app && bun run test && bunx tsc --noEmit
```

## Como verificar o ambiente

```bash
# Backend rodando
systemctl --user status ccui-backend

# Rebuild do deb apos mudancas
cd legal-workbench/ccui-app
bun run tauri build --bundles deb
scp src-tauri/target/release/bundle/deb/ccui-app_0.1.0_amd64.deb cmr-auto@100.102.249.9:~/

# No PC do usuario:
sudo dpkg -i ~/ccui-app_0.1.0_amd64.deb

# MCP bridge (tunnel reverso, rodar no PC):
ssh -R 9223:localhost:9223 opc@100.123.73.128 -N
# Conectar no Claude Code:
# mcp__tauri__driver_session start host=127.0.0.1 port=9223
```

## Branch atual

`wrapper-legal-agents-front` (worktree em `lex-vector/.worktrees/wrapper-legal-agents-front`)
Nao mergeada -- usuario quer polir antes.
