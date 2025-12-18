
## 2024-12-18: Adicionar Tools a Subagentes Corretamente

**Contexto:** Ao tentar rodar testes E2E, o subagente `frontend-developer` não tinha acesso ao `mcp__chrome-devtools__*`. Tentou contornar via `npx @modelcontextprotocol/inspector` — que não funciona.

**Lição:**
Quando PGR pede para "adicionar tools a um agente", significa:
1. **Editar o arquivo `.claude/agents/<agente>.md`**
2. **Adicionar no frontmatter `tools:`** as tools necessárias
3. **Sincronizar:** `rsync -av .claude/agents/ ~/.claude/agents/`
4. **Relançar o agente** (novas tools só aplicam em nova instância)

**Antipadrão:** Lançar outro agente "que tem todas as tools" em vez de adicionar as tools corretas ao agente especializado.

**Motivo:** Se as tools MCP existem no projeto, os agentes relevantes devem tê-las. Senão, a existência delas perde propósito.

**Agentes atualizados:**
- `frontend-developer` → +`mcp__chrome-devtools__*`
- `test-writer-fixer` → +`mcp__chrome-devtools__*`, +`mcp__playwright__*`

## 2024-12-18: Gemini CLI via Bash (não MCP)

**Contexto:** Gemini CLI está instalado (`~/.local/bin/gemini`). O MCP wrapper adiciona latência.

**TODO:** Ajustar `gemini-assistant` agent para usar:
```bash
gemini -m gemini-2.5-flash "prompt aqui"
```
Em vez de `mcp__gemini-cli__ask-gemini` que passa por MCP server.

**Benefício:** Menor latência, resposta mais rápida para análises de contexto.
