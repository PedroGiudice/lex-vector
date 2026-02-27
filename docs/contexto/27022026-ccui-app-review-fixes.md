# Contexto: ccui-app -- Review Completo + Correcoes P0 + MCP Bridge

**Data:** 2026-02-27
**Sessao:** branch `wrapper-legal-agents-front` (mergeado em main)
**Duracao:** ~1h

---

## O que foi feito

### 1. Review completo via agent team Opus (2 reviewers)

Team `ccui-review` com 2 teammates Opus revisou todo o ccui-app:

- **frontend-reviewer**: 18 arquivos analisados, media 4.1/5 qualidade
- **tauri-reviewer**: 6 arquivos analisados, media 3.8/5 qualidade

10 achados totais, 5 classificados como P0.

### 2. Correcoes P0 via agent team Sonnet (3 fixers)

Team `ccui-fixes` com 3 teammates Sonnet em worktrees isolados:

**Fix 1 -- Race condition connect/createSession (ws-fixer)**
- `WebSocketContext.tsx`: `connect()` retorna `Promise<void>` (resolve no onopen, rejeita no onerror)
- `CaseSelector.tsx`: `handleSelect` agora e `async` com `await connect()`
- Problema: `createSession` era chamado antes do WS estar OPEN, mensagem descartada silenciosamente

**Fix 2 -- Seguranca shell + SSH lifecycle (rust-fixer)**
- `capabilities/default.json`: removidos `shell:allow-spawn` e `shell:allow-open` (sem scope). Args do SSH agora usam validators regex
- `lib.rs`: `TunnelState(Mutex<Option<CommandChild>>)` armazena o processo SSH. `close_tunnel` command adicionado. Porta usa `config.local_port` (nao hardcoded)

**Fix 3 -- xterm.js no TerminalPane (xterm-fixer)**
- `TerminalPane.tsx`: reescrito com `@xterm/xterm` + `@xterm/addon-fit`. Terminal read-only (disableStdin), ResizeObserver, reset ao trocar canal
- Removidos `terminalParser.ts` e `MarkdownRenderer.tsx` (usados apenas pelo TerminalPane antigo)

### 3. MCP Bridge plugin adicionado

- `Cargo.toml`: `tauri-plugin-mcp-bridge = "0.9"`
- `lib.rs`: plugin registrado com `#[cfg(debug_assertions)]` (apenas debug builds)
- `tauri.conf.json`: `withGlobalTauri: true`
- `capabilities/default.json`: `mcp-bridge:default`

### 4. Build e deploy

- `cargo tauri build` gerou 3 bundles (AppImage 78MB, .deb, .rpm)
- `.deb` transferido para PC Linux (`cmr-auto:~/Desktop/`)

## Commits desta sessao

```
37800a9 feat(ccui-app): adicionar MCP Bridge plugin para automacao Tauri
34a7a7a Merge branch 'wrapper-legal-agents-front'
6ab2851 docs(ccui-app): contexto e prompts de implementacao
c5b4130 feat(ccui-app): app Tauri standalone para advogados
```

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `legal-workbench/ccui-app/src/contexts/WebSocketContext.tsx` | Modificado -- connect() retorna Promise |
| `legal-workbench/ccui-app/src/components/CaseSelector.tsx` | Modificado -- handleSelect async |
| `legal-workbench/ccui-app/src/components/TerminalPane.tsx` | Reescrito -- xterm.js |
| `legal-workbench/ccui-app/src/lib/terminalParser.ts` | Removido |
| `legal-workbench/ccui-app/src/components/MarkdownRenderer.tsx` | Removido |
| `legal-workbench/ccui-app/src-tauri/src/lib.rs` | Modificado -- TunnelState, close_tunnel, MCP bridge |
| `legal-workbench/ccui-app/src-tauri/capabilities/default.json` | Modificado -- permissoes restritivas, mcp-bridge |
| `legal-workbench/ccui-app/src-tauri/tauri.conf.json` | Modificado -- withGlobalTauri |
| `legal-workbench/ccui-app/src-tauri/Cargo.toml` | Modificado -- tauri-plugin-mcp-bridge |
| `legal-workbench/ccui-app/package.json` | Modificado -- @xterm/xterm, @xterm/addon-fit |

## Achados do review (nao corrigidos ainda)

| # | Sev | Area | Problema |
|---|-----|------|----------|
| 1 | P1 | Frontend | MarkdownRenderer perdia indentacao em code blocks (arquivo removido com xterm.js) |
| 2 | P1 | Frontend | Spinners dependem de p5.js via CDN global (falha silenciosa) |
| 3 | P2 | Backend | `StrictHostKeyChecking=no` no SSH (MITM em producao) |
| 4 | P2 | Frontend | ErrorBanner ignora `config.icon` por tipo |
| 5 | P2 | Frontend | `segmentIdCounter` global em TerminalPane (removido com xterm.js) |

## Pendencias identificadas

1. **Testes desatualizados** -- TerminalPane.test.tsx testa o componente antigo (sem xterm.js). Precisa reescrever
2. **Teste real do app** -- usuario vai enviar screenshots na proxima sessao
3. **p5.js CDN** -- Spinners dependem de `window.p5` que pode nao carregar
4. **StrictHostKeyChecking** -- remover `=no` em producao, usar known_hosts gerenciado
5. **Embedding dos cases** -- pipeline de embedding nao definido (knowledge.db e placeholder)

## Decisoes tomadas

- **xterm.js em vez de strip ANSI**: output do Claude Code usa TUI features que nao podem ser stripped
- **MCP bridge apenas em debug**: seguranca -- nao expor WS 9223 em release
- **.deb para Ubuntu**: melhor integracao que AppImage
- **Validators regex no shell scope**: compromisso entre seguranca e funcionalidade (Tauri v2 suporta)
