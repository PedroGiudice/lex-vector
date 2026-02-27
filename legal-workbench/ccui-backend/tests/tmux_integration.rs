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
