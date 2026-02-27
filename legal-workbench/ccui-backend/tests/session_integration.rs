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

#[tokio::test]
async fn recover_orphan_sessions() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();

    // Criar sessao tmux diretamente, fora do SessionManager.
    let orphan_session = format!("{}-orphan-test", config.tmux_session_prefix);
    tmux.new_session(&orphan_session, 200, 50).await.unwrap();

    // Novo SessionManager que nao conhece a sessao criada acima.
    let mgr = SessionManager::new(config.clone(), tmux.clone());

    // Antes de recover, get_session nao retorna nada.
    assert!(mgr.get_session("orphan-test").await.is_none());

    let recovered = mgr.recover_orphan_sessions().await.unwrap();

    // Deve conter o sufixo "orphan-test".
    assert!(
        recovered.iter().any(|id| id == "orphan-test"),
        "esperado 'orphan-test' em recovered, obtido: {recovered:?}"
    );

    // Agora get_session deve retornar Some.
    assert!(mgr.get_session("orphan-test").await.is_some());

    // Cleanup.
    tmux.kill_session(&orphan_session).await.unwrap();
}

#[tokio::test]
async fn create_session_stores_working_dir() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let mgr = SessionManager::new(config, tmux);

    let id = mgr.create_session(Some("/tmp")).await.unwrap();

    let info = mgr.get_session(&id).await.expect("sessao deve existir");
    assert_eq!(
        info.working_dir,
        Some("/tmp".to_string()),
        "working_dir deve ser /tmp"
    );

    // Cleanup.
    mgr.destroy_session(&id).await.unwrap();
}

#[tokio::test]
async fn session_id_is_8_chars() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let mgr = SessionManager::new(config, tmux);

    let id1 = mgr.create_session(None).await.unwrap();
    let id2 = mgr.create_session(None).await.unwrap();
    let id3 = mgr.create_session(None).await.unwrap();

    assert_eq!(id1.len(), 8, "id1 deve ter 8 chars, obtido: {id1}");
    assert_eq!(id2.len(), 8, "id2 deve ter 8 chars, obtido: {id2}");
    assert_eq!(id3.len(), 8, "id3 deve ter 8 chars, obtido: {id3}");

    // Os tres ids devem ser diferentes.
    assert_ne!(id1, id2, "id1 e id2 nao devem ser iguais");
    assert_ne!(id1, id3, "id1 e id3 nao devem ser iguais");
    assert_ne!(id2, id3, "id2 e id3 nao devem ser iguais");

    // Cleanup.
    mgr.destroy_session(&id1).await.unwrap();
    mgr.destroy_session(&id2).await.unwrap();
    mgr.destroy_session(&id3).await.unwrap();
}

#[tokio::test]
async fn create_session_has_valid_main_pane() {
    let config = AppConfig::default();
    let tmux = TmuxDriver::new();
    let mgr = SessionManager::new(config, tmux);

    let id = mgr.create_session(None).await.unwrap();

    let info = mgr.get_session(&id).await.expect("sessao deve existir");
    assert!(
        info.main_pane_id.starts_with('%'),
        "main_pane_id deve comecar com '%', obtido: '{}'",
        info.main_pane_id
    );

    // Cleanup.
    mgr.destroy_session(&id).await.unwrap();
}
