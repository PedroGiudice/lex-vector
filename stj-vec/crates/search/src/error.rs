use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};

#[derive(Debug, thiserror::Error)]
pub enum SearchError {
    #[error("embedding failed: {0}")]
    Embedding(#[from] anyhow::Error),
    #[error("qdrant error: {0}")]
    Qdrant(String),
    #[error("sqlite error: {0}")]
    Sqlite(#[from] rusqlite::Error),
    #[error("not found: {0}")]
    NotFound(String),
    #[error("pool error: {0}")]
    Pool(String),
}

impl IntoResponse for SearchError {
    fn into_response(self) -> Response {
        let status = match &self {
            SearchError::NotFound(_) => StatusCode::NOT_FOUND,
            _ => StatusCode::INTERNAL_SERVER_ERROR,
        };
        let body = serde_json::json!({ "error": self.to_string() });
        (status, axum::Json(body)).into_response()
    }
}
