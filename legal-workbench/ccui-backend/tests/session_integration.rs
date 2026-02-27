//! Integration tests for SessionManager.
//! Run with: `cargo test --test session_integration -- --test-threads=1`

use ccui_backend::config::AppConfig;
use ccui_backend::session::SessionManager;
use ccui_backend::tmux::TmuxDriver;

#[tokio::test]
async fn create_session_starts_tmux() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let mgr = SessionManager::new(config.clone(), tmux.clone());

    let session_id = mgr.create_session(None).await.unwrap();

    // Sessao tmux deve existir com o prefixo
    let session_name = format!("{}-{session_id}", config.tmux_session_prefix);
    assert!(tmux.session_exists(&session_name).await);

    // Cleanup
    mgr.destroy_session(&session_id).await.unwrap();
    assert!(!tmux.session_exists(&session_name).await);
}

#[tokio::test]
async fn list_sessions_returns_active() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let mgr = SessionManager::new(config, tmux);

    let id = mgr.create_session(None).await.unwrap();

    let sessions = mgr.list_sessions().await;
    assert!(sessions.iter().any(|s| s.id == id));

    mgr.destroy_session(&id).await.unwrap();
}

#[tokio::test]
async fn get_session_returns_info() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let mgr = SessionManager::new(config, tmux);

    let id = mgr.create_session(None).await.unwrap();

    let info = mgr.get_session(&id).await;
    assert!(info.is_some());
    assert_eq!(info.unwrap().id, id);

    mgr.destroy_session(&id).await.unwrap();
    assert!(mgr.get_session(&id).await.is_none());
}

#[tokio::test]
async fn destroy_nonexistent_returns_error() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let mgr = SessionManager::new(config, tmux);

    let result = mgr.destroy_session("nonexistent-id").await;
    assert!(result.is_err());
}
