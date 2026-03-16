//! Enriquecimento de documentos com dados dos espelhos de acordaos do STJ.
//!
//! Cruza JSONs de espelhos (CKAN) com a tabela `documents` no SQLite,
//! preenchendo campos `classe`, `orgao_julgador`, `data_julgamento` e `ministro`
//! quando estiverem vazios.

use std::path::Path;

use anyhow::{Context, Result};
use serde::Deserialize;
use tracing::{debug, info, warn};

use stj_vec_core::storage::Storage;

/// Espelho de acordao deserializado do JSON CKAN.
///
/// Apenas os campos necessarios para o enriquecimento sao obrigatorios;
/// os demais sao opcionais para tolerar variacao entre orgaos.
#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct EspelhoAcordao {
    /// ID interno do espelho (ex: "000815399")
    pub id: String,
    /// Numero do processo -- apenas digitos (ex: "1424080")
    pub numero_processo: String,
    /// Sigla da classe processual (ex: "EDcl no AgInt nos EDcl no REsp")
    pub sigla_classe: Option<String>,
    /// Nome do orgao julgador (ex: "PRIMEIRA TURMA")
    pub nome_orgao_julgador: Option<String>,
    /// Ministro relator (ex: "REGINA HELENA COSTA")
    pub ministro_relator: Option<String>,
    /// Data da decisao no formato YYYYMMDD (ex: "20220523")
    pub data_decisao: Option<String>,
}

/// Resumo da operacao de enriquecimento.
#[derive(Debug, Default)]
pub struct EnrichSummary {
    /// Quantidade de arquivos JSON processados
    pub files_processed: usize,
    /// Quantidade de espelhos carregados dos JSONs
    pub espelhos_loaded: usize,
    /// Quantidade de espelhos que encontraram match no banco
    pub matched: usize,
    /// Quantidade de documentos efetivamente atualizados
    pub updated: usize,
    /// Quantidade de espelhos sem match no banco
    pub unmatched: usize,
}

/// Extrai apenas digitos de uma string de processo.
///
/// Usado para normalizar tanto o campo `processo` de `documents` quanto
/// o `numeroProcesso` dos espelhos, permitindo join por igualdade.
///
/// # Exemplos
///
/// ```
/// use stj_vec_ingest::enrich::normalize_processo;
///
/// assert_eq!(normalize_processo("REsp 1.424.080 - RS"), "1424080");
/// assert_eq!(normalize_processo("AREsp 2292471"), "2292471");
/// assert_eq!(normalize_processo("1424080"), "1424080");
/// assert_eq!(normalize_processo(""), "");
/// ```
pub fn normalize_processo(raw: &str) -> String {
    raw.chars().filter(|c| c.is_ascii_digit()).collect()
}

/// Converte data no formato YYYYMMDD para YYYY-MM-DD.
///
/// Retorna `None` se o input nao tiver exatamente 8 caracteres.
fn format_data_decisao(raw: &str) -> Option<String> {
    if raw.len() != 8 {
        return None;
    }
    let (year, rest) = raw.split_at(4);
    let (month, day) = rest.split_at(2);
    Some(format!("{year}-{month}-{day}"))
}

/// Carrega espelhos de acordaos de um arquivo JSON.
///
/// O JSON deve ser um array de objetos conforme schema CKAN do STJ.
pub fn load_espelhos(path: &Path) -> Result<Vec<EspelhoAcordao>> {
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("falha ao ler espelho {}", path.display()))?;
    let espelhos: Vec<EspelhoAcordao> = serde_json::from_str(&content)
        .with_context(|| format!("falha ao parsear espelho {}", path.display()))?;
    Ok(espelhos)
}

/// Enriquece documentos no banco com dados de todos os JSONs de espelhos
/// encontrados no diretorio informado (busca recursiva por `*.json`).
///
/// O diretorio esperado tem estrutura:
/// ```text
/// espelhos/
///   primeira-turma/
///     20220531.json
///   segunda-turma/
///     20220531.json
/// ```
pub fn enrich_from_espelhos(storage: &Storage, espelhos_dir: &Path) -> Result<EnrichSummary> {
    let mut summary = EnrichSummary::default();

    let json_files = collect_json_files(espelhos_dir)?;
    if json_files.is_empty() {
        warn!(dir = %espelhos_dir.display(), "nenhum JSON de espelho encontrado");
        return Ok(summary);
    }

    info!(files = json_files.len(), dir = %espelhos_dir.display(), "iniciando enriquecimento");

    for path in &json_files {
        let espelhos = match load_espelhos(path) {
            Ok(e) => e,
            Err(err) => {
                warn!(file = %path.display(), %err, "falha ao carregar espelho, pulando");
                continue;
            }
        };

        summary.files_processed += 1;
        summary.espelhos_loaded += espelhos.len();

        for esp in &espelhos {
            let digits = normalize_processo(&esp.numero_processo);
            if digits.is_empty() {
                continue;
            }

            let docs = storage.find_documents_by_processo_digits(&digits)?;
            if docs.is_empty() {
                summary.unmatched += 1;
                debug!(processo = %digits, espelho_id = %esp.id, "sem match no banco");
                continue;
            }

            summary.matched += 1;

            let data_formatada = esp.data_decisao.as_deref().and_then(format_data_decisao);

            for (doc_id, _, _, _, _, _) in &docs {
                let updated = storage.enrich_document(
                    doc_id,
                    esp.sigla_classe.as_deref(),
                    esp.nome_orgao_julgador.as_deref(),
                    data_formatada.as_deref(),
                    esp.ministro_relator.as_deref(),
                )?;
                if updated {
                    summary.updated += 1;
                }
            }
        }
    }

    info!(
        files = summary.files_processed,
        espelhos = summary.espelhos_loaded,
        matched = summary.matched,
        updated = summary.updated,
        unmatched = summary.unmatched,
        "enriquecimento concluido"
    );

    Ok(summary)
}

/// Coleta recursivamente todos os arquivos `.json` dentro de um diretorio.
fn collect_json_files(dir: &Path) -> Result<Vec<std::path::PathBuf>> {
    let mut files = Vec::new();
    if !dir.is_dir() {
        anyhow::bail!("diretorio de espelhos nao encontrado: {}", dir.display());
    }
    collect_json_recursive(dir, &mut files)?;
    files.sort();
    Ok(files)
}

fn collect_json_recursive(dir: &Path, out: &mut Vec<std::path::PathBuf>) -> Result<()> {
    for entry in std::fs::read_dir(dir)
        .with_context(|| format!("falha ao ler diretorio {}", dir.display()))?
    {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir() {
            collect_json_recursive(&path, out)?;
        } else if path
            .extension()
            .is_some_and(|ext| ext.eq_ignore_ascii_case("json"))
        {
            // Ignorar manifest.json
            if path.file_name().is_some_and(|n| n != "manifest.json") {
                out.push(path);
            }
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use stj_vec_core::types::Document;
    use tempfile::tempdir;

    // === normalize_processo ===

    #[test]
    fn test_normalize_processo_digits_only() {
        assert_eq!(normalize_processo("1424080"), "1424080");
    }

    #[test]
    fn test_normalize_processo_with_class_prefix() {
        assert_eq!(normalize_processo("AREsp 2292471"), "2292471");
    }

    #[test]
    fn test_normalize_processo_with_dots_and_dashes() {
        assert_eq!(normalize_processo("REsp 1.424.080 - RS"), "1424080");
    }

    #[test]
    fn test_normalize_processo_with_registro() {
        // Quando o campo processo inclui numero de registro, todos os digitos sao extraidos.
        // Na pratica o campo `processo` no banco raramente inclui o registro entre parenteses.
        // Se incluir, o match nao acontece (digitos divergem), o que e seguro:
        // prefere falso negativo a falso positivo.
        assert_eq!(
            normalize_processo("REsp 1424080 (2013/0404391-1)"),
            "1424080201304043911"
        );
    }

    #[test]
    fn test_normalize_processo_empty() {
        assert_eq!(normalize_processo(""), "");
    }

    #[test]
    fn test_normalize_processo_no_digits() {
        assert_eq!(normalize_processo("abc def"), "");
    }

    // === format_data_decisao ===

    #[test]
    fn test_format_data_decisao_valid() {
        assert_eq!(format_data_decisao("20220523"), Some("2022-05-23".into()));
    }

    #[test]
    fn test_format_data_decisao_invalid_length() {
        assert_eq!(format_data_decisao("2022052"), None);
        assert_eq!(format_data_decisao("202205233"), None);
    }

    // === load_espelhos ===

    #[test]
    fn test_load_espelhos_from_fixture() {
        let fixture_path =
            Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/espelho_sample.json");
        let espelhos = load_espelhos(&fixture_path).expect("falha ao carregar fixture");

        assert_eq!(espelhos.len(), 3);

        assert_eq!(espelhos[0].id, "000815399");
        assert_eq!(espelhos[0].numero_processo, "1424080");
        assert_eq!(
            espelhos[0].sigla_classe.as_deref(),
            Some("EDcl no AgInt nos EDcl no REsp")
        );
        assert_eq!(
            espelhos[0].nome_orgao_julgador.as_deref(),
            Some("PRIMEIRA TURMA")
        );
        assert_eq!(
            espelhos[0].ministro_relator.as_deref(),
            Some("REGINA HELENA COSTA")
        );
        assert_eq!(espelhos[0].data_decisao.as_deref(), Some("20220523"));

        assert_eq!(espelhos[1].numero_processo, "2292471");
        assert_eq!(espelhos[1].sigla_classe.as_deref(), Some("AREsp"));
    }

    #[test]
    fn test_load_espelhos_invalid_path() {
        let result = load_espelhos(Path::new("/nonexistent/path.json"));
        assert!(result.is_err());
    }

    // === enrich_from_espelhos (integration) ===

    #[test]
    fn test_enrich_from_espelhos_integration() {
        let dir = tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();

        // Inserir documentos que correspondem aos espelhos da fixture
        let docs = vec![
            Document {
                id: "doc1".into(),
                processo: Some("REsp 1424080".into()),
                classe: None,
                ministro: None,
                orgao_julgador: None,
                data_publicacao: Some("2022-05-25".into()),
                data_julgamento: None,
                assuntos: None,
                teor: None,
                tipo: Some("ACORDAO".into()),
                chunk_count: 0,
                source_file: Some("202205".into()),
            },
            Document {
                id: "doc2".into(),
                processo: Some("AREsp 2292471".into()),
                classe: None,
                ministro: Some("EXISTENTE".into()), // ja tem ministro
                orgao_julgador: None,
                data_publicacao: Some("2023-06-10".into()),
                data_julgamento: None,
                assuntos: None,
                teor: None,
                tipo: None,
                chunk_count: 0,
                source_file: Some("202306".into()),
            },
            Document {
                id: "doc3".into(),
                processo: Some("HC 12345".into()), // nao tem match nos espelhos
                classe: None,
                ministro: None,
                orgao_julgador: None,
                data_publicacao: None,
                data_julgamento: None,
                assuntos: None,
                teor: None,
                tipo: None,
                chunk_count: 0,
                source_file: Some("202301".into()),
            },
        ];

        for doc in &docs {
            storage.insert_document(doc).unwrap();
        }

        // Montar diretorio de espelhos com o fixture
        let espelhos_dir = dir.path().join("espelhos");
        let turma_dir = espelhos_dir.join("primeira-turma");
        fs::create_dir_all(&turma_dir).unwrap();

        let fixture_path =
            Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/espelho_sample.json");
        fs::copy(&fixture_path, turma_dir.join("20220531.json")).unwrap();

        // Executar enrich
        let summary = enrich_from_espelhos(&storage, &espelhos_dir).unwrap();

        assert_eq!(summary.files_processed, 1);
        assert_eq!(summary.espelhos_loaded, 3);
        assert_eq!(summary.matched, 2); // 1424080 e 2292471
        assert_eq!(summary.unmatched, 1); // 9999999 nao tem match

        // Verificar doc1: todos os campos devem ter sido preenchidos
        let doc1 = storage.get_document("doc1").unwrap().unwrap();
        assert_eq!(
            doc1.classe.as_deref(),
            Some("EDcl no AgInt nos EDcl no REsp")
        );
        assert_eq!(doc1.orgao_julgador.as_deref(), Some("PRIMEIRA TURMA"));
        assert_eq!(doc1.data_julgamento.as_deref(), Some("2022-05-23"));
        assert_eq!(doc1.ministro.as_deref(), Some("REGINA HELENA COSTA"));

        // Verificar doc2: ministro ja existia como "EXISTENTE", nao deve ser sobrescrito
        let doc2 = storage.get_document("doc2").unwrap().unwrap();
        assert_eq!(doc2.classe.as_deref(), Some("AREsp"));
        assert_eq!(doc2.orgao_julgador.as_deref(), Some("SEGUNDA TURMA"));
        assert_eq!(doc2.ministro.as_deref(), Some("EXISTENTE")); // preservado!
        assert_eq!(doc2.data_julgamento.as_deref(), Some("2023-06-05"));

        // Verificar doc3: nao deve ter sido tocado
        let doc3 = storage.get_document("doc3").unwrap().unwrap();
        assert!(doc3.classe.is_none());
        assert!(doc3.orgao_julgador.is_none());
    }

    #[test]
    fn test_enrich_idempotent() {
        let dir = tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();

        let doc = Document {
            id: "doc1".into(),
            processo: Some("REsp 1424080".into()),
            classe: None,
            ministro: None,
            orgao_julgador: None,
            data_publicacao: None,
            data_julgamento: None,
            assuntos: None,
            teor: None,
            tipo: None,
            chunk_count: 0,
            source_file: None,
        };
        storage.insert_document(&doc).unwrap();

        let espelhos_dir = dir.path().join("espelhos");
        let turma_dir = espelhos_dir.join("primeira-turma");
        fs::create_dir_all(&turma_dir).unwrap();
        let fixture_path =
            Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/espelho_sample.json");
        fs::copy(&fixture_path, turma_dir.join("20220531.json")).unwrap();

        // Primeira execucao
        let s1 = enrich_from_espelhos(&storage, &espelhos_dir).unwrap();
        assert_eq!(s1.updated, 1);

        // Segunda execucao -- nao deve atualizar nada
        let s2 = enrich_from_espelhos(&storage, &espelhos_dir).unwrap();
        assert_eq!(s2.updated, 0);
    }

    // === Storage enrich_document ===

    #[test]
    fn test_enrich_document_selective() {
        let dir = tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();

        let doc = Document {
            id: "d1".into(),
            processo: Some("REsp 123".into()),
            classe: Some("REsp".into()), // ja preenchido
            ministro: None,              // vazio
            orgao_julgador: None,        // vazio
            data_publicacao: None,
            data_julgamento: None, // vazio
            assuntos: None,
            teor: None,
            tipo: None,
            chunk_count: 0,
            source_file: None,
        };
        storage.insert_document(&doc).unwrap();

        let updated = storage
            .enrich_document(
                "d1",
                Some("NOVA_CLASSE"),
                Some("TURMA"),
                Some("2024-01-01"),
                Some("MINISTRO"),
            )
            .unwrap();
        assert!(updated);

        let fetched = storage.get_document("d1").unwrap().unwrap();
        // classe ja existia -- deve manter o original
        assert_eq!(fetched.classe.as_deref(), Some("REsp"));
        // campos vazios -- devem ter sido preenchidos
        assert_eq!(fetched.orgao_julgador.as_deref(), Some("TURMA"));
        assert_eq!(fetched.data_julgamento.as_deref(), Some("2024-01-01"));
        assert_eq!(fetched.ministro.as_deref(), Some("MINISTRO"));
    }

    #[test]
    fn test_enrich_document_all_filled_no_update() {
        let dir = tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();

        let doc = Document {
            id: "d1".into(),
            processo: Some("REsp 123".into()),
            classe: Some("REsp".into()),
            ministro: Some("NANCY".into()),
            orgao_julgador: Some("TERCEIRA TURMA".into()),
            data_publicacao: None,
            data_julgamento: Some("2024-01-01".into()),
            assuntos: None,
            teor: None,
            tipo: None,
            chunk_count: 0,
            source_file: None,
        };
        storage.insert_document(&doc).unwrap();

        // Todos os 4 campos ja preenchidos -- WHERE nao casa
        let updated = storage
            .enrich_document("d1", Some("X"), Some("Y"), Some("Z"), Some("W"))
            .unwrap();
        assert!(!updated);
    }
}
