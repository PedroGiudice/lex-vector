# Retomada: ccui-app -- Fix session reconnect + cleanup

## Contexto rapido

O ccui-app tem backend com endpoints PATCH/DELETE para sessoes (campo `name`), frontend com SessionsList refatorado (inline rename, delete, click), plugins Tauri nativos (fs, dialog, notification) e command `list_case_files`. Build funcional, .deb instalado no PC Linux.

**Problema principal nao resolvido:** clicar numa sessao na sidebar nao reconecta -- destroi a sessao atual e tenta criar nova com session_id como case_id, que falha e volta ao CaseSelector. Precisa de mecanismo de reconexao real.

Contexto detalhado: `docs/contexto/03032026-ccui-session-mgmt-tauri-apis.md`

## Arquivos principais

- `legal-workbench/ccui-app/src/components/SessionView.tsx` -- SessionsList, handleSwitchSession
- `legal-workbench/ccui-app/src/hooks/useCcuiApi.ts` -- renameSession, deleteSession, useSessions
- `legal-workbench/ccui-app/src/contexts/WebSocketContext.tsx` -- WS connect/send
- `legal-workbench/ccui-backend/src/routes.rs` -- endpoints REST + WS handler
- `legal-workbench/ccui-backend/src/ws.rs` -- protocolo WS (ClientMessage/ServerMessage)
- `legal-workbench/ccui-backend/src/session.rs` -- SessionManager, SessionInfo

## Proximos passos (por prioridade)

### 1. Implementar reconnect_session no backend
**Onde:** `ccui-backend/src/routes.rs` (WS handler), `ccui-backend/src/ws.rs` (ClientMessage)
**O que:** Novo tipo de mensagem WS `reconnect_session { session_id }` que re-attach ao canal tmux existente sem criar sessao nova. Se a sessao tmux ainda estiver viva, retorna `session_reconnected`. Se nao, retorna erro.
**Por que:** Sem isso, clicar em sessoes da sidebar nao funciona
**Verificar:** Via Tauri MCP -- criar sessao, desconectar WS, reconectar, enviar input

### 2. Limpar sessoes zumbi
**Onde:** `ccui-backend/src/session.rs`
**O que:** Ao listar sessoes, verificar se o processo Claude dentro do tmux esta vivo (`tmux list-panes -t {session} -F "#{pane_pid}"`). Se o processo morreu, marcar como inativa ou remover.
**Verificar:** `curl http://localhost:8005/api/sessions` deve listar apenas sessoes com Claude vivo

### 3. Rebuild e restart do backend
**Onde:** VM Contabo
**O que:** O backend rodando ainda e versao antiga (retorna strings em GET /api/sessions). Recompilar e reiniciar.
**Verificar:** `curl -s http://localhost:8005/api/sessions | python3 -m json.tool` deve retornar objetos com session_id, case_id, name, created_at

### 4. Frontend: usar reconnect em vez de create
**Onde:** `ccui-app/src/components/SessionView.tsx` -- `handleSwitchSession`
**O que:** Se a sessao clicada ja existe, enviar `reconnect_session` em vez de `destroy + create`. So criar nova se for caso diferente.
**Verificar:** Clicar numa sessao na sidebar mostra o chat daquela sessao

### 5. File tree real via Tauri command
**Onde:** `ccui-app/src/components/SessionView.tsx` -- componente `FileTree`
**O que:** Substituir placeholder por chamada a `invoke('list_case_files', { caseId })`. O command ja existe no backend Tauri.
**Verificar:** Sidebar "Arquivos" mostra arquivos reais do caso

### 6. Sidebar busca e configuracoes
**Onde:** `SessionView.tsx` -- tabs "search" e "settings"
**O que:** Busca filtra mensagens do chat por texto. Configuracoes usa `@tauri-apps/plugin-store` para persistir tema, modelo, backend_url.
**Verificar:** Digitar texto filtra mensagens; preferencias persistem entre sessoes

## Como verificar

```bash
cd legal-workbench/ccui-app

# Build frontend
PATH="/home/opc/.bun/bin:/home/opc/.nvm/versions/node/v22.22.0/bin:$PATH" bun run build

# Build Tauri
CC=/usr/bin/gcc PATH="/home/opc/.bun/bin:/home/opc/.cargo/bin:/home/opc/.nvm/versions/node/v22.22.0/bin:/usr/bin:$PATH" NO_STRIP=true APPIMAGE_EXTRACT_AND_RUN=1 cargo tauri build --bundles deb

# Backend tests
cd ../ccui-backend
cargo test --test config_error_unit --test session_integration --test session_persistence -- --test-threads=1
cargo test --test routes_integration -- --test-threads=1 sessions_empty health list_cases channels not_found rename delete list_sessions_includes
cargo clippy -- -W clippy::pedantic

# Transferir e instalar
scp src-tauri/target/release/bundle/deb/ccui-app_0.1.0_amd64.deb cmr-auto@100.102.249.9:/tmp/
ssh cmr-auto@100.102.249.9 "sudo dpkg -i /tmp/ccui-app_0.1.0_amd64.deb"
```
