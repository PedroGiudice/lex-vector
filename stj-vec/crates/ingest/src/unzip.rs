//! Extracao de ZIPs de integras do STJ.
//!
//! Cada ZIP de integras contem arquivos TXT nomeados por `seqDocumento`.
//! Este modulo extrai os TXTs para subdiretorios no formato que o scanner
//! espera (ex: `integras/202202/000001.txt`).

use std::path::Path;

use anyhow::{Context, Result};
use tracing::{debug, info, warn};

/// Resumo de uma extracao de ZIP.
#[derive(Debug, Default)]
pub struct ExtractSummary {
    /// Quantidade de arquivos extraidos
    pub extracted: usize,
    /// Quantidade de arquivos pulados (ja existiam)
    pub skipped: usize,
}

/// Extrai TXTs de um ZIP de integras para o diretorio destino.
///
/// O `source_name` e usado como nome do subdiretorio (ex: "202202").
/// Arquivos ja existentes no destino sao pulados.
///
/// # Argumentos
///
/// * `zip_path` - Caminho do arquivo ZIP
/// * `dest_dir` - Diretorio base das integras (ex: `/home/opc/juridico-data/stj/integras/textos`)
/// * `source_name` - Nome do source/subdiretorio (ex: "202202")
pub fn extract_integras_zip(
    zip_path: &Path,
    dest_dir: &Path,
    source_name: &str,
) -> Result<ExtractSummary> {
    let mut summary = ExtractSummary::default();
    let target_dir = dest_dir.join(source_name);

    std::fs::create_dir_all(&target_dir)
        .with_context(|| format!("falha ao criar diretorio {}", target_dir.display()))?;

    let file = std::fs::File::open(zip_path)
        .with_context(|| format!("falha ao abrir ZIP {}", zip_path.display()))?;
    let mut archive = zip::ZipArchive::new(file)
        .with_context(|| format!("falha ao ler ZIP {}", zip_path.display()))?;

    info!(
        zip = %zip_path.display(),
        entries = archive.len(),
        dest = %target_dir.display(),
        "extraindo ZIP de integras"
    );

    for i in 0..archive.len() {
        let mut entry = archive
            .by_index(i)
            .with_context(|| format!("falha ao ler entrada {} do ZIP", i))?;

        // Pular diretorios
        if entry.is_dir() {
            continue;
        }

        let entry_name = entry.name().to_string();

        // Apenas arquivos TXT
        if !entry_name.to_lowercase().ends_with(".txt") {
            debug!(entry = %entry_name, "pulando entrada nao-TXT");
            continue;
        }

        // Extrair apenas o nome do arquivo (sem path interno do ZIP)
        let filename = Path::new(&entry_name)
            .file_name()
            .map(|f| f.to_string_lossy().into_owned())
            .unwrap_or_else(|| entry_name.clone());

        let dest_path = target_dir.join(&filename);

        // Pular se ja existe
        if dest_path.exists() {
            summary.skipped += 1;
            continue;
        }

        let mut outfile = std::fs::File::create(&dest_path)
            .with_context(|| format!("falha ao criar {}", dest_path.display()))?;
        std::io::copy(&mut entry, &mut outfile)
            .with_context(|| format!("falha ao extrair {}", filename))?;

        summary.extracted += 1;
    }

    info!(
        source = source_name,
        extracted = summary.extracted,
        skipped = summary.skipped,
        "extracao concluida"
    );

    Ok(summary)
}

/// Extrai o nome do source (YYYYMM) de um nome de arquivo ZIP.
///
/// Ex: "202202.zip" -> Some("202202"), "integras_202202.zip" -> None
pub fn source_name_from_zip(filename: &str) -> Option<String> {
    let stem = Path::new(filename)
        .file_stem()?
        .to_str()?;
    // Validar que e um YYYYMM (6 digitos) ou YYYYMMDD (8 digitos)
    if (stem.len() == 6 || stem.len() == 8) && stem.chars().all(|c| c.is_ascii_digit()) {
        Some(stem.to_string())
    } else {
        None
    }
}

/// Processa todos os ZIPs nao-extraidos no diretorio de downloads.
///
/// Para cada ZIP encontrado em `downloads_dir/integras/`, extrai os TXTs
/// para `integras_dir/{YYYYMM}/`. Tambem move metadados JSON para `metadata_dir`.
pub fn extract_all_pending_zips(
    downloads_dir: &Path,
    integras_dir: &Path,
    metadata_dir: &Path,
) -> Result<ExtractSummary> {
    let mut total = ExtractSummary::default();
    let dl_integras = downloads_dir.join("integras");

    if !dl_integras.is_dir() {
        info!(dir = %dl_integras.display(), "diretorio de downloads de integras nao existe");
        return Ok(total);
    }

    let entries: Vec<_> = std::fs::read_dir(&dl_integras)?
        .filter_map(|e| e.ok())
        .collect();

    for entry in &entries {
        let path = entry.path();
        let filename = path
            .file_name()
            .map(|f| f.to_string_lossy().into_owned())
            .unwrap_or_default();

        // Processar ZIPs
        if filename.to_lowercase().ends_with(".zip") {
            if let Some(source_name) = source_name_from_zip(&filename) {
                // Verificar se ja foi extraido (diretorio existe com arquivos)
                let target = integras_dir.join(&source_name);
                if target.is_dir() {
                    let has_files = std::fs::read_dir(&target)?
                        .filter_map(|e| e.ok())
                        .any(|e| {
                            e.path()
                                .extension()
                                .is_some_and(|ext| ext.eq_ignore_ascii_case("txt"))
                        });
                    if has_files {
                        debug!(source = %source_name, "ja extraido, pulando");
                        total.skipped += 1;
                        continue;
                    }
                }

                match extract_integras_zip(&path, integras_dir, &source_name) {
                    Ok(summary) => {
                        total.extracted += summary.extracted;
                        total.skipped += summary.skipped;
                    }
                    Err(e) => {
                        warn!(zip = %filename, error = %e, "falha ao extrair ZIP");
                    }
                }
            } else {
                debug!(filename = %filename, "ZIP com nome nao reconhecido, pulando");
            }
        }

        // Copiar metadados JSON para metadata_dir
        if filename.starts_with("metadados") && filename.ends_with(".json") {
            let dest = metadata_dir.join(&filename);
            if !dest.exists() {
                std::fs::create_dir_all(metadata_dir)
                    .with_context(|| {
                        format!("falha ao criar diretorio {}", metadata_dir.display())
                    })?;
                std::fs::copy(&path, &dest).with_context(|| {
                    format!(
                        "falha ao copiar metadados {} -> {}",
                        path.display(),
                        dest.display()
                    )
                })?;
                info!(file = %filename, "metadados copiados para metadata_dir");
            }
        }
    }

    Ok(total)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::tempdir;

    #[test]
    fn test_source_name_from_zip() {
        assert_eq!(
            source_name_from_zip("202202.zip"),
            Some("202202".into())
        );
        assert_eq!(
            source_name_from_zip("20220315.zip"),
            Some("20220315".into())
        );
        assert_eq!(source_name_from_zip("integras.zip"), None);
        assert_eq!(source_name_from_zip("abc.zip"), None);
        assert_eq!(source_name_from_zip("12345.zip"), None);
    }

    #[test]
    fn test_extract_integras_zip() {
        let dir = tempdir().unwrap();
        let zip_path = dir.path().join("202203.zip");
        let dest_dir = dir.path().join("integras");

        // Criar ZIP de teste
        {
            let file = std::fs::File::create(&zip_path).unwrap();
            let mut zip_writer = zip::ZipWriter::new(file);
            let options = zip::write::SimpleFileOptions::default()
                .compression_method(zip::CompressionMethod::Stored);

            zip_writer.start_file("000001.txt", options).unwrap();
            zip_writer.write_all(b"Conteudo do documento 1").unwrap();

            zip_writer.start_file("000002.txt", options).unwrap();
            zip_writer.write_all(b"Conteudo do documento 2").unwrap();

            zip_writer.start_file("README.md", options).unwrap();
            zip_writer.write_all(b"Ignorar este arquivo").unwrap();

            zip_writer.finish().unwrap();
        }

        let summary = extract_integras_zip(&zip_path, &dest_dir, "202203").unwrap();
        assert_eq!(summary.extracted, 2);
        assert_eq!(summary.skipped, 0);

        // Verificar arquivos extraidos
        assert!(dest_dir.join("202203/000001.txt").exists());
        assert!(dest_dir.join("202203/000002.txt").exists());
        assert!(!dest_dir.join("202203/README.md").exists());

        // Re-extrair deve pular
        let summary2 = extract_integras_zip(&zip_path, &dest_dir, "202203").unwrap();
        assert_eq!(summary2.extracted, 0);
        assert_eq!(summary2.skipped, 2);
    }
}
