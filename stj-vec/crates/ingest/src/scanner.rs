use anyhow::{Context, Result};
use std::path::{Path, PathBuf};

use stj_vec_core::storage::Storage;

/// Diretorio-fonte de integras do STJ
#[derive(Debug, Clone)]
pub struct SourceDir {
    pub name: String,
    pub path: PathBuf,
    pub file_count: usize,
}

/// Varre subdiretorios de integras, contando .txt em cada um.
pub fn scan_integras_dir(path: &Path) -> Result<Vec<SourceDir>> {
    let entries = std::fs::read_dir(path)
        .with_context(|| format!("falha ao ler diretorio {}", path.display()))?;

    let mut sources = Vec::new();
    for entry in entries {
        let entry = entry?;
        if !entry.file_type()?.is_dir() {
            continue;
        }
        let name = entry.file_name().to_string_lossy().into_owned();
        let dir_path = entry.path();
        let file_count = std::fs::read_dir(&dir_path)?
            .filter_map(|e| e.ok())
            .filter(|e| {
                e.path()
                    .extension()
                    .is_some_and(|ext| ext.eq_ignore_ascii_case("txt"))
            })
            .count();

        sources.push(SourceDir {
            name,
            path: dir_path,
            file_count,
        });
    }

    sources.sort_by(|a, b| a.name.cmp(&b.name));
    Ok(sources)
}

/// Retorna apenas sources sem entrada no ingest_log.
pub fn find_new_sources(sources: &[SourceDir], storage: &Storage) -> Result<Vec<SourceDir>> {
    let mut new = Vec::new();
    for s in sources {
        if storage.get_ingest_status(&s.name)?.is_none() {
            new.push(s.clone());
        }
    }
    Ok(new)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::tempdir;

    #[test]
    fn test_scan_finds_subdirs() {
        let dir = tempdir().unwrap();
        fs::create_dir_all(dir.path().join("202203")).unwrap();
        fs::write(dir.path().join("202203/12345.txt"), "content").unwrap();
        fs::create_dir_all(dir.path().join("20220502")).unwrap();
        fs::write(dir.path().join("20220502/67890.txt"), "content").unwrap();

        let sources = scan_integras_dir(dir.path()).unwrap();
        assert_eq!(sources.len(), 2);
        assert_eq!(sources[0].name, "202203");
        assert_eq!(sources[0].file_count, 1);
    }

    #[test]
    fn test_scan_counts_files() {
        let dir = tempdir().unwrap();
        fs::create_dir_all(dir.path().join("202203")).unwrap();
        for i in 0..5 {
            fs::write(dir.path().join(format!("202203/{i}.txt")), "content").unwrap();
        }
        let sources = scan_integras_dir(dir.path()).unwrap();
        assert_eq!(sources[0].file_count, 5);
    }

    #[test]
    fn test_scan_ignores_files() {
        let dir = tempdir().unwrap();
        fs::create_dir_all(dir.path().join("202203")).unwrap();
        fs::write(dir.path().join("README.txt"), "not a source").unwrap();
        let sources = scan_integras_dir(dir.path()).unwrap();
        assert_eq!(sources.len(), 1);
    }
}
