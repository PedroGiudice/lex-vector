//! Testes de persistencia de metadados de sessao em disco.
//! Run with: `cargo test --test session_persistence -- --test-threads=1`

use ccui_backend::config::AppConfig;
use ccui_backend::session::{SessionManager, SessionMetadata};
use ccui_backend::tmux::TmuxDriver;

fn test_config(_tmp: &tempfile::TempDir) -> AppConfig {
    AppConfig::default()
}

#[tokio::test]
async fn create_session_writes_metadata_file() {
    let tmp = tempfile::tempdir().unwrap();
    let config = test_config(&tmp);
    let tmux = TmuxDriver::new();
    let mgr = SessionManager::new(config, tmux);

    let session_id = mgr.create_session(None).await.unwrap();

    // Arquivo JSON deve existir
    let meta_path = std::path::PathBuf::from("/tmp/ccui-sessions")
        .join(format!("{session_id}.json"));
    assert!(meta_path.exists(), "arquivo de metadados nao foi criado");

    // Conteudo deve ser um SessionMetadata valido
    let content = tokio::fs::read_to_string(&meta_path).await.unwrap();
    let metadata: SessionMetadata = serde_json::from_str(&content).unwrap();
    assert_eq!(metadata.id, session_id);
    assert!(!metadata.created_at.is_empty());

    // Cleanup
    mgr.destroy_session(&session_id).await.unwrap();
}

#[tokio::test]
async fn destroy_session_removes_metadata_file() {
    let tmp = tempfile::tempdir().unwrap();
    let config = test_config(&tmp);
    let tmux = TmuxDriver::new();
    let mgr = SessionManager::new(config, tmux);

    let session_id = mgr.create_session(None).await.unwrap();
    let meta_path = std::path::PathBuf::from("/tmp/ccui-sessions")
        .join(format!("{session_id}.json"));
    assert!(meta_path.exists());

    mgr.destroy_session(&session_id).await.unwrap();
    assert!(!meta_path.exists(), "arquivo de metadados nao foi removido");
}

#[tokio::test]
async fn recover_sessions_from_disk_restores_alive_sessions() {
    let tmp = tempfile::tempdir().unwrap();
    let config = test_config(&tmp);
    let tmux = TmuxDriver::new();

    // Cria sessao com o primeiro manager
    let mgr1 = SessionManager::new(config.clone(), tmux.clone());
    let session_id = mgr1.create_session(None).await.unwrap();

    // Segundo manager (simula restart) -- sem sessoes em memoria
    let mgr2 = SessionManager::new(config.clone(), tmux.clone());
    assert!(mgr2.list_sessions().await.is_empty());

    // Recupera do disco
    let recovered = mgr2.recover_sessions_from_disk().await.unwrap();
    assert!(recovered.contains(&session_id), "sessao nao foi recuperada");

    // Sessao deve estar no mapa agora
    let info = mgr2.get_session(&session_id).await;
    assert!(info.is_some());
    assert_eq!(info.unwrap().id, session_id);

    // Cleanup
    mgr2.destroy_session(&session_id).await.unwrap();
}

#[tokio::test]
async fn recover_sessions_from_disk_ignores_dead_sessions() {
    let tmp = tempfile::tempdir().unwrap();
    let config = test_config(&tmp);
    let tmux = TmuxDriver::new();
    let mgr = SessionManager::new(config.clone(), tmux.clone());

    // Cria sessao e destroi o tmux (mas deixa o arquivo)
    let session_id = mgr.create_session(None).await.unwrap();
    let info = mgr.get_session(&session_id).await.unwrap();
    tmux.kill_session(&info.tmux_session).await.unwrap();

    // Remove do mapa interno sem apagar o arquivo
    mgr.list_sessions().await; // noop, so para confirmar

    // Novo manager tenta recuperar
    let mgr2 = SessionManager::new(config.clone(), tmux.clone());
    let recovered = mgr2.recover_sessions_from_disk().await.unwrap();
    assert!(
        recovered.is_empty(),
        "sessao morta nao deveria ser recuperada"
    );

    // Arquivo deve ter sido removido
    let meta_path = std::path::PathBuf::from("/tmp/ccui-sessions")
        .join(format!("{session_id}.json"));
    assert!(
        !meta_path.exists(),
        "arquivo de sessao morta nao foi removido"
    );
}

#[tokio::test]
async fn recover_sessions_from_disk_empty_dir() {
    let tmp = tempfile::tempdir().unwrap();
    let config = test_config(&tmp);
    let tmux = TmuxDriver::new();
    let mgr = SessionManager::new(config, tmux);

    // Sem diretorio sessions/ -- deve retornar vazio sem erro
    let recovered = mgr.recover_sessions_from_disk().await.unwrap();
    assert!(recovered.is_empty());
}

#[tokio::test]
async fn create_session_with_case_id_persists_it() {
    let cases_tmp = tempfile::tempdir().unwrap();
    // Cria diretorio do caso
    let case_dir = cases_tmp.path().join("caso-teste");
    std::fs::create_dir_all(&case_dir).unwrap();

    let config = AppConfig {
        cases_dir: cases_tmp.path().to_path_buf(),
        ..AppConfig::default()
    };
    let tmux = TmuxDriver::new();
    let mgr = SessionManager::new(config, tmux);

    let session_id = mgr.create_session(Some("caso-teste")).await.unwrap();

    let meta_path = std::path::PathBuf::from("/tmp/ccui-sessions")
        .join(format!("{session_id}.json"));
    let content = tokio::fs::read_to_string(&meta_path).await.unwrap();
    let metadata: SessionMetadata = serde_json::from_str(&content).unwrap();
    assert_eq!(metadata.case_id.as_deref(), Some("caso-teste"));
    assert!(metadata.working_dir.is_some());

    mgr.destroy_session(&session_id).await.unwrap();
}
