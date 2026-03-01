# Retomada: Implementar stream-json no ccui-app

## Contexto rapido

O ccui-app (Tauri, para advogados) exibia output bruto do terminal. Um debate arquitetural com 3 agentes determinou que a solucao e usar `claude -p --output-format stream-json --input-format stream-json --permission-mode dontAsk` como canal principal de comunicacao com o Claude Code. Output vem como NDJSON tipado (thinking, text, tool_use). Zero parsing heuristico. O tmux pipe-pane atual e impossivel de parsear (TUI com cursor movement). Logs JSONL internos do Claude Code (~/.claude/projects/) servem como canal secundario para reconexao e historico.

Nenhum codigo foi alterado -- apenas decisoes arquiteturais. A implementacao comeca agora.

## Arquivos principais

- `docs/contexto/28022026-ccui-app-parsing-debate.md` -- debate completo e decisoes
- `docs/plans/2026-02-27-ccui-app-standalone-design.md` -- design original (PARCIALMENTE OBSOLETO: secoes sobre pipe-pane e parsing substituidas pelas decisoes do debate)
- `legal-workbench/ccui-backend/src/pane_proxy.rs` -- sera substituido por ProcessProxy
- `legal-workbench/ccui-backend/src/ws.rs` -- protocolo WS, precisa de nova variante ChatUpdate
- `legal-workbench/ccui-backend/src/config.rs` -- ja tem `--dangerously-skip-permissions` (linha 28)
- `/home/opc/ADK-sandboxed-legal/src/components/ChatWorkspace.tsx` -- pattern de dual mode a replicar
- `/home/opc/ADK-sandboxed-legal/src/components/MarkdownRenderer.tsx` -- parser MD a copiar

## Proximos passos (por prioridade)

### 1. Investigar schema do stream-json
**Onde:** terminal (fora de sessao Claude Code)
**O que:** executar `CLAUDECODE= claude -p --output-format stream-json --model haiku "diga teste"` e capturar output completo. Mapear tipos de evento (text, thinking, tool_use, tool_result, etc.)
**Por que:** sem conhecer o schema exato, nao da pra definir os tipos TypeScript/Rust
**Verificar:** arquivo com output JSON real salvo em `docs/`

### 2. Investigar multi-turn com stream-json
**Onde:** terminal
**O que:** testar se `--input-format stream-json` suporta enviar mensagens subsequentes (conversacao) ou se e single-shot. Testar com `--resume` / `--continue`
**Por que:** define se o backend gerencia um processo longo (multi-turn) ou recria a cada mensagem
**Verificar:** conseguir enviar 2+ mensagens numa mesma sessao via stdin JSON

### 3. Implementar ProcessProxy no backend
**Onde:** `ccui-backend/src/process_proxy.rs` (novo)
**O que:** substituir `pane_proxy.rs` para o canal principal. Spawnar `claude -p --output-format stream-json` via `tokio::process::Command`. Ler stdout como NDJSON. Emitir `ServerMessage::ChatUpdate` via WS
**Por que:** canal principal de comunicacao com Claude Code
**Verificar:** `cargo test` passa, WS emite mensagens tipadas

### 4. Implementar ChatPane no frontend
**Onde:** `ccui-app/src/components/ChatPane.tsx` (novo, substitui TerminalPane)
**O que:** receber `ChatUpdate` do WS, mapear para `MessagePart[]`, renderizar dual mode (client/developer). Copiar patterns do ADK: ChatWorkspace, AgentMessageBody, getClientIntent
**Por que:** advogado precisa ver chat, nao terminal
**Verificar:** `bun run dev`, mensagens aparecem como bolhas de chat

### 5. Integrar logs JSONL para reconexao
**Onde:** `ccui-backend/src/` (novo modulo)
**O que:** ao reconectar WS, ler `~/.claude/projects/{hash}/{session}.jsonl` para reconstruir historico da conversa
**Por que:** se o advogado fecha e reabre o app, deve ver a conversa anterior
**Verificar:** fechar e reabrir app, historico aparece

## Como verificar

```bash
# Backend compila e testes passam
cd legal-workbench/ccui-backend && cargo test

# Frontend builda
cd legal-workbench/ccui-app && bun run build

# App Tauri roda
cd legal-workbench/ccui-app && cargo tauri dev
```

## Nota importante

O design doc original (`2026-02-27-ccui-app-standalone-design.md`) esta PARCIALMENTE OBSOLETO. As secoes sobre pipe-pane, TerminalPane, e parsing de output devem ser ignoradas. As decisoes do debate (`28022026-ccui-app-parsing-debate.md`) substituem essas secoes.
