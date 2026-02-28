use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};

/// Application-wide error types.
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("tmux command failed: {0}")]
    Tmux(String),

    #[error("session not found: {id}")]
    SessionNotFound { id: String },

    #[error("pane not found: {pane_id} in session {session_id}")]
    PaneNotFound { session_id: String, pane_id: String },

    #[error("websocket error: {0}")]
    WebSocket(String),

    #[error("process error: {0}")]
    Process(String),

    #[error(transparent)]
    Io(#[from] std::io::Error),

    #[error(transparent)]
    Json(#[from] serde_json::Error),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let status = match &self {
            Self::SessionNotFound { .. } | Self::PaneNotFound { .. } => StatusCode::NOT_FOUND,
            _ => StatusCode::INTERNAL_SERVER_ERROR,
        };
        (status, self.to_string()).into_response()
    }
}
