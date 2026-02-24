use std::path::PathBuf;

#[derive(Debug, thiserror::Error)]
pub enum StjVecError {
    #[error("storage error: {0}")]
    Storage(#[from] rusqlite::Error),

    #[error("embedding not configured (dim=0)")]
    EmbeddingNotConfigured,

    #[error("embedding failed: {message}")]
    EmbeddingFailed { message: String },

    #[error("document not found: {id}")]
    DocumentNotFound { id: String },

    #[error("config error: {0}")]
    Config(String),

    #[error("io error at {path}")]
    Io {
        path: PathBuf,
        #[source]
        source: std::io::Error,
    },

    #[error(transparent)]
    Other(#[from] anyhow::Error),
}
