use std::path::Path;
use std::sync::Mutex;

use ndarray::Array2;
use ort::session::Session;
use ort::value::Tensor;
use tokenizers::Tokenizer;

/// Reranker ONNX para rescoring de pares (query, passage).
///
/// Usa modelo cross-encoder (ex: bge-reranker-v2-m3) para calcular
/// score de relevancia entre query e cada passagem candidata.
pub struct OnnxReranker {
    session: Mutex<Session>,
    tokenizer: Tokenizer,
}

impl OnnxReranker {
    /// Carrega modelo ONNX e tokenizer de um diretorio.
    ///
    /// O diretorio deve conter `model.onnx` e `tokenizer.json`.
    pub fn load(model_dir: &Path, threads: usize) -> anyhow::Result<Self> {
        let model_path = model_dir.join("model.onnx");
        anyhow::ensure!(
            model_path.exists(),
            "modelo reranker nao encontrado: {}",
            model_path.display()
        );

        let tokenizer_path = model_dir.join("tokenizer.json");
        anyhow::ensure!(
            tokenizer_path.exists(),
            "tokenizer.json do reranker nao encontrado em {}",
            tokenizer_path.display()
        );

        let session = Session::builder()
            .map_err(|e| anyhow::anyhow!("falha ao criar session builder do reranker: {e}"))?
            .with_intra_threads(threads)
            .map_err(|e| anyhow::anyhow!("falha ao configurar threads do reranker: {e}"))?
            .commit_from_file(&model_path)
            .map_err(|e| anyhow::anyhow!("falha ao carregar modelo reranker ONNX: {e}"))?;

        let tokenizer = Tokenizer::from_file(&tokenizer_path)
            .map_err(|e| anyhow::anyhow!("falha ao carregar tokenizer do reranker: {e}"))?;

        tracing::info!(
            model = %model_path.display(),
            threads,
            "OnnxReranker carregado"
        );

        Ok(Self {
            session: Mutex::new(session),
            tokenizer,
        })
    }

    /// Calcula score de relevancia para cada par (query, passage).
    ///
    /// Retorna vetor de scores (sigmoid) na mesma ordem dos passages.
    /// Scores mais altos indicam maior relevancia.
    pub fn rerank(&self, query: &str, passages: &[&str]) -> anyhow::Result<Vec<f32>> {
        if passages.is_empty() {
            return Ok(vec![]);
        }

        let mut scores = Vec::with_capacity(passages.len());
        let mut session = self
            .session
            .lock()
            .map_err(|e| anyhow::anyhow!("mutex do reranker envenenado: {e}"))?;

        for passage in passages {
            let encoding = self
                .tokenizer
                .encode((query, *passage), true)
                .map_err(|e| anyhow::anyhow!("tokenizacao do reranker falhou: {e}"))?;

            let ids = encoding.get_ids();
            let mask = encoding.get_attention_mask();
            let seq_len = ids.len();

            let input_ids_data: Vec<i64> = ids.iter().map(|&x| i64::from(x)).collect();
            let mask_data: Vec<i64> = mask.iter().map(|&x| i64::from(x)).collect();

            let input_ids_arr = Array2::from_shape_vec((1, seq_len), input_ids_data)?;
            let mask_arr = Array2::from_shape_vec((1, seq_len), mask_data)?;

            let input_ids_tensor = Tensor::from_array(input_ids_arr)?;
            let mask_tensor = Tensor::from_array(mask_arr)?;

            let outputs = session.run(ort::inputs![
                "input_ids" => input_ids_tensor,
                "attention_mask" => mask_tensor,
            ])?;

            let (_shape, logits_data) = outputs[0].try_extract_tensor::<f32>()?;
            let logit = logits_data[0];
            let score = 1.0 / (1.0 + (-logit).exp()); // sigmoid
            scores.push(score);
        }

        Ok(scores)
    }
}
