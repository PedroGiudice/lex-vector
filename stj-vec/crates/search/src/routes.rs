use std::sync::Arc;
use std::time::Instant;

use axum::extract::{Path, State};
use axum::response::IntoResponse;
use axum::Json;

use crate::config::SearchConfig;
use crate::embedder::OnnxEmbedder;
use crate::error::SearchError;
use crate::metadata::MetadataStore;
use crate::searcher::QdrantSearcher;
use crate::types::{
    FiltersResponse, HealthResponse, QueryInfo, Scores, SearchRequest,
    SearchResponse, SearchResultItem,
};

/// Estado compartilhado da aplicacao.
#[derive(Clone)]
pub struct AppState {
    pub embedder: Arc<OnnxEmbedder>,
    pub searcher: Arc<QdrantSearcher>,
    pub metadata: Arc<MetadataStore>,
    pub filters_cache: Arc<FiltersResponse>,
    pub config: SearchConfig,
    pub start_time: Instant,
}

/// POST /api/search
///
/// Pipeline completo: embed query -> busca Qdrant -> metadados SQLite -> filtros -> resposta.
pub async fn search_handler(
    State(state): State<AppState>,
    Json(req): Json<SearchRequest>,
) -> Result<impl IntoResponse, SearchError> {
    let total_start = Instant::now();
    let limit = req
        .limit
        .unwrap_or(state.config.search.default_limit)
        .min(state.config.search.max_results);

    // Overfetch para compensar filtros pos-busca
    let overfetch_limit = if req.filters.as_ref().is_some_and(|f| !f.is_empty()) {
        limit * state.config.search.overfetch_factor
    } else {
        limit
    };

    // 1. Embedding
    let embed_start = Instant::now();
    let embedding = state
        .embedder
        .embed(&req.query)
        .map_err(SearchError::Embedding)?;
    let embedding_ms = embed_start.elapsed().as_millis() as u64;

    // 2. Busca Qdrant
    let search_start = Instant::now();
    let ranked = state
        .searcher
        .search(&embedding.dense, &embedding.sparse, overfetch_limit)
        .await
        .map_err(SearchError::Embedding)?;
    let search_ms = search_start.elapsed().as_millis() as u64;

    let dense_candidates = ranked.iter().filter(|r| r.dense_rank > 0).count();
    let sparse_candidates = ranked.iter().filter(|r| r.sparse_rank > 0).count();
    let pre_filter_count = ranked.len();

    // 3. Extrair chunk_ids
    let chunk_ids: Vec<String> = ranked.iter().map(|r| r.chunk_id.clone()).collect();

    // 4. Filtros (se presentes)
    let filtered_ids = if let Some(ref filters) = req.filters {
        if !filters.is_empty() {
            state
                .metadata
                .filter_chunk_ids(&chunk_ids, filters)
                .map_err(SearchError::Embedding)?
        } else {
            chunk_ids.clone()
        }
    } else {
        chunk_ids.clone()
    };

    // 5. Metadados
    let metadata_start = Instant::now();
    let metadata_map = state
        .metadata
        .get_chunks_with_metadata(&filtered_ids)
        .map_err(SearchError::Embedding)?;
    let metadata_ms = metadata_start.elapsed().as_millis() as u64;

    // 6. Montar resposta, respeitando a ordem RRF
    let mut results = Vec::new();
    for ranked_item in &ranked {
        if let Some(meta) = metadata_map.get(&ranked_item.chunk_id) {
            results.push(SearchResultItem {
                chunk_id: meta.chunk_id.clone(),
                content: meta.content.clone(),
                chunk_index: meta.chunk_index,
                doc_id: meta.doc_id.clone(),
                processo: meta.processo.clone(),
                classe: meta.classe.clone(),
                ministro: meta.ministro.clone(),
                orgao_julgador: meta.orgao_julgador.clone(),
                data_julgamento: meta.data_julgamento.clone(),
                tipo: meta.tipo.clone(),
                assuntos: meta.assuntos.clone(),
                scores: Scores {
                    dense: ranked_item.dense_score,
                    sparse: ranked_item.sparse_score,
                    rrf: ranked_item.rrf_score,
                    dense_rank: ranked_item.dense_rank,
                    sparse_rank: ranked_item.sparse_rank,
                },
            });
            if results.len() >= limit {
                break;
            }
        }
    }

    let post_filter_count = results.len();
    let total_ms = total_start.elapsed().as_millis() as u64;

    Ok(Json(SearchResponse {
        results,
        query_info: QueryInfo {
            embedding_ms,
            search_ms,
            metadata_ms,
            total_ms,
            dense_candidates,
            sparse_candidates,
            pre_filter_count,
            post_filter_count,
        },
    }))
}

/// GET /api/document/:doc_id
pub async fn document_handler(
    State(state): State<AppState>,
    Path(doc_id): Path<String>,
) -> Result<impl IntoResponse, SearchError> {
    let response = state
        .metadata
        .get_document_chunks(&doc_id)
        .map_err(|e| {
            if e.to_string().contains("no rows") {
                SearchError::NotFound(format!("documento {doc_id} nao encontrado"))
            } else {
                SearchError::Embedding(e)
            }
        })?;

    Ok(Json(response))
}

/// GET /api/health
pub async fn health_handler(
    State(state): State<AppState>,
) -> impl IntoResponse {
    let qdrant_ok = state.searcher.health_check().await;
    let sqlite_ok = state.metadata.health_check();
    let points = state
        .searcher
        .collection_point_count()
        .await
        .unwrap_or(0);
    let doc_count = state.metadata.document_count().unwrap_or(0);
    let uptime = state.start_time.elapsed().as_secs();

    let all_ok = qdrant_ok && sqlite_ok;

    Json(HealthResponse {
        status: if all_ok {
            "ok".to_string()
        } else {
            "degraded".to_string()
        },
        qdrant: qdrant_ok,
        sqlite: sqlite_ok,
        model_loaded: true,
        model_name: "bge-m3-onnx".to_string(),
        collection_points: points,
        document_count: doc_count,
        uptime_secs: uptime,
    })
}

/// GET /api/filters
pub async fn filters_handler(
    State(state): State<AppState>,
) -> impl IntoResponse {
    Json(state.filters_cache.as_ref().clone())
}
