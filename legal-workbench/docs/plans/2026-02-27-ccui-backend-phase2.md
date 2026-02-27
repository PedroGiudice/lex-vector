# ccui-backend Phase 2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Tornar o backend ccui-backend utilizavel por um advogado via wrapper web -- selecao de caso, auto-start do Claude, auto-registro de canais, reconexao.

**Architecture:** 5 evolucoes incrementais sobre o backend Rust existente (axum + tokio + tmux). Cada task adiciona funcionalidade testada sem quebrar o que existe. O frontend nao e tocado.

**Tech Stack:** Rust, axum 0.8, tokio 1.x, serde, tmux, sqlite3 (para verificar knowledge.db)

**Design doc:** `docs/plans/2026-02-27-ccui-backend-phase2-design.md`

**Pre-requisitos:**
- 78 testes passando (Phase 1)
- `cargo clippy -- -W clippy::pedantic` limpo
- Branch: `wrapper-legal-agents-test`

**Regra absoluta:** Nenhum teste existente pode quebrar. Nenhuma funcionalidade existente pode ser removida ou alterada em comportamento.

---

## Task 1: Config -- adicionar `cases_dir`

**Files:**
- Modify: `ccui-backend/src/config.rs`
- Modify: `ccui-backend/tests/config_error_unit.rs`

**Step 1: Write failing tests**

```rust
// tests/config_error_unit.rs -- adicionar

#[test]
fn default_cases_dir() {
    let config = AppConfig::default();
    assert_eq!(config.cases_dir, PathBuf::from("/home/opc/casos"));
}

#[test]
fn from_env_reads_cases_dir() {
    unsafe { std::env::set_var("CCUI_CASES_DIR", "/tmp/test-cases") };
    let config = AppConfig::from_env();
    assert_eq!(config.cases_dir, PathBuf::from("/tmp/test-cases"));
    unsafe { std::env::remove_var("CCUI_CASES_DIR") };
}
```

**Step 2: Run tests to verify they fail**

Run: `cargo test --test config_error_unit -- --test-threads=1`
Expected: FAIL -- campo `cases_dir` nao existe em AppConfig

**Step 3: Write minimal implementation**

```rust
// config.rs -- adicionar campo
pub cases_dir: PathBuf,

// Default
cases_dir: PathBuf::from("/home/opc/casos"),

// from_env
if let Ok(d) = std::env::var("CCUI_CASES_DIR") {
    cfg.cases_dir = PathBuf::from(d);
}
```

**Step 4: Run tests to verify they pass**

Run: `cargo test --test config_error_unit -- --test-threads=1`
Expected: PASS (todos, incluindo existentes)

**Step 5: Commit**

```bash
git add ccui-backend/src/config.rs ccui-backend/tests/config_error_unit.rs
git commit -m "feat(ccui-backend): adicionar cases_dir ao config"
```

---

## Task 2: Protocolo -- substituir `working_dir` por `case_id`

**Files:**
- Modify: `ccui-backend/src/ws.rs`
- Modify: `ccui-backend/tests/ws_protocol.rs`

**Step 1: Write failing tests**

```rust
// tests/ws_protocol.rs -- adicionar

#[test]
fn deserialize_create_session_with_case_id() {
    let json = r#"{"type": "create_session", "case_id": "bianka-sfdc"}"#;
    let msg: ClientMessage = serde_json::from_str(json).unwrap();
    match msg {
        ClientMessage::CreateSession { case_id } => {
            assert_eq!(case_id.as_deref(), Some("bianka-sfdc"));
        }
        _ => panic!("expected CreateSession"),
    }
}

#[test]
fn deserialize_create_session_without_case_id() {
    let json = r#"{"type": "create_session"}"#;
    let msg: ClientMessage = serde_json::from_str(json).unwrap();
    assert!(matches!(msg, ClientMessage::CreateSession { case_id: None }));
}

#[test]
fn serialize_session_created_with_case_id() {
    let msg = ServerMessage::SessionCreated {
        session_id: "abc".into(),
        case_id: Some("bianka-sfdc".into()),
    };
    let json = serde_json::to_string(&msg).unwrap();
    assert!(json.contains("bianka-sfdc"));
}
```

**Step 2: Run tests to verify they fail**

Run: `cargo test --test ws_protocol -- --test-threads=1`
Expected: FAIL -- CreateSession ainda tem `working_dir`, nao `case_id`

**Step 3: Write minimal implementation**

Alterar `ws.rs`:
- `CreateSession { working_dir: Option<String> }` -> `CreateSession { case_id: Option<String> }`
- `SessionCreated { session_id }` -> `SessionCreated { session_id, case_id: Option<String> }`

**ATENCAO:** Isso quebra o teste existente `deserialize_create_session` e o `serialize_session_created`. Atualizar esses testes para o novo formato. Tambem quebra `routes.rs` handler -- atualizar para compilar (pode passar `None` como case_id por enquanto).

**Step 4: Run ALL tests**

Run: `cargo test -- --test-threads=1`
Expected: PASS (todos)

**Step 5: Commit**

```bash
git add ccui-backend/src/ws.rs ccui-backend/tests/ws_protocol.rs ccui-backend/src/routes.rs
git commit -m "feat(ccui-backend): substituir working_dir por case_id no protocolo"
```

---

## Task 3: Endpoint `GET /api/cases`

**Files:**
- Modify: `ccui-backend/src/routes.rs`
- Modify: `ccui-backend/tests/routes_integration.rs`

**Step 1: Write failing tests**

```rust
// tests/routes_integration.rs -- adicionar

#[tokio::test]
async fn list_cases_returns_array() {
    use tower::ServiceExt;
    use axum::body::Body;
    use hyper::Request;

    // Criar diretorio temporario com um caso mock
    let tmp = tempfile::tempdir().unwrap();
    let case_dir = tmp.path().join("caso-teste");
    std::fs::create_dir_all(case_dir.join("base")).unwrap();
    // Criar knowledge.db vazio para marcar como ready
    std::fs::File::create(case_dir.join("knowledge.db")).unwrap();
    // Criar 2 arquivos em base/
    std::fs::write(case_dir.join("base/doc1.md"), "conteudo").unwrap();
    std::fs::write(case_dir.join("base/doc2.md"), "conteudo").unwrap();

    let mut config = AppConfig::default();
    config.cases_dir = tmp.path().to_path_buf();
    let state = AppState::new(config);
    let app = create_router(state);

    let request = Request::builder()
        .uri("/api/cases")
        .body(Body::empty())
        .unwrap();

    let response = app.oneshot(request).await.unwrap();
    assert_eq!(response.status(), StatusCode::OK);

    let body_bytes = response.into_body().collect().await.unwrap().to_bytes();
    let parsed: serde_json::Value = serde_json::from_slice(&body_bytes).unwrap();

    let cases = parsed["cases"].as_array().expect("cases deve ser array");
    assert_eq!(cases.len(), 1);
    assert_eq!(cases[0]["id"].as_str(), Some("caso-teste"));
    assert_eq!(cases[0]["ready"].as_bool(), Some(true));
    assert_eq!(cases[0]["doc_count"].as_u64(), Some(2));
}

#[tokio::test]
async fn list_cases_not_ready_without_knowledge_db() {
    use tower::ServiceExt;
    use axum::body::Body;
    use hyper::Request;

    let tmp = tempfile::tempdir().unwrap();
    let case_dir = tmp.path().join("caso-incompleto");
    std::fs::create_dir_all(case_dir.join("base")).unwrap();
    // SEM knowledge.db

    let mut config = AppConfig::default();
    config.cases_dir = tmp.path().to_path_buf();
    let state = AppState::new(config);
    let app = create_router(state);

    let request = Request::builder()
        .uri("/api/cases")
        .body(Body::empty())
        .unwrap();

    let response = app.oneshot(request).await.unwrap();
    let body_bytes = response.into_body().collect().await.unwrap().to_bytes();
    let parsed: serde_json::Value = serde_json::from_slice(&body_bytes).unwrap();

    let cases = parsed["cases"].as_array().unwrap();
    assert_eq!(cases[0]["ready"].as_bool(), Some(false));
}
```

**Step 2: Run tests to verify they fail**

Run: `cargo test --test routes_integration -- --test-threads=1`
Expected: FAIL -- rota `/api/cases` nao existe (404)

**Step 3: Implement handler**

Em `routes.rs`:
- Adicionar `use std::path::PathBuf;`
- Novo handler `list_cases` que le `config.cases_dir`, itera subdiretorios, verifica `knowledge.db` e `base/`, conta arquivos, cruza com sessoes ativas
- Registrar rota `.route("/api/cases", get(list_cases))`

**Step 4: Run ALL tests**

Run: `cargo test -- --test-threads=1`
Expected: PASS

**Step 5: Commit**

```bash
git add ccui-backend/src/routes.rs ccui-backend/tests/routes_integration.rs
git commit -m "feat(ccui-backend): endpoint GET /api/cases com metadados"
```

---

## Task 4: Fix working_dir + auto-start Claude

**Files:**
- Modify: `ccui-backend/src/tmux.rs`
- Modify: `ccui-backend/src/session.rs`
- Modify: `ccui-backend/src/routes.rs`
- Modify: `ccui-backend/tests/tmux_integration.rs`
- Modify: `ccui-backend/tests/session_integration.rs`

**Step 1: Write failing test para tmux working_dir**

```rust
// tests/tmux_integration.rs -- adicionar

#[tokio::test]
async fn new_session_with_working_dir() {
    let tmux = TmuxDriver::new();
    let session = "ccui-test-workdir";
    let _ = tmux.kill_session(session).await;

    tmux.new_session_in_dir(session, 200, 50, Some("/tmp"))
        .await
        .unwrap();
    let pane_id = &tmux.list_panes(session).await.unwrap()[0].id;

    tmux.send_keys(session, pane_id, "pwd").await.unwrap();
    tokio::time::sleep(std::time::Duration::from_millis(500)).await;

    let output = tmux.capture_pane(session, pane_id).await.unwrap();
    assert!(output.contains("/tmp"), "pwd deveria ser /tmp, output: {output}");

    tmux.kill_session(session).await.unwrap();
}
```

**Step 2: Run test to verify it fails**

Expected: FAIL -- metodo `new_session_in_dir` nao existe

**Step 3: Implement**

Em `tmux.rs`:
- Renomear `new_session` para `new_session_in_dir` com parametro `working_dir: Option<&str>`
- Se `working_dir` e Some, adicionar `-c working_dir` aos args do tmux
- Manter `new_session` como wrapper que chama `new_session_in_dir(name, w, h, None)` para nao quebrar callers existentes

Em `session.rs`:
- `create_session` resolve `case_id` -> path via `config.cases_dir`
- Valida que o diretorio existe e tem `knowledge.db`
- Passa path como working_dir ao tmux

Em `routes.rs`:
- Handler CreateSession recebe `case_id`, chama session_mgr com ele
- Apos criar sessao: registra canal "main" no pane_proxy
- Envia `claude --dangerously-skip-permissions` via send_keys

**Step 4: Run ALL tests**

Run: `cargo test -- --test-threads=1`
Expected: PASS

**Step 5: Commit**

```bash
git add ccui-backend/src/tmux.rs ccui-backend/src/session.rs ccui-backend/src/routes.rs \
       ccui-backend/tests/tmux_integration.rs ccui-backend/tests/session_integration.rs
git commit -m "feat(ccui-backend): working_dir via case_id, auto-start Claude, auto-registro canal main"
```

---

## Task 5: Auto-registro de canais de teammates

**Files:**
- Modify: `ccui-backend/src/routes.rs` (ou novo modulo `src/channel_manager.rs`)
- Modify: `ccui-backend/src/pane_proxy.rs` (metodo `list_channel_details`)
- Create: `ccui-backend/tests/channel_auto_register.rs`

**Step 1: Write failing tests**

```rust
// tests/channel_auto_register.rs

// Teste 1: Quando AgentJoined chega via broadcast, canal e registrado automaticamente
// Teste 2: Quando AgentLeft chega, canal e desregistrado
// Teste 3: list_channel_details retorna nome + pane_id dos canais ativos
```

O mecanismo: o handler WS (ou uma task dedicada) escuta o broadcast. Quando recebe AgentJoined, chama `pane_proxy.register_channel(name, session, pane_id)`. Quando recebe AgentLeft, chama `pane_proxy.unregister_channel(name)`.

**Problema de vinculacao:** Manter mapa `pane_id -> session_id` no AppState para resolver a qual sessao pertence o teammate.

**Step 2-4:** Ciclo RED-GREEN-REFACTOR standard.

**Step 5: Commit**

```bash
git commit -m "feat(ccui-backend): auto-registro de canais de teammates via TeamWatcher"
```

---

## Task 6: Endpoint `GET /api/sessions/{id}/channels`

**Files:**
- Modify: `ccui-backend/src/routes.rs`
- Modify: `ccui-backend/src/pane_proxy.rs`
- Modify: `ccui-backend/tests/routes_integration.rs`

**Step 1: Write failing test**

```rust
#[tokio::test]
async fn get_session_channels() {
    // Criar sessao via WS, verificar que GET /api/sessions/{id}/channels
    // retorna ao menos canal "main"
}
```

**Step 2-4:** Ciclo standard.

**Step 5: Commit**

```bash
git commit -m "feat(ccui-backend): endpoint GET /api/sessions/{id}/channels para reconexao"
```

---

## Task 7: Persistencia de sessoes (metadados em disco)

**Files:**
- Modify: `ccui-backend/src/session.rs`
- Create: `ccui-backend/tests/session_persistence.rs`

**Step 1: Write failing tests**

```rust
// Teste 1: create_session grava JSON em {pane_log_dir}/sessions/{id}.json
// Teste 2: destroy_session remove o JSON
// Teste 3: recover_orphan_sessions le os JSONs e restaura case_id + working_dir
```

**Step 2-4:** Ciclo standard.

**Step 5: Commit**

```bash
git commit -m "feat(ccui-backend): persistencia de metadados de sessao em disco"
```

---

## Task 8: Clippy pedantic + cargo fmt + teste completo

**Files:** Todos

**Step 1:** `cargo clippy -- -W clippy::pedantic` -- corrigir warnings
**Step 2:** `cargo fmt`
**Step 3:** `cargo test -- --test-threads=1` -- todos passando
**Step 4:** Commit final

```bash
git commit -m "chore(ccui-backend): clippy pedantic clean phase 2"
```

---

## Ordem de execucao

```
Task 1 (config)
  |
Task 2 (protocolo)
  |
Task 3 (GET /api/cases)
  |
Task 4 (working_dir + auto-start + auto-registro main)
  |
Task 5 (auto-registro teammates)
  |
Task 6 (GET /api/sessions/{id}/channels)
  |
Task 7 (persistencia)
  |
Task 8 (cleanup)
```

Tasks 1-2 sao preparatorias. Tasks 3-6 sao o core. Task 7 e robustez. Task 8 e higiene.

## Verificacao final

Apos task 8, o backend deve:
- [ ] Listar casos disponiveis com metadados
- [ ] Criar sessao num caso especifico com Claude auto-iniciado
- [ ] Registrar canal "main" automaticamente
- [ ] Registrar canais de teammates automaticamente quando AgentJoined
- [ ] Desregistrar canais quando AgentLeft
- [ ] Expor canais ativos para reconexao
- [ ] Persistir metadados de sessao em disco
- [ ] Recuperar sessoes orfas com metadados no startup
- [ ] 78+ testes existentes continuam passando
- [ ] Clippy pedantic limpo
