//! SQLite + sqlite-vec Storage para documentos legais (CF, TCU, TESEMO)

use anyhow::{Context, Result};
use rusqlite::{params, Connection};
use std::path::Path;
use std::sync::Mutex;
use zerocopy::AsBytes;

use crate::types::{DbStats, LegalChunk, LegalDocument, SourceStats};

const SCHEMA_SQL: &str = r#"
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    tipo TEXT,
    titulo TEXT,
    texto TEXT,
    fonte TEXT,
    url TEXT,
    data_publicacao TEXT,
    metadata TEXT,
    source_name TEXT
);

CREATE INDEX IF NOT EXISTS idx_docs_tipo ON documents(tipo);
CREATE INDEX IF NOT EXISTS idx_docs_source ON documents(source_name);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    chunk_index INTEGER,
    content TEXT NOT NULL,
    token_count INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);

CREATE TABLE IF NOT EXISTS ingest_log (
    source_name TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    doc_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    started_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    error TEXT
);
"#;

/// Storage thread-safe para documentos legais.
pub struct Storage {
    conn: Mutex<Connection>,
    embedding_dim: usize,
}

fn register_sqlite_vec() {
    unsafe {
        rusqlite::ffi::sqlite3_auto_extension(Some(std::mem::transmute(
            sqlite_vec::sqlite3_vec_init as *const (),
        )));
    }
}

impl Storage {
    /// Abre ou cria banco com schema legal.
    pub fn open(path: &str, embedding_dim: usize) -> Result<Self> {
        register_sqlite_vec();

        if let Some(parent) = Path::new(path).parent() {
            std::fs::create_dir_all(parent).ok();
        }

        let conn =
            Connection::open(path).with_context(|| format!("falha ao abrir SQLite em {path}"))?;

        conn.execute_batch(SCHEMA_SQL)
            .context("falha ao aplicar schema")?;

        if embedding_dim > 0 {
            let vec_sql = format!(
                "CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
                    chunk_id TEXT PRIMARY KEY,
                    embedding float[{embedding_dim}] distance_metric=cosine
                )"
            );
            conn.execute_batch(&vec_sql)
                .context("falha ao criar vec_chunks")?;
        }

        Ok(Self {
            conn: Mutex::new(conn),
            embedding_dim,
        })
    }

    fn lock(&self) -> Result<std::sync::MutexGuard<'_, Connection>> {
        self.conn
            .lock()
            .map_err(|e| anyhow::anyhow!("mutex poisoned: {e}"))
    }

    // === Documents ===

    /// Insere ou atualiza documento legal.
    pub fn insert_document(&self, doc: &LegalDocument, source_name: &str) -> Result<()> {
        let conn = self.lock()?;
        let metadata_str = serde_json::to_string(&doc.metadata)
            .unwrap_or_else(|_| "{}".to_string());
        conn.execute(
            "INSERT OR REPLACE INTO documents
             (id, tipo, titulo, texto, fonte, url, data_publicacao, metadata, source_name)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
            params![
                doc.id,
                doc.tipo,
                doc.titulo,
                doc.texto,
                doc.fonte,
                doc.url,
                doc.data_publicacao,
                metadata_str,
                source_name,
            ],
        )?;
        Ok(())
    }

    /// Insere documentos em batch.
    pub fn insert_documents_batch(
        &self,
        docs: &[LegalDocument],
        source_name: &str,
    ) -> Result<()> {
        let conn = self.lock()?;
        let mut stmt = conn.prepare(
            "INSERT OR REPLACE INTO documents
             (id, tipo, titulo, texto, fonte, url, data_publicacao, metadata, source_name)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
        )?;
        for doc in docs {
            let metadata_str = serde_json::to_string(&doc.metadata)
                .unwrap_or_else(|_| "{}".to_string());
            stmt.execute(params![
                doc.id,
                doc.tipo,
                doc.titulo,
                doc.texto,
                doc.fonte,
                doc.url,
                doc.data_publicacao,
                metadata_str,
                source_name,
            ])?;
        }
        Ok(())
    }

    // === Chunks ===

    /// Insere chunks em batch.
    pub fn insert_chunks(&self, chunks: &[LegalChunk]) -> Result<()> {
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

    // === Embeddings ===

    /// Insere embedding para um chunk.
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

    /// Insere embeddings em batch.
    pub fn insert_embeddings_batch(&self, pairs: &[(String, Vec<f32>)]) -> Result<()> {
        if self.embedding_dim == 0 {
            anyhow::bail!("embedding not configured (dim=0)");
        }
        let conn = self.lock()?;
        let mut stmt = conn.prepare(
            "INSERT OR REPLACE INTO vec_chunks (chunk_id, embedding) VALUES (?1, ?2)",
        )?;
        for (chunk_id, embedding) in pairs {
            stmt.execute(params![chunk_id, embedding.as_bytes()])?;
        }
        Ok(())
    }

    /// Retorna chunks sem embeddings.
    pub fn chunks_without_embeddings(&self) -> Result<Vec<LegalChunk>> {
        let conn = self.lock()?;

        let sql = if self.embedding_dim > 0 {
            "SELECT c.id, c.doc_id, c.chunk_index, c.content, c.token_count
             FROM chunks c
             LEFT JOIN vec_chunks v ON v.chunk_id = c.id
             WHERE v.chunk_id IS NULL
             ORDER BY c.doc_id, c.chunk_index"
        } else {
            // Sem vec_chunks, todos os chunks estao sem embedding
            "SELECT id, doc_id, chunk_index, content, token_count
             FROM chunks ORDER BY doc_id, chunk_index"
        };

        let mut stmt = conn.prepare(sql)?;
        let chunks = stmt
            .query_map([], |row| {
                Ok(LegalChunk {
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

    // === Ingest Log ===

    /// Define status de ingestion.
    pub fn set_ingest_status(
        &self,
        source: &str,
        status: &str,
        doc_count: i32,
        chunk_count: i32,
    ) -> Result<()> {
        let conn = self.lock()?;
        conn.execute(
            "INSERT INTO ingest_log (source_name, status, doc_count, chunk_count)
             VALUES (?1, ?2, ?3, ?4)
             ON CONFLICT(source_name) DO UPDATE SET
             status = ?2, doc_count = ?3, chunk_count = ?4,
             completed_at = CASE WHEN ?2 = 'done' THEN datetime('now') ELSE completed_at END",
            params![source, status, doc_count, chunk_count],
        )?;
        Ok(())
    }

    /// Retorna status de ingestion de um source.
    pub fn get_ingest_status(&self, source: &str) -> Result<Option<String>> {
        let conn = self.lock()?;
        let result = conn.query_row(
            "SELECT status FROM ingest_log WHERE source_name = ?",
            params![source],
            |row| row.get::<_, String>(0),
        );

        match result {
            Ok(s) => Ok(Some(s)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(e.into()),
        }
    }

    // === Stats ===

    /// Estatisticas do banco.
    pub fn stats(&self) -> Result<DbStats> {
        let conn = self.lock()?;

        let document_count: i64 =
            conn.query_row("SELECT COUNT(*) FROM documents", [], |row| row.get(0))?;
        let chunk_count: i64 =
            conn.query_row("SELECT COUNT(*) FROM chunks", [], |row| row.get(0))?;

        let embedding_count: i64 = if self.embedding_dim > 0 {
            conn.query_row("SELECT COUNT(*) FROM vec_chunks", [], |row| row.get(0))
                .unwrap_or(0)
        } else {
            0
        };

        let mut stmt = conn.prepare(
            "SELECT source_name, status, doc_count, chunk_count FROM ingest_log ORDER BY source_name",
        )?;
        let sources = stmt
            .query_map([], |row| {
                Ok(SourceStats {
                    source: row.get(0)?,
                    status: row.get(1)?,
                    doc_count: row.get::<_, Option<i32>>(2)?.unwrap_or(0),
                    chunk_count: row.get::<_, Option<i32>>(3)?.unwrap_or(0),
                })
            })?
            .filter_map(|r| r.ok())
            .collect();

        Ok(DbStats {
            document_count,
            chunk_count,
            embedding_count,
            sources,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn make_doc(id: &str) -> LegalDocument {
        LegalDocument {
            id: id.into(),
            tipo: "constituicao".into(),
            titulo: "Art. 5".into(),
            texto: "Todos sao iguais perante a lei".into(),
            fonte: "cf88".into(),
            url: Some("http://example.com".into()),
            data_publicacao: Some("1988-10-05".into()),
            metadata: json!({}),
        }
    }

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
    fn test_insert_and_query_document() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();

        let doc = make_doc("d1");
        storage.insert_document(&doc, "cf88").unwrap();

        let stats = storage.stats().unwrap();
        assert_eq!(stats.document_count, 1);
    }

    #[test]
    fn test_insert_documents_batch() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();

        let docs = vec![make_doc("d1"), make_doc("d2"), make_doc("d3")];
        storage.insert_documents_batch(&docs, "cf88").unwrap();

        let stats = storage.stats().unwrap();
        assert_eq!(stats.document_count, 3);
    }

    #[test]
    fn test_insert_chunks_and_without_embeddings() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 4).unwrap();

        let chunks = vec![
            LegalChunk {
                id: "c1".into(),
                doc_id: "d1".into(),
                chunk_index: 0,
                content: "texto do chunk".into(),
                token_count: 3,
            },
            LegalChunk {
                id: "c2".into(),
                doc_id: "d1".into(),
                chunk_index: 1,
                content: "segundo chunk".into(),
                token_count: 2,
            },
        ];
        storage.insert_chunks(&chunks).unwrap();

        let without = storage.chunks_without_embeddings().unwrap();
        assert_eq!(without.len(), 2);

        // Inserir embedding para c1
        storage.insert_embedding("c1", &[0.1, 0.2, 0.3, 0.4]).unwrap();

        let without = storage.chunks_without_embeddings().unwrap();
        assert_eq!(without.len(), 1);
        assert_eq!(without[0].id, "c2");
    }

    #[test]
    fn test_embeddings_batch() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 4).unwrap();

        storage.insert_chunks(&[LegalChunk {
            id: "c1".into(),
            doc_id: "d1".into(),
            chunk_index: 0,
            content: "t".into(),
            token_count: 1,
        }]).unwrap();

        let pairs = vec![("c1".into(), vec![0.1, 0.2, 0.3, 0.4])];
        storage.insert_embeddings_batch(&pairs).unwrap();

        let stats = storage.stats().unwrap();
        assert_eq!(stats.embedding_count, 1);
    }

    #[test]
    fn test_embedding_requires_dim() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();
        assert!(storage.insert_embedding("c1", &[0.0; 4]).is_err());
    }

    #[test]
    fn test_ingest_log() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();

        storage.set_ingest_status("cf88", "pending", 0, 0).unwrap();
        assert_eq!(storage.get_ingest_status("cf88").unwrap(), Some("pending".into()));

        storage.set_ingest_status("cf88", "done", 10, 50).unwrap();
        assert_eq!(storage.get_ingest_status("cf88").unwrap(), Some("done".into()));

        assert_eq!(storage.get_ingest_status("nope").unwrap(), None);

        let stats = storage.stats().unwrap();
        assert_eq!(stats.sources.len(), 1);
        assert_eq!(stats.sources[0].doc_count, 10);
    }
}
