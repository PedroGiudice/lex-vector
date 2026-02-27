# Contexto: ccui-backend Phase 2 -- Wrapper Web para Advogados

**Data:** 2026-02-27
**Sessao:** branch `wrapper-legal-agents-test` (mergeado em main)
**Duracao:** ~2h

---

## O que foi feito

Implementacao completa do plano Phase 2 do ccui-backend (8 tasks), tornando o backend utilizavel por advogados via wrapper web: selecao de caso, auto-start do Claude, auto-registro de canais, persistencia de sessoes.

### 1. Config cases_dir (Task 1)
Campo `cases_dir: PathBuf` em `AppConfig`, default `/home/opc/casos`, env `CCUI_CASES_DIR`.

### 2. Protocolo WS migrado (Task 2)
`CreateSession.working_dir` substituido por `CreateSession.case_id`. `SessionCreated` agora inclui `case_id: Option<String>` (skip_serializing_if None).

### 3. Endpoint GET /api/cases (Task 3)
Lista subdiretorios de `cases_dir` com metadados:
```json
{
  "cases": [{
    "id": "bianka-sfdc",
    "path": "/home/opc/casos/bianka-sfdc",
    "ready": true,
    "doc_count": 15,
    "active_sessions": [],
    "last_modified": 1709012345
  }]
}
```
`ready` = `knowledge.db` existe. `doc_count` = arquivos em `base/`.

### 4. working_dir + auto-start Claude (Task 4)
- `TmuxDriver::new_session_in_dir()` com parametro `working_dir: Option<&str>` que adiciona `-c dir` ao tmux
- `SessionManager::create_session(case_id)` resolve `case_id` -> path via `cases_dir.join(cid)`, valida existencia
- Handler WS auto-registra canal "main" no `PaneProxy` e envia `claude --dangerously-skip-permissions` via `send_keys`

### 5. Auto-registro de canais de teammates (Task 5)
No broadcast arm do WS handler:
- `AgentJoined` -> `pane_proxy.register_channel(name, tmux_session, pane_id)`
- `AgentLeft` -> `pane_proxy.unregister_channel(name)`
- Novo metodo `PaneProxy::list_channel_details()` retorna `Vec<(String, String)>` (name, pane_id)

### 6. Endpoint GET /api/sessions/{id}/channels (Task 6)
Retorna canais ativos para reconexao:
```json
{ "channels": [{ "name": "main", "pane_id": "%0" }] }
```
404 se sessao nao existe.

### 7. Persistencia de sessoes (Task 7)
- `create_session` grava `{pane_log_dir}/sessions/{id}.json` com `SessionMetadata`
- `destroy_session` remove o JSON
- `recover_sessions_from_disk` restaura sessoes cujo tmux session ainda existe

### 8. Clippy pedantic + limpeza (Task 8)
Zero warnings clippy pedantic, codigo morto removido, doc comments duplicados limpos.

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `ccui-backend/src/config.rs` | Modificado -- campo `cases_dir` |
| `ccui-backend/src/ws.rs` | Modificado -- `case_id` no protocolo |
| `ccui-backend/src/routes.rs` | Modificado -- handlers cases, channels, auto-start |
| `ccui-backend/src/session.rs` | Modificado -- case_id resolution, persistencia |
| `ccui-backend/src/tmux.rs` | Modificado -- `new_session_in_dir` |
| `ccui-backend/src/pane_proxy.rs` | Modificado -- unregister, list_channel_details |
| `ccui-backend/tests/channel_auto_register.rs` | Criado -- 5 testes |
| `ccui-backend/tests/session_persistence.rs` | Criado -- 6 testes |
| `CLAUDE.md` | Modificado -- estrutura com ccui-backend |
| `legal-workbench/CLAUDE.md` | Modificado -- arquitetura, endpoints, servicos |

## Commits desta sessao

```
d56838e feat(ccui-backend): adicionar cases_dir ao config
30d7420 feat(ccui-backend): substituir working_dir por case_id no protocolo WS
695854b feat(ccui-backend): endpoint GET /api/cases com metadados
00f8648 feat(ccui-backend): working_dir via case_id, auto-start Claude, auto-registro canal main
ba27e49 feat(ccui-backend): auto-registro de canais de teammates via broadcast
b09f9c0 feat(ccui-backend): endpoint GET /api/sessions/{id}/channels para reconexao
381daa2 fix(ccui-backend): ajustes em testes de integracao
23c10cc feat(ccui-backend): persistencia de metadados de sessao em disco
5a96023 chore(ccui-backend): clippy pedantic clean + limpeza de codigo morto phase 2
```

## Pendencias identificadas

1. **CLAUDE.md commit pendente** -- as alteracoes nos CLAUDE.md (raiz e LW) foram escritas mas o bash ficou com cwd invalido apos remocao do worktree. Commitar manualmente.
2. **Teste flaky team_watcher** -- `agent_left_emitted_when_member_removed` falha intermitentemente com timeout. Nao e regressao da phase 2, e pre-existente.
3. **Frontend do wrapper** -- nao foi tocado. Precisa de UI para selecao de caso, visualizacao de canais, reconexao.
4. **Integracao Docker** -- `ccui-backend` tem Dockerfile mas nao esta no docker-compose.yml ainda.
5. **Testes E2E** -- fluxo completo create_session -> auto-start -> agent_joined -> channels nao foi testado end-to-end com Claude real.

## Decisoes tomadas

- **case_id em vez de working_dir no protocolo**: o frontend envia apenas o nome do caso, o backend resolve o path. Simplifica a interface e evita expor paths do servidor.
- **Auto-start no handler WS, nao no SessionManager**: manter separacao de responsabilidades. SessionManager gerencia tmux, o handler orquestra o fluxo.
- **Persistencia em JSON no filesystem**: simples, sem deps extras. Suficiente para o cenario single-server atual.
- **Subagent-driven development**: Tasks 4-8 delegadas a subagentes rust-developer. Spec review em Task 4 confirmou conformidade.
