use std::sync::Arc;
use std::time::Instant;

use axum::extract::{Path, State};
use axum::response::IntoResponse;
use axum::Json;

use crate::config::SearchConfig;
use crate::embedder::OnnxEmbedder;
use crate::error::SearchError;
use crate::metadata::MetadataStore;
use crate::query_preprocessor::{self, PreprocessedQuery};
use crate::searcher::QdrantSearcher;
use crate::types::{
    BatchSearchRequest, BatchSearchResponse, FiltersResponse, HealthResponse, QueryInfo, Scores,
    SearchRequest, SearchResponse, SearchResultItem,
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
pub async fn search_handler(
    State(state): State<AppState>,
    Json(req): Json<SearchRequest>,
) -> Result<impl IntoResponse, SearchError> {
    let resp = execute_search(&state, req).await?;
    Ok(Json(resp))
}

/// POST /api/search/batch
///
/// Executa multiplas buscas em paralelo. Embedding sequencial (ONNX single-threaded),
/// buscas Qdrant em paralelo via tokio.
pub async fn batch_search_handler(
    State(state): State<AppState>,
    Json(req): Json<BatchSearchRequest>,
) -> Result<impl IntoResponse, SearchError> {
    let total_start = Instant::now();
    let futures: Vec<_> = req
        .queries
        .into_iter()
        .map(|q| execute_search(&state, q))
        .collect();
    let results: Result<Vec<_>, _> = futures::future::join_all(futures)
        .await
        .into_iter()
        .collect();
    let results = results?;
    let total_ms = total_start.elapsed().as_millis() as u64;
    Ok(Json(BatchSearchResponse { results, total_ms }))
}

/// Pipeline core: preprocessing -> embed -> busca Qdrant -> metadados -> filtros -> rerank -> dedup.
async fn execute_search(state: &AppState, req: SearchRequest) -> Result<SearchResponse, SearchError> {
    let total_start = Instant::now();
    let original_query = req.query.clone();
    let limit = req
        .limit
        .unwrap_or(state.config.search.default_limit)
        .min(state.config.search.max_results);

    let preprocessed = run_preprocessing(state, &req);

    let mut merged_filters = req.filters.clone().unwrap_or_default();
    if !preprocessed.extracted_filters.is_empty() {
        merged_filters.merge_extracted(&preprocessed.extracted_filters);
    }

    let has_filters = !merged_filters.is_empty();
    let overfetch_limit = if has_filters {
        limit * state.config.search.overfetch_factor
    } else {
        limit
    };

    // 1. Embedding
    let embed_start = Instant::now();
    let embedding = state
        .embedder
        .embed(&preprocessed.semantic_query)
        .map_err(SearchError::Embedding)?;
    let embedding_ms = embed_start.elapsed().as_millis() as u64;

    // 2. Busca Qdrant
    let search_start = Instant::now();
    let ranked = state
        .searcher
        .search(
            &embedding.dense,
            &embedding.sparse,
            overfetch_limit,
            req.rrf_k,
            req.dense_weight,
            req.sparse_weight,
        )
        .await
        .map_err(SearchError::Embedding)?;
    let search_ms = search_start.elapsed().as_millis() as u64;

    let dense_candidates = ranked.iter().filter(|r| r.dense_rank > 0).count();
    let sparse_candidates = ranked.iter().filter(|r| r.sparse_rank > 0).count();
    let pre_filter_count = ranked.len();

    let chunk_ids: Vec<String> = ranked.iter().map(|r| r.chunk_id.clone()).collect();

    // 3. Metadados + filtros em memoria
    let metadata_start = Instant::now();
    let mut metadata_map = state
        .metadata
        .get_chunks_with_metadata(&chunk_ids)
        .map_err(SearchError::Embedding)?;
    if has_filters {
        metadata_map.retain(|_, meta| merged_filters.matches(meta));
    }
    let metadata_ms = metadata_start.elapsed().as_millis() as u64;

    // 4. Reranking: co-ocorrencia + tipo boost
    let mut ranked = ranked;
    {
        let query_lower = original_query.to_lowercase();
        let concepts: Vec<&str> = query_lower
            .split_whitespace()
            .filter(|w| w.len() >= 4)
            .collect();
        let concept_count = concepts.len().max(1) as f64;

        for item in ranked.iter_mut() {
            if let Some(meta) = metadata_map.get(&item.chunk_id) {
                let content_lower = meta.content.to_lowercase();
                let matches = concepts
                    .iter()
                    .filter(|c| content_lower.contains(*c))
                    .count() as f64;
                let cooccurrence_bonus = (matches / concept_count) * 0.3;
                let tipo_factor = if meta.tipo.contains("CORD") { 1.10 } else { 0.90 };
                item.rrf_score = item.rrf_score * (1.0 + cooccurrence_bonus) * tipo_factor;
            }
        }
        ranked.sort_by(|a, b| {
            b.rrf_score
                .partial_cmp(&a.rrf_score)
                .unwrap_or(std::cmp::Ordering::Equal)
        });
    }

    // 5. Dedup por processo (prioriza acordao)
    let mut results: Vec<SearchResultItem> = Vec::new();
    let mut seen: std::collections::HashMap<String, usize> = std::collections::HashMap::new();
    for ri in &ranked {
        if let Some(meta) = metadata_map.get(&ri.chunk_id) {
            let key = meta.processo.clone();
            if let Some(&idx) = seen.get(&key) {
                if meta.tipo.contains("CORD") && !results[idx].tipo.contains("CORD") {
                    results[idx] = build_result_item(meta, ri);
                }
                continue;
            }
            results.push(build_result_item(meta, ri));
            seen.insert(key, results.len() - 1);
            if results.len() >= limit {
                break;
            }
        }
    }

    let post_filter_count = results.len();
    let total_ms = total_start.elapsed().as_millis() as u64;

    let extracted_filters = if preprocessed.extracted_filters.is_empty() {
        None
    } else {
        Some(preprocessed.extracted_filters)
    };

    Ok(SearchResponse {
        results,
        query_info: QueryInfo {
            original_query,
            processed_query: preprocessed.semantic_query,
            extracted_filters,
            extractions: preprocessed.extractions,
            expanded_terms: preprocessed.expanded_terms,
            embedding_ms,
            search_ms,
            metadata_ms,
            total_ms,
            dense_candidates,
            sparse_candidates,
            pre_filter_count,
            post_filter_count,
        },
    })
}

fn build_result_item(
    meta: &crate::types::ChunkWithMetadata,
    ri: &crate::searcher::RankedResult,
) -> SearchResultItem {
    SearchResultItem {
        chunk_id: meta.chunk_id.clone(),
        content: meta.content.clone(),
        chunk_index: meta.chunk_index,
        doc_id: meta.doc_id.clone(),
        processo: meta.processo.clone(),
        classe: meta.classe.clone(),
        ministro: meta.ministro.clone(),
        orgao_julgador: meta.orgao_julgador.clone(),
        data_publicacao: meta.data_publicacao.clone(),
        tipo: meta.tipo.clone(),
        assuntos: meta.assuntos.clone(),
        scores: Scores {
            dense: ri.dense_score,
            sparse: ri.sparse_score,
            rrf: ri.rrf_score,
            dense_rank: ri.dense_rank,
            sparse_rank: ri.sparse_rank,
        },
    }
}

/// Executa o preprocessing da query, respeitando config global e overrides por request.
fn run_preprocessing(state: &AppState, req: &SearchRequest) -> PreprocessedQuery {
    let cfg = &state.config.preprocessing;

    if !cfg.enabled {
        return PreprocessedQuery {
            semantic_query: req.query.clone(),
            extracted_filters: Default::default(),
            extractions: Vec::new(),
            expanded_terms: Vec::new(),
        };
    }

    // Aplicar overrides do request sobre o config global
    let mut effective_config = cfg.clone();
    if let Some(ref opts) = req.preprocessing {
        if let Some(v) = opts.extract_metadata {
            effective_config.extract_metadata = v;
        }
        if let Some(v) = opts.remove_stopwords {
            effective_config.remove_stopwords = v;
        }
        if let Some(v) = opts.expand_query {
            effective_config.expand_query = v;
        }
    }

    let ministros = &state.filters_cache.ministros;
    query_preprocessor::preprocess(&req.query, &effective_config, ministros)
}

/// GET /api/document/:doc_id
pub async fn document_handler(
    State(state): State<AppState>,
    Path(doc_id): Path<String>,
) -> Result<impl IntoResponse, SearchError> {
    let response = state.metadata.get_document_chunks(&doc_id).map_err(|e| {
        if e.to_string().contains("no rows") {
            SearchError::NotFound(format!("documento {doc_id} nao encontrado"))
        } else {
            SearchError::Embedding(e)
        }
    })?;

    Ok(Json(response))
}

/// GET /api/health
pub async fn health_handler(State(state): State<AppState>) -> impl IntoResponse {
    let qdrant_ok = state.searcher.health_check().await;
    let sqlite_ok = state.metadata.health_check();
    let points = state.searcher.collection_point_count().await.unwrap_or(0);
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
pub async fn filters_handler(State(state): State<AppState>) -> impl IntoResponse {
    Json(state.filters_cache.as_ref().clone())
}
