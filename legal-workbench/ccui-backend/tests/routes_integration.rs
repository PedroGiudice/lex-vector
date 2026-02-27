//! Testes de integracao HTTP e WebSocket para o modulo routes.rs.

use ccui_backend::{
    config::AppConfig,
    routes::{create_router, AppState},
};
use futures_util::{SinkExt, StreamExt};
use http_body_util::BodyExt;
use hyper::StatusCode;
use tokio_tungstenite::{connect_async, tungstenite::Message as WsMessage};

// ---------------------------------------------------------------------------
// Helper: servidor em porta efemera
// ---------------------------------------------------------------------------

async fn spawn_test_server() -> (String, tokio::task::JoinHandle<()>) {
    let config = AppConfig::default();
    let state = AppState::new(config);
    let app = create_router(state);
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();
    let handle = tokio::spawn(async move {
        axum::serve(listener, app).await.unwrap();
    });
    (format!("127.0.0.1:{}", addr.port()), handle)
}

// ---------------------------------------------------------------------------
// Testes HTTP simples via tower::ServiceExt::oneshot
// ---------------------------------------------------------------------------

#[tokio::test]
async fn health_returns_ok() {
    use axum::body::Body;
    use hyper::Request;
    use tower::ServiceExt;

    let config = AppConfig::default();
    let state = AppState::new(config);
    let app = create_router(state);

    let request = Request::builder()
        .uri("/health")
        .body(Body::empty())
        .unwrap();

    let response = app.oneshot(request).await.unwrap();

    assert_eq!(response.status(), StatusCode::OK);

    let body_bytes = response.into_body().collect().await.unwrap().to_bytes();
    let body_str = std::str::from_utf8(&body_bytes).unwrap();
    assert!(
        body_str.contains("ok"),
        "body deve conter 'ok', recebeu: {body_str}"
    );
}

#[tokio::test]
async fn sessions_empty_initially() {
    use axum::body::Body;
    use hyper::Request;
    use tower::ServiceExt;

    let config = AppConfig::default();
    let state = AppState::new(config);
    let app = create_router(state);

    let request = Request::builder()
        .uri("/api/sessions")
        .body(Body::empty())
        .unwrap();

    let response = app.oneshot(request).await.unwrap();

    assert_eq!(response.status(), StatusCode::OK);

    let body_bytes = response.into_body().collect().await.unwrap().to_bytes();
    let body_str = std::str::from_utf8(&body_bytes).unwrap();
    let parsed: serde_json::Value = serde_json::from_str(body_str)
        .unwrap_or_else(|e| panic!("body nao e JSON valido: {e}\nbody: {body_str}"));

    let sessions = parsed.get("sessions").expect("campo 'sessions' ausente");
    assert!(
        sessions.is_array(),
        "'sessions' deve ser array, recebeu: {sessions}"
    );
    assert_eq!(
        sessions.as_array().unwrap().len(),
        0,
        "sessoes devem estar vazias inicialmente"
    );
}

#[tokio::test]
async fn not_found_for_unknown_route() {
    use axum::body::Body;
    use hyper::Request;
    use tower::ServiceExt;

    let config = AppConfig::default();
    let state = AppState::new(config);
    let app = create_router(state);

    let request = Request::builder()
        .uri("/unknown")
        .body(Body::empty())
        .unwrap();

    let response = app.oneshot(request).await.unwrap();

    assert_eq!(response.status(), StatusCode::NOT_FOUND);
}

// ---------------------------------------------------------------------------
// GET /api/cases
// ---------------------------------------------------------------------------

#[tokio::test]
async fn list_cases_returns_array() {
    use axum::body::Body;
    use hyper::Request;
    use tower::ServiceExt;

    let tmp = tempfile::tempdir().unwrap();
    let case_dir = tmp.path().join("caso-teste");
    std::fs::create_dir_all(case_dir.join("base")).unwrap();
    std::fs::File::create(case_dir.join("knowledge.db")).unwrap();
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
    use axum::body::Body;
    use hyper::Request;
    use tower::ServiceExt;

    let tmp = tempfile::tempdir().unwrap();
    let case_dir = tmp.path().join("caso-incompleto");
    std::fs::create_dir_all(case_dir.join("base")).unwrap();

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

#[tokio::test]
async fn list_cases_empty_dir() {
    use axum::body::Body;
    use hyper::Request;
    use tower::ServiceExt;

    let tmp = tempfile::tempdir().unwrap();
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
    assert!(cases.is_empty());
}

// ---------------------------------------------------------------------------
// GET /api/sessions/{id}/channels
// ---------------------------------------------------------------------------

#[tokio::test]
async fn channels_returns_404_for_nonexistent_session() {
    use axum::body::Body;
    use hyper::Request;
    use tower::ServiceExt;

    let config = AppConfig::default();
    let state = AppState::new(config);
    let app = create_router(state);

    let request = Request::builder()
        .uri("/api/sessions/inexistente/channels")
        .body(Body::empty())
        .unwrap();

    let response = app.oneshot(request).await.unwrap();
    assert_eq!(response.status(), StatusCode::NOT_FOUND);
}

#[tokio::test]
async fn channels_returns_ok_for_valid_session() {
    use axum::body::Body;
    use hyper::Request;
    use tower::ServiceExt;

    let config = AppConfig::default();
    let state = AppState::new(config);

    // Inserir sessao fake no session_mgr (sem tmux real)
    state.session_mgr.insert_fake_session("test-id").await;

    let app = create_router(state);

    let request = Request::builder()
        .uri("/api/sessions/test-id/channels")
        .body(Body::empty())
        .unwrap();

    let response = app.oneshot(request).await.unwrap();
    assert_eq!(response.status(), StatusCode::OK);

    let body_bytes = response.into_body().collect().await.unwrap().to_bytes();
    let parsed: serde_json::Value = serde_json::from_slice(&body_bytes).unwrap();

    let channels = parsed["channels"]
        .as_array()
        .expect("channels deve ser array");
    // Sem canais registrados (nao ha tmux real), mas o formato esta correto
    assert!(
        channels.is_empty(),
        "sem canais registrados, lista deve estar vazia"
    );
}

// ---------------------------------------------------------------------------
// Testes WebSocket via tokio-tungstenite
// ---------------------------------------------------------------------------

#[tokio::test]
async fn ws_ping_pong() {
    let (addr, _handle) = spawn_test_server().await;
    let url = format!("ws://{addr}/ws");

    let (mut ws, _) = connect_async(&url)
        .await
        .expect("falha ao conectar WebSocket");

    ws.send(WsMessage::Text(r#"{"type":"ping"}"#.into()))
        .await
        .unwrap();

    let msg = ws.next().await.expect("sem resposta").unwrap();
    let text = match msg {
        WsMessage::Text(t) => t.to_string(),
        other => panic!("esperava Text, recebeu: {other:?}"),
    };

    let parsed: serde_json::Value = serde_json::from_str(&text).unwrap();
    assert_eq!(
        parsed.get("type").and_then(|v| v.as_str()),
        Some("pong"),
        "esperava type=pong, recebeu: {text}"
    );

    ws.close(None).await.ok();
}

#[tokio::test]
async fn ws_create_and_destroy_session() {
    let (addr, _handle) = spawn_test_server().await;
    let url = format!("ws://{addr}/ws");

    let (mut ws, _) = connect_async(&url)
        .await
        .expect("falha ao conectar WebSocket");

    // Criar sessao
    ws.send(WsMessage::Text(r#"{"type":"create_session"}"#.into()))
        .await
        .unwrap();

    let msg = ws
        .next()
        .await
        .expect("sem resposta a create_session")
        .unwrap();
    let text = match msg {
        WsMessage::Text(t) => t.to_string(),
        other => panic!("esperava Text, recebeu: {other:?}"),
    };

    let parsed: serde_json::Value = serde_json::from_str(&text).unwrap();

    // tmux DEVE estar disponivel -- este backend roda na VM onde tmux esta instalado.
    // Nenhum fallback para "error" e aceito aqui.
    assert_eq!(
        parsed.get("type").and_then(|v| v.as_str()),
        Some("session_created"),
        "esperava session_created, recebeu: {text}"
    );

    let session_id = parsed
        .get("session_id")
        .and_then(|v| v.as_str())
        .expect("session_id ausente em session_created")
        .to_string();

    assert_eq!(session_id.len(), 8, "session_id deve ter 8 chars");

    // Destruir sessao
    let destroy_msg = serde_json::json!({
        "type": "destroy_session",
        "session_id": session_id
    })
    .to_string();
    ws.send(WsMessage::Text(destroy_msg.into())).await.unwrap();

    let destroy_resp = ws
        .next()
        .await
        .expect("sem resposta a destroy_session")
        .unwrap();
    let destroy_text = match destroy_resp {
        WsMessage::Text(t) => t.to_string(),
        other => panic!("esperava Text, recebeu: {other:?}"),
    };

    let destroy_parsed: serde_json::Value = serde_json::from_str(&destroy_text).unwrap();
    assert_eq!(
        destroy_parsed.get("type").and_then(|v| v.as_str()),
        Some("session_ended"),
        "esperava session_ended, recebeu: {destroy_text}"
    );

    ws.close(None).await.ok();
}

#[tokio::test]
async fn ws_invalid_message_returns_error() {
    let (addr, _handle) = spawn_test_server().await;
    let url = format!("ws://{addr}/ws");

    let (mut ws, _) = connect_async(&url)
        .await
        .expect("falha ao conectar WebSocket");

    ws.send(WsMessage::Text(r#"{"type":"garbage"}"#.into()))
        .await
        .unwrap();

    let msg = ws.next().await.expect("sem resposta").unwrap();
    let text = match msg {
        WsMessage::Text(t) => t.to_string(),
        other => panic!("esperava Text, recebeu: {other:?}"),
    };

    let parsed: serde_json::Value = serde_json::from_str(&text).unwrap();
    assert_eq!(
        parsed.get("type").and_then(|v| v.as_str()),
        Some("error"),
        "esperava type=error para mensagem invalida, recebeu: {text}"
    );

    ws.close(None).await.ok();
}

#[tokio::test]
async fn ws_input_to_nonexistent_channel_returns_error() {
    let (addr, _handle) = spawn_test_server().await;
    let url = format!("ws://{addr}/ws");

    let (mut ws, _) = connect_async(&url)
        .await
        .expect("falha ao conectar WebSocket");

    ws.send(WsMessage::Text(
        r#"{"type":"input","channel":"ghost","text":"hello"}"#.into(),
    ))
    .await
    .unwrap();

    let msg = ws.next().await.expect("sem resposta").unwrap();
    let text = match msg {
        WsMessage::Text(t) => t.to_string(),
        other => panic!("esperava Text, recebeu: {other:?}"),
    };

    let parsed: serde_json::Value = serde_json::from_str(&text).unwrap();
    assert_eq!(
        parsed.get("type").and_then(|v| v.as_str()),
        Some("error"),
        "esperava type=error para canal inexistente, recebeu: {text}"
    );

    ws.close(None).await.ok();
}
