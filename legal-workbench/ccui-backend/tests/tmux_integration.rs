//! Integration tests for TmuxDriver.
//! These create real tmux sessions -- run with: `cargo test --test tmux_integration -- --test-threads=1`

use ccui_backend::tmux::TmuxDriver;

#[tokio::test]
async fn create_and_destroy_session() {
    let tmux = TmuxDriver::new();
    let session = "ccui-test-create";

    // Preventive cleanup
    let _ = tmux.kill_session(session).await;

    tmux.new_session(session, 200, 50).await.unwrap();
    assert!(tmux.session_exists(session).await);

    tmux.kill_session(session).await.unwrap();
    assert!(!tmux.session_exists(session).await);
}

#[tokio::test]
async fn send_keys_and_capture() {
    let tmux = TmuxDriver::new();
    let session = "ccui-test-keys";
    let _ = tmux.kill_session(session).await;

    tmux.new_session(session, 200, 50).await.unwrap();
    let pane_id = &tmux.list_panes(session).await.unwrap()[0].id;

    tmux.send_keys(session, pane_id, "echo HELLO_CCUI")
        .await
        .unwrap();
    tokio::time::sleep(std::time::Duration::from_millis(500)).await;

    let output = tmux.capture_pane(session, pane_id).await.unwrap();
    assert!(output.contains("HELLO_CCUI"), "output was: {output}");

    tmux.kill_session(session).await.unwrap();
}

#[tokio::test]
async fn list_panes() {
    let tmux = TmuxDriver::new();
    let session = "ccui-test-panes";
    let _ = tmux.kill_session(session).await;

    tmux.new_session(session, 200, 50).await.unwrap();
    let panes = tmux.list_panes(session).await.unwrap();
    assert_eq!(panes.len(), 1);
    assert!(!panes[0].dead);

    tmux.kill_session(session).await.unwrap();
}

#[tokio::test]
async fn resize_pane() {
    let tmux = TmuxDriver::new();
    let session = "ccui-test-resize";
    let _ = tmux.kill_session(session).await;

    tmux.new_session(session, 200, 50).await.unwrap();
    let pane_id = &tmux.list_panes(session).await.unwrap()[0].id;

    tmux.resize_pane(pane_id, 120, 40).await.unwrap();

    tmux.kill_session(session).await.unwrap();
}

#[tokio::test]
async fn pipe_pane_to_file() {
    let tmux = TmuxDriver::new();
    let session = "ccui-test-pipe";
    let _ = tmux.kill_session(session).await;

    let log_path = "/tmp/ccui-test-pipe.log";
    let _ = std::fs::remove_file(log_path);

    tmux.new_session(session, 200, 50).await.unwrap();
    let pane_id = &tmux.list_panes(session).await.unwrap()[0].id;

    tmux.pipe_pane(pane_id, log_path).await.unwrap();

    tmux.send_keys(session, pane_id, "echo PIPE_TEST")
        .await
        .unwrap();
    tokio::time::sleep(std::time::Duration::from_millis(500)).await;

    let content = std::fs::read_to_string(log_path).unwrap_or_default();
    assert!(content.contains("PIPE_TEST"), "log content: {content}");

    tmux.kill_session(session).await.unwrap();
    let _ = std::fs::remove_file(log_path);
}

#[tokio::test]
async fn send_text_multiline() {
    let tmux = TmuxDriver::new();
    let session = "ccui-test-multiline";
    let _ = tmux.kill_session(session).await;

    tmux.new_session(session, 200, 50).await.unwrap();
    let pane_id = tmux.list_panes(session).await.unwrap()[0].id.clone();

    tmux.send_text_multiline(session, &pane_id, "echo MULTI_LINE_TEST\n")
        .await
        .unwrap();
    tokio::time::sleep(std::time::Duration::from_millis(500)).await;

    let output = tmux.capture_pane(session, &pane_id).await.unwrap();
    assert!(output.contains("MULTI_LINE_TEST"), "output was: {output}");

    tmux.kill_session(session).await.unwrap();
}

#[tokio::test]
async fn list_sessions_with_prefix() {
    let tmux = TmuxDriver::new();
    let session_a = "ccui-test-prefix-a";
    let session_b = "ccui-test-prefix-b";
    let _ = tmux.kill_session(session_a).await;
    let _ = tmux.kill_session(session_b).await;

    tmux.new_session(session_a, 200, 50).await.unwrap();
    tmux.new_session(session_b, 200, 50).await.unwrap();

    let sessions = tmux
        .list_sessions_with_prefix("ccui-test-prefix")
        .await
        .unwrap();

    assert!(
        sessions.contains(&session_a.to_owned()),
        "sessions: {sessions:?}"
    );
    assert!(
        sessions.contains(&session_b.to_owned()),
        "sessions: {sessions:?}"
    );

    tmux.kill_session(session_a).await.unwrap();
    tmux.kill_session(session_b).await.unwrap();
}

#[tokio::test]
async fn session_exists_false_for_nonexistent() {
    let tmux = TmuxDriver::new();
    assert!(!tmux.session_exists("ccui-nonexistent-session-xyz").await);
}

#[tokio::test]
async fn kill_nonexistent_session_returns_error() {
    let tmux = TmuxDriver::new();
    let result = tmux.kill_session("ccui-nonexistent-xyz").await;
    assert!(result.is_err(), "expected Err, got Ok");
}

#[tokio::test]
async fn list_panes_nonexistent_session_returns_error() {
    let tmux = TmuxDriver::new();
    let result = tmux.list_panes("ccui-nonexistent-xyz").await;
    assert!(result.is_err(), "expected Err, got Ok");
}

#[tokio::test]
async fn capture_pane_with_global_id() {
    let tmux = TmuxDriver::new();
    let session = "ccui-test-global-id";
    let _ = tmux.kill_session(session).await;

    tmux.new_session(session, 200, 50).await.unwrap();
    let pane_id = tmux.list_panes(session).await.unwrap()[0].id.clone();

    // pane_id comeca com '%' -- resolve_target usa o ID global diretamente
    assert!(pane_id.starts_with('%'), "pane_id: {pane_id}");

    tmux.send_keys(session, &pane_id, "echo GLOBAL_ID_TEST")
        .await
        .unwrap();
    tokio::time::sleep(std::time::Duration::from_millis(500)).await;

    let output = tmux.capture_pane(session, &pane_id).await.unwrap();
    assert!(output.contains("GLOBAL_ID_TEST"), "output was: {output}");

    tmux.kill_session(session).await.unwrap();
}
