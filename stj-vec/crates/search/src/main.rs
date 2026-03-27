use std::net::SocketAddr;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::Instant;

use axum::routing::{get, post};
use axum::Router;
use clap::Parser;
use tower_http::cors::{Any, CorsLayer};
use tower_http::services::{ServeDir, ServeFile};

use stj_vec_search::config::SearchConfig;
use stj_vec_search::embedder::OnnxEmbedder;
use stj_vec_search::metadata::MetadataStore;
use stj_vec_search::routes::{self, AppState};
use stj_vec_search::searcher::QdrantSearcher;

#[derive(Parser)]
#[command(name = "stj-vec-search", about = "Busca hibrida STJ")]
struct Cli {
    /// Caminho para o arquivo de configuracao TOML.
    #[arg(long, default_value = "search-config.toml")]
    config: PathBuf,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();
    let cli = Cli::parse();

    // 1. Carregar configuracao
    let config_str = std::fs::read_to_string(&cli.config)
        .map_err(|e| anyhow::anyhow!("falha ao ler config {}: {e}", cli.config.display()))?;
    let mut config: SearchConfig = toml::from_str(&config_str)?;
    tracing::info!(config = ?cli.config, "configuracao carregada");

    // 2. Abrir SQLite (read-only)
    let metadata = MetadataStore::open(&config.sqlite.path, config.sqlite.pool_size)?;
    tracing::info!(path = %config.sqlite.path, "SQLite aberto");

    // 3. Carregar modelo ONNX
    let model_dir = Path::new(&config.model.dir);
    let embedder = OnnxEmbedder::load(model_dir, config.model.threads)?;

    // 4. Conectar Qdrant via gRPC
    let searcher = QdrantSearcher::new(
        &config.qdrant.url,
        &config.qdrant.collection,
        config.qdrant.dense_top_k,
        config.qdrant.sparse_top_k,
        config.qdrant.rrf_k,
        config.search.dense_weight,
        config.search.sparse_weight,
    )
    .await?;

    // 5. Carregar dicionario de expansao
    let config_base_dir = cli.config.parent().unwrap_or(Path::new("."));
    config.preprocessing.load_expansion_dict(config_base_dir)?;

    // 6. Cache de filtros
    let filters_cache = metadata.get_filter_values()?;
    tracing::info!(
        ministros = filters_cache.ministros.len(),
        classes = filters_cache.classes.len(),
        tipos = filters_cache.tipos.len(),
        "filtros cacheados"
    );

    // 7. Montar estado e router
    let state = AppState {
        embedder: Arc::new(embedder),
        searcher: Arc::new(searcher),
        metadata: Arc::new(metadata),
        filters_cache: Arc::new(filters_cache),
        config: config.clone(),
        start_time: Instant::now(),
    };

    // CORS
    let cors = build_cors(&config.server.cors_origins);

    // Rotas API
    let api_routes = Router::new()
        .route("/search", post(routes::search_handler))
        .route("/search/batch", post(routes::batch_search_handler))
        .route("/document/{doc_id}", get(routes::document_handler))
        .route("/health", get(routes::health_handler))
        .route("/filters", get(routes::filters_handler));

    // Servir arquivos estaticos com fallback para SPA
    let static_dir = &config.server.static_dir;
    let app = if Path::new(static_dir).exists() {
        let index_path = format!("{static_dir}/index.html");
        let serve_dir = ServeDir::new(static_dir).not_found_service(ServeFile::new(&index_path));

        Router::new()
            .nest("/api", api_routes)
            .fallback_service(serve_dir)
            .layer(cors)
            .with_state(state)
    } else {
        tracing::warn!(
            dir = static_dir,
            "diretorio de arquivos estaticos nao encontrado, servindo apenas API"
        );
        Router::new()
            .nest("/api", api_routes)
            .layer(cors)
            .with_state(state)
    };

    // 7. Bind e listen
    let addr = SocketAddr::from(([0, 0, 0, 0], config.server.port));
    let listener = tokio::net::TcpListener::bind(addr).await?;
    tracing::info!(addr = %addr, "servidor iniciado");
    axum::serve(listener, app).await?;

    Ok(())
}

/// Constroi layer CORS a partir das origens configuradas.
fn build_cors(origins: &[String]) -> CorsLayer {
    if origins.is_empty() {
        CorsLayer::new()
            .allow_origin(Any)
            .allow_methods(Any)
            .allow_headers(Any)
    } else {
        let allowed: Vec<_> = origins.iter().filter_map(|o| o.parse().ok()).collect();
        CorsLayer::new()
            .allow_origin(allowed)
            .allow_methods(Any)
            .allow_headers(Any)
    }
}
