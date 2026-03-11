use std::sync::Arc;
use std::time::Instant;

use axum::extract::{Path, State};
use axum::response::IntoResponse;
use axum::Json;

use crate::config::SearchConfig;
use crate::embedder::OnnxEmbedder;
use crate::error::SearchError;
use crate::filter_builder;
use crate::metadata::MetadataStore;
use crate::query_preprocessor::{self, PreprocessedQuery};
use crate::reranker::OnnxReranker;
use crate::searcher::QdrantSearcher;
use crate::types::{
    ContextChunk, FiltersResponse, HealthResponse, QueryInfo, Scores, SearchRequest,
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
    pub reranker: Option<Arc<OnnxReranker>>,
}

/// POST /api/search
///
/// Pipeline: preprocessing -> embed query -> busca Qdrant (com filtros pre-busca)
/// -> metadados SQLite -> filtros residuais -> reranking -> expansao de contexto -> resposta.
pub async fn search_handler(
    State(state): State<AppState>,
    Json(req): Json<SearchRequest>,
) -> Result<impl IntoResponse, SearchError> {
    let total_start = Instant::now();
    let original_query = req.query.clone();
    let limit = req
        .limit
        .unwrap_or(state.config.search.default_limit)
        .min(state.config.search.max_results);

    // 0. Preprocessing
    let preprocessed = run_preprocessing(&state, &req);

    // Merge filtros extraidos com filtros explicitos do request
    let mut merged_filters = req.filters.clone().unwrap_or_default();
    if !preprocessed.extracted_filters.is_empty() {
        merged_filters.merge_extracted(&preprocessed.extracted_filters);
    }

    // Construir filtro Qdrant (pre-busca) a partir dos campos suportados
    let qdrant_filter = filter_builder::build_qdrant_filter(&merged_filters);
    let has_residual = filter_builder::has_residual_filters(&merged_filters);

    // Overfetch: necessario apenas se ha filtros residuais (pos-busca no SQLite)
    let overfetch_limit = if has_residual {
        limit * state.config.search.overfetch_factor
    } else {
        limit
    };

    // 1. Embedding (usa semantic_query preprocessada)
    let embed_start = Instant::now();
    let embedding = state
        .embedder
        .embed(&preprocessed.semantic_query)
        .map_err(SearchError::Embedding)?;
    let embedding_ms = embed_start.elapsed().as_millis() as u64;

    // 2. Busca Qdrant (com filtro pre-busca quando disponivel)
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
            qdrant_filter,
        )
        .await
        .map_err(SearchError::Embedding)?;
    let search_ms = search_start.elapsed().as_millis() as u64;

    let dense_candidates = ranked.iter().filter(|r| r.dense_rank > 0).count();
    let sparse_candidates = ranked.iter().filter(|r| r.sparse_rank > 0).count();
    let pre_filter_count = ranked.len();

    // 3. Extrair chunk_ids
    let chunk_ids: Vec<String> = ranked.iter().map(|r| r.chunk_id.clone()).collect();

    // 4. Filtros residuais (SQLite) -- apenas campos nao suportados no Qdrant
    let filtered_ids = if has_residual {
        state
            .metadata
            .filter_chunk_ids(&chunk_ids, &merged_filters)
            .map_err(SearchError::Embedding)?
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
                data_publicacao: meta.data_publicacao.clone(),
                tipo: meta.tipo.clone(),
                assuntos: meta.assuntos.clone(),
                secao: meta.secao.clone(),
                scores: Scores {
                    dense: ranked_item.dense_score,
                    sparse: ranked_item.sparse_score,
                    rrf: ranked_item.rrf_score,
                    dense_rank: ranked_item.dense_rank,
                    sparse_rank: ranked_item.sparse_rank,
                    rerank_score: None,
                },
                context_chunks: None,
            });
            if results.len() >= limit {
                break;
            }
        }
    }

    // 7. Reranking (opcional, apos RRF, antes de expansao de contexto)
    let mut rerank_ms: Option<u64> = None;
    let rerank_enabled = req
        .rerank
        .unwrap_or_else(|| state.config.reranker.as_ref().map_or(false, |r| r.enabled));

    if rerank_enabled {
        if let Some(ref reranker) = state.reranker {
            let rcfg = state.config.reranker.as_ref().expect("reranker config presente quando reranker carregado");
            let top_k = rcfg.top_k.min(results.len());
            if top_k > 0 {
                let passages: Vec<&str> = results[..top_k]
                    .iter()
                    .map(|r| r.content.as_str())
                    .collect();

                let rerank_start = Instant::now();
                match reranker.rerank(&preprocessed.semantic_query, &passages) {
                    Ok(scores) => {
                        let mut scored: Vec<_> = results
                            .drain(..top_k)
                            .zip(scores.iter())
                            .collect();
                        scored.sort_by(|a, b| {
                            b.1.partial_cmp(a.1)
                                .unwrap_or(std::cmp::Ordering::Equal)
                        });

                        let mut reranked: Vec<SearchResultItem> = scored
                            .into_iter()
                            .take(rcfg.return_top)
                            .map(|(mut item, &score)| {
                                item.scores.rerank_score = Some(score);
                                item
                            })
                            .collect();

                        // Anexar resultados restantes (nao rerankeados) apos os rerankeados
                        reranked.append(&mut results);
                        results = reranked;

                        let elapsed = rerank_start.elapsed().as_millis() as u64;
                        rerank_ms = Some(elapsed);
                        tracing::debug!(
                            top_k,
                            rerank_ms = elapsed,
                            "reranking concluido"
                        );
                    }
                    Err(e) => {
                        tracing::warn!(error = %e, "reranking falhou, mantendo ordem RRF");
                    }
                }
            }
        }
    }

    // 8. Expansao de contexto (chunks adjacentes)
    if req.expand_context.unwrap_or(false) {
        let window = req.context_window.unwrap_or(1);
        for result in &mut results {
            let adjacent = state
                .metadata
                .get_adjacent_chunks(&result.doc_id, result.chunk_index, window)
                .unwrap_or_default();
            result.context_chunks = Some(
                adjacent
                    .into_iter()
                    .map(|(idx, content, secao)| ContextChunk {
                        chunk_index: idx,
                        content,
                        secao,
                    })
                    .collect(),
            );
        }
    }

    let post_filter_count = results.len();
    let total_ms = total_start.elapsed().as_millis() as u64;

    let extracted_filters = if preprocessed.extracted_filters.is_empty() {
        None
    } else {
        Some(preprocessed.extracted_filters)
    };

    Ok(Json(SearchResponse {
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
            rerank_ms,
            total_ms,
            dense_candidates,
            sparse_candidates,
            pre_filter_count,
            post_filter_count,
        },
    }))
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
