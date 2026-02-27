//! Testes para auto-registro de canais via broadcast (AgentJoined/AgentLeft).
//!
//! Run: `cargo test --test channel_auto_register -- --test-threads=1`

use ccui_backend::config::AppConfig;
use ccui_backend::pane_proxy::PaneProxy;
use ccui_backend::tmux::TmuxDriver;
use ccui_backend::ws::ServerMessage;
use tokio::sync::broadcast;

// ---------------------------------------------------------------------------
// list_channel_details retorna nome + pane_id
// ---------------------------------------------------------------------------

#[tokio::test]
async fn list_channel_details_empty() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let (tx, _rx) = broadcast::channel::<ServerMessage>(16);
    let proxy = PaneProxy::new(config, tmux, tx);

    let details = proxy.list_channel_details().await;
    assert!(details.is_empty());
}

#[tokio::test]
async fn list_channel_details_after_register() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let (tx, _rx) = broadcast::channel::<ServerMessage>(16);
    let proxy = PaneProxy::new(config, tmux.clone(), tx);

    let session = "ccui-test-chan-details";
    let _ = tmux.kill_session(session).await;
    tmux.new_session(session, 80, 24).await.unwrap();
    let pane_id = &tmux.list_panes(session).await.unwrap()[0].id;

    proxy
        .register_channel("agent-a", session, pane_id)
        .await
        .unwrap();

    let details = proxy.list_channel_details().await;
    assert_eq!(details.len(), 1);
    assert_eq!(details[0].0, "agent-a");
    assert_eq!(details[0].1, *pane_id);

    proxy.unregister_channel("agent-a").await.unwrap();
    tmux.kill_session(session).await.unwrap();
}

// ---------------------------------------------------------------------------
// unregister_channel de canal inexistente retorna erro
// ---------------------------------------------------------------------------

#[tokio::test]
async fn unregister_nonexistent_channel_returns_error() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let (tx, _rx) = broadcast::channel::<ServerMessage>(16);
    let proxy = PaneProxy::new(config, tmux, tx);

    let result = proxy.unregister_channel("fantasma").await;
    assert!(result.is_err());
}

// ---------------------------------------------------------------------------
// Simulacao de auto-registro via broadcast (unidade)
// ---------------------------------------------------------------------------

/// Simula o que o WS handler faria: ao receber AgentJoined no broadcast,
/// chama register_channel; ao receber AgentLeft, chama unregister_channel.
#[tokio::test]
async fn auto_register_on_agent_joined_and_unregister_on_left() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let (tx, mut rx) = broadcast::channel::<ServerMessage>(16);
    let proxy = PaneProxy::new(config, tmux.clone(), tx.clone());

    let session = "ccui-test-auto-reg";
    let _ = tmux.kill_session(session).await;
    tmux.new_session(session, 80, 24).await.unwrap();
    let pane_id = tmux.list_panes(session).await.unwrap()[0].id.clone();

    // Simula AgentJoined -> registra canal
    let _ = tx.send(ServerMessage::AgentJoined {
        name: "researcher".to_owned(),
        color: "blue".to_owned(),
        model: "sonnet".to_owned(),
        pane_id: pane_id.clone(),
    });

    // Consome do broadcast e processa
    if let Ok(ServerMessage::AgentJoined { name, pane_id: pid, .. }) = rx.recv().await {
        proxy
            .register_channel(&name, session, &pid)
            .await
            .unwrap();
    }

    // Verifica que canal existe
    let channels = proxy.list_channel_details().await;
    assert_eq!(channels.len(), 1);
    assert_eq!(channels[0].0, "researcher");
    assert_eq!(channels[0].1, pane_id);

    // Simula AgentLeft -> desregistra canal
    let _ = tx.send(ServerMessage::AgentLeft {
        name: "researcher".to_owned(),
    });

    if let Ok(ServerMessage::AgentLeft { name }) = rx.recv().await {
        proxy.unregister_channel(&name).await.unwrap();
    }

    let channels = proxy.list_channel_details().await;
    assert!(channels.is_empty());

    tmux.kill_session(session).await.unwrap();
}

// ---------------------------------------------------------------------------
// WS handler integra auto-registro (teste via broadcast em routes)
// ---------------------------------------------------------------------------

/// Testa que o WS handler no routes.rs faz auto-registro ao receber
/// AgentJoined/AgentLeft via broadcast. Este teste usa o router real.
#[tokio::test]
async fn ws_handler_auto_registers_on_agent_joined() {
    use ccui_backend::routes::{create_router, AppState};
    use futures_util::{SinkExt, StreamExt};
    use tokio_tungstenite::tungstenite;

    let state = AppState::new(AppConfig::default());
    let broadcast_tx = state.broadcast_tx.clone();
    let pane_proxy = state.pane_proxy.clone();
    let session_mgr = state.session_mgr.clone();
    let tmux = state.tmux.clone();

    let app = create_router(state);
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();

    tokio::spawn(async move {
        axum::serve(listener, app).await.unwrap();
    });

    // Conecta WS
    let (mut ws, _) =
        tokio_tungstenite::connect_async(format!("ws://{addr}/ws"))
            .await
            .unwrap();

    // Cria sessao tmux para ter um pane valido
    let test_session = "ccui-test-ws-autoreg";
    let _ = tmux.kill_session(test_session).await;
    tmux.new_session(test_session, 80, 24).await.unwrap();
    let pane_id = tmux.list_panes(test_session).await.unwrap()[0].id.clone();

    // Envia CreateSession via WS para estabelecer sessao no handler
    let create_msg = serde_json::json!({
        "type": "create_session"
    });
    ws.send(tungstenite::Message::Text(create_msg.to_string().into()))
        .await
        .unwrap();

    // Espera SessionCreated
    let mut session_id = String::new();
    let deadline = tokio::time::Instant::now() + std::time::Duration::from_secs(3);
    while tokio::time::Instant::now() < deadline {
        match tokio::time::timeout(std::time::Duration::from_millis(500), ws.next()).await {
            Ok(Some(Ok(tungstenite::Message::Text(text)))) => {
                if let Ok(val) = serde_json::from_str::<serde_json::Value>(&text) {
                    if val.get("type").and_then(|t| t.as_str()) == Some("session_created") {
                        session_id = val["session_id"].as_str().unwrap().to_owned();
                        break;
                    }
                }
            }
            _ => {}
        }
    }
    assert!(!session_id.is_empty(), "sessao deveria ter sido criada");

    // Publica AgentJoined no broadcast
    let _ = broadcast_tx.send(ServerMessage::AgentJoined {
        name: "test-agent".to_owned(),
        color: "green".to_owned(),
        model: "haiku".to_owned(),
        pane_id: pane_id.clone(),
    });

    // Espera que o WS handler processe e registre o canal
    tokio::time::sleep(std::time::Duration::from_millis(300)).await;

    // Verifica que o canal foi registrado no pane_proxy
    let details = pane_proxy.list_channel_details().await;
    let found = details.iter().any(|(name, pid)| name == "test-agent" && pid == &pane_id);
    assert!(found, "canal 'test-agent' deveria ter sido auto-registrado. canais: {:?}", details);

    // Publica AgentLeft
    let _ = broadcast_tx.send(ServerMessage::AgentLeft {
        name: "test-agent".to_owned(),
    });

    tokio::time::sleep(std::time::Duration::from_millis(300)).await;

    let details = pane_proxy.list_channel_details().await;
    let found = details.iter().any(|(name, _)| name == "test-agent");
    assert!(!found, "canal 'test-agent' deveria ter sido removido. canais: {:?}", details);

    // Cleanup
    let _ = session_mgr.destroy_session(&session_id).await;
    let _ = tmux.kill_session(test_session).await;
}
