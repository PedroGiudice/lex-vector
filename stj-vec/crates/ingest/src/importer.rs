//! Importa embeddings (.npz + .json) gerados pelo Modal para SQLite.

use anyhow::{Context, Result};
use std::io::Read;
use std::path::Path;

use stj_vec_core::storage::Storage;

/// Importa embeddings de um diretorio com .npz + .json.
/// Retorna (sources_imported, embeddings_imported).
pub fn import_embeddings_from_modal(
    storage: &Storage,
    input_dir: &Path,
    limit: Option<usize>,
) -> Result<(usize, usize)> {
    let mut npz_files: Vec<_> = std::fs::read_dir(input_dir)?
        .filter_map(|e| e.ok())
        .filter(|e| e.path().extension().is_some_and(|ext| ext == "npz"))
        .collect();

    npz_files.sort_by_key(|e| e.file_name());

    let files_to_process = match limit {
        Some(n) => &npz_files[..n.min(npz_files.len())],
        None => &npz_files,
    };

    let mut total_sources = 0;
    let mut total_embeddings = 0;

    for entry in files_to_process {
        let npz_path = entry.path();
        let source_name = npz_path
            .file_stem()
            .unwrap_or_default()
            .to_string_lossy()
            .into_owned();

        let json_path = input_dir.join(format!("{source_name}.json"));
        if !json_path.exists() {
            tracing::warn!(source = %source_name, "index JSON not found, skipping");
            continue;
        }

        // Ler chunk IDs
        let ids_content = std::fs::read_to_string(&json_path)?;
        let chunk_ids: Vec<String> = serde_json::from_str(&ids_content)?;

        // Ler embeddings do .npz
        let embeddings = read_npz_embeddings(&npz_path)?;

        if chunk_ids.len() != embeddings.len() {
            anyhow::bail!(
                "mismatch {source_name}: {} ids vs {} embeddings",
                chunk_ids.len(),
                embeddings.len()
            );
        }

        // Inserir em batch
        let pairs: Vec<(String, Vec<f32>)> = chunk_ids.into_iter().zip(embeddings).collect();

        let count = pairs.len();
        storage.insert_embeddings_batch(&pairs)?;

        // Atualizar ingest_log para "done"
        if let Ok(Some(status)) = storage.get_ingest_status(&source_name) {
            storage.set_ingest_status(
                &source_name,
                "done",
                status.doc_count,
                status.chunk_count,
            )?;
        }

        tracing::info!(source = %source_name, embeddings = count, "imported");
        total_sources += 1;
        total_embeddings += count;
    }

    Ok((total_sources, total_embeddings))
}

/// Le array de embeddings de um arquivo .npz (numpy compressed).
/// Espera key "embeddings" com shape (N, dim) e dtype float32.
fn read_npz_embeddings(path: &Path) -> Result<Vec<Vec<f32>>> {
    let file =
        std::fs::File::open(path).with_context(|| format!("falha ao abrir {}", path.display()))?;

    let mut archive = zip::ZipArchive::new(file)
        .with_context(|| format!("falha ao ler npz {}", path.display()))?;

    // .npz e um zip com arrays .npy dentro. A key "embeddings" gera "embeddings.npy".
    let mut npy_file = archive
        .by_name("embeddings.npy")
        .with_context(|| "key 'embeddings' nao encontrada no npz")?;

    let mut data = Vec::new();
    npy_file.read_to_end(&mut data)?;

    parse_npy_f32_2d(&data)
}

/// Parser minimo de .npy format (numpy array serializado).
/// Suporta apenas dtype float32 (<f4), C-contiguous, 2D.
fn parse_npy_f32_2d(data: &[u8]) -> Result<Vec<Vec<f32>>> {
    // .npy format: 6 magic bytes, 2 version bytes, 2 header_len bytes, header, data
    if data.len() < 10 || &data[..6] != b"\x93NUMPY" {
        anyhow::bail!("nao e formato .npy valido");
    }

    let header_len = u16::from_le_bytes([data[8], data[9]]) as usize;
    let header_str = std::str::from_utf8(&data[10..10 + header_len])?;

    let shape = parse_npy_shape(header_str)?;
    if shape.len() != 2 {
        anyhow::bail!("esperado array 2D, got {}D", shape.len());
    }

    let (rows, cols) = (shape[0], shape[1]);
    let data_start = 10 + header_len;
    let expected_bytes = rows * cols * 4;

    if data.len() < data_start + expected_bytes {
        anyhow::bail!(
            "dados insuficientes: {} bytes, esperado {}",
            data.len() - data_start,
            expected_bytes
        );
    }

    let float_data = &data[data_start..data_start + expected_bytes];
    let mut result = Vec::with_capacity(rows);

    for i in 0..rows {
        let start = i * cols * 4;
        let end = start + cols * 4;
        let row: Vec<f32> = float_data[start..end]
            .chunks_exact(4)
            .map(|bytes| f32::from_le_bytes([bytes[0], bytes[1], bytes[2], bytes[3]]))
            .collect();
        result.push(row);
    }

    Ok(result)
}

/// Extrai shape do header .npy.
fn parse_npy_shape(header: &str) -> Result<Vec<usize>> {
    let shape_start = header
        .find("'shape':")
        .or_else(|| header.find("\"shape\":"))
        .ok_or_else(|| anyhow::anyhow!("shape nao encontrado no header"))?;

    let after = &header[shape_start..];
    let paren_start = after
        .find('(')
        .ok_or_else(|| anyhow::anyhow!("( nao encontrado"))?;
    let paren_end = after
        .find(')')
        .ok_or_else(|| anyhow::anyhow!(") nao encontrado"))?;

    let shape_str = &after[paren_start + 1..paren_end];
    let dims: Vec<usize> = shape_str
        .split(',')
        .filter_map(|s| s.trim().parse().ok())
        .collect();

    Ok(dims)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_npy_shape() {
        let header = "{'descr': '<f4', 'fortran_order': False, 'shape': (100, 1024), }";
        let shape = parse_npy_shape(header).unwrap();
        assert_eq!(shape, vec![100, 1024]);
    }

    #[test]
    fn test_parse_npy_shape_single_row() {
        let header = "{'descr': '<f4', 'fortran_order': False, 'shape': (1, 4), }";
        let shape = parse_npy_shape(header).unwrap();
        assert_eq!(shape, vec![1, 4]);
    }

    #[test]
    fn test_parse_npy_f32_2d() {
        // Construir .npy manualmente: 2 rows, 3 cols, float32
        let mut data = Vec::new();
        // Magic
        data.extend_from_slice(b"\x93NUMPY");
        // Version 1.0
        data.push(1);
        data.push(0);
        // Header
        let header = b"{'descr': '<f4', 'fortran_order': False, 'shape': (2, 3), }          \n";
        let header_len = header.len() as u16;
        data.extend_from_slice(&header_len.to_le_bytes());
        data.extend_from_slice(header);
        // Data: 6 float32s
        for v in &[1.0f32, 2.0, 3.0, 4.0, 5.0, 6.0] {
            data.extend_from_slice(&v.to_le_bytes());
        }

        let result = parse_npy_f32_2d(&data).unwrap();
        assert_eq!(result.len(), 2);
        assert_eq!(result[0], vec![1.0, 2.0, 3.0]);
        assert_eq!(result[1], vec![4.0, 5.0, 6.0]);
    }
}
