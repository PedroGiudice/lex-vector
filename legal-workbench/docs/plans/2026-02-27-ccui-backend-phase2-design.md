# ccui-backend Phase 2 -- Design Doc

**Data:** 2026-02-27
**Status:** Aprovado
**Branch:** wrapper-legal-agents-test
**Prerequisito:** Phase 1 completa (8 modulos, 78 testes, clippy clean)

---

## Contexto

O backend Rust `ccui-backend` faz proxy bidirecional WebSocket <-> panes tmux para sessoes Claude Code. Phase 1 entregou a infraestrutura base. Phase 2 torna o backend utilizavel por um advogado via wrapper web.

O advogado nao tem acesso a VM. Ele abre o wrapper, escolhe um caso, e trabalha. O backend cuida de tudo: tmux, Claude, canais, knowledge base.

## Principios

1. **O frontend e burro** -- nao sabe de tmux, panes, Claude CLI. Envia "caso X" e recebe output.
2. **Isolamento de caso e critico** -- `search_case` resolve pelo working_dir. Diretorio errado = dados errados = fatal.
3. **Sessoes persistem** -- fechar aba nao mata a sessao. O advogado pode voltar horas depois.
4. **Canais sao automaticos** -- o backend registra/desregistra canais sem intervencao do frontend.

## Bases de conhecimento acessiveis por sessao

| Base | Escopo | Interface | Resolvido por |
|------|--------|-----------|---------------|
| case-knowledge | Por caso | MCP tool `search_case` | working_dir da sessao |
| legal-knowledge-base | Global | CLI Rust | Path absoluto |
| stj-vec | Global (STJ) | HTTP API :3100 | Rede local |
| cogmem | Global (memoria) | Unix socket | Path fixo |

Os agentes ja tem skills e prompts para acessar todas. O backend nao intermedia -- o Claude Code dentro do pane tem acesso direto.

## Evolucoes

### 1. Fix working_dir + auto-start Claude

**Onde:** `src/tmux.rs` (new_session) + `src/session.rs` (create_session) + `src/routes.rs` (handler)

**O que muda:**

- `TmuxDriver::new_session` recebe `working_dir: Option<&str>` e passa `-c` ao tmux
- `SessionManager::create_session` apos criar a sessao tmux:
  a. Registra canal "main" no PaneProxy (auto-registro)
  b. Envia `claude --dangerously-skip-permissions` via send_keys no pane principal
- O frontend envia apenas `{"type":"create_session","case_id":"bianka-sfdc"}` -- o backend resolve o path a partir do case_id

**Validacao:**

- O backend verifica que o diretorio do caso existe
- Verifica que `knowledge.db` existe (caso inicializado)
- Retorna erro estruturado se falhar

**Protocolo -- mudanca:**

```json
// Antes
{"type": "create_session", "working_dir": "/path/to/case"}

// Depois
{"type": "create_session", "case_id": "bianka-sfdc"}
```

O frontend nao lida com paths. `case_id` e o nome do subdiretorio dentro de `CCUI_CASES_DIR`.

### 2. Auto-registro de canais

**Onde:** `src/routes.rs` (handler CreateSession) + novo modulo ou extensao de `src/pane_proxy.rs`

**Fluxo:**

```
create_session
  -> tmux new-session -c working_dir
  -> list_panes -> main_pane_id
  -> pane_proxy.register_channel("main", session, main_pane_id)
  -> send_keys("claude --dangerously-skip-permissions")
  -> broadcast SessionCreated

TeamWatcher emite AgentJoined { name, pane_id }
  -> pane_proxy.register_channel(name, session, pane_id)
  -> broadcast AgentJoined

TeamWatcher emite AgentLeft { name }
  -> pane_proxy.unregister_channel(name)
  -> broadcast AgentLeft

destroy_session
  -> pane_proxy desregistra todos os canais da sessao
  -> tmux kill_session
  -> broadcast SessionEnded
```

**Problema de vinculacao TeamWatcher <-> sessao:**

O TeamWatcher observa `~/.claude/teams/` globalmente. Quando um AgentJoined chega, o backend precisa saber a qual sessao vincular. Solucao: manter mapa `tmux_session_name -> session_id` no AppState. O TeamWatcher resolve via tmux_session do pane_id (panes globais pertencem a uma sessao).

### 3. Endpoint de casos

**Onde:** `src/routes.rs` (novo handler) + `src/config.rs` (novo campo)

**Config:**

```rust
// AppConfig
pub cases_dir: PathBuf,  // default: /home/opc/casos
// env: CCUI_CASES_DIR
```

**Endpoint:** `GET /api/cases`

**Response:**

```json
{
  "cases": [
    {
      "id": "bianka-sfdc",
      "path": "/home/opc/casos/bianka-sfdc",
      "ready": true,
      "doc_count": 12,
      "last_modified": "2026-02-25T14:30:00Z",
      "active_sessions": ["a1b2c3d4"]
    },
    {
      "id": "maria-x-joao",
      "path": "/home/opc/casos/maria-x-joao",
      "ready": false,
      "doc_count": 0,
      "last_modified": "2026-02-20T10:00:00Z",
      "active_sessions": []
    }
  ]
}
```

- `ready`: true se `knowledge.db` existe no diretorio
- `doc_count`: quantidade de arquivos em `base/`
- `active_sessions`: sessoes ativas cujo working_dir aponta para este caso

### 4. Endpoint de canais (reconexao)

**Onde:** `src/routes.rs` (novo handler) + `src/pane_proxy.rs` (novo metodo)

**Endpoint:** `GET /api/sessions/{id}/channels`

**Response:**

```json
{
  "session_id": "a1b2c3d4",
  "channels": [
    {"name": "main", "pane_id": "%0"},
    {"name": "legal-researcher", "pane_id": "%34"},
    {"name": "legal-case-analyst", "pane_id": "%37"}
  ]
}
```

Usado pelo frontend na reconexao para saber quais paineis montar antes de receber eventos.

`PaneProxy` precisa de metodo `list_channel_details()` que retorna nome + pane_id.

### 5. Persistencia de sessoes

**O que ja existe:** `recover_orphan_sessions()` no startup.

**O que falta:**

- Persistir `working_dir` e `case_id` no recovery (hoje recupera sessao tmux mas perde metadados)
- Opcao: gravar metadados em arquivo JSON por sessao em `pane_log_dir/sessions/`
- No startup, ler os metadados e reconstruir o estado completo (sessao + canais registrados)

**Formato:** `{pane_log_dir}/sessions/{session_id}.json`

```json
{
  "session_id": "a1b2c3d4",
  "tmux_session": "ccui-a1b2c3d4",
  "case_id": "bianka-sfdc",
  "working_dir": "/home/opc/casos/bianka-sfdc",
  "created_at": "2026-02-27T15:00:00Z"
}
```

## Mudancas no protocolo WS

| Mensagem | Mudanca |
|----------|---------|
| `CreateSession` | `working_dir` substituido por `case_id` |
| `SessionCreated` | Adiciona `case_id` na resposta |
| Demais | Sem mudanca |

## Testes necessarios (TDD)

Cada evolucao segue o ciclo RED-GREEN-REFACTOR:

1. **working_dir + auto-start**: teste de integracao que cria sessao com case_id, verifica pwd no pane, verifica canal "main" registrado
2. **Auto-registro**: teste que simula AgentJoined e verifica canal registrado; AgentLeft e verifica desregistrado
3. **GET /api/cases**: teste HTTP com diretorio temporario contendo casos mock
4. **GET /api/sessions/{id}/channels**: teste HTTP apos criar sessao
5. **Persistencia**: teste que cria sessao, mata o backend (simula restart), verifica recovery com metadados

## Fora de escopo

- Keepalive / AgentCrashed (fase posterior)
- Docker / deploy (decisao: binario direto na VM)
- Frontend (sessao separada)
- Timeout de sessoes (longo prazo, nao urgente)
- Gestao de documentos do caso (automatizado externamente)
