# Retomada: Penpot MCP -- Conectar Claude ao Penpot

## Contexto rapido

Penpot self-hosted esta rodando na VM via Docker (`http://100.123.73.128:9001`). O MCP server do Penpot (que faz a ponte entre Claude e o Penpot) tambem esta rodando na VM (porta 4401). O plugin Penpot foi instalado no browser do PC e conecta ao MCP via WebSocket na porta 4402.

O problema nao resolvido: o Claude Code nao consegue carregar o MCP `penpot` via `type: http` -- a tool `mcp__penpot__execute_code` nunca aparece. O endpoint responde corretamente ao curl, mas o Claude Code nao inicializa a sessao MCP.

Os dois bugfixes do ccui-app (deduplicacao de mensagens + colapso de pills) foram commitados em `wrapper-legal-agents-front` e precisam de merge.

## Arquivos principais

- `~/.claude/settings.json` -- MCP penpot configurado como `{ "type": "http", "url": "http://localhost:4401/mcp" }`
- `/home/opc/penpot/docker-compose.yaml` -- Penpot self-hosted
- `/home/opc/penpot-mcp-src/mcp/packages/` -- codigo-fonte do MCP server (server/, plugin/)
- `/home/opc/penpot-mcp-src/mcp/packages/plugin/vite.config.ts` -- alterado com VITE_WS_HOST
- `legal-workbench/docs/contexto/28022026-penpot-mcp-setup.md` -- contexto detalhado

## Verificar estado inicial

```bash
# Penpot Docker (deve mostrar 6 containers Up)
docker ps --filter "name=penpot"

# MCP server e plugin UI (deve mostrar PIDs)
lsof -ti:4401 && echo "MCP ok" || echo "MCP DOWN"
lsof -ti:4400 && echo "plugin-ui ok" || echo "plugin-ui DOWN"

# Testar endpoint MCP manualmente
curl -s -X POST http://localhost:4401/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' | head -3
```

## Reiniciar processos se necessario

```bash
# MCP server
cd /home/opc/penpot-mcp-src/mcp/packages/server
/home/opc/.nvm/versions/node/v22.22.0/bin/node dist/index.js > /tmp/penpot-server.log 2>&1 &

# Plugin UI
cd /home/opc/penpot-mcp-src/mcp/packages/plugin
/home/opc/.nvm/versions/node/v22.22.0/bin/node node_modules/vite/bin/vite.js preview \
  --host 0.0.0.0 --port 4400 > /tmp/penpot-plugin.log 2>&1 &
```

## Proximos passos (por prioridade)

### 1. Resolver carregamento do MCP penpot no Claude Code

**Problema:** `type: http` nao funciona; `mcp-remote` crasha com Node 18 do sistema.

**Abordagem recomendada -- wrapper script:**
```bash
# Criar /home/opc/.local/bin/penpot-mcp-proxy
#!/bin/bash
export PATH=/home/opc/.nvm/versions/node/v22.22.0/bin:$PATH
exec npx -y mcp-remote http://localhost:4401/sse --allow-http "$@"
```
```bash
chmod +x /home/opc/.local/bin/penpot-mcp-proxy
```

Atualizar `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "penpot": {
      "command": "/home/opc/.local/bin/penpot-mcp-proxy"
    }
  }
}
```

Reiniciar Claude Code e verificar se `mcp__penpot__execute_code` aparece disponivel.

**Verificar:** `ToolSearch("penpot")` deve retornar tools como `mcp__penpot__execute_code`, `mcp__penpot__high_level_overview`

### 2. Testar conexao ponta-a-ponta

Apos MCP carregar:
1. Garantir que plugin Penpot no browser esta conectado (status "Connected to MCP server")
2. Chamar `mcp__penpot__execute_code` com `return penpot.currentPage?.name`
3. Deve retornar o nome da pagina atual no Penpot

### 3. Merge dos bugfixes ccui-app

```bash
cd /home/opc/lex-vector
git checkout main
git merge --ff-only wrapper-legal-agents-front
# ou via PR
```

**Commits a mergear:**
- `a3799a6 fix(ccui-app): deduplicar chat_start e suprimir pills apos streaming`

### 4. Criar units systemd para Penpot MCP (opcional)

Para persistir apos reboot sem precisar reiniciar manualmente.
