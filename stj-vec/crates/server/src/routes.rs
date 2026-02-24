use axum::extract::{Path, State};
use axum::http::StatusCode;
use axum::response::IntoResponse;
use axum::Json;
use serde::{Deserialize, Serialize};

use crate::context::AppState;
use stj_vec_core::types::SearchFilters;

#[derive(Serialize)]
pub struct HealthResponse {
    status: String,
}

#[derive(Deserialize)]
pub struct SearchRequest {
    pub query: String,
    #[serde(default = "default_limit")]
    pub limit: usize,
    #[serde(default)]
    pub filters: SearchFilters,
}

fn default_limit() -> usize {
    10
}


pub async fn health() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok".into(),
    })
}

pub async fn stats(State(state): State<AppState>) -> impl IntoResponse {
    match state.storage.stats() {
        Ok(s) => (StatusCode::OK, Json(serde_json::to_value(s).unwrap())).into_response(),
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(serde_json::json!({"error": e.to_string()})),
        )
            .into_response(),
    }
}

pub async fn get_document(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> impl IntoResponse {
    match state.storage.get_document(&id) {
        Ok(Some(doc)) => {
            (StatusCode::OK, Json(serde_json::to_value(doc).unwrap())).into_response()
        }
        Ok(None) => (
            StatusCode::NOT_FOUND,
            Json(serde_json::json!({"error": "document not found"})),
        )
            .into_response(),
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(serde_json::json!({"error": e.to_string()})),
        )
            .into_response(),
    }
}

pub async fn get_document_chunks(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> impl IntoResponse {
    match state.storage.get_chunks_by_doc(&id) {
        Ok(chunks) => {
            (StatusCode::OK, Json(serde_json::to_value(chunks).unwrap())).into_response()
        }
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(serde_json::json!({"error": e.to_string()})),
        )
            .into_response(),
    }
}

pub async fn search(
    State(state): State<AppState>,
    Json(req): Json<SearchRequest>,
) -> impl IntoResponse {
    let embedding = match state.embedder.embed(&req.query).await {
        Ok(e) => e,
        Err(e) => {
            return (
                StatusCode::SERVICE_UNAVAILABLE,
                Json(serde_json::json!({"error": format!("embedding failed: {}", e)})),
            )
                .into_response();
        }
    };

    let limit = if req.limit > 0 {
        req.limit
    } else {
        state.config.max_results
    };

    match state
        .storage
        .search(&embedding, limit, state.config.default_threshold, &req.filters)
    {
        Ok(results) => {
            (StatusCode::OK, Json(serde_json::to_value(results).unwrap())).into_response()
        }
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(serde_json::json!({"error": e.to_string()})),
        )
            .into_response(),
    }
}

pub fn router() -> axum::Router<AppState> {
    axum::Router::new()
        .route("/health", axum::routing::get(health))
        .route("/stats", axum::routing::get(stats))
        .route("/doc/{id}", axum::routing::get(get_document))
        .route("/doc/{id}/chunks", axum::routing::get(get_document_chunks))
        .route("/search", axum::routing::post(search))
}
