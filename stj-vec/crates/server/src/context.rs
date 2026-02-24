use std::sync::Arc;
use stj_vec_core::config::ServerConfig;
use stj_vec_core::embedder::Embedder;
use stj_vec_core::storage::Storage;

#[derive(Clone)]
pub struct AppState {
    pub storage: Arc<Storage>,
    pub embedder: Arc<dyn Embedder>,
    pub config: ServerConfig,
}
