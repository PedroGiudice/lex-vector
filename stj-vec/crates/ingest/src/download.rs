//! Download de resources do CKAN (integras e espelhos do STJ).
//!
//! Suporta download incremental via manifest JSON por diretorio,
//! progress bars com indicatif e retry com backoff exponencial.

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::time::Duration;

use anyhow::{Context, Result};
use futures_util::StreamExt;
use indicatif::{MultiProgress, ProgressBar, ProgressStyle};
use serde::{Deserialize, Serialize};
use tracing::{debug, info, warn};

use stj_vec_core::config::CkanConfig;

// ---------------------------------------------------------------------------
// Tipos CKAN
// ---------------------------------------------------------------------------

/// Resposta da API CKAN `/api/3/action/package_show`.
#[derive(Debug, Deserialize)]
pub struct CkanPackageResponse {
    pub success: bool,
    pub result: CkanPackage,
}

/// Metadados de um dataset CKAN.
#[derive(Debug, Deserialize)]
pub struct CkanPackage {
    pub id: String,
    pub name: String,
    pub resources: Vec<CkanResource>,
}

/// Resource individual dentro de um dataset CKAN.
#[derive(Debug, Clone, Deserialize)]
pub struct CkanResource {
    pub id: String,
    pub name: String,
    pub url: String,
    pub format: String,
    #[serde(default)]
    pub size: Option<u64>,
}

// ---------------------------------------------------------------------------
// Manifest (tracking incremental)
// ---------------------------------------------------------------------------

/// Manifest de downloads realizados. Persistido como JSON em cada diretorio.
#[derive(Debug, Default, Serialize, Deserialize)]
pub struct DownloadManifest {
    pub downloaded: HashMap<String, DownloadedResource>,
}

/// Registro de um resource ja baixado.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DownloadedResource {
    pub resource_id: String,
    pub name: String,
    pub downloaded_at: String,
    pub size: u64,
    pub path: String,
}

impl DownloadManifest {
    /// Carrega manifest de um arquivo JSON. Retorna vazio se nao existir.
    pub fn load(path: &Path) -> Result<Self> {
        if !path.exists() {
            return Ok(Self::default());
        }
        let content = std::fs::read_to_string(path)
            .with_context(|| format!("falha ao ler manifest {}", path.display()))?;
        let manifest: Self = serde_json::from_str(&content)
            .with_context(|| format!("falha ao parsear manifest {}", path.display()))?;
        Ok(manifest)
    }

    /// Salva manifest como JSON formatado.
    pub fn save(&self, path: &Path) -> Result<()> {
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)
                .with_context(|| format!("falha ao criar diretorio {}", parent.display()))?;
        }
        let content = serde_json::to_string_pretty(self)
            .context("falha ao serializar manifest")?;
        std::fs::write(path, content)
            .with_context(|| format!("falha ao escrever manifest {}", path.display()))?;
        Ok(())
    }

    /// Verifica se um resource ja foi baixado (por resource_id CKAN).
    pub fn is_downloaded(&self, resource_id: &str) -> bool {
        self.downloaded.contains_key(resource_id)
    }

    /// Registra um download no manifest.
    pub fn register(&mut self, resource: &CkanResource, path: &Path, size: u64) {
        let now = chrono::Utc::now().to_rfc3339();
        self.downloaded.insert(
            resource.id.clone(),
            DownloadedResource {
                resource_id: resource.id.clone(),
                name: resource.name.clone(),
                downloaded_at: now,
                size,
                path: path.to_string_lossy().into_owned(),
            },
        );
    }
}

// ---------------------------------------------------------------------------
// Resumo de download
// ---------------------------------------------------------------------------

/// Resumo da operacao de download.
#[derive(Debug, Default)]
pub struct DownloadSummary {
    /// Resources ja existentes no manifest (pulados)
    pub skipped: usize,
    /// Resources baixados com sucesso
    pub downloaded: usize,
    /// Resources que falharam apos retries
    pub failed: usize,
    /// Bytes totais baixados
    pub bytes_downloaded: u64,
}

// ---------------------------------------------------------------------------
// Fonte de download (enum para CLI)
// ---------------------------------------------------------------------------

/// Fonte de dados para download.
#[derive(Debug, Clone, clap::ValueEnum)]
pub enum DownloadSource {
    /// Integras de decisoes (ZIPs + JSONs de metadados)
    Integras,
    /// Espelhos de acordaos (JSONs por orgao)
    Espelhos,
    /// Todas as fontes
    All,
}

// ---------------------------------------------------------------------------
// Funcoes de API CKAN
// ---------------------------------------------------------------------------

/// Lista resources de um dataset CKAN.
pub async fn list_resources(
    client: &reqwest::Client,
    base_url: &str,
    dataset_id: &str,
) -> Result<Vec<CkanResource>> {
    let url = format!("{}/api/3/action/package_show?id={}", base_url, dataset_id);
    debug!(url = %url, "consultando CKAN API");

    let response: CkanPackageResponse = client
        .get(&url)
        .send()
        .await
        .with_context(|| format!("falha ao consultar CKAN: {}", url))?
        .error_for_status()
        .with_context(|| format!("CKAN retornou erro HTTP para {}", dataset_id))?
        .json()
        .await
        .with_context(|| format!("falha ao parsear resposta CKAN para {}", dataset_id))?;

    if !response.success {
        anyhow::bail!("CKAN retornou success=false para dataset {}", dataset_id);
    }

    info!(
        dataset = dataset_id,
        resources = response.result.resources.len(),
        "resources listados"
    );

    Ok(response.result.resources)
}

/// Baixa um resource individual para o diretorio destino.
///
/// Retorna o caminho do arquivo baixado e o tamanho em bytes.
/// Suporta progress bar e retry com backoff exponencial.
pub async fn download_resource(
    client: &reqwest::Client,
    resource: &CkanResource,
    dest_dir: &Path,
    pb: Option<&ProgressBar>,
) -> Result<(PathBuf, u64)> {
    std::fs::create_dir_all(dest_dir)
        .with_context(|| format!("falha ao criar diretorio {}", dest_dir.display()))?;

    // Nome do arquivo: usar o name do resource, sanitizando caracteres problemáticos
    let filename = sanitize_filename(&resource.name);
    let dest_path = dest_dir.join(&filename);

    let max_retries = 3;
    let mut last_error = None;

    for attempt in 0..max_retries {
        if attempt > 0 {
            let delay = Duration::from_secs(2u64.pow(attempt as u32));
            warn!(
                attempt = attempt + 1,
                delay_secs = delay.as_secs(),
                resource = %resource.name,
                "retentando download"
            );
            tokio::time::sleep(delay).await;
        }

        match download_with_progress(client, &resource.url, &dest_path, pb).await {
            Ok(size) => return Ok((dest_path, size)),
            Err(e) => {
                warn!(
                    attempt = attempt + 1,
                    resource = %resource.name,
                    error = %e,
                    "falha no download"
                );
                last_error = Some(e);
            }
        }
    }

    Err(last_error
        .expect("deve ter pelo menos um erro")
        .context(format!(
            "falha apos {} tentativas: {}",
            max_retries, resource.name
        )))
}

/// Download com streaming e progress bar.
async fn download_with_progress(
    client: &reqwest::Client,
    url: &str,
    dest: &Path,
    pb: Option<&ProgressBar>,
) -> Result<u64> {
    let response = client
        .get(url)
        .send()
        .await
        .with_context(|| format!("falha ao conectar: {}", url))?
        .error_for_status()
        .with_context(|| format!("HTTP erro ao baixar: {}", url))?;

    let total_size = response.content_length().unwrap_or(0);
    if let Some(pb) = pb {
        if total_size > 0 {
            pb.set_length(total_size);
        }
    }

    let mut stream = response.bytes_stream();
    let mut file = tokio::fs::File::create(dest)
        .await
        .with_context(|| format!("falha ao criar arquivo {}", dest.display()))?;
    let mut downloaded: u64 = 0;

    use tokio::io::AsyncWriteExt;
    while let Some(chunk) = stream.next().await {
        let chunk = chunk.with_context(|| format!("erro ao receber dados de {}", url))?;
        file.write_all(&chunk).await
            .with_context(|| format!("falha ao escrever em {}", dest.display()))?;
        downloaded += chunk.len() as u64;
        if let Some(pb) = pb {
            pb.set_position(downloaded);
        }
    }

    file.flush().await?;

    if let Some(pb) = pb {
        pb.set_position(downloaded);
    }

    Ok(downloaded)
}

// ---------------------------------------------------------------------------
// Download de espelhos
// ---------------------------------------------------------------------------

/// Baixa todos os JSONs de espelhos novos dos 10 datasets de orgaos.
///
/// Para cada dataset, lista resources via CKAN API e baixa os que nao
/// estao no manifest. Os JSONs sao salvos em `espelhos_dir/{orgao}/`.
pub async fn download_espelhos(
    client: &reqwest::Client,
    config: &CkanConfig,
    espelhos_dir: &Path,
    limit: Option<usize>,
) -> Result<DownloadSummary> {
    let mut summary = DownloadSummary::default();
    let manifest_path = espelhos_dir.join("manifest.json");
    let mut manifest = DownloadManifest::load(&manifest_path)?;

    let mp = MultiProgress::new();
    let style = ProgressStyle::default_bar()
        .template("[{elapsed_precise}] {bar:40} {bytes}/{total_bytes} {msg}")
        .expect("template valido");

    for dataset_id in &config.espelhos_datasets {
        // Extrair nome do orgao do dataset ID (ex: "espelhos-de-acordaos-primeira-turma" -> "primeira-turma")
        let orgao = dataset_id
            .strip_prefix("espelhos-de-acordaos-")
            .unwrap_or(dataset_id);
        let orgao_dir = espelhos_dir.join(orgao);

        let resources = match list_resources(client, &config.base_url, dataset_id).await {
            Ok(r) => r,
            Err(e) => {
                warn!(dataset = %dataset_id, error = %e, "falha ao listar resources, pulando dataset");
                continue;
            }
        };

        let mut downloaded_this_dataset = 0;

        for resource in &resources {
            // Verificar limit global
            if let Some(lim) = limit {
                if summary.downloaded >= lim {
                    info!(limit = lim, "limite de downloads atingido");
                    manifest.save(&manifest_path)?;
                    return Ok(summary);
                }
            }

            // Pular se ja baixado
            if manifest.is_downloaded(&resource.id) {
                summary.skipped += 1;
                continue;
            }

            // Pular ZIPs historicos (sao grandes e contem dados duplicados dos JSONs)
            if resource.format.eq_ignore_ascii_case("zip") {
                debug!(resource = %resource.name, "pulando ZIP historico de espelho");
                summary.skipped += 1;
                continue;
            }

            let pb = mp.add(ProgressBar::new(0));
            pb.set_style(style.clone());
            pb.set_message(format!("{}/{}", orgao, resource.name));

            match download_resource(client, resource, &orgao_dir, Some(&pb)).await {
                Ok((path, size)) => {
                    manifest.register(resource, &path, size);
                    summary.downloaded += 1;
                    summary.bytes_downloaded += size;
                    downloaded_this_dataset += 1;
                    pb.finish_with_message(format!("{}/{} OK", orgao, resource.name));
                }
                Err(e) => {
                    warn!(resource = %resource.name, error = %e, "download falhou");
                    summary.failed += 1;
                    pb.abandon_with_message(format!("{}/{} FALHOU", orgao, resource.name));
                }
            }
        }

        if downloaded_this_dataset > 0 {
            info!(
                dataset = %dataset_id,
                orgao = %orgao,
                downloaded = downloaded_this_dataset,
                "downloads de espelhos concluidos para orgao"
            );
        }
    }

    manifest.save(&manifest_path)?;
    Ok(summary)
}

// ---------------------------------------------------------------------------
// Download de integras
// ---------------------------------------------------------------------------

/// Baixa integras novas (ZIPs + JSONs de metadados) do dataset CKAN.
///
/// Cada resource e um par: `YYYYMM.zip` (textos das integras) +
/// `metadadosYYYYMM.json` (metadados dos documentos). Ambos sao baixados
/// para `downloads_dir/integras/`.
pub async fn download_integras(
    client: &reqwest::Client,
    config: &CkanConfig,
    downloads_dir: &Path,
    limit: Option<usize>,
) -> Result<DownloadSummary> {
    let mut summary = DownloadSummary::default();
    let integras_dl_dir = downloads_dir.join("integras");
    let manifest_path = integras_dl_dir.join("manifest.json");
    let mut manifest = DownloadManifest::load(&manifest_path)?;

    let resources = list_resources(client, &config.base_url, &config.integras_dataset).await?;

    let mp = MultiProgress::new();
    let style = ProgressStyle::default_bar()
        .template("[{elapsed_precise}] {bar:40} {bytes}/{total_bytes} {msg}")
        .expect("template valido");

    for resource in &resources {
        if let Some(lim) = limit {
            if summary.downloaded >= lim {
                info!(limit = lim, "limite de downloads atingido");
                break;
            }
        }

        if manifest.is_downloaded(&resource.id) {
            summary.skipped += 1;
            continue;
        }

        let pb = mp.add(ProgressBar::new(0));
        pb.set_style(style.clone());
        pb.set_message(resource.name.clone());

        match download_resource(client, resource, &integras_dl_dir, Some(&pb)).await {
            Ok((path, size)) => {
                manifest.register(resource, &path, size);
                summary.downloaded += 1;
                summary.bytes_downloaded += size;
                pb.finish_with_message(format!("{} OK", resource.name));
            }
            Err(e) => {
                warn!(resource = %resource.name, error = %e, "download falhou");
                summary.failed += 1;
                pb.abandon_with_message(format!("{} FALHOU", resource.name));
            }
        }
    }

    manifest.save(&manifest_path)?;
    Ok(summary)
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/// Sanitiza nome de arquivo removendo caracteres problemáticos.
fn sanitize_filename(name: &str) -> String {
    name.chars()
        .map(|c| match c {
            '/' | '\\' | ':' | '*' | '?' | '"' | '<' | '>' | '|' => '_',
            _ => c,
        })
        .collect()
}

/// Cria um `reqwest::Client` configurado para downloads CKAN.
pub fn create_client(config: &CkanConfig) -> Result<reqwest::Client> {
    reqwest::Client::builder()
        .timeout(Duration::from_secs(config.download_timeout_secs))
        .connect_timeout(Duration::from_secs(30))
        .user_agent("stj-vec-ingest/0.1.0")
        .build()
        .context("falha ao criar HTTP client")
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_manifest_load_save_roundtrip() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("manifest.json");

        let mut manifest = DownloadManifest::default();
        let resource = CkanResource {
            id: "res-123".into(),
            name: "20220531.json".into(),
            url: "https://example.com/file.json".into(),
            format: "JSON".into(),
            size: Some(1024),
        };
        manifest.register(&resource, Path::new("/tmp/file.json"), 1024);
        manifest.save(&path).unwrap();

        let loaded = DownloadManifest::load(&path).unwrap();
        assert!(loaded.is_downloaded("res-123"));
        assert!(!loaded.is_downloaded("res-456"));
        assert_eq!(loaded.downloaded["res-123"].name, "20220531.json");
    }

    #[test]
    fn test_manifest_load_nonexistent() {
        let manifest = DownloadManifest::load(Path::new("/nonexistent/manifest.json")).unwrap();
        assert!(manifest.downloaded.is_empty());
    }

    #[test]
    fn test_sanitize_filename() {
        assert_eq!(sanitize_filename("file.json"), "file.json");
        assert_eq!(sanitize_filename("path/to/file"), "path_to_file");
        assert_eq!(sanitize_filename("a:b*c?d"), "a_b_c_d");
    }
}
