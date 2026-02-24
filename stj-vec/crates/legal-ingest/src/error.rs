use std::path::PathBuf;

#[derive(Debug, thiserror::Error)]
pub enum LegalVecError {
    #[error("storage error: {0}")]
    Storage(#[from] rusqlite::Error),
    #[error("embedding failed: {message}")]
    EmbeddingFailed { message: String },
    #[error("corpus not found: {path}")]
    CorpusNotFound { path: PathBuf },
    #[error("config error: {0}")]
    Config(String),
    #[error("io error at {path}")]
    Io { path: PathBuf, #[source] source: std::io::Error },
    #[error(transparent)]
    Other(#[from] anyhow::Error),
}
