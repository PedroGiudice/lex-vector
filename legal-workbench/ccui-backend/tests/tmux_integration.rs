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
async fn send_keys_to_pane() {
    let tmux = TmuxDriver::new();
    let session = "ccui-test-keys";
    let _ = tmux.kill_session(session).await;

    tmux.new_session(session, 200, 50).await.unwrap();
    let pane_id = &tmux.list_panes(session).await.unwrap()[0].id;

    // Verifica que send_keys nao retorna erro (nao capturamos output -- removido com PaneProxy)
    tmux.send_keys(session, pane_id, "echo HELLO_CCUI")
        .await
        .unwrap();

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
async fn send_text_multiline() {
    let tmux = TmuxDriver::new();
    let session = "ccui-test-multiline";
    let _ = tmux.kill_session(session).await;

    tmux.new_session(session, 200, 50).await.unwrap();
    let pane_id = tmux.list_panes(session).await.unwrap()[0].id.clone();

    // Verifica que send_text_multiline nao retorna erro
    tmux.send_text_multiline(session, &pane_id, "echo MULTI_LINE_TEST\n")
        .await
        .unwrap();

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
async fn new_session_with_working_dir() {
    let tmux = TmuxDriver::new();
    let session = "ccui-test-workdir";
    let _ = tmux.kill_session(session).await;

    tmux.new_session_in_dir(session, 200, 50, Some("/tmp"))
        .await
        .unwrap();
    let pane_id = &tmux.list_panes(session).await.unwrap()[0].id;

    // Verifica que send_keys funciona sem erro (capture_pane removido com PaneProxy)
    tmux.send_keys(session, pane_id, "pwd").await.unwrap();

    tmux.kill_session(session).await.unwrap();
}

#[tokio::test]
async fn new_session_in_dir_none_works_like_new_session() {
    let tmux = TmuxDriver::new();
    let session = "ccui-test-workdir-none";
    let _ = tmux.kill_session(session).await;

    tmux.new_session_in_dir(session, 200, 50, None)
        .await
        .unwrap();
    assert!(tmux.session_exists(session).await);

    tmux.kill_session(session).await.unwrap();
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
async fn send_keys_with_global_pane_id() {
    let tmux = TmuxDriver::new();
    let session = "ccui-test-global-id";
    let _ = tmux.kill_session(session).await;

    tmux.new_session(session, 200, 50).await.unwrap();
    let pane_id = tmux.list_panes(session).await.unwrap()[0].id.clone();

    // pane_id comeca com '%' -- resolve_target usa o ID global diretamente
    assert!(pane_id.starts_with('%'), "pane_id: {pane_id}");

    // Verifica que send_keys aceita pane_id global sem erro
    tmux.send_keys(session, &pane_id, "echo GLOBAL_ID_TEST")
        .await
        .unwrap();

    tmux.kill_session(session).await.unwrap();
}
