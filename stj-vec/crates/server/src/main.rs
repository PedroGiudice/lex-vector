use std::path::PathBuf;
use std::sync::Arc;

use anyhow::Context as _;
use clap::Parser;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::net::UnixListener;
use tokio_util::sync::CancellationToken;
use tracing_subscriber::EnvFilter;

use stj_vec_core::config::AppConfig;
use stj_vec_core::embedder::NoopEmbedder;
use stj_vec_core::storage::Storage;

mod context;
mod routes;

use context::AppState;

#[derive(Parser)]
#[command(name = "stj-vec-server", version, about = "STJ vector search server")]
struct Cli {
    /// Path to config file
    #[arg(short, long, default_value = "config.toml")]
    config: PathBuf,

    /// HTTP port override
    #[arg(short, long)]
    port: Option<u16>,

    /// Unix socket path override
    #[arg(short, long)]
    socket: Option<PathBuf>,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive("stj_vec=info".parse()?))
        .init();

    let cli = Cli::parse();
    let config = AppConfig::load(&cli.config)
        .with_context(|| format!("failed to load config from {}", cli.config.display()))?;

    let port = cli.port.unwrap_or(config.server.port);
    let socket_path = cli
        .socket
        .clone()
        .unwrap_or_else(|| PathBuf::from(&config.server.socket));

    let storage = Arc::new(
        Storage::open_readonly(&config.data.db_path)
            .with_context(|| format!("failed to open db at {}", config.data.db_path))?,
    );

    let embedder: Arc<dyn stj_vec_core::embedder::Embedder> = Arc::new(NoopEmbedder);

    let state = AppState {
        storage: storage.clone(),
        embedder,
        config: config.server,
    };

    let app = routes::router().with_state(state.clone());
    let token = CancellationToken::new();

    // HTTP listener
    let http_token = token.clone();
    let http_handle = tokio::spawn(async move {
        let addr = format!("0.0.0.0:{port}");
        tracing::info!("HTTP listening on {}", addr);
        let listener = tokio::net::TcpListener::bind(&addr)
            .await
            .expect("failed to bind HTTP listener");
        axum::serve(listener, app)
            .with_graceful_shutdown(async move { http_token.cancelled().await })
            .await
            .expect("HTTP server error");
    });

    // Unix socket listener (JSON line protocol)
    let sock_token = token.clone();
    let sock_storage = storage;
    let sock_handle = tokio::spawn(async move {
        let _ = std::fs::remove_file(&socket_path);
        let listener = UnixListener::bind(&socket_path).expect("failed to bind unix socket");
        tracing::info!("Socket listening on {}", socket_path.display());

        loop {
            tokio::select! {
                _ = sock_token.cancelled() => break,
                result = listener.accept() => {
                    if let Ok((stream, _)) = result {
                        let st = sock_storage.clone();
                        tokio::spawn(async move {
                            handle_socket_connection(stream, st).await;
                        });
                    }
                }
            }
        }
    });

    tokio::signal::ctrl_c().await?;
    tracing::info!("shutting down...");
    token.cancel();

    let _ = tokio::join!(http_handle, sock_handle);
    Ok(())
}

async fn handle_socket_connection(stream: tokio::net::UnixStream, storage: Arc<Storage>) {
    let (reader, mut writer) = stream.into_split();
    let reader = BufReader::new(reader);
    let mut lines = reader.lines();

    while let Ok(Some(line)) = lines.next_line().await {
        let response = match serde_json::from_str::<serde_json::Value>(&line) {
            Ok(req) => {
                let action = req.get("action").and_then(|a| a.as_str()).unwrap_or("");
                match action {
                    "ping" => serde_json::json!({"status": "ok"}),
                    "stats" => match storage.stats() {
                        Ok(s) => serde_json::to_value(s).unwrap_or_default(),
                        Err(e) => serde_json::json!({"error": e.to_string()}),
                    },
                    "doc" => {
                        let id = req.get("id").and_then(|v| v.as_str()).unwrap_or("");
                        match storage.get_document(id) {
                            Ok(Some(doc)) => serde_json::to_value(doc).unwrap_or_default(),
                            Ok(None) => serde_json::json!({"error": "not found"}),
                            Err(e) => serde_json::json!({"error": e.to_string()}),
                        }
                    }
                    _ => serde_json::json!({"error": format!("unknown action: {action}")}),
                }
            }
            Err(e) => serde_json::json!({"error": format!("invalid json: {e}")}),
        };

        let mut out = serde_json::to_string(&response).unwrap_or_default();
        out.push('\n');
        if writer.write_all(out.as_bytes()).await.is_err() {
            break;
        }
    }
}
