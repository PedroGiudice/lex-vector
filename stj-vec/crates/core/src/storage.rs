//! SQLite + sqlite-vec Storage para jurisprudencia STJ
//!
//! Gerencia documentos, chunks e buscas por similaridade vetorial.
//! Usa `Mutex<Connection>` porque rusqlite `Connection` nao e `Send`.
//! WAL mode permite 1 writer + N readers simultaneos.

use anyhow::{Context, Result};
use rusqlite::{params, Connection, OpenFlags};
use std::path::Path;
use std::sync::Mutex;
use zerocopy::AsBytes;

use crate::types::{Chunk, DbStats, Document, IngestStatus, SearchFilters, SearchResult};

/// Schema base (sem vec_chunks -- criada dinamicamente se dim > 0)
const SCHEMA_SQL: &str = r#"
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    processo TEXT,
    classe TEXT,
    ministro TEXT,
    orgao_julgador TEXT,
    data_publicacao TEXT,
    data_julgamento TEXT,
    assuntos TEXT,
    teor TEXT,
    tipo TEXT,
    chunk_count INTEGER DEFAULT 0,
    source_file TEXT,
    processo_digits TEXT
);

CREATE INDEX IF NOT EXISTS idx_docs_processo ON documents(processo);
CREATE INDEX IF NOT EXISTS idx_docs_ministro ON documents(ministro);
CREATE INDEX IF NOT EXISTS idx_docs_data ON documents(data_publicacao);
CREATE INDEX IF NOT EXISTS idx_docs_tipo ON documents(tipo);
CREATE INDEX IF NOT EXISTS idx_documents_processo_digits ON documents(processo_digits);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    chunk_index INTEGER,
    content TEXT NOT NULL,
    token_count INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);

-- Full-text search (BM25 sparse retrieval)
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    chunk_id UNINDEXED,
    content,
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TABLE IF NOT EXISTS ingest_log (
    source_file TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    doc_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    started_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    error TEXT
);

CREATE INDEX IF NOT EXISTS idx_ingest_status ON ingest_log(status);
"#;

/// Storage thread-safe para uso em contexto async.
pub struct Storage {
    conn: Mutex<Connection>,
    embedding_dim: usize,
}

/// Registra extensao sqlite-vec
fn register_sqlite_vec() {
    unsafe {
        rusqlite::ffi::sqlite3_auto_extension(Some(std::mem::transmute(
            sqlite_vec::sqlite3_vec_init as *const (),
        )));
    }
}

impl Storage {
    /// Abre banco SQLite existente ou cria novo com schema (read-write)
    pub fn open(path: &str, embedding_dim: usize) -> Result<Self> {
        register_sqlite_vec();

        // Garantir que diretorio pai existe
        if let Some(parent) = Path::new(path).parent() {
            std::fs::create_dir_all(parent).ok();
        }

        let conn =
            Connection::open(path).with_context(|| format!("falha ao abrir SQLite em {}", path))?;

        conn.execute_batch(SCHEMA_SQL)
            .context("falha ao aplicar schema")?;

        // Criar tabela vec_chunks se dim > 0
        if embedding_dim > 0 {
            let vec_sql = format!(
                "CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
                    chunk_id TEXT PRIMARY KEY,
                    embedding float[{}] distance_metric=cosine
                )",
                embedding_dim
            );
            conn.execute_batch(&vec_sql)
                .context("falha ao criar vec_chunks")?;
        }

        Ok(Self {
            conn: Mutex::new(conn),
            embedding_dim,
        })
    }

    /// Abre banco SQLite em modo read-only
    pub fn open_readonly(path: &str) -> Result<Self> {
        register_sqlite_vec();

        if !Path::new(path).exists() {
            anyhow::bail!("banco nao encontrado: {}", path);
        }

        let conn = Connection::open_with_flags(
            path,
            OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
        )
        .with_context(|| format!("falha ao abrir SQLite readonly em {}", path))?;

        conn.execute_batch("PRAGMA busy_timeout=5000;")
            .context("falha ao configurar busy_timeout")?;

        Ok(Self {
            conn: Mutex::new(conn),
            embedding_dim: 0,
        })
    }

    fn lock(&self) -> Result<std::sync::MutexGuard<'_, Connection>> {
        self.conn
            .lock()
            .map_err(|e| anyhow::anyhow!("mutex poisoned: {}", e))
    }

    // === Documents ===

    /// Insere ou atualiza documento
    pub fn insert_document(&self, doc: &Document) -> Result<()> {
        let conn = self.lock()?;
        let processo_digits: Option<String> = doc.processo.as_ref().map(|p| {
            p.chars().filter(|c| c.is_ascii_digit()).collect()
        });
        conn.execute(
            "INSERT OR REPLACE INTO documents (id, processo, classe, ministro, orgao_julgador,
             data_publicacao, data_julgamento, assuntos, teor, tipo, chunk_count, source_file, processo_digits)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13)",
            params![
                doc.id,
                doc.processo,
                doc.classe,
                doc.ministro,
                doc.orgao_julgador,
                doc.data_publicacao,
                doc.data_julgamento,
                doc.assuntos,
                doc.teor,
                doc.tipo,
                doc.chunk_count,
                doc.source_file,
                processo_digits,
            ],
        )?;
        Ok(())
    }

    /// Busca documento por ID
    pub fn get_document(&self, id: &str) -> Result<Option<Document>> {
        let conn = self.lock()?;
        let mut stmt = conn.prepare(
            "SELECT id, processo, classe, ministro, orgao_julgador,
             data_publicacao, data_julgamento, assuntos, teor, tipo, chunk_count, source_file
             FROM documents WHERE id = ?",
        )?;

        let result = stmt.query_row(params![id], |row| {
            Ok(Document {
                id: row.get(0)?,
                processo: row.get(1)?,
                classe: row.get(2)?,
                ministro: row.get(3)?,
                orgao_julgador: row.get(4)?,
                data_publicacao: row.get(5)?,
                data_julgamento: row.get(6)?,
                assuntos: row.get(7)?,
                teor: row.get(8)?,
                tipo: row.get(9)?,
                chunk_count: row.get::<_, Option<i32>>(10)?.unwrap_or(0),
                source_file: row.get(11)?,
            })
        });

        match result {
            Ok(doc) => Ok(Some(doc)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(e.into()),
        }
    }

    /// Atualiza chunk_count de um documento
    pub fn update_document_chunk_count(&self, doc_id: &str) -> Result<()> {
        let conn = self.lock()?;
        conn.execute(
            "UPDATE documents SET chunk_count =
             (SELECT COUNT(*) FROM chunks WHERE doc_id = ?) WHERE id = ?",
            params![doc_id, doc_id],
        )?;
        Ok(())
    }

    // === Chunks ===

    /// Insere chunks em batch
    pub fn insert_chunks(&self, chunks: &[Chunk]) -> Result<()> {
        let conn = self.lock()?;
        let mut stmt = conn.prepare(
            "INSERT OR IGNORE INTO chunks (id, doc_id, chunk_index, content, token_count)
             VALUES (?1, ?2, ?3, ?4, ?5)",
        )?;

        for chunk in chunks {
            stmt.execute(params![
                chunk.id,
                chunk.doc_id,
                chunk.chunk_index,
                chunk.content,
                chunk.token_count,
            ])?;
        }
        Ok(())
    }

    /// Retorna chunks de um documento ordenados por index
    pub fn get_chunks_by_doc(&self, doc_id: &str) -> Result<Vec<Chunk>> {
        let conn = self.lock()?;
        let mut stmt = conn.prepare(
            "SELECT id, doc_id, chunk_index, content, token_count
             FROM chunks WHERE doc_id = ? ORDER BY chunk_index ASC",
        )?;

        let chunks = stmt
            .query_map(params![doc_id], |row| {
                Ok(Chunk {
                    id: row.get(0)?,
                    doc_id: row.get(1)?,
                    chunk_index: row.get::<_, Option<i32>>(2)?.unwrap_or(0),
                    content: row.get(3)?,
                    token_count: row.get::<_, Option<i32>>(4)?.unwrap_or(0),
                })
            })?
            .filter_map(|r| r.ok())
            .collect();

        Ok(chunks)
    }

    /// Verifica se chunk existe
    pub fn chunk_exists(&self, id: &str) -> Result<bool> {
        let conn = self.lock()?;
        let count: i64 = conn.query_row(
            "SELECT COUNT(*) FROM chunks WHERE id = ?",
            params![id],
            |row| row.get(0),
        )?;
        Ok(count > 0)
    }

    // === Embeddings ===

    /// Insere embedding para um chunk
    pub fn insert_embedding(&self, chunk_id: &str, embedding: &[f32]) -> Result<()> {
        if self.embedding_dim == 0 {
            anyhow::bail!("embedding not configured (dim=0)");
        }
        let conn = self.lock()?;
        conn.execute(
            "INSERT OR REPLACE INTO vec_chunks (chunk_id, embedding) VALUES (?1, ?2)",
            params![chunk_id, embedding.as_bytes()],
        )?;
        Ok(())
    }

    /// Insere embeddings em batch
    pub fn insert_embeddings_batch(&self, pairs: &[(String, Vec<f32>)]) -> Result<()> {
        if self.embedding_dim == 0 {
            anyhow::bail!("embedding not configured (dim=0)");
        }
        let conn = self.lock()?;
        let mut stmt = conn
            .prepare("INSERT OR REPLACE INTO vec_chunks (chunk_id, embedding) VALUES (?1, ?2)")?;
        for (chunk_id, embedding) in pairs {
            stmt.execute(params![chunk_id, embedding.as_bytes()])?;
        }
        Ok(())
    }

    // === Search ===

    /// Busca vetorial por similaridade com filtros opcionais
    pub fn search(
        &self,
        query_embedding: &[f32],
        limit: usize,
        threshold: f64,
        filters: &SearchFilters,
    ) -> Result<Vec<SearchResult>> {
        if self.embedding_dim == 0 {
            anyhow::bail!("embedding not configured (dim=0), search unavailable");
        }

        let conn = self.lock()?;
        let knn_limit = (limit * 4) as i64;

        // KNN + JOIN com filtros
        let mut sql = String::from(
            "SELECT c.id, c.doc_id, c.chunk_index, c.content, c.token_count, v.distance,
             d.id, d.processo, d.classe, d.ministro, d.orgao_julgador,
             d.data_publicacao, d.data_julgamento, d.assuntos, d.teor, d.tipo,
             d.chunk_count, d.source_file
             FROM vec_chunks v
             INNER JOIN chunks c ON c.id = v.chunk_id
             INNER JOIN documents d ON d.id = c.doc_id
             WHERE v.embedding MATCH ?1
               AND k = ?2",
        );

        let mut param_idx = 3;
        let mut filter_clauses = Vec::new();

        if filters.ministro.is_some() {
            filter_clauses.push(format!("AND d.ministro = ?{}", param_idx));
            param_idx += 1;
        }
        if filters.tipo.is_some() {
            filter_clauses.push(format!("AND d.tipo = ?{}", param_idx));
            param_idx += 1;
        }
        if filters.data_from.is_some() {
            filter_clauses.push(format!("AND d.data_publicacao >= ?{}", param_idx));
            param_idx += 1;
        }
        if filters.data_to.is_some() {
            filter_clauses.push(format!("AND d.data_publicacao <= ?{}", param_idx));
            // param_idx += 1;
        }

        for clause in &filter_clauses {
            sql.push(' ');
            sql.push_str(clause);
        }

        sql.push_str(&format!(" ORDER BY v.distance LIMIT {}", limit));

        let mut stmt = conn.prepare(&sql)?;

        // Bind parameters dynamicamente
        let embedding_bytes = query_embedding.as_bytes();
        stmt.raw_bind_parameter(1, embedding_bytes)?;
        stmt.raw_bind_parameter(2, knn_limit)?;

        let mut bind_idx = 3;
        if let Some(ref ministro) = filters.ministro {
            stmt.raw_bind_parameter(bind_idx, ministro.as_str())?;
            bind_idx += 1;
        }
        if let Some(ref tipo) = filters.tipo {
            stmt.raw_bind_parameter(bind_idx, tipo.as_str())?;
            bind_idx += 1;
        }
        if let Some(ref data_from) = filters.data_from {
            stmt.raw_bind_parameter(bind_idx, data_from.as_str())?;
            bind_idx += 1;
        }
        if let Some(ref data_to) = filters.data_to {
            stmt.raw_bind_parameter(bind_idx, data_to.as_str())?;
            // bind_idx += 1;
        }

        let mut results = Vec::new();
        let mut rows = stmt.raw_query();
        while let Some(row) = rows.next()? {
            let distance: f64 = row.get(5)?;
            let score = 1.0 - distance;
            if score < threshold {
                continue;
            }

            results.push(SearchResult {
                score,
                chunk: Chunk {
                    id: row.get(0)?,
                    doc_id: row.get(1)?,
                    chunk_index: row.get::<_, Option<i32>>(2)?.unwrap_or(0),
                    content: row.get(3)?,
                    token_count: row.get::<_, Option<i32>>(4)?.unwrap_or(0),
                },
                document: Document {
                    id: row.get(6)?,
                    processo: row.get(7)?,
                    classe: row.get(8)?,
                    ministro: row.get(9)?,
                    orgao_julgador: row.get(10)?,
                    data_publicacao: row.get(11)?,
                    data_julgamento: row.get(12)?,
                    assuntos: row.get(13)?,
                    teor: row.get(14)?,
                    tipo: row.get(15)?,
                    chunk_count: row.get::<_, Option<i32>>(16)?.unwrap_or(0),
                    source_file: row.get(17)?,
                },
            });
        }

        Ok(results)
    }

    // === FTS5 ===

    /// Insere chunks no indice FTS5
    pub fn insert_chunks_fts(&self, chunks: &[Chunk]) -> Result<()> {
        let conn = self.lock()?;
        let mut stmt =
            conn.prepare("INSERT OR IGNORE INTO chunks_fts (chunk_id, content) VALUES (?1, ?2)")?;
        for chunk in chunks {
            stmt.execute(params![chunk.id, chunk.content])?;
        }
        Ok(())
    }

    /// Busca FTS5 (BM25 sparse). Retorna (chunk_id, bm25_score).
    pub fn fts5_search(&self, query: &str, limit: usize) -> Result<Vec<(String, f64)>> {
        let conn = self.lock()?;

        // Sanitizar: manter alfanumericos, espacos e hifens (termos juridicos como REsp-1234)
        let safe_query: String = query
            .chars()
            .filter(|c| c.is_alphanumeric() || c.is_whitespace() || *c == '-')
            .collect();
        if safe_query.trim().is_empty() {
            return Ok(vec![]);
        }

        let mut stmt = conn.prepare(
            "SELECT f.chunk_id, bm25(chunks_fts) as rank
             FROM chunks_fts f
             WHERE chunks_fts MATCH ?1
             ORDER BY rank
             LIMIT ?2",
        )?;

        let results = stmt
            .query_map(params![safe_query, limit as i64], |row| {
                Ok((row.get::<_, String>(0)?, row.get::<_, f64>(1)?))
            })?
            .filter_map(|r| r.ok())
            .collect();

        Ok(results)
    }

    /// Hybrid search: dense (sqlite-vec) + sparse (FTS5 BM25) com RRF fusion.
    ///
    /// Combina resultados de busca vetorial e textual usando Reciprocal Rank Fusion.
    pub fn hybrid_search(
        &self,
        query_embedding: &[f32],
        query_text: &str,
        limit: usize,
        threshold: f64,
        filters: &SearchFilters,
    ) -> Result<Vec<SearchResult>> {
        let k = 60.0_f64; // RRF constant

        // 1. Dense search (fetch more candidates for fusion)
        let dense_results = self.search(query_embedding, limit * 3, 0.0, filters)?;

        // 2. Sparse search (FTS5) - graceful fallback
        let sparse_results = self.fts5_search(query_text, limit * 3).unwrap_or_default();

        // 3. RRF fusion
        let mut rrf_scores: std::collections::HashMap<String, f64> =
            std::collections::HashMap::new();
        let mut result_map: std::collections::HashMap<String, &SearchResult> =
            std::collections::HashMap::new();

        for (rank, result) in dense_results.iter().enumerate() {
            let score = 1.0 / (k + rank as f64 + 1.0);
            *rrf_scores.entry(result.chunk.id.clone()).or_default() += score;
            result_map.insert(result.chunk.id.clone(), result);
        }

        for (rank, (id, _bm25)) in sparse_results.iter().enumerate() {
            let score = 1.0 / (k + rank as f64 + 1.0);
            *rrf_scores.entry(id.clone()).or_default() += score;
        }

        // 4. Sort by RRF score
        let mut ranked: Vec<_> = rrf_scores.into_iter().collect();
        ranked.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        ranked.truncate(limit);

        // 5. Build results
        let mut results = Vec::new();
        for (id, rrf_score) in &ranked {
            if let Some(sr) = result_map.get(id.as_str()) {
                if sr.score >= threshold || sparse_results.iter().any(|(sid, _)| sid == id) {
                    results.push(SearchResult {
                        score: *rrf_score,
                        chunk: sr.chunk.clone(),
                        document: sr.document.clone(),
                    });
                }
            } else {
                // FTS-only result: fetch chunk + doc from DB
                let conn = self.lock()?;
                let opt = conn.query_row(
                    "SELECT c.id, c.doc_id, c.chunk_index, c.content, c.token_count,
                            d.id, d.processo, d.classe, d.ministro, d.orgao_julgador,
                            d.data_publicacao, d.data_julgamento, d.assuntos, d.teor, d.tipo,
                            d.chunk_count, d.source_file
                     FROM chunks c
                     JOIN documents d ON d.id = c.doc_id
                     WHERE c.id = ?1",
                    params![id],
                    |row| {
                        Ok(SearchResult {
                            score: *rrf_score,
                            chunk: Chunk {
                                id: row.get(0)?,
                                doc_id: row.get(1)?,
                                chunk_index: row.get::<_, Option<i32>>(2)?.unwrap_or(0),
                                content: row.get(3)?,
                                token_count: row.get::<_, Option<i32>>(4)?.unwrap_or(0),
                            },
                            document: Document {
                                id: row.get(5)?,
                                processo: row.get(6)?,
                                classe: row.get(7)?,
                                ministro: row.get(8)?,
                                orgao_julgador: row.get(9)?,
                                data_publicacao: row.get(10)?,
                                data_julgamento: row.get(11)?,
                                assuntos: row.get(12)?,
                                teor: row.get(13)?,
                                tipo: row.get(14)?,
                                chunk_count: row.get::<_, Option<i32>>(15)?.unwrap_or(0),
                                source_file: row.get(16)?,
                            },
                        })
                    },
                );
                if let Ok(sr) = opt {
                    results.push(sr);
                }
            }
        }

        Ok(results)
    }

    // === Ingest Log ===

    /// Define status de ingestion
    pub fn set_ingest_status(
        &self,
        source: &str,
        status: &str,
        doc_count: i32,
        chunk_count: i32,
    ) -> Result<()> {
        let conn = self.lock()?;
        conn.execute(
            "INSERT INTO ingest_log (source_file, status, doc_count, chunk_count)
             VALUES (?1, ?2, ?3, ?4)
             ON CONFLICT(source_file) DO UPDATE SET
             status = ?2, doc_count = ?3, chunk_count = ?4,
             completed_at = CASE WHEN ?2 = 'done' THEN datetime('now') ELSE completed_at END",
            params![source, status, doc_count, chunk_count],
        )?;
        Ok(())
    }

    /// Retorna status de ingestion de um source
    pub fn get_ingest_status(&self, source: &str) -> Result<Option<IngestStatus>> {
        let conn = self.lock()?;
        let result = conn.query_row(
            "SELECT source_file, status, doc_count, chunk_count, error
             FROM ingest_log WHERE source_file = ?",
            params![source],
            |row| {
                Ok(IngestStatus {
                    source_file: row.get(0)?,
                    status: row.get(1)?,
                    doc_count: row.get::<_, Option<i32>>(2)?.unwrap_or(0),
                    chunk_count: row.get::<_, Option<i32>>(3)?.unwrap_or(0),
                    error: row.get(4)?,
                })
            },
        );

        match result {
            Ok(s) => Ok(Some(s)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(e.into()),
        }
    }

    /// Lista sources por status
    pub fn list_ingest_by_status(&self, status: &str) -> Result<Vec<IngestStatus>> {
        let conn = self.lock()?;
        let mut stmt = conn.prepare(
            "SELECT source_file, status, doc_count, chunk_count, error
             FROM ingest_log WHERE status = ? ORDER BY source_file",
        )?;

        let items = stmt
            .query_map(params![status], |row| {
                Ok(IngestStatus {
                    source_file: row.get(0)?,
                    status: row.get(1)?,
                    doc_count: row.get::<_, Option<i32>>(2)?.unwrap_or(0),
                    chunk_count: row.get::<_, Option<i32>>(3)?.unwrap_or(0),
                    error: row.get(4)?,
                })
            })?
            .filter_map(|r| r.ok())
            .collect();

        Ok(items)
    }

    /// Reseta status de um source para reprocessar
    pub fn reset_ingest(&self, source: &str) -> Result<()> {
        let conn = self.lock()?;
        // Deletar chunks associados
        conn.execute(
            "DELETE FROM chunks WHERE doc_id IN
             (SELECT id FROM documents WHERE source_file = ?)",
            params![source],
        )?;
        // Deletar documentos
        conn.execute(
            "DELETE FROM documents WHERE source_file = ?",
            params![source],
        )?;
        // Resetar log
        conn.execute(
            "DELETE FROM ingest_log WHERE source_file = ?",
            params![source],
        )?;
        Ok(())
    }

    // === Document Queries ===

    /// Lista IDs de documentos de um source.
    pub fn list_documents_by_source(&self, source: &str) -> Result<Vec<String>> {
        let conn = self.lock()?;
        let mut stmt =
            conn.prepare("SELECT id FROM documents WHERE source_file = ? ORDER BY id")?;
        let ids = stmt
            .query_map(params![source], |row| row.get::<_, String>(0))?
            .filter_map(|r| r.ok())
            .collect();
        Ok(ids)
    }

    // === Enrich ===

    /// Busca documentos cujo campo `processo_digits` corresponde exatamente.
    ///
    /// Usa indice `idx_documents_processo_digits` para busca O(log n).
    /// Retorna tuplas `(id, processo, classe, orgao_julgador, data_julgamento, ministro)`.
    pub fn find_documents_by_processo_digits(
        &self,
        digits: &str,
    ) -> Result<
        Vec<(
            String,
            String,
            Option<String>,
            Option<String>,
            Option<String>,
            Option<String>,
        )>,
    > {
        let conn = self.lock()?;
        let mut stmt = conn.prepare(
            "SELECT id, processo, classe, orgao_julgador, data_julgamento, ministro
             FROM documents WHERE processo_digits = ?1",
        )?;

        let rows = stmt
            .query_map([digits], |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, Option<String>>(2)?,
                    row.get::<_, Option<String>>(3)?,
                    row.get::<_, Option<String>>(4)?,
                    row.get::<_, Option<String>>(5)?,
                ))
            })?
            .filter_map(|r| r.ok())
            .collect();

        Ok(rows)
    }

    /// UPDATE seletivo de metadados usando COALESCE (nao sobrescreve campos ja preenchidos).
    ///
    /// Para cada campo: se o documento ja tem valor preenchido, mantem. Se esta NULL/vazio
    /// e o parametro fornece valor, atualiza. Se o parametro e `None`, mantem o original.
    ///
    /// Retorna `true` se alguma linha foi atualizada.
    pub fn enrich_document(
        &self,
        doc_id: &str,
        classe: Option<&str>,
        orgao: Option<&str>,
        data_julg: Option<&str>,
        ministro: Option<&str>,
    ) -> Result<bool> {
        let conn = self.lock()?;
        // COALESCE(NULLIF(campo, ''), ?N) -- se campo ja tem valor, usa ele.
        // Se campo e NULL/'', tenta ?N. Se ?N tambem e NULL, fica NULL.
        let rows = conn.execute(
            "UPDATE documents SET
                classe = COALESCE(NULLIF(classe, ''), ?1, classe),
                orgao_julgador = COALESCE(NULLIF(orgao_julgador, ''), ?2, orgao_julgador),
                data_julgamento = COALESCE(NULLIF(data_julgamento, ''), ?3, data_julgamento),
                ministro = COALESCE(NULLIF(ministro, ''), ?4, ministro)
             WHERE id = ?5
               AND (classe IS NULL OR classe = ''
                    OR orgao_julgador IS NULL OR orgao_julgador = ''
                    OR data_julgamento IS NULL OR data_julgamento = ''
                    OR ministro IS NULL OR ministro = '')",
            params![classe, orgao, data_julg, ministro, doc_id,],
        )?;
        Ok(rows > 0)
    }

    // === Stats ===

    /// Estatisticas do banco
    pub fn stats(&self) -> Result<DbStats> {
        let conn = self.lock()?;

        let document_count: i64 =
            conn.query_row("SELECT COUNT(*) FROM documents", [], |row| row.get(0))?;
        let chunk_count: i64 =
            conn.query_row("SELECT COUNT(*) FROM chunks", [], |row| row.get(0))?;

        // vec_chunks pode nao existir se dim=0
        let embedding_count: i64 = if self.embedding_dim > 0 {
            conn.query_row("SELECT COUNT(*) FROM vec_chunks", [], |row| row.get(0))
                .unwrap_or(0)
        } else {
            0
        };

        let ingest_pending: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM ingest_log WHERE status = 'pending'",
                [],
                |row| row.get(0),
            )
            .unwrap_or(0);

        let ingest_chunked: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM ingest_log WHERE status = 'chunked'",
                [],
                |row| row.get(0),
            )
            .unwrap_or(0);

        let ingest_done: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM ingest_log WHERE status = 'done'",
                [],
                |row| row.get(0),
            )
            .unwrap_or(0);

        Ok(DbStats {
            document_count,
            chunk_count,
            embedding_count,
            ingest_pending,
            ingest_chunked,
            ingest_done,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_open_and_stats() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();
        let stats = storage.stats().unwrap();
        assert_eq!(stats.document_count, 0);
        assert_eq!(stats.chunk_count, 0);
        assert_eq!(stats.embedding_count, 0);
    }

    #[test]
    fn test_insert_and_get_document() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();

        let doc = Document {
            id: "12345".into(),
            processo: Some("REsp 1234567".into()),
            classe: Some("RECURSO ESPECIAL".into()),
            ministro: Some("NANCY ANDRIGHI".into()),
            orgao_julgador: None,
            data_publicacao: Some("2024-03-15".into()),
            data_julgamento: None,
            assuntos: Some("11806".into()),
            teor: Some("Dando provimento".into()),
            tipo: Some("ACÓRDÃO".into()),
            chunk_count: 0,
            source_file: Some("202403".into()),
        };
        storage.insert_document(&doc).unwrap();

        let fetched = storage.get_document("12345").unwrap().unwrap();
        assert_eq!(fetched.processo.unwrap(), "REsp 1234567");
        assert_eq!(fetched.ministro.unwrap(), "NANCY ANDRIGHI");

        let stats = storage.stats().unwrap();
        assert_eq!(stats.document_count, 1);
    }

    #[test]
    fn test_insert_and_get_chunks() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();

        let chunks = vec![
            Chunk {
                id: "c1".into(),
                doc_id: "d1".into(),
                chunk_index: 0,
                content: "primeiro chunk".into(),
                token_count: 2,
            },
            Chunk {
                id: "c2".into(),
                doc_id: "d1".into(),
                chunk_index: 1,
                content: "segundo chunk".into(),
                token_count: 2,
            },
        ];
        storage.insert_chunks(&chunks).unwrap();

        let fetched = storage.get_chunks_by_doc("d1").unwrap();
        assert_eq!(fetched.len(), 2);
        assert_eq!(fetched[0].chunk_index, 0);
        assert_eq!(fetched[1].chunk_index, 1);

        assert!(storage.chunk_exists("c1").unwrap());
        assert!(!storage.chunk_exists("c99").unwrap());
    }

    #[test]
    fn test_ingest_log() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();

        storage
            .set_ingest_status("202203", "pending", 0, 0)
            .unwrap();
        let status = storage.get_ingest_status("202203").unwrap().unwrap();
        assert_eq!(status.status, "pending");

        storage
            .set_ingest_status("202203", "chunked", 100, 500)
            .unwrap();
        let status = storage.get_ingest_status("202203").unwrap().unwrap();
        assert_eq!(status.status, "chunked");
        assert_eq!(status.doc_count, 100);
        assert_eq!(status.chunk_count, 500);

        let pending = storage.list_ingest_by_status("pending").unwrap();
        assert_eq!(pending.len(), 0);
        let chunked = storage.list_ingest_by_status("chunked").unwrap();
        assert_eq!(chunked.len(), 1);
    }

    #[test]
    fn test_reset_ingest() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();

        let doc = Document {
            id: "d1".into(),
            processo: None,
            classe: None,
            ministro: None,
            orgao_julgador: None,
            data_publicacao: None,
            data_julgamento: None,
            assuntos: None,
            teor: None,
            tipo: None,
            chunk_count: 0,
            source_file: Some("202203".into()),
        };
        storage.insert_document(&doc).unwrap();
        storage
            .insert_chunks(&[Chunk {
                id: "c1".into(),
                doc_id: "d1".into(),
                chunk_index: 0,
                content: "text".into(),
                token_count: 1,
            }])
            .unwrap();
        storage
            .set_ingest_status("202203", "chunked", 1, 1)
            .unwrap();

        storage.reset_ingest("202203").unwrap();
        assert!(storage.get_document("d1").unwrap().is_none());
        assert!(storage.get_ingest_status("202203").unwrap().is_none());
        assert_eq!(storage.stats().unwrap().chunk_count, 0);
    }

    #[test]
    fn test_embedding_requires_dim() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();

        let result = storage.insert_embedding("c1", &[0.0; 1024]);
        assert!(result.is_err());
    }

    #[test]
    fn test_embedding_with_dim() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 4).unwrap();

        // Inserir chunk primeiro
        storage
            .insert_chunks(&[Chunk {
                id: "c1".into(),
                doc_id: "d1".into(),
                chunk_index: 0,
                content: "text".into(),
                token_count: 1,
            }])
            .unwrap();

        // Inserir embedding
        storage
            .insert_embedding("c1", &[0.1, 0.2, 0.3, 0.4])
            .unwrap();

        let stats = storage.stats().unwrap();
        assert_eq!(stats.embedding_count, 1);
    }
}
