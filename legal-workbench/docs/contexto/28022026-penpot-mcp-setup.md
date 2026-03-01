# Contexto: Setup Penpot Self-Hosted + MCP para Vibe Design

**Data:** 2026-02-28
**Sessao:** wrapper-legal-agents-front
**Foco:** Configuracao de ambiente de design (Penpot + MCP) e dois bugfixes no ccui-app

---

## O que foi feito

### 1. Bugfixes ccui-app (commit a3799a6)

Dois bugs corrigidos via subagente `frontend-developer`:

**Bug 1 -- Duplicatas em chat_start (`useChat.ts`):**
O backend usa `--include-partial-messages` e re-emite `chat_start` com o mesmo `message_id`. Fix: verificar se a mensagem ja existe antes de adicionar.

```typescript
// hooks/useChat.ts -- case "chat_start"
setMessages((prev) => {
  if (prev.find(m => m.id === msg.message_id)) return prev;
  return [...prev, { id: msg.message_id, role: "assistant", parts: [], ... }];
});
```

**Bug 2 -- Status pills repetidos no modo cliente (`ChatView.tsx`):**
Cada `chat_delta` com `tool_use` gerava um StatusPill. Fix: colapsar em indicador unico durante streaming, suprimir todos apos `chat_end`.

### 2. Setup Penpot Self-Hosted na VM

**Docker Compose:** `/home/opc/penpot/docker-compose.yaml`
- Baixado de `https://raw.githubusercontent.com/penpot/penpot/main/docker/images/docker-compose.yaml`
- `PENPOT_PUBLIC_URI` alterado para `http://100.123.73.128:9001`
- Stack: penpot-frontend, penpot-backend, penpot-exporter, penpot-postgres, penpot-valkey, penpot-mailcatch
- Porta: 9001 (acessivel do PC via Tailscale em `http://100.123.73.128:9001`)

```bash
# Subir
cd /home/opc/penpot && docker compose -p penpot -f docker-compose.yaml up -d

# Status
docker ps --filter "name=penpot"
```

### 3. Setup Penpot MCP Server

**Fonte:** clone sparse do repo penpot/penpot em `/home/opc/penpot-mcp-src/mcp/`

**Problema de arquitetura resolvido:**
O plugin Penpot (roda no browser do PC) precisa conectar via WebSocket ao servidor MCP. A URL estava hardcoded como `ws://localhost:4402` -- inacessivel do browser do PC. Fix: rebuild do plugin com o IP Tailscale da VM.

**Build do plugin com IP correto:**
```bash
# vite.config.ts -- alterado para:
let WS_URI = process.env.VITE_WS_HOST
  ? `ws://${process.env.VITE_WS_HOST}:4402`
  : "ws://localhost:4402";

# Rebuild:
cd /home/opc/penpot-mcp-src/mcp && VITE_WS_HOST=100.123.73.128 \
  ~/.nvm/versions/node/v22.22.0/bin/npx pnpm --filter ./packages/plugin run build
```

**Processos em background (precisam ser reiniciados apos reboot):**

```bash
# MCP server (porta 4401 HTTP/SSE, 4402 WS, 4403 REPL)
cd /home/opc/penpot-mcp-src/mcp/packages/server
/home/opc/.nvm/versions/node/v22.22.0/bin/node dist/index.js > /tmp/penpot-server.log 2>&1 &

# Plugin UI server (porta 4400)
cd /home/opc/penpot-mcp-src/mcp/packages/plugin
/home/opc/.nvm/versions/node/v22.22.0/bin/node node_modules/vite/bin/vite.js preview \
  --host 0.0.0.0 --port 4400 > /tmp/penpot-plugin.log 2>&1 &
```

### 4. Configuracao MCP no Claude Code

**`~/.claude/settings.json`:**
```json
{
  "mcpServers": {
    "penpot": {
      "type": "http",
      "url": "http://localhost:4401/mcp"
    }
  }
}
```

**Problema nao resolvido:** O Claude Code nao carrega o MCP `penpot` na inicializacao. A tool `mcp__penpot__execute_code` nunca aparece disponivel. O endpoint `/mcp` responde corretamente ao curl (SSE format com JSON-RPC valido). Possiveis causas:
1. Claude Code 2.1.63 pode ter bug/incompatibilidade com Streamable HTTP
2. Timing: Claude Code inicializa antes do servidor estar pronto
3. O formato de resposta SSE pode nao ser o esperado para Streamable HTTP

**Tentativas falhas:**
- `mcp-remote` via npx: crasha com `File is not defined` pois usa Node 18 do sistema em vez de Node 22 do nvm (cache em `/home/opc/.npm/_npx/705d23756ff7dacc/`)
- `type: http` direto: erro "Server not initialized"

### 5. Vibma (abandonado)

Tentativa inicial com Vibma (Figma MCP) abandonada pois o usuario prefere Penpot (gratuito).
O tunnel Vibma ainda roda em background (porta 3055, PID 2218159) -- pode ser killado.

---

## Estado dos processos na VM

| Servico | Porta | PID | Status |
|---------|-------|-----|--------|
| Penpot Docker | 9001 | - | Up (docker compose -p penpot) |
| Penpot MCP server | 4401/4402/4403 | 2284669 | Rodando |
| Plugin UI | 4400 | 2285678 | Rodando |
| Vibma tunnel | 3055 | 2218159 | Rodando (nao necessario) |

---

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `legal-workbench/ccui-app/src/hooks/useChat.ts` | Modificado -- deduplicacao chat_start |
| `legal-workbench/ccui-app/src/components/ChatView.tsx` | Modificado -- colapsar pills |
| `/home/opc/penpot/docker-compose.yaml` | Criado -- Penpot self-hosted |
| `/home/opc/penpot-mcp-src/mcp/packages/plugin/vite.config.ts` | Modificado -- VITE_WS_HOST |
| `~/.claude/settings.json` | Modificado -- MCP penpot adicionado |
| `~/.claude.json` | Modificado -- MCP Vibma adicionado (pode ignorar) |

---

## Commits desta sessao

```
a3799a6 fix(ccui-app): deduplicar chat_start e suprimir pills apos streaming
```

---

## Pendencias identificadas

1. **[CRITICO] MCP penpot nao carrega no Claude Code** -- o `mcp__penpot__*` nunca fica disponivel. Investigar alternativa: (a) wrapper shell script com PATH correto para Node 22 + mcp-remote, (b) aguardar fix do Claude Code, (c) usar endpoint SSE via proxy diferente

2. **[MEDIO] Processos nao persistem apos reboot** -- Penpot MCP e Plugin UI rodam como processos background sem systemd. Criar units systemd ou adicionar ao startup.

3. **[MEDIO] Vibma tunnel orfao** -- processo na porta 3055 pode ser killado: `kill $(lsof -ti:3055)`

4. **[BAIXO] Merge da branch** -- os dois bugfixes do ccui-app estao commitados em `wrapper-legal-agents-front`. Precisa de PR ou merge direto para main.

## Decisoes tomadas

- **Penpot vs Figma:** Usuario escolheu Penpot por ser gratuito (sugestao do Reddit)
- **Self-hosted vs cloud:** Self-hosted na VM para evitar tunnels; browser acessa via Tailscale
- **MCP direto vs mcp-remote:** Tentamos ambos; nenhum funcionou ainda. Proximo passo: wrapper script com PATH explicitp para Node 22
- **Plugin UI rebuild:** Necessario porque WS URL estava hardcoded como localhost; alterado para VITE_WS_HOST env var
