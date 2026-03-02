# Contexto: ccui-app -- Session management + Tauri native APIs

**Data:** 2026-03-03
**Sessao:** ccui-redesign-vibma (continuacao da sessao funcional rodada 2)

---

## O que foi feito

### 1. Testes WS via Tauri MCP (validacao end-to-end)

Testados fluxos WS diretamente no app rodando no PC Linux (cmr-auto) via `mcp__tauri__*`:
- **ping/pong**: OK
- **create_session**: OK (retorna `session_created` com id)
- **Chat input -> output**: OK (Claude respondeu "Oi")
- **destroy_session (botao Encerrar)**: OK (volta ao CaseSelector)
- **invalid message**: OK (retorna erro)
- **input to nonexistent channel**: Gap -- backend ignora silenciosamente (legado)

Conclusao: os 4 testes WS que travam no `cargo test` travam porque spawnam Claude CLI via tmux. Nao e bug do backend -- e limitacao do ambiente de teste (sem Claude CLI disponivel).

### 2. Fix scroll do chat

O container do ChatView (`SessionView.tsx` linha 480) nao tinha `overflow-hidden` + `flex flex-col`, fazendo o chat expandir infinitamente sem scroll. Fix: adicionado `flex flex-col overflow-hidden` ao wrapper.

### 3. Backend: campo `name` + endpoints PATCH/DELETE

**`session.rs`:**
- Campo `name: Option<String>` em `SessionInfo` e `SessionMetadata`
- Metodo `rename_session(&self, session_id, name)` -- atualiza mapa + disco
- `from_info` e `into_info` propagam `name`

**`routes.rs`:**
- `GET /api/sessions` inclui `"name"` no JSON
- `PATCH /api/sessions/{id}` -- aceita `{"name": "..."}` ou `{"name": null}`, retorna 200/404
- `DELETE /api/sessions/{id}` -- mata Claude + tmux, remove mapa + disco, retorna 204/404

**`tests/routes_integration.rs`:** 5 testes novos (rename, rename 404, rename null, delete 404, list includes name).

### 4. Frontend: SessionsList refatorado

**`SessionView.tsx` -- `SessionsList` componente:**
- Click passa `session_id` (nao mais `case_id`) para `onSwitchSession(sessionId, caseId?)`
- Double-click no nome abre input inline para rename (blur/Enter confirma, Escape cancela)
- Botao X (delete) aparece no hover (`opacity-0 group-hover:opacity-100`)
- Deletar sessao ativa chama `handleClose` (volta ao CaseSelector)
- Display name: `name` -> `case_id` -> `session_id.slice(0,8)`

**`useCcuiApi.ts`:**
- `renameSession(id, name)` -- PATCH com refetch automatico
- `deleteSession(id)` -- DELETE com refetch automatico

### 5. Tauri: plugins nativos + command list_case_files

**Cargo.toml:** `tauri-plugin-fs`, `tauri-plugin-dialog`, `tauri-plugin-notification`

**`lib.rs`:**
- Registrados 3 novos plugins no builder
- Struct `FileEntry` (name, path, size, is_dir)
- Command `list_case_files(case_id)` -- lista recursiva ate 2 niveis em `/home/opc/juridico-data/cases/{case_id}/`

**`capabilities/default.json`:** permissoes `fs:default`, `dialog:default`, `notification:default`

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `ccui-app/src/components/SessionView.tsx` | Modificado -- scroll fix, SessionsList refatorado |
| `ccui-app/src/hooks/useCcuiApi.ts` | Modificado -- renameSession, deleteSession |
| `ccui-app/src/types/protocol.ts` | Modificado -- name field |
| `ccui-app/src-tauri/Cargo.toml` | Modificado -- 3 plugins novos |
| `ccui-app/src-tauri/src/lib.rs` | Modificado -- 3 plugins, FileEntry, list_case_files |
| `ccui-app/src-tauri/capabilities/default.json` | Modificado -- permissoes |
| `ccui-backend/src/session.rs` | Modificado -- campo name, rename_session |
| `ccui-backend/src/routes.rs` | Modificado -- PATCH, DELETE, name no GET |
| `ccui-backend/tests/routes_integration.rs` | Modificado -- 5 testes novos |

## Bugs conhecidos (NAO resolvidos)

### BUG 1: Click na sessao volta ao CaseSelector
Ao clicar numa sessao na sidebar, o app volta ao menu de sessoes (CaseSelector) em vez de abrir/reconectar a sessao clicada. O `handleSwitchSession` destroi a sessao atual e chama `createSession(targetCaseId ?? targetSessionId)`. O problema e que sessoes antigas nao tem `case_id` (backend retorna strings), e o `createSession` com um session_id como case_id cria sessao em diretorio inexistente que encerra imediatamente.

**Causa raiz:** Nao existe mecanismo de reconexao a sessao existente. O backend so sabe criar sessoes novas. Reconectar requer: (a) protocolo WS `reconnect_session` no backend, ou (b) frontend re-attach ao canal tmux existente.

### BUG 2: Sessoes zumbi acumulam
17 sessoes listadas pelo backend sao sessoes tmux orfas que nunca foram limpas. O backend reconhece sessoes tmux com prefixo `ccui-` como ativas mas nao sabe que o Claude dentro delas ja encerrou.

### BUG 3: Backend rodando precisa rebuild
O backend em producao (porta 8005) ainda roda versao antiga que retorna strings em vez de objetos no `GET /api/sessions`. Precisa recompilar e reiniciar: `cargo build --release && ./target/release/ccui-backend`.

## Decisoes tomadas

- Testes WS dependentes de Claude CLI validados via Tauri MCP no app real (nao via cargo test)
- Sessoes sem case_id mostram session_id.slice(0,8) como fallback
- Plugins Tauri adicionados preventivamente (fs, dialog, notification) mesmo sem uso imediato pelo frontend
- `list_case_files` usa path convencional hardcoded (`/home/opc/juridico-data/cases/`)
