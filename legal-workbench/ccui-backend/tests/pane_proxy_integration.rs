//! Integration tests for PaneProxy.
//! Run with: `cargo test --test pane_proxy_integration -- --test-threads=1`

use ccui_backend::config::AppConfig;
use ccui_backend::pane_proxy::PaneProxy;
use ccui_backend::tmux::TmuxDriver;
use ccui_backend::ws::ServerMessage;
use tokio::sync::broadcast;

#[tokio::test]
async fn register_channel_and_receive_output() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let (tx, mut rx) = broadcast::channel::<ServerMessage>(256);
    let proxy = PaneProxy::new(config, tmux.clone(), tx);

    let session = "ccui-test-proxy";
    let _ = tmux.kill_session(session).await;
    tmux.new_session(session, 200, 50).await.unwrap();
    let pane_id = &tmux.list_panes(session).await.unwrap()[0].id;

    // Registrar canal
    proxy
        .register_channel("main", session, pane_id)
        .await
        .unwrap();

    // Enviar algo e esperar output no broadcast
    tmux.send_keys(session, pane_id, "echo PROXY_TEST_OUTPUT")
        .await
        .unwrap();

    // Aguardar ate 2s por uma mensagem Output no broadcast
    let deadline = tokio::time::Instant::now() + std::time::Duration::from_secs(2);
    let mut found = false;
    while tokio::time::Instant::now() < deadline {
        match tokio::time::timeout(std::time::Duration::from_millis(200), rx.recv()).await {
            Ok(Ok(ServerMessage::Output { channel, data })) => {
                if channel == "main" && data.contains("PROXY_TEST_OUTPUT") {
                    found = true;
                    break;
                }
            }
            _ => {}
        }
    }
    assert!(found, "expected Output message with PROXY_TEST_OUTPUT");

    proxy.unregister_channel("main").await.unwrap();
    tmux.kill_session(session).await.unwrap();
}

#[tokio::test]
async fn send_input_via_proxy() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let (tx, _rx) = broadcast::channel::<ServerMessage>(256);
    let proxy = PaneProxy::new(config, tmux.clone(), tx);

    let session = "ccui-test-proxy-input";
    let _ = tmux.kill_session(session).await;
    tmux.new_session(session, 200, 50).await.unwrap();
    let pane_id = &tmux.list_panes(session).await.unwrap()[0].id;

    proxy
        .register_channel("main", session, pane_id)
        .await
        .unwrap();

    // Enviar input via proxy
    proxy
        .send_input("main", "echo INPUT_VIA_PROXY")
        .await
        .unwrap();
    tokio::time::sleep(std::time::Duration::from_millis(500)).await;

    // Verificar via capture_pane direto
    let output = tmux.capture_pane(session, pane_id).await.unwrap();
    assert!(
        output.contains("INPUT_VIA_PROXY"),
        "capture output: {output}"
    );

    proxy.unregister_channel("main").await.unwrap();
    tmux.kill_session(session).await.unwrap();
}

#[tokio::test]
async fn list_channels() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let (tx, _rx) = broadcast::channel::<ServerMessage>(256);
    let proxy = PaneProxy::new(config, tmux.clone(), tx);

    let session = "ccui-test-proxy-list";
    let _ = tmux.kill_session(session).await;
    tmux.new_session(session, 200, 50).await.unwrap();
    let pane_id = &tmux.list_panes(session).await.unwrap()[0].id;

    assert!(proxy.list_channels().await.is_empty());

    proxy
        .register_channel("main", session, pane_id)
        .await
        .unwrap();
    let channels = proxy.list_channels().await;
    assert_eq!(channels.len(), 1);
    assert!(channels.contains(&"main".to_string()));

    proxy.unregister_channel("main").await.unwrap();
    assert!(proxy.list_channels().await.is_empty());

    tmux.kill_session(session).await.unwrap();
}

#[tokio::test]
async fn capture_snapshot() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let (tx, _rx) = broadcast::channel::<ServerMessage>(256);
    let proxy = PaneProxy::new(config, tmux.clone(), tx);

    let session = "ccui-test-proxy-snap";
    let _ = tmux.kill_session(session).await;
    tmux.new_session(session, 200, 50).await.unwrap();
    let pane_id = &tmux.list_panes(session).await.unwrap()[0].id;

    proxy
        .register_channel("main", session, pane_id)
        .await
        .unwrap();

    tmux.send_keys(session, pane_id, "echo SNAPSHOT_DATA")
        .await
        .unwrap();
    tokio::time::sleep(std::time::Duration::from_millis(500)).await;

    let snapshot = proxy.capture_snapshot("main").await.unwrap();
    assert!(snapshot.contains("SNAPSHOT_DATA"), "snapshot: {snapshot}");

    proxy.unregister_channel("main").await.unwrap();
    tmux.kill_session(session).await.unwrap();
}

#[tokio::test]
async fn send_input_multiline() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let (tx, _rx) = broadcast::channel::<ServerMessage>(256);
    let proxy = PaneProxy::new(config, tmux.clone(), tx);

    let session = "ccui-test-proxy-multi";
    let _ = tmux.kill_session(session).await;
    tmux.new_session(session, 200, 50).await.unwrap();
    let pane_id = &tmux.list_panes(session).await.unwrap()[0].id;

    proxy
        .register_channel("main", session, pane_id)
        .await
        .unwrap();

    proxy
        .send_input("main", "echo LINE1\necho LINE2")
        .await
        .unwrap();
    tokio::time::sleep(std::time::Duration::from_millis(500)).await;

    let output = tmux.capture_pane(session, pane_id).await.unwrap();
    assert!(
        output.contains("LINE1"),
        "esperado LINE1 no output: {output}"
    );
    assert!(
        output.contains("LINE2"),
        "esperado LINE2 no output: {output}"
    );

    proxy.unregister_channel("main").await.unwrap();
    tmux.kill_session(session).await.unwrap();
}

#[tokio::test]
async fn send_input_nonexistent_channel_returns_error() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let (tx, _rx) = broadcast::channel::<ServerMessage>(256);
    let proxy = PaneProxy::new(config, tmux.clone(), tx);

    let session = "ccui-test-proxy-ghost-input";
    let _ = tmux.kill_session(session).await;
    tmux.new_session(session, 200, 50).await.unwrap();

    let result = proxy.send_input("ghost", "text").await;
    assert!(result.is_err(), "esperado Err para canal inexistente");

    tmux.kill_session(session).await.unwrap();
}

#[tokio::test]
async fn unregister_nonexistent_channel_returns_error() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let (tx, _rx) = broadcast::channel::<ServerMessage>(256);
    let proxy = PaneProxy::new(config, tmux.clone(), tx);

    let result = proxy.unregister_channel("ghost").await;
    assert!(result.is_err(), "esperado Err para canal inexistente");
}

#[tokio::test]
async fn capture_snapshot_nonexistent_channel_returns_error() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let (tx, _rx) = broadcast::channel::<ServerMessage>(256);
    let proxy = PaneProxy::new(config, tmux.clone(), tx);

    let result = proxy.capture_snapshot("ghost").await;
    assert!(result.is_err(), "esperado Err para canal inexistente");
}

#[tokio::test]
async fn resize_channel() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let (tx, _rx) = broadcast::channel::<ServerMessage>(256);
    let proxy = PaneProxy::new(config, tmux.clone(), tx);

    let session = "ccui-test-proxy-resize";
    let _ = tmux.kill_session(session).await;
    tmux.new_session(session, 200, 50).await.unwrap();
    let pane_id = &tmux.list_panes(session).await.unwrap()[0].id;

    proxy
        .register_channel("main", session, pane_id)
        .await
        .unwrap();

    let result = proxy.resize_channel("main", 100, 30).await;
    assert!(
        result.is_ok(),
        "esperado Ok ao redimensionar canal: {result:?}"
    );

    proxy.unregister_channel("main").await.unwrap();
    tmux.kill_session(session).await.unwrap();
}

#[tokio::test]
async fn resize_nonexistent_channel_returns_error() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let (tx, _rx) = broadcast::channel::<ServerMessage>(256);
    let proxy = PaneProxy::new(config, tmux.clone(), tx);

    let result = proxy.resize_channel("ghost", 100, 30).await;
    assert!(result.is_err(), "esperado Err para canal inexistente");
}
