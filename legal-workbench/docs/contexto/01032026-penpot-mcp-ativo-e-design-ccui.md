# Contexto: Penpot MCP Ativo + Início do Design CCUI

**Data:** 2026-03-01
**Sessão:** wrapper-legal-agents-front
**Duração:** ~2h

---

## O que foi feito

### 1. Penpot MCP funcionando no Claude Code

O MCP do Penpot agora carrega corretamente. O problema raiz era que o campo
`mcpServers` em `~/.claude/settings.json` **não** é lido para MCP servers — o
Claude Code usa o arquivo `~/.claude.json` (top-level, não o subdiretório).

**Solução final:**
- Wrapper em `/home/opc/.local/bin/penpot-mcp-proxy`:
  ```bash
  #!/bin/bash
  NODE=/home/opc/.nvm/versions/node/v22.22.0/bin/node
  MCP_REMOTE=/home/opc/.nvm/versions/node/v22.22.0/bin/mcp-remote
  exec "$NODE" "$MCP_REMOTE" http://localhost:4401/sse --allow-http --transport sse-only "$@"
  ```
- Registro via CLI (escopo user → vai para `~/.claude.json`):
  ```bash
  claude mcp add --scope user penpot /home/opc/.local/bin/penpot-mcp-proxy
  ```
- `--transport sse-only` elimina o fallback http→sse (que causava delay e timeout)

**Infraestrutura Penpot:**
- Penpot self-hosted: `http://100.123.73.128:9001` (Docker, 6 containers)
- MCP server: porta 4401 (Node 22, `dist/index.js`)
- Plugin UI: porta 4400 (vite preview)
- WebSocket bridge: porta 4402
- `mcp-remote` instalado em `/home/opc/.nvm/versions/node/v22.22.0/bin/mcp-remote`

**Validação:** `mcp__penpot__execute_code` disponível. `penpot.currentPage.name` retornou `"Page 1"`. Estrutura da página confirmada.

### 2. Início do design CCUI no Penpot

3 páginas criadas no Penpot:
- `Design System` (renomeada de "Page 1")
- `CaseSelector`
- `SessionView`

Conteúdo criado na página Design System:
- Board principal 1200×1600 com fundo `#0a0a0a`
- **Color tokens**: 11 swatches (bg-base → rose) com nome e hex
- **Tipografia**: 5 amostras de tamanho + sample mono
- **Componentes**: StatusPill, Badge ready/incomplete, Send button, ModeToggle, Input field (idle + focus), CaseCard ready (hover state), CaseCard incomplete

**Interrompido** ao tentar definir `text.width` (propriedade read-only em Text shapes). As mensagens de bubble ficaram para continuar.

**Lição aprendida:** `Text.width` é read-only no Penpot API. Para controlar largura de texto, usar `growType = "fixed"` + `resize(w, h)`.

---

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `/home/opc/.local/bin/penpot-mcp-proxy` | Criado — wrapper Node 22 + mcp-remote |
| `~/.claude.json` | Modificado — `mcpServers.penpot` adicionado via CLI |
| `~/.claude/settings.json` | Modificado — `mcpServers: {}` (esvaziado, não é o lugar certo) |
| Penpot (design) | Design System page com tokens + componentes parciais |

---

## Commits desta sessão

Nenhum commit novo (trabalho de configuração e design).

---

## Pendências identificadas

1. **Continuar design CCUI no Penpot** — faltam: message bubbles no DS, tela CaseSelector completa, tela SessionView completa
2. **Merge dos bugfixes ccui-app** — commits `a3799a6` e anteriores em `wrapper-legal-agents-front` precisam ir para `main`
3. **Serviços Penpot não persistem no reboot** — não há units systemd; precisam ser reiniciados manualmente

---

## Decisões tomadas

- **`~/.claude.json` é o config real de MCPs**: `settings.json` mcpServers é ignorado pelo Claude Code para MCP servers
- **`--transport sse-only`**: eliminar fallback http-first que causa ~1.5s de delay na inicialização
- **Node 22 com paths absolutos**: shebang `#!/usr/bin/env node` no mcp-remote pegava Node 18; solução é chamar `$NODE $MCP_REMOTE` com paths explícitos
- **Design ccui**: criar no Penpot as 3 seções (Design System, CaseSelector, SessionView) para ter referência visual antes de qualquer refactor visual

---

## Como reiniciar serviços Penpot (se necessário)

```bash
# Verificar se estão up
lsof -ti:4401 && echo "MCP ok" || echo "MCP DOWN"
lsof -ti:4400 && echo "plugin-ui ok" || echo "plugin-ui DOWN"

# MCP server
cd /home/opc/penpot-mcp-src/mcp/packages/server
/home/opc/.nvm/versions/node/v22.22.0/bin/node dist/index.js > /tmp/penpot-server.log 2>&1 &

# Plugin UI
cd /home/opc/penpot-mcp-src/mcp/packages/plugin
/home/opc/.nvm/versions/node/v22.22.0/bin/node node_modules/vite/bin/vite.js preview \
  --host 0.0.0.0 --port 4400 > /tmp/penpot-plugin.log 2>&1 &
```
