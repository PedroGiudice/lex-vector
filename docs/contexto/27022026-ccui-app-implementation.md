# Contexto: ccui-app -- Implementacao Completa do App Tauri

**Data:** 2026-02-27
**Sessao:** branch `wrapper-legal-agents-front`
**Duracao:** ~2h

---

## O que foi feito

### 1. Implementacao completa do ccui-app via Agent Team (6 tasks)

App Tauri standalone criado em `legal-workbench/ccui-app/` usando agent team com 2 teammates (sonnet). Design doc pre-existente em `legal-workbench/docs/plans/2026-02-27-ccui-app-standalone-design.md`.

Tasks executadas:
- Task 1: Scaffold Tauri + Rust commands (tauri-scaffold)
- Task 2: Tipos, contextos, hooks TypeScript (ts-layer)
- Task 3: CaseSelector component (ts-layer)
- Task 4: SessionView + ChannelTabs + TerminalPane (tauri-scaffold)
- Task 5: Testes unitarios vitest -- 30/30 passando (tauri-scaffold)
- Task 6: Polish visual -- dark theme, cor #d97757 (ts-layer)

### 2. StartupGate -- tunnel SSH automatico

Componente `StartupGate.tsx` adicionado ao App.tsx que:
- Primeira execucao: gera keypair ED25519 em `~/.ccui/`, mostra pub key
- Execucoes seguintes: abre tunnel SSH automaticamente, aguarda health check
- So renderiza o app (CaseSelector) apos backend responder

### 3. Correcoes de deploy

- `tauri.conf.json`: campo `scope` removido do plugin shell (Tauri v2 nao suporta)
- `capabilities/default.json`: permissoes shell adicionadas (allow-spawn, allow-execute)
- `lib.rs`: vm_host alterado de IP Tailscale (`100.123.73.128`) para IP publico (`217.76.48.35`) -- Tailscale SSH intercepta e exige auth web, incompativel com tunnel convencional

### 4. ccui-backend como systemd service

Servico criado em `~/.config/systemd/user/ccui-backend.service` com `Restart=always`. Backend escuta em localhost:8005.

### 5. Caso de teste criado

Diretorio `/home/opc/casos/teste-escritorio/` com 3 arquivos em `base/` e `knowledge.db` (vazio, apenas para marcar ready).

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `legal-workbench/ccui-app/` (inteiro) | Criado -- app Tauri completo |
| `legal-workbench/ccui-app/src-tauri/src/lib.rs` | 6 Tauri commands (config, health, keypair, tunnel) |
| `legal-workbench/ccui-app/src-tauri/tauri.conf.json` | CSP para WS localhost:8005, shell plugin corrigido |
| `legal-workbench/ccui-app/src-tauri/capabilities/default.json` | Permissoes shell para SSH |
| `legal-workbench/ccui-app/src/types/protocol.ts` | ClientMessage, ServerMessage (match ws.rs real) |
| `legal-workbench/ccui-app/src/contexts/WebSocketContext.tsx` | WS sob demanda, reconnect, sem auth |
| `legal-workbench/ccui-app/src/contexts/SessionContext.tsx` | State: caseId, sessionId, channels[] |
| `legal-workbench/ccui-app/src/hooks/useCcuiApi.ts` | Fetch wrappers REST |
| `legal-workbench/ccui-app/src/components/StartupGate.tsx` | Tunnel SSH automatico + onboarding |
| `legal-workbench/ccui-app/src/components/CaseSelector.tsx` | Lista casos, staggered animations |
| `legal-workbench/ccui-app/src/components/SessionView.tsx` | Layout principal com input |
| `legal-workbench/ccui-app/src/components/ChannelTabs.tsx` | Abas dinamicas por agente |
| `legal-workbench/ccui-app/src/components/TerminalPane.tsx` | Output streaming (PROBLEMA -- ver pendencias) |
| `legal-workbench/ccui-app/src/components/AppRouter.tsx` | Routing por estado |
| `legal-workbench/ccui-app/src/styles.css` | CSS vars, dark theme, coral #d97757 |
| `legal-workbench/ccui-app/src/__tests__/` | 5 suites, 30 testes |
| `~/.config/systemd/user/ccui-backend.service` | Systemd service |
| `/home/opc/casos/teste-escritorio/` | Caso de teste |

## Divergencias protocolo: design doc vs backend real (ws.rs)

O ts-layer encontrou 6 divergencias. Os tipos em `protocol.ts` refletem o backend real:

1. `input`: backend usa `{ channel, text }` (design doc tinha `{ session_id, data, channel? }`)
2. `resize`: backend usa `{ channel, cols, rows }` (design doc tinha `{ session_id, cols, rows }`)
3. `session_destroyed` no doc -> `session_ended` no backend
4. `agent_joined`: backend tem `color` e `model` (doc tinha `tmux_session`)
5. `agent_crashed`: novo tipo nao documentado
6. `ping`/`pong`: nao estavam no design doc

## Pendencias identificadas (CRITICAS)

1. **Output ilegivel** -- TerminalPane mostra texto cru do terminal. ANSI strip inadequado resulta em texto sem espacos. O output deveria ser processado e user-friendly (nao terminal emulado). Referencia: repo ADK-sandboxed-legal (clonado em /tmp/adk-ref/) tem padrao de wrapper de output. **2 teammates opus despachados para corrigir (rodando).**

2. **Input nao funciona** -- O campo de input na SessionView possivelmente nao envia mensagem WS no formato correto ou nao inclui `\n` para simular Enter. Claude Code pede confirmacao de trust e o usuario nao consegue responder. **Teammate opus despachado (rodando).**

3. **Commits pendentes** -- Nenhum codigo do ccui-app foi commitado ainda. Tudo esta untracked.

4. **CLAUDE.md pendente** -- Alteracoes nos CLAUDE.md (raiz + LW) da Phase 2 do backend ainda nao commitadas.

5. **Sistema de embedding dos cases** -- Estrutura de pastas e acionamento do embedding nao definidos. `knowledge.db` e apenas placeholder. Precisa definir: como/quando embeddings sao gerados, qual pipeline, formato do DB.

## Decisoes tomadas

- **App Tauri standalone** (nao rota no LW): sessoes longas precisam de janela dedicada
- **SSH tunnel via IP publico** (nao Tailscale): Tailscale SSH intercepta e exige auth web
- **Tailwind v4** (nao v3): compativel com Vite 7 do create-tauri-app
- **ssh-key crate** para keypair (nao ssh-keygen): sem dependencia externa
- **happy-dom** para testes (nao jsdom): jsdom v28 incompativel com Node 18
- **Strip ANSI com regex** (MVP): suficiente para v0.1, mas precisa ser reescrito
- **Agent team com sonnet**: bom custo-beneficio, qualidade adequada para scaffold
- **Opus para bugs criticos**: output e input requerem maior qualidade de raciocinio
