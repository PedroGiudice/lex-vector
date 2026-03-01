# Contexto: Debate Arquitetural -- Parsing/Wrapping de Output do Claude Code

**Data:** 2026-02-28
**Sessao:** wrapper-legal-agents-front
**Tipo:** Decisao arquitetural (sem codigo)

---

## O que foi feito

### 1. Analise do estado atual do ccui-app

O app Tauri (ccui-app) foi avaliado via screenshot. Diagnostico: renderiza output bruto do terminal (Claude Code CLI via tmux pipe-pane) diretamente na tela. E um terminal embutido -- advogados veem ANSI codes, trust prompts, spinners. Zero funcionalidade (trust prompt interativo trava o app).

### 2. Analise do repositorio ADK-sandboxed-legal como referencia

Clonado em `/home/opc/ADK-sandboxed-legal/`. Identificados patterns reaproveitaveis:

- `ChatWorkspace.tsx`: renderizacao dual developer/client mode
- `MessagePart[]`: tipagem (text, thought, tool_call, bash, file_op)
- `getClientIntent()`: traduz artefatos tecnicos para linguagem leiga
- `MarkdownRenderer.tsx`: parser custom de markdown
- `agentBridge.ts`: NAO reaproveitavel (sentinelas `__ADK_EVENT__` do Gemini ADK)

### 3. Debate com agent team (3 agentes, Opus)

Time `parsing-debate` com frontend-dev, rust-dev, backend-arch. 3 rodadas:

**Rodada 1 -- Posicoes iniciais:**
- frontend-dev: parsing 100% frontend
- rust-dev: parsing 100% backend (enum ChatPart, mod parser)
- backend-arch: hibrido (backend ANSI strip, frontend semantica)

**Rodada 2 -- Contra-argumentos:**
- Todos convergiram para hibrido
- Consenso: ANSI strip no backend, classificacao semantica no frontend
- `--dangerously-skip-permissions` inaceitavel (docs confidenciais)
- Trust prompt interceptado no backend via send_keys

**Rodada 3 -- Descoberta critica:**
- Logs reais em `/tmp/ccui-pane-logs/` revelam: output do Claude Code via tmux pipe-pane e TUI completa (cursor movement `\x1b[7A`, spinners animados, screen rewriting). NAO e texto com ANSI de cor.
- Parsing heuristico de TUI: IMPOSSIVEL
- Descoberta: `claude -p --output-format stream-json` existe (flag oficial)
- Descoberta: `--input-format stream-json`, `--include-partial-messages`, `--permission-mode dontAsk`
- Descoberta: logs JSONL em `~/.claude/projects/{hash}/{session}.jsonl` contem dados estruturados escritos em tempo real (thinking, text, tool_use, com timestamps, model, usage)

**Consenso final (3/3):** stream-json como canal principal, logs JSONL para reconexao/historico.

### 4. Decisao final do TD

stream-json. Motivo: interface oficial documentada > formato interno sem contrato.

## Decisoes tomadas

| Decisao | Escolha | Justificativa |
|---------|---------|---------------|
| Canal principal de output | `claude -p --output-format stream-json` | Oficial, documentado, NDJSON tipado |
| Canal de input | `--input-format stream-json` | Bidirecional estruturado |
| Canal secundario | Logs JSONL (~/.claude/projects/) | Reconexao, historico, analytics |
| tmux pipe-pane | Developer mode apenas | TUI impossivel de parsear |
| Trust prompt | `--permission-mode dontAsk` | Elimina prompts interativos |
| Classificacao semantica | Frontend | Heuristica, muda com versoes CLI |
| Reaproveitamento ADK | ChatWorkspace, MessagePart[], getClientIntent | Patterns de UI, nao parsing |
| Upload de arquivos | Nao existe -- @arquivo via CLI | Docs ja nos case files |
| StateChange no protocolo | Nao | Frontend infere estado localmente |

## Pendencias identificadas

1. **Schema exato do stream-json** -- precisa testar `claude -p --output-format stream-json` fora de sessao Claude Code (CLAUDECODE env bloqueia nested)
2. **Multi-turn com stream-json** -- `--input-format stream-json` suporta conversacao continua ou e single-shot? Se single-shot, precisa de `--resume`/`--continue`
3. **Redesign do backend** -- pane_proxy.rs substituido por ProcessProxy (child process headless)
4. **Redesign do frontend** -- TerminalPane substituido por ChatPane com MessagePart[] + dual mode

## Arquivos de referencia

| Arquivo | Relevancia |
|---------|-----------|
| `legal-workbench/docs/plans/2026-02-27-ccui-app-standalone-design.md` | Design doc original |
| `/home/opc/ADK-sandboxed-legal/src/components/ChatWorkspace.tsx` | Pattern de dual mode |
| `/home/opc/ADK-sandboxed-legal/src/services/agentBridge.ts` | Referencia de parsing (NAO reaproveitavel) |
| `legal-workbench/ccui-backend/src/pane_proxy.rs` | Sera substituido por ProcessProxy |
| `/tmp/ccui-pane-logs/` | Logs reais que provam TUI impossivel de parsear |
| `~/.claude/projects/` | Logs JSONL internos (canal secundario) |

## Commits desta sessao

Nenhum. Sessao puramente de debate e decisao arquitetural.
