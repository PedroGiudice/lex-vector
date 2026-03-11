use std::collections::HashMap;

use qdrant_client::qdrant::{
    value, SearchPointsBuilder, SparseIndices,
};
use qdrant_client::Qdrant;

/// Resultado ranqueado com scores de ambas as buscas (densa e esparsa).
#[derive(Debug, Clone)]
pub struct RankedResult {
    pub chunk_id: String,
    pub dense_score: f32,
    pub sparse_score: f32,
    /// Rank 1-indexed na busca densa (0 se ausente).
    pub dense_rank: usize,
    /// Rank 1-indexed na busca esparsa (0 se ausente).
    pub sparse_rank: usize,
    pub rrf_score: f64,
}

/// Funde resultados de busca densa e esparsa via Reciprocal Rank Fusion.
///
/// `dense` e `sparse` sao pares `(chunk_id, score)` ordenados por relevancia decrescente.
/// `dense_weight` e `sparse_weight` permitem ajustar a importancia relativa de cada busca.
/// Retorna ate `limit` resultados ordenados por RRF score decrescente.
pub fn fuse_rrf(
    dense: &[(String, f32)],
    sparse: &[(String, f32)],
    limit: usize,
    rrf_k: f64,
    dense_weight: f64,
    sparse_weight: f64,
) -> Vec<RankedResult> {
    let mut scores: HashMap<String, RankedResult> = HashMap::new();

    for (rank_0, (id, score)) in dense.iter().enumerate() {
        let rank = rank_0 + 1;
        let rrf_contrib = dense_weight / (rrf_k + rank as f64);
        let entry = scores.entry(id.clone()).or_insert_with(|| RankedResult {
            chunk_id: id.clone(),
            dense_score: 0.0,
            sparse_score: 0.0,
            dense_rank: 0,
            sparse_rank: 0,
            rrf_score: 0.0,
        });
        entry.dense_score = *score;
        entry.dense_rank = rank;
        entry.rrf_score += rrf_contrib;
    }

    for (rank_0, (id, score)) in sparse.iter().enumerate() {
        let rank = rank_0 + 1;
        let rrf_contrib = sparse_weight / (rrf_k + rank as f64);
        let entry = scores.entry(id.clone()).or_insert_with(|| RankedResult {
            chunk_id: id.clone(),
            dense_score: 0.0,
            sparse_score: 0.0,
            dense_rank: 0,
            sparse_rank: 0,
            rrf_score: 0.0,
        });
        entry.sparse_score = *score;
        entry.sparse_rank = rank;
        entry.rrf_score += rrf_contrib;
    }

    let mut results: Vec<RankedResult> = scores.into_values().collect();
    results.sort_by(|a, b| b.rrf_score.partial_cmp(&a.rrf_score).unwrap_or(std::cmp::Ordering::Equal));
    results.truncate(limit);
    results
}

/// Cliente de busca hibrida no Qdrant via gRPC.
pub struct QdrantSearcher {
    client: Qdrant,
    collection: String,
    dense_top_k: u64,
    sparse_top_k: u64,
    rrf_k: f64,
    dense_weight: f64,
    sparse_weight: f64,
}

impl QdrantSearcher {
    /// Cria um novo searcher conectando ao Qdrant via gRPC.
    pub async fn new(
        url: &str,
        collection: &str,
        dense_top_k: u64,
        sparse_top_k: u64,
        rrf_k: f64,
        dense_weight: f64,
        sparse_weight: f64,
    ) -> anyhow::Result<Self> {
        let client = Qdrant::from_url(url)
            .build()
            .map_err(|e| anyhow::anyhow!("falha ao conectar ao Qdrant: {e}"))?;

        // Verificar que a colecao existe
        let exists = client
            .collection_exists(collection)
            .await
            .map_err(|e| anyhow::anyhow!("falha ao verificar colecao: {e}"))?;

        anyhow::ensure!(
            exists,
            "colecao '{collection}' nao encontrada no Qdrant"
        );

        tracing::info!(
            collection,
            url,
            dense_top_k,
            sparse_top_k,
            rrf_k,
            "QdrantSearcher conectado"
        );

        Ok(Self {
            client,
            collection: collection.to_string(),
            dense_top_k,
            sparse_top_k,
            rrf_k,
            dense_weight,
            sparse_weight,
        })
    }

    /// Executa busca hibrida: dense + sparse em paralelo, fusao RRF local.
    ///
    /// Os overrides opcionais permitem ajustar rrf_k e pesos por request.
    pub async fn search(
        &self,
        dense_vec: &[f32],
        sparse: &HashMap<u32, f32>,
        limit: usize,
        rrf_k_override: Option<f64>,
        dense_weight_override: Option<f64>,
        sparse_weight_override: Option<f64>,
    ) -> anyhow::Result<Vec<RankedResult>> {
        // Preparar busca densa
        let dense_request = SearchPointsBuilder::new(
            &self.collection,
            dense_vec.to_vec(),
            self.dense_top_k,
        )
        .vector_name("dense")
        .with_payload(true);

        // Preparar busca esparsa: separar indices e valores
        let mut indices: Vec<u32> = Vec::with_capacity(sparse.len());
        let mut values: Vec<f32> = Vec::with_capacity(sparse.len());
        for (&idx, &val) in sparse {
            indices.push(idx);
            values.push(val);
        }

        let sparse_request = SearchPointsBuilder::new(
            &self.collection,
            values,
            self.sparse_top_k,
        )
        .vector_name("sparse")
        .sparse_indices(SparseIndices { data: indices })
        .with_payload(true);

        // Executar ambas as buscas em paralelo
        let (dense_result, sparse_result) = tokio::join!(
            self.client.search_points(dense_request),
            self.client.search_points(sparse_request),
        );

        let dense_response = dense_result
            .map_err(|e| anyhow::anyhow!("busca densa falhou: {e}"))?;
        let sparse_response = sparse_result
            .map_err(|e| anyhow::anyhow!("busca esparsa falhou: {e}"))?;

        // Extrair chunk_ids e scores
        let dense_hits = extract_hits(&dense_response.result);
        let sparse_hits = extract_hits(&sparse_response.result);

        let rrf_k = rrf_k_override.unwrap_or(self.rrf_k);
        let dw = dense_weight_override.unwrap_or(self.dense_weight);
        let sw = sparse_weight_override.unwrap_or(self.sparse_weight);

        Ok(fuse_rrf(&dense_hits, &sparse_hits, limit, rrf_k, dw, sw))
    }

    /// Retorna o numero de pontos na colecao (para health check).
    pub async fn collection_point_count(&self) -> anyhow::Result<u64> {
        let info = self
            .client
            .collection_info(&self.collection)
            .await
            .map_err(|e| anyhow::anyhow!("falha ao obter info da colecao: {e}"))?;
        Ok(info
            .result
            .map(|r| r.points_count.unwrap_or(0))
            .unwrap_or(0))
    }

    /// Verifica se o Qdrant esta acessivel.
    pub async fn health_check(&self) -> bool {
        self.client.health_check().await.is_ok()
    }
}

/// Extrai pares (chunk_id, score) dos pontos retornados pelo Qdrant.
fn extract_hits(
    points: &[qdrant_client::qdrant::ScoredPoint],
) -> Vec<(String, f32)> {
    points
        .iter()
        .filter_map(|p| {
            let chunk_id = p.payload.get("chunk_id").and_then(|v| {
                if let Some(value::Kind::StringValue(s)) = &v.kind {
                    Some(s.clone())
                } else {
                    None
                }
            })?;
            Some((chunk_id, p.score))
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rrf_both_sides() {
        // "b" aparece em ambos os lados com bom rank -> deve ser primeiro
        let dense = vec![
            ("a".to_string(), 0.9),
            ("b".to_string(), 0.85),
            ("c".to_string(), 0.7),
        ];
        let sparse = vec![
            ("b".to_string(), 15.0),
            ("d".to_string(), 12.0),
            ("a".to_string(), 10.0),
        ];

        let results = fuse_rrf(&dense, &sparse, 10, 60.0, 1.0, 1.0);

        // "b" tem RRF = 1/(60+2) + 1/(60+1) = 1/62 + 1/61
        // "a" tem RRF = 1/(60+1) + 1/(60+3) = 1/61 + 1/63
        // "b" deve vir primeiro
        assert_eq!(results[0].chunk_id, "b");
        assert_eq!(results[0].dense_rank, 2);
        assert_eq!(results[0].sparse_rank, 1);

        // "a" em segundo
        assert_eq!(results[1].chunk_id, "a");
        assert_eq!(results[1].dense_rank, 1);
        assert_eq!(results[1].sparse_rank, 3);
    }

    #[test]
    fn test_rrf_single_side_only() {
        let dense = vec![
            ("x".to_string(), 0.95),
            ("y".to_string(), 0.8),
        ];
        let sparse: Vec<(String, f32)> = vec![];

        let results = fuse_rrf(&dense, &sparse, 10, 60.0, 1.0, 1.0);
        assert_eq!(results.len(), 2);
        assert_eq!(results[0].chunk_id, "x");
        assert_eq!(results[0].sparse_rank, 0); // ausente no lado esparso
        assert_eq!(results[0].dense_rank, 1);
    }

    #[test]
    fn test_rrf_respects_limit() {
        let dense = vec![
            ("a".to_string(), 0.9),
            ("b".to_string(), 0.8),
            ("c".to_string(), 0.7),
        ];
        let sparse = vec![
            ("d".to_string(), 15.0),
            ("e".to_string(), 12.0),
        ];

        let results = fuse_rrf(&dense, &sparse, 3, 60.0, 1.0, 1.0);
        assert_eq!(results.len(), 3);
    }

    #[test]
    fn test_rrf_weighted_dense_bias() {
        // Com dense_weight=2.0, o rank denso vale o dobro
        let dense = vec![
            ("a".to_string(), 0.9),
            ("b".to_string(), 0.85),
        ];
        let sparse = vec![
            ("b".to_string(), 15.0),
            ("a".to_string(), 10.0),
        ];

        // Pesos iguais: "b" vence (rank 2+1 vs 1+2 -- empata, mas b tem melhor soma)
        let equal = fuse_rrf(&dense, &sparse, 10, 60.0, 1.0, 1.0);
        // "b": dense_weight/(60+2) + sparse_weight/(60+1) = 1/62 + 1/61
        // "a": 1/61 + 1/63
        assert_eq!(equal[0].chunk_id, "b");

        // Dense bias 2.0: "a" pode vencer
        // "a": 2/61 + 1/63 = 0.03279 + 0.01587 = 0.04866
        // "b": 2/62 + 1/61 = 0.03226 + 0.01639 = 0.04865
        let biased = fuse_rrf(&dense, &sparse, 10, 60.0, 2.0, 1.0);
        assert_eq!(biased[0].chunk_id, "a");
    }

    #[tokio::test]
    #[ignore]
    async fn test_qdrant_search_integration() {
        let searcher = QdrantSearcher::new(
            "http://localhost:6334",
            "stj",
            10,
            10,
            60.0,
            1.0,
            1.0,
        )
        .await
        .expect("falha ao conectar ao Qdrant");

        // Vetor denso dummy de 1024 dimensoes
        let dense: Vec<f32> = vec![0.01; 1024];
        let mut sparse = HashMap::new();
        sparse.insert(42u32, 1.0f32);
        sparse.insert(100, 0.5);

        let results = searcher.search(&dense, &sparse, 5, None, None, None).await;
        assert!(results.is_ok(), "busca falhou: {:?}", results.err());
    }
}
