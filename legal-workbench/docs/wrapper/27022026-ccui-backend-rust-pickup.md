# Retomada: ccui-backend Rust -- Smoke Test e Integracao com Frontend

## Contexto rapido

Backend Rust completo (`ccui-backend`) implementado em 9 tasks com 23 testes passando e revisao de codigo aplicada. O backend substitui o `ccui-ws` Python e faz proxy bidirecional WebSocket <-> panes tmux para sessoes Claude Code, incluindo deteccao automatica de Agent Teams via inotify.

O backend compila, testes passam, health endpoint responde. Falta: smoke test end-to-end com Claude Code real (requer conta Max do usuario) e integracao com o frontend React (WebSocketContext + xterm.js).

Branch: `wrap-legal-agent-teams` (worktree). Binario release: 2.7MB em `ccui-backend/target/release/ccui-backend`.

## Arquivos principais

- `ccui-backend/src/` -- 8 modulos Rust (tmux, session, pane_proxy, routes, ws, team_watcher, config, error)
- `ccui-backend/tests/` -- 4 suites de teste (23 testes)
- `docs/wrapper/27022026-ccui-backend-rust-context.md` -- contexto detalhado desta sessao
- `docs/plans/2026-02-27-ccui-rust-backend-design.md` -- design doc com arquitetura, protocolo, fluxos
- `frontend/src/components/ccui-v2/` -- frontend CCUI existente (React)
- `frontend/src/components/ccui-v2/contexts/WebSocketContext.tsx` -- provider WS atual (precisa adaptacao)

## Proximos passos (por prioridade)

### 1. Smoke test e2e com Claude Code real

**Onde:** Terminal da VM
**O que:** Iniciar backend, criar sessao, iniciar Claude manualmente na sessao tmux, executar /legal-team, verificar agent_joined events no WebSocket
**Por que:** Validar que o fluxo completo funciona antes de integrar no frontend
**Guia completo:**

```bash
# Terminal 1: backend
cd /home/opc/lex-vector/legal-workbench/ccui-backend
RUST_LOG=debug cargo run

# Terminal 2: health check + websocat
curl localhost:8005/health  # "ok"
websocat ws://localhost:8005/ws
# Digitar: {"type":"ping"}  -> esperar {"type":"pong"}
# Digitar: {"type":"create_session"}  -> esperar session_created com ID

# Terminal 3: iniciar Claude na sessao tmux
tmux list-sessions | grep ccui  # descobrir nome
tmux attach -t ccui-XXXXXXXX
claude --dangerously-skip-permissions
# Executar: /legal-team:legal-team

# Terminal 2 (websocat): observar agent_joined events

# Cleanup: {"type":"destroy_session","session_id":"XXXXXXXX"}
```

**Problema conhecido:** O canal "main" nao e registrado automaticamente no PaneProxy apos create_session. Input/output via WS so funciona para canais registrados. Proxima task: auto-registrar canal main no create_session, e canais de teammates quando agent_joined chega.

### 2. Auto-registro de canais no PaneProxy

**Onde:** `ccui-backend/src/routes.rs` handler `CreateSession` + callback de `TeamWatcher`
**O que:** Apos create_session, registrar automaticamente o canal "main" com o pane principal. Quando TeamWatcher emite AgentJoined, registrar canal com nome do agente e pane_id.
**Por que:** Sem registro, o PaneProxy nao faz streaming de output nem roteia input
**Verificar:** `cargo test -- --test-threads=1`

### 3. Integrar frontend React com novo backend

**Onde:** `frontend/src/components/ccui-v2/contexts/WebSocketContext.tsx`
**O que:** Adaptar o WebSocketContext para o novo protocolo (tagged messages por tipo). Adicionar xterm.js para renderizar output ANSI. Multi-panel layout para canais de agentes.
**Por que:** O frontend atual espera mensagens do formato antigo (token/done/thinking). O novo protocolo usa `output`/`agent_joined`/etc.
**Verificar:** Abrir `legalwb.duckdns.org/ccui-assistant` e verificar que conecta ao WS

### 4. Implementar keepalive e deteccao de AgentCrashed

**Onde:** `ccui-backend/src/routes.rs` (keepalive), `ccui-backend/src/pane_proxy.rs` ou novo modulo (health check)
**O que:** Ping proativo do server a cada 30s. Health check de panes via `list_panes` + `pane_dead` flag. Emitir `AgentCrashed` quando pane morre.
**Por que:** Conexoes ociosas caem sem keepalive. Crashes de agentes precisam ser reportados ao frontend.
**Verificar:** Matar um pane tmux manualmente e verificar que AgentCrashed chega no WS

### 5. Corrigir working_dir no create_session

**Onde:** `ccui-backend/src/tmux.rs` (`new_session`) e `ccui-backend/src/session.rs` (`create_session`)
**O que:** Passar `-c working_dir` ao tmux new-session. O parametro ja e aceito mas ignorado.
**Verificar:** Criar sessao com working_dir e verificar `pwd` no pane

### 6. Docker / deploy

**Onde:** `docker-compose.yml`, `ccui-backend/Dockerfile`
**O que:** Decidir: rodar binario direto na VM (mais simples, acesso ao tmux) vs Docker com volume mounts. Atualizar Traefik labels para apontar ao Rust backend.
**Por que:** O Python ccui-ws ainda esta no docker-compose. Precisa ser substituido.

## Como verificar (estado atual)

```bash
cd /home/opc/lex-vector/legal-workbench/ccui-backend

# Testes
cargo test -- --test-threads=1

# Clippy
cargo clippy -- -W clippy::pedantic

# Build release
cargo build --release

# Rodar (debug)
RUST_LOG=debug cargo run
# -> curl localhost:8005/health  # "ok"
```
