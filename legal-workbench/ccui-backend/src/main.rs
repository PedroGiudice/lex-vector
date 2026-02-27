use ccui_backend::config::AppConfig;
use ccui_backend::routes::{create_router, AppState};
use ccui_backend::team_watcher::TeamWatcher;
use tracing_subscriber::EnvFilter;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::try_from_default_env().unwrap_or_else(|_| "info".into()))
        .json()
        .init();

    let config = AppConfig::from_env();
    let state = AppState::new(config.clone());

    // Recuperar sessoes tmux orfas do startup anterior.
    match state.session_mgr.recover_orphan_sessions().await {
        Ok(recovered) if !recovered.is_empty() => {
            tracing::info!(count = recovered.len(), "recovered orphan sessions");
        }
        Err(e) => tracing::warn!("failed to recover orphan sessions: {e}"),
        _ => {}
    }

    // Iniciar TeamWatcher (observa ~/.claude/teams/ para detectar teammates).
    let watcher = TeamWatcher::new(config.teams_dir.clone(), state.broadcast_tx.clone());
    let _watcher_handle = watcher.start();

    let app = create_router(state);

    let addr = format!("{}:{}", config.host, config.port);
    tracing::info!(%addr, "ccui-backend starting");

    let listener = tokio::net::TcpListener::bind(&addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}
