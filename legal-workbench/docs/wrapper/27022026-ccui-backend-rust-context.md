# Contexto: ccui-backend Rust -- Backend WebSocket para Agent Teams GUI

**Data:** 2026-02-27
**Branch:** wrap-legal-agent-teams (worktree)
**Sessao:** Implementacao completa do backend Rust (9 tasks), revisao de codigo, correcoes

---

## Objetivo do projeto

Substituir o `ccui-ws` Python (placeholder com respostas hardcoded) por um backend Rust que:
1. Cria sessoes tmux headless com Claude Code
2. Faz proxy bidirecional entre WebSocket e panes tmux (input/output)
3. Detecta teammates de Agent Teams via inotify no `~/.claude/teams/*/config.json`
4. Permite que advogados usem Agent Teams (`/legal-team`) via GUI sem terminal

## Arquitetura

```
Frontend (React/xterm.js)
    |
    v  WebSocket (multiplexado por canal)
ccui-backend (Rust/axum) :8005
    |
    |-- SessionManager --> tmux new-session -d
    |-- PaneProxy --> pipe-pane + tail_log async
    |-- TeamWatcher --> inotify em ~/.claude/teams/
    |
    v
tmux (headless na VM)
    |-- pane main: claude --dangerously-skip-permissions
    |-- pane %34: legal-researcher (teammate)
    |-- pane %37: legal-case-analyst (teammate)
    |-- pane %39: legal-strategist (teammate)
```

## Modulos implementados (1714 linhas Rust, 8 modulos)

### `src/tmux.rs` (260 linhas) -- TmuxDriver

Unico ponto de entrada para subprocessos tmux. Sem estado interno (wrapper puro).

Metodos publicos:
- `new_session(name, width, height)` -- sessao headless
- `session_exists(name) -> bool`
- `kill_session(name)`
- `send_keys(session, pane_id, text)` -- usa `-l` (literal) + Enter separado
- `send_text_multiline(session, pane_id, text)` -- load-buffer + paste-buffer
- `capture_pane(session, pane_id)` -- snapshot com ANSI (`-e -p`)
- `list_panes(session) -> Vec<PaneInfo>`
- `resize_pane(pane_id, cols, rows)`
- `pipe_pane(pane_id, log_path)` -- `cat >> 'path'`
- `unpipe_pane(pane_id)`
- `list_sessions_with_prefix(prefix)`

**Bug descoberto e corrigido:** pane IDs globais (`%XX`) NAO aceitam formato `session:%XX` como target. Adicionado `resolve_target()` que usa apenas `%XX` diretamente quando o ID comeca com `%`.

### `src/session.rs` (166 linhas) -- SessionManager

Gerencia sessoes Claude Code. `Arc<RwLock<HashMap>>` para concorrencia.

- `create_session(working_dir)` -- cria tmux headless, descobre pane via list_panes, retorna UUID curto (8 chars). NAO inicia Claude Code (feito externamente).
- `destroy_session(id)` -- remove do map + kill_session
- `recover_orphan_sessions()` -- startup recovery de sessoes tmux com prefixo

### `src/pane_proxy.rs` (220 linhas) -- PaneProxy

Bridge bidirecional pane tmux <-> broadcast WebSocket.

- `register_channel(name, session, pane_id)` -- cria log file, inicia pipe-pane, spawna tail_log com CancellationToken
- `unregister_channel(name)` -- cancela tail_log, unpipe, remove log
- `send_input(name, text)` -- roteia para send_keys ou send_text_multiline
- `capture_snapshot(name)` -- capture-pane para catchup na reconexao

`tail_log` e uma funcao async que faz polling do arquivo de log (100ms interval). Usa `tokio::fs::File::read` que avanca o file descriptor automaticamente. CancellationToken garante shutdown limpo via `tokio::select!`.

### `src/team_watcher.rs` (187 linhas) -- TeamWatcher

Observa `~/.claude/teams/*/config.json` via `notify` crate (inotify no Linux).

Tracking: `HashMap<team_name, HashMap<member_name, tmux_pane_id>>`. Emite `AgentJoined` quando `tmux_pane_id` aparece pela primeira vez (nao quando o membro e adicionado -- o pane_id pode chegar num update posterior). Emite `AgentLeft` quando membro desaparece.

Canal sync->async: callback do inotify usa `blocking_send` para `mpsc::channel(100)`.

### `src/ws.rs` (77 linhas) -- Protocolo

```rust
// ClientMessage (tagged por "type")
Input { channel, text }
Resize { channel, cols: u32, rows: u32 }
CreateSession { working_dir: Option<String> }
DestroySession { session_id }
Ping

// ServerMessage (tagged por "type")
Output { channel, data }
SessionCreated { session_id }
SessionEnded { session_id }
AgentJoined { name, color, model, pane_id }
AgentLeft { name }
AgentCrashed { name }  // definido mas nao emitido ainda
Error { message }
Pong
```

### `src/routes.rs` (253 linhas) -- Router HTTP + WebSocket

- `GET /health` -- "ok"
- `GET /api/sessions` -- JSON com IDs
- `GET /ws` -- upgrade WebSocket

AppState contem: config, session_mgr, tmux, pane_proxy, broadcast_tx.

Handler WS: loop `tokio::select!` entre recv do client e broadcast. Responde `Message::Ping` com `Message::Pong` (RFC 6455). Events de sessao enviados apenas via broadcast (sem duplicacao).

### `src/config.rs` (53 linhas) / `src/error.rs` (34 linhas)

Config com defaults sensiveis (porta 8005, prefixo "ccui", logs em /tmp/ccui-pane-logs). Apenas CCUI_PORT e CCUI_HOST configuraveis via env.

AppError com thiserror + IntoResponse para axum.

## Testes (23 passando)

| Suite | Testes | O que cobre |
|-------|--------|-------------|
| tmux_integration | 5 | create/destroy, send_keys/capture, list_panes, resize, pipe_pane |
| session_integration | 4 | create/destroy, list, get, destroy nonexistent |
| pane_proxy_integration | 4 | register/output broadcast, send_input, list_channels, capture_snapshot |
| ws_protocol | 10 | serialize/deserialize de todos os tipos de mensagem |

Testes de integracao criam sessoes tmux reais. Rodar com `--test-threads=1`.

## Revisao de codigo -- correcoes aplicadas

| Issue | Severidade | Correcao |
|-------|-----------|----------|
| tail_log sem shutdown | Critico | CancellationToken via tokio-util |
| WS Ping descartado sem Pong | Critico | Handler para Message::Ping |
| SessionCreated duplicado | Importante | Enviar apenas via broadcast |
| TeamWatcher perde AgentJoined | Importante | Track tmux_pane_id separadamente |
| pipe_pane path sem quoting | Importante | Apostrofes no cat >> 'path' |
| notify feature macos_kqueue | Importante | Removido, usar default |

## Issues pendentes pos-revisao (sugestoes, nao criticos)

1. `send_server_msg` deveria retornar Result e propagar erro para encerrar loop WS
2. `from_env` nao le todas as variaveis de config (CCUI_PANE_LOG_DIR, etc)
3. `AgentCrashed` definido no protocolo mas nenhum componente emite
4. Keepalive proativo (server-initiated ping) nao implementado
5. `working_dir` aceito em create_session mas nao passado ao tmux (-c flag)
6. Dockerfile sem cache de dependencias (rebuild completo a cada mudanca)

## Commits desta sessao

```
53d36c6 fix(ccui-backend): correcoes da revisao de codigo
e67a364 feat(ccui-backend): Dockerfile multi-stage para deploy
3624f07 feat(ccui-backend): integracao completa SessionManager + PaneProxy + TeamWatcher
d66ec0a feat(ccui-backend): PaneProxy bridge bidirecional pane <-> WebSocket
18e93a8 feat(ccui-backend): protocolo WebSocket, router HTTP e TeamWatcher
7874f75 feat(ccui-backend): SessionManager cria e gerencia sessoes Claude via tmux
819fe2f feat(ccui-backend): TmuxDriver com testes de integracao
2cd109a fix(ccui-backend): add .gitignore, remove target/ from tracking
5cd2c4d feat(ccui-backend): scaffold projeto Rust com config e error types
```

## Decisoes tomadas

- **Rust sobre Python**: robustez, performance, type safety para componente critico
- **axum sobre actix-web**: WS builtin, ecossistema tokio nativo
- **pipe-pane + tail_log sobre capture-pane polling**: streaming real-time vs snapshot periodico. capture-pane usado apenas para catchup na reconexao
- **Canal multiplexado**: 1 WS connection, mensagens taggeadas por `channel` (nome do agente)
- **CancellationToken sobre oneshot**: mais ergonomico, suporta clone, padrao tokio-util
- **Binario direto na VM (nao Docker)**: precisa acesso ao tmux server do host. Docker adicionaria friccao sem beneficio. Dockerfile mantido para referencia futura
- **create_session NAO inicia Claude**: separacao de concerns. O frontend/usuario decide quando iniciar Claude na sessao
- **resolve_target**: pane IDs globais (%XX) nao precisam de prefixo de sessao no tmux

## Documentos relacionados

- Design doc: `docs/plans/2026-02-27-ccui-rust-backend-design.md`
- Plano de implementacao: `~/.claude/plans/ancient-knitting-meerkat.md`
- Frontend CCUI existente: `frontend/src/components/ccui-v2/`
- Backend Python (substituido): `docker/services/ccui-ws/main.py`
