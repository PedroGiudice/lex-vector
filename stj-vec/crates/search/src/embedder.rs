use std::collections::HashMap;
use std::path::Path;
use std::sync::Mutex;
use std::time::Instant;

use ndarray::Array2;
use ort::session::Session;
use ort::value::Tensor;
use tokenizers::Tokenizer;

/// Saida do embedding com vetores denso e esparso.
pub struct EmbeddingOutput {
    /// Vetor denso de 1024 dimensoes, normalizado L2.
    pub dense: Vec<f32>,
    /// Mapa token_id -> peso para busca esparsa.
    pub sparse: HashMap<u32, f32>,
    /// Tempo de inferencia em milissegundos.
    pub elapsed_ms: u64,
}

/// Embedder ONNX para BGE-M3 (dense + sparse).
///
/// Usa `Mutex<Session>` internamente pois `Session::run` requer `&mut self`.
pub struct OnnxEmbedder {
    session: Mutex<Session>,
    tokenizer: Tokenizer,
}

impl OnnxEmbedder {
    /// Carrega modelo ONNX e tokenizer a partir do diretorio do modelo.
    ///
    /// Espera `model.onnx` e `tokenizer.json` dentro de `model_dir`.
    pub fn load(model_dir: &Path, threads: usize) -> anyhow::Result<Self> {
        let model_path = model_dir.join("model.onnx");
        anyhow::ensure!(
            model_path.exists(),
            "modelo ONNX nao encontrado em {}",
            model_path.display()
        );

        let tokenizer_path = model_dir.join("tokenizer.json");
        anyhow::ensure!(
            tokenizer_path.exists(),
            "tokenizer.json nao encontrado em {}",
            tokenizer_path.display()
        );

        let session = Session::builder()
            .map_err(|e| anyhow::anyhow!("falha ao criar session builder: {e}"))?
            .with_intra_threads(threads)
            .map_err(|e| anyhow::anyhow!("falha ao configurar threads: {e}"))?
            .commit_from_file(&model_path)
            .map_err(|e| anyhow::anyhow!("falha ao carregar modelo ONNX: {e}"))?;

        let tokenizer = Tokenizer::from_file(&tokenizer_path)
            .map_err(|e| anyhow::anyhow!("falha ao carregar tokenizer: {e}"))?;

        tracing::info!(
            model = %model_path.display(),
            threads,
            "modelo ONNX carregado"
        );

        Ok(Self {
            session: Mutex::new(session),
            tokenizer,
        })
    }

    /// Gera embeddings denso e esparso para o texto fornecido.
    pub fn embed(&self, text: &str) -> anyhow::Result<EmbeddingOutput> {
        let start = Instant::now();

        // Tokenizar
        let encoding = self
            .tokenizer
            .encode(text, true)
            .map_err(|e| anyhow::anyhow!("falha na tokenizacao: {e}"))?;

        let token_ids = encoding.get_ids();
        let attention_mask = encoding.get_attention_mask();
        let seq_len = token_ids.len();

        // Criar arrays ndarray [1, seq_len]
        let input_ids_data: Vec<i64> = token_ids.iter().map(|&id| i64::from(id)).collect();
        let mask_data: Vec<i64> = attention_mask.iter().map(|&m| i64::from(m)).collect();

        let input_ids_arr = Array2::from_shape_vec((1, seq_len), input_ids_data)?;
        let mask_arr = Array2::from_shape_vec((1, seq_len), mask_data)?;

        // Criar Tensors (owned)
        let input_ids_tensor = Tensor::from_array(input_ids_arr)?;
        let mask_tensor = Tensor::from_array(mask_arr)?;

        // Inferencia ONNX
        let mut session = self
            .session
            .lock()
            .map_err(|e| anyhow::anyhow!("mutex envenenado: {e}"))?;
        let outputs = session.run(ort::inputs![
            "input_ids" => input_ids_tensor,
            "attention_mask" => mask_tensor,
        ])?;

        // Extrair last_hidden_state [1, seq_len, hidden_dim]
        let (shape, hidden_data) = outputs[0].try_extract_tensor::<f32>()?;
        anyhow::ensure!(
            shape.len() == 3 && shape[0] == 1,
            "shape inesperado do hidden_state: {shape:?}"
        );
        let hidden_dim = shape[2] as usize;

        // Dense: mean pooling com attention mask + normalizacao L2
        let dense = mean_pool_and_normalize(hidden_data, attention_mask, seq_len, hidden_dim);

        // Sparse: peso maximo por token, ReLU, limiar 0.01, sem CLS/SEP
        let sparse =
            extract_sparse_weights(hidden_data, token_ids, attention_mask, seq_len, hidden_dim);

        let elapsed_ms = start.elapsed().as_millis() as u64;

        Ok(EmbeddingOutput {
            dense,
            sparse,
            elapsed_ms,
        })
    }
}

/// Mean pooling com attention mask seguido de normalizacao L2.
///
/// `hidden_data` e um slice flat [1 x seq_len x hidden_dim].
fn mean_pool_and_normalize(
    hidden_data: &[f32],
    attention_mask: &[u32],
    seq_len: usize,
    hidden_dim: usize,
) -> Vec<f32> {
    let mut pooled = vec![0.0f32; hidden_dim];
    let mut mask_sum = 0.0f32;

    for (t, &mask_val) in attention_mask.iter().enumerate().take(seq_len) {
        let m = mask_val as f32;
        if m > 0.0 {
            mask_sum += m;
            let offset = t * hidden_dim;
            for d in 0..hidden_dim {
                pooled[d] += hidden_data[offset + d] * m;
            }
        }
    }

    if mask_sum > 0.0 {
        for d in &mut pooled {
            *d /= mask_sum;
        }
    }

    // Normalizacao L2
    let norm: f32 = pooled.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm > 0.0 {
        for d in &mut pooled {
            *d /= norm;
        }
    }

    pooled
}

/// Extrai pesos esparsos: para cada token (exceto CLS/SEP), calcula o
/// maximo das dimensoes do hidden state, aplica ReLU e filtra por limiar.
///
/// `hidden_data` e um slice flat [1 x seq_len x hidden_dim].
fn extract_sparse_weights(
    hidden_data: &[f32],
    token_ids: &[u32],
    attention_mask: &[u32],
    seq_len: usize,
    hidden_dim: usize,
) -> HashMap<u32, f32> {
    let mut sparse = HashMap::new();

    // Encontrar posicao do ultimo token nao-padding (SEP)
    let last_valid = attention_mask
        .iter()
        .rposition(|&m| m > 0)
        .unwrap_or(seq_len.saturating_sub(1));

    for t in 0..seq_len {
        // Pular CLS (posicao 0) e SEP (ultima posicao valida)
        if t == 0 || t == last_valid {
            continue;
        }

        // Pular tokens de padding
        if attention_mask[t] == 0 {
            continue;
        }

        let token_id = token_ids[t];

        // Maximo das dimensoes do hidden state para este token
        let offset = t * hidden_dim;
        let mut max_val = f32::NEG_INFINITY;
        for d in 0..hidden_dim {
            let v = hidden_data[offset + d];
            if v > max_val {
                max_val = v;
            }
        }

        // ReLU + limiar
        let weight = max_val.max(0.0);
        if weight > 0.01 {
            // Se o token ja existe, manter o peso maximo (subwords)
            let entry = sparse.entry(token_id).or_insert(0.0f32);
            if weight > *entry {
                *entry = weight;
            }
        }
    }

    sparse
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_mean_pool_simple() {
        // Hidden state flat 1x3x2 com mask [1, 1, 0]
        let data = [1.0f32, 2.0, 3.0, 4.0, 5.0, 6.0];
        let mask = [1u32, 1, 0];

        let result = mean_pool_and_normalize(&data, &mask, 3, 2);
        assert_eq!(result.len(), 2);

        // Mean de [1,2] e [3,4] = [2.0, 3.0], norm = sqrt(4+9) = sqrt(13)
        let norm = (2.0f32 * 2.0 + 3.0 * 3.0).sqrt();
        let expected_0 = 2.0 / norm;
        let expected_1 = 3.0 / norm;
        assert!((result[0] - expected_0).abs() < 1e-5);
        assert!((result[1] - expected_1).abs() < 1e-5);
    }

    #[test]
    fn test_sparse_extraction() {
        // Flat 1x4x2 hidden state, tokens [101, 42, 55, 102], mask [1,1,1,1]
        // Posicao 0 (CLS=101) e 3 (SEP=102) sao puladas
        let data = [
            0.5f32, 0.3, // token 0 (CLS) - pulado
            0.8, 0.02, // token 1 (42) - max=0.8
            -0.1, -0.5, // token 2 (55) - max=-0.1 -> ReLU -> 0.0 < 0.01
            0.9, 0.7, // token 3 (SEP) - pulado
        ];
        let token_ids = [101u32, 42, 55, 102];
        let mask = [1u32, 1, 1, 1];

        let sparse = extract_sparse_weights(&data, &token_ids, &mask, 4, 2);
        assert_eq!(sparse.len(), 1);
        assert!((sparse[&42] - 0.8).abs() < 1e-5);
        assert!(!sparse.contains_key(&55)); // abaixo do limiar
    }

    #[test]
    #[ignore]
    fn test_embed_produces_1024d_dense() {
        let model_dir = Path::new("models/bge-m3-onnx");
        let embedder = OnnxEmbedder::load(model_dir, 4).expect("falha ao carregar modelo");
        let output = embedder
            .embed("dano moral em contrato")
            .expect("falha no embed");
        assert_eq!(output.dense.len(), 1024);

        // Verificar normalizacao L2
        let norm: f32 = output.dense.iter().map(|x| x * x).sum::<f32>().sqrt();
        assert!(
            (norm - 1.0).abs() < 1e-4,
            "vetor denso nao normalizado: norm={norm}"
        );
    }

    #[test]
    #[ignore]
    fn test_embed_sparse_not_empty() {
        let model_dir = Path::new("models/bge-m3-onnx");
        let embedder = OnnxEmbedder::load(model_dir, 4).expect("falha ao carregar modelo");
        let output = embedder
            .embed("responsabilidade civil objetiva")
            .expect("falha no embed");
        assert!(
            !output.sparse.is_empty(),
            "vetor esparso nao deve ser vazio"
        );
    }

    #[test]
    #[ignore]
    fn test_embed_deterministic() {
        let model_dir = Path::new("models/bge-m3-onnx");
        let embedder = OnnxEmbedder::load(model_dir, 4).expect("falha ao carregar modelo");
        let text = "habeas corpus";
        let out1 = embedder.embed(text).expect("falha no embed 1");
        let out2 = embedder.embed(text).expect("falha no embed 2");

        assert_eq!(out1.dense.len(), out2.dense.len());
        for (a, b) in out1.dense.iter().zip(out2.dense.iter()) {
            assert!(
                (a - b).abs() < 1e-6,
                "embeddings nao deterministicos: {a} != {b}"
            );
        }
        assert_eq!(out1.sparse, out2.sparse);
    }
}
