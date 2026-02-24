//! Pipeline de ingestao: scan -> read -> chunk -> embed -> store.

use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use rusqlite::Connection;

use stj_vec_core::chunker::{chunk_legal_text, strip_html};
use stj_vec_core::config::ChunkingConfig;
use stj_vec_core::embedder::Embedder;
use stj_vec_core::storage::Storage;
use stj_vec_core::types::{Chunk, Document};

use std::collections::HashSet;

use crate::file_index::{compute_file_hash, get_mtime, FileIndex};

/// Caminho absoluto do wrapper MCP search-case.
const SEARCH_CASE_WRAPPER: &str = "/home/opc/lex-vector/stj-vec/tools/search-case/wrapper.mjs";

const DB_NAME: &str = "knowledge.db";
const EMBEDDING_DIM: usize = 1024;

/// Pipeline de ingestao para um diretorio de caso juridico.
pub struct Ingestor {
    pub storage: Storage,
    pub db_path: PathBuf,
    pub base_dir: PathBuf,
    pub chunking: ChunkingConfig,
}

impl Ingestor {
    /// Cria `knowledge.db` e garante que `base/` existe.
    ///
    /// # Errors
    ///
    /// Retorna erro se nao conseguir criar o banco ou o diretorio base.
    pub fn create(work_dir: &Path) -> Result<Self> {
        let db_path = work_dir.join(DB_NAME);
        let base_dir = work_dir.join("base");

        std::fs::create_dir_all(&base_dir)
            .with_context(|| format!("falha ao criar {}", base_dir.display()))?;

        let storage = Storage::open(
            db_path.to_str().context("db_path nao e UTF-8")?,
            EMBEDDING_DIM,
        )
        .context("falha ao criar knowledge.db")?;

        // Criar file_index table via conexao separada
        init_file_index_table(&db_path)?;

        Ok(Self {
            storage,
            db_path,
            base_dir,
            chunking: default_chunking(),
        })
    }

    /// Abre `knowledge.db` existente e valida que `base/` existe.
    ///
    /// # Errors
    ///
    /// Retorna erro se o banco nao existir ou `base/` nao for diretorio.
    pub fn open(work_dir: &Path) -> Result<Self> {
        let db_path = work_dir.join(DB_NAME);
        let base_dir = work_dir.join("base");

        anyhow::ensure!(db_path.exists(), "knowledge.db nao encontrado em {}", work_dir.display());
        anyhow::ensure!(base_dir.is_dir(), "diretorio base/ nao encontrado em {}", work_dir.display());

        let storage = Storage::open(
            db_path.to_str().context("db_path nao e UTF-8")?,
            EMBEDDING_DIM,
        )
        .context("falha ao abrir knowledge.db")?;

        Ok(Self {
            storage,
            db_path,
            base_dir,
            chunking: default_chunking(),
        })
    }

    /// Escaneia `base/`, processa todos os arquivos e retorna `(doc_count, chunk_count)`.
    ///
    /// # Errors
    ///
    /// Retorna erro se falhar ao ler arquivos, chunkar, embedar ou persistir.
    pub async fn init(&self, embedder: &dyn Embedder) -> Result<(usize, usize)> {
        let files = scan_base_dir(&self.base_dir)?;
        let mut total_docs: usize = 0;
        let mut total_chunks: usize = 0;

        for file_path in &files {
            self.ingest_file(file_path, embedder).await
                .with_context(|| format!("falha ao ingerir {}", file_path.display()))?;
            total_docs += 1;

            // Contar chunks inseridos para este doc
            let rel = rel_path(&self.base_dir, file_path);
            let doc_id = doc_id_from_rel(&rel);
            let chunks = self.storage.get_chunks_by_doc(&doc_id)?;
            total_chunks += chunks.len();
        }

        Ok((total_docs, total_chunks))
    }

    /// Processa um unico arquivo: ler, chunkar, embedar, persistir.
    ///
    /// # Errors
    ///
    /// Retorna erro em qualquer etapa do pipeline.
    pub async fn ingest_file(&self, abs_path: &Path, embedder: &dyn Embedder) -> Result<()> {
        let rel = rel_path(&self.base_dir, abs_path);
        let doc_id = doc_id_from_rel(&rel);

        // Ler conteudo
        let content = read_file_content(abs_path)
            .with_context(|| format!("falha ao ler {}", abs_path.display()))?;

        if content.trim().is_empty() {
            eprintln!("[ingest] {rel} (vazio, ignorado)");
            return Ok(());
        }

        // Chunk
        let output = chunk_legal_text(&content, &doc_id, &self.chunking);
        let chunk_count = output.chunks.len();

        if chunk_count == 0 {
            eprintln!("[ingest] {rel} (0 chunks, ignorado)");
            return Ok(());
        }

        eprintln!("[ingest] {rel} ({chunk_count} chunks)");

        // Persistir documento
        let doc = Document {
            id: doc_id.clone(),
            processo: None,
            classe: None,
            ministro: None,
            orgao_julgador: None,
            data_publicacao: None,
            data_julgamento: None,
            assuntos: None,
            teor: Some(content.chars().take(500).collect()),
            tipo: None,
            #[allow(clippy::cast_possible_truncation, clippy::cast_possible_wrap)]
            chunk_count: chunk_count as i32,
            source_file: Some(rel.clone()),
        };
        self.storage.insert_document(&doc)?;

        // Converter RawChunks -> Chunks e persistir
        let chunks: Vec<Chunk> = output
            .chunks
            .iter()
            .map(|rc| Chunk {
                id: rc.id.clone(),
                doc_id: doc_id.clone(),
                #[allow(clippy::cast_possible_truncation, clippy::cast_possible_wrap)]
                chunk_index: rc.chunk_index as i32,
                content: rc.content.clone(),
                #[allow(clippy::cast_possible_truncation, clippy::cast_possible_wrap)]
                token_count: rc.token_count as i32,
            })
            .collect();
        self.storage.insert_chunks(&chunks)?;

        // Embed
        let texts: Vec<String> = chunks.iter().map(|c| c.content.clone()).collect();
        let embeddings = embedder.embed_batch(&texts).await
            .context("falha ao gerar embeddings")?;

        let pairs: Vec<(String, Vec<f32>)> = chunks
            .iter()
            .zip(embeddings)
            .map(|(c, emb)| (c.id.clone(), emb))
            .collect();
        self.storage.insert_embeddings_batch(&pairs)?;

        // Atualizar file_index
        let conn = Connection::open(&self.db_path)
            .context("falha ao abrir conexao para file_index")?;
        let idx = FileIndex::new(&conn)?;
        let mtime = get_mtime(abs_path).unwrap_or(0);
        let hash = compute_file_hash(abs_path).unwrap_or_default();
        idx.upsert(&rel, mtime, &hash)?;

        Ok(())
    }

    /// Detecta mudancas em `base/` comparando com `file_index`.
    ///
    /// Retorna `(novos, modificados, removidos_rel_paths)`.
    ///
    /// # Errors
    ///
    /// Retorna erro se falhar ao acessar o file index ou escanear `base/`.
    pub fn detect_changes(&self) -> Result<(Vec<PathBuf>, Vec<PathBuf>, Vec<String>)> {
        let conn = Connection::open(&self.db_path)
            .context("falha ao abrir conexao para file_index (detect_changes)")?;
        let idx = FileIndex::new(&conn)?;
        let records = idx.all()?;

        let indexed: std::collections::HashMap<String, String> = records
            .into_iter()
            .map(|r| (r.path, r.hash_md5))
            .collect();

        let disk_files = scan_base_dir(&self.base_dir)?;

        let mut disk_rels: HashSet<String> = HashSet::new();
        let mut new_files = Vec::new();
        let mut modified_files = Vec::new();

        for file_path in &disk_files {
            let rel = rel_path(&self.base_dir, file_path);
            disk_rels.insert(rel.clone());

            match indexed.get(&rel) {
                None => new_files.push(file_path.clone()),
                Some(old_hash) => {
                    let current_hash = compute_file_hash(file_path).unwrap_or_default();
                    if &current_hash != old_hash {
                        modified_files.push(file_path.clone());
                    }
                }
            }
        }

        let removed: Vec<String> = indexed
            .keys()
            .filter(|p| !disk_rels.contains(p.as_str()))
            .cloned()
            .collect();

        Ok((new_files, modified_files, removed))
    }

    /// Sync: processa delta (novos + modificados + removidos).
    ///
    /// Retorna `(new_count, modified_count, removed_count)`.
    ///
    /// # Errors
    ///
    /// Retorna erro se falhar ao processar qualquer arquivo do delta.
    pub async fn sync(&self, embedder: &dyn Embedder) -> Result<(usize, usize, usize)> {
        let (new_files, modified_files, removed_rels) = self.detect_changes()?;

        let new_count = new_files.len();
        let modified_count = modified_files.len();
        let removed_count = removed_rels.len();

        for rel in &removed_rels {
            self.remove_file_data(rel)
                .with_context(|| format!("falha ao remover dados de {rel}"))?;
        }

        for file_path in &modified_files {
            let rel = rel_path(&self.base_dir, file_path);
            self.remove_file_data(&rel)
                .with_context(|| format!("falha ao remover dados antigos de {rel}"))?;
            self.ingest_file(file_path, embedder).await
                .with_context(|| format!("falha ao re-ingerir {}", file_path.display()))?;
        }

        for file_path in &new_files {
            self.ingest_file(file_path, embedder).await
                .with_context(|| format!("falha ao ingerir {}", file_path.display()))?;
        }

        Ok((new_count, modified_count, removed_count))
    }

    /// Gera `.claude.json` com config do MCP server `search-case` e hook de sync.
    ///
    /// Se o arquivo ja existir, nao sobrescreve.
    ///
    /// # Errors
    ///
    /// Retorna erro se falhar ao serializar ou escrever o arquivo.
    pub fn generate_claude_config(work_dir: &Path) -> Result<()> {
        let config_path = work_dir.join(".claude.json");
        if config_path.exists() {
            eprintln!("[init] .claude.json ja existe, pulando");
            return Ok(());
        }

        let case_ingest_bin = std::env::current_exe()
            .unwrap_or_else(|_| PathBuf::from("case-ingest"));

        let config = serde_json::json!({
            "mcpServers": {
                "search-case": {
                    "command": "node",
                    "args": [SEARCH_CASE_WRAPPER]
                }
            },
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "mcp__search-case__search_case",
                        "hooks": [
                            {
                                "type": "command",
                                "command": format!("{} sync", case_ingest_bin.display())
                            }
                        ]
                    }
                ]
            }
        });

        std::fs::write(&config_path, serde_json::to_string_pretty(&config)?)?;
        eprintln!("[init] .claude.json criado com MCP server e hook de sync");
        Ok(())
    }

    /// Remove todos os dados de um arquivo: chunks, embeddings, documento e `file_index`.
    ///
    /// # Errors
    ///
    /// Retorna erro se falhar ao executar as queries de limpeza.
    pub fn remove_file_data(&self, rel_path: &str) -> Result<()> {
        let doc_id = doc_id_from_rel(rel_path);

        let conn = Connection::open(&self.db_path)
            .context("falha ao abrir conexao para remove_file_data")?;

        // Buscar chunk IDs
        let chunk_ids: Vec<String> = {
            let mut stmt = conn.prepare("SELECT id FROM chunks WHERE doc_id = ?1")?;
            let rows = stmt.query_map([&doc_id], |row| row.get::<_, String>(0))?;
            rows.filter_map(std::result::Result::ok).collect()
        };

        // Deletar embeddings (vec_chunks)
        for chunk_id in &chunk_ids {
            conn.execute("DELETE FROM vec_chunks WHERE chunk_id = ?1", [chunk_id])?;
        }

        // Deletar chunks
        conn.execute("DELETE FROM chunks WHERE doc_id = ?1", [&doc_id])?;

        // Deletar documento
        conn.execute("DELETE FROM documents WHERE id = ?1", [&doc_id])?;

        // Deletar do file_index
        conn.execute("DELETE FROM file_index WHERE path = ?1", [rel_path])?;

        eprintln!("[sync] removido: {rel_path} ({} chunks)", chunk_ids.len());

        Ok(())
    }
}

/// Cria tabela `file_index` via conexao separada.
fn init_file_index_table(db_path: &Path) -> Result<()> {
    let conn = Connection::open(db_path)
        .context("falha ao abrir conexao para file_index init")?;
    let _idx = FileIndex::new(&conn)?;
    Ok(())
}

/// Config de chunking padrao para case-ingest.
fn default_chunking() -> ChunkingConfig {
    ChunkingConfig {
        max_tokens: 512,
        overlap_tokens: 64,
        min_chunk_tokens: 30,
    }
}

/// Escaneia top-level de `base/`, retorna paths de arquivos suportados ordenados.
fn scan_base_dir(base: &Path) -> Result<Vec<PathBuf>> {
    let mut files = Vec::new();
    let entries = std::fs::read_dir(base)
        .with_context(|| format!("falha ao ler diretorio {}", base.display()))?;

    for entry in entries {
        let entry = entry?;
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("");
        if matches!(ext, "md" | "txt" | "json") {
            files.push(path);
        }
    }

    files.sort();
    Ok(files)
}

/// Le conteudo de arquivo, extraindo campo "texto" de JSONs quando presente.
fn read_file_content(path: &Path) -> Result<String> {
    let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("");
    let raw = std::fs::read_to_string(path)
        .with_context(|| format!("falha ao ler {}", path.display()))?;

    if ext == "json" {
        if let Ok(val) = serde_json::from_str::<serde_json::Value>(&raw) {
            if let Some(texto) = val.get("texto").and_then(|v| v.as_str()) {
                return Ok(texto.to_string());
            }
        }
    }

    Ok(strip_html(&raw))
}

/// Caminho relativo a partir do base dir.
fn rel_path(base: &Path, abs: &Path) -> String {
    abs.strip_prefix(base)
        .map_or_else(|_| abs.to_string_lossy().into_owned(), |p| p.to_string_lossy().into_owned())
}

/// Gera `doc_id` deterministico a partir do caminho relativo.
fn doc_id_from_rel(rel: &str) -> String {
    format!("{:x}", md5::compute(rel.as_bytes()))
}
