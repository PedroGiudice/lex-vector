use std::collections::HashMap;
use std::path::Path;
use std::sync::Arc;

use rusqlite::{Connection, OpenFlags};
use tokio::sync::Semaphore;

use crate::types::{
    ChunkWithMetadata, DocumentChunk, DocumentMeta, DocumentResponse, FiltersResponse,
    SearchFilters,
};

/// Pool simples de conexoes SQLite read-only.
///
/// Usa semaforo para limitar concorrencia. Cada chamada abre uma
/// conexao efemera (SQLite em WAL mode suporta leitores concorrentes).
pub struct MetadataStore {
    path: String,
    semaphore: Arc<Semaphore>,
}

impl MetadataStore {
    /// Abre o store SQLite em modo read-only.
    ///
    /// Verifica que o arquivo existe e que as tabelas esperadas estao presentes.
    pub fn open(path: &str, pool_size: u32) -> anyhow::Result<Self> {
        anyhow::ensure!(
            Path::new(path).exists(),
            "banco SQLite nao encontrado em {path}"
        );

        // Verificar que as tabelas existem
        let conn = open_readonly(path)?;
        let table_check: i64 = conn.query_row(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name IN ('documents', 'chunks')",
            [],
            |row| row.get(0),
        )?;
        anyhow::ensure!(
            table_check == 2,
            "tabelas 'documents' e/ou 'chunks' nao encontradas no banco"
        );

        tracing::info!(path, pool_size, "MetadataStore aberto");

        Ok(Self {
            path: path.to_string(),
            semaphore: Arc::new(Semaphore::new(pool_size as usize)),
        })
    }

    /// Busca metadados de chunks pelo ID, fazendo JOIN com documents.
    pub fn get_chunks_with_metadata(
        &self,
        chunk_ids: &[String],
    ) -> anyhow::Result<HashMap<String, ChunkWithMetadata>> {
        if chunk_ids.is_empty() {
            return Ok(HashMap::new());
        }

        let _permit = self.semaphore.try_acquire()
            .map_err(|_| anyhow::anyhow!("pool de conexoes SQLite esgotado"))?;

        let conn = open_readonly(&self.path)?;

        // Construir query com placeholders
        let placeholders: Vec<&str> = vec!["?"; chunk_ids.len()];
        let sql = format!(
            "SELECT c.id, c.content, c.chunk_index, c.doc_id,
                    d.processo, d.classe, d.ministro, d.orgao_julgador,
                    d.data_publicacao, d.tipo, d.assuntos, c.secao
             FROM chunks c
             JOIN documents d ON c.doc_id = d.id
             WHERE c.id IN ({})",
            placeholders.join(",")
        );

        let params: Vec<&dyn rusqlite::types::ToSql> = chunk_ids
            .iter()
            .map(|id| id as &dyn rusqlite::types::ToSql)
            .collect();

        let mut stmt = conn.prepare(&sql)?;
        let rows = stmt.query_map(params.as_slice(), |row| {
            Ok(ChunkWithMetadata {
                chunk_id: row.get(0)?,
                content: row.get(1)?,
                chunk_index: row.get(2)?,
                doc_id: row.get(3)?,
                processo: row.get::<_, Option<String>>(4)?.unwrap_or_default(),
                classe: row.get::<_, Option<String>>(5)?.unwrap_or_default(),
                ministro: row.get::<_, Option<String>>(6)?.unwrap_or_default(),
                orgao_julgador: row.get::<_, Option<String>>(7)?.unwrap_or_default(),
                data_publicacao: row.get::<_, Option<String>>(8)?.unwrap_or_default(),
                tipo: row.get::<_, Option<String>>(9)?.unwrap_or_default(),
                assuntos: row.get::<_, Option<String>>(10)?.unwrap_or_default(),
                secao: row.get::<_, Option<String>>(11)?,
            })
        })?;

        let mut result = HashMap::new();
        for row in rows {
            let chunk = row?;
            result.insert(chunk.chunk_id.clone(), chunk);
        }
        Ok(result)
    }

    /// Busca todos os chunks de um documento pelo doc_id.
    pub fn get_document_chunks(&self, doc_id: &str) -> anyhow::Result<DocumentResponse> {
        let _permit = self.semaphore.try_acquire()
            .map_err(|_| anyhow::anyhow!("pool de conexoes SQLite esgotado"))?;

        let conn = open_readonly(&self.path)?;

        // Buscar metadados do documento
        let doc = conn.query_row(
            "SELECT id, processo, classe, ministro, orgao_julgador,
                    data_publicacao, tipo, assuntos
             FROM documents WHERE id = ?",
            [doc_id],
            |row| {
                Ok(DocumentMeta {
                    id: row.get(0)?,
                    processo: row.get::<_, Option<String>>(1)?.unwrap_or_default(),
                    classe: row.get::<_, Option<String>>(2)?.unwrap_or_default(),
                    ministro: row.get::<_, Option<String>>(3)?.unwrap_or_default(),
                    orgao_julgador: row.get::<_, Option<String>>(4)?.unwrap_or_default(),
                    data_publicacao: row.get::<_, Option<String>>(5)?.unwrap_or_default(),
                    tipo: row.get::<_, Option<String>>(6)?.unwrap_or_default(),
                    assuntos: row.get::<_, Option<String>>(7)?.unwrap_or_default(),
                })
            },
        )?;

        // Buscar chunks
        let mut stmt = conn.prepare(
            "SELECT id, chunk_index, content, token_count
             FROM chunks WHERE doc_id = ? ORDER BY chunk_index",
        )?;
        let chunks: Vec<DocumentChunk> = stmt
            .query_map([doc_id], |row| {
                Ok(DocumentChunk {
                    id: row.get(0)?,
                    chunk_index: row.get(1)?,
                    content: row.get(2)?,
                    token_count: row.get(3)?,
                })
            })?
            .collect::<Result<Vec<_>, _>>()?;

        let total_chunks = chunks.len();

        Ok(DocumentResponse {
            document: doc,
            chunks,
            total_chunks,
        })
    }

    /// Retorna valores unicos para os filtros (ministros, classes, tipos, orgaos).
    pub fn get_filter_values(&self) -> anyhow::Result<FiltersResponse> {
        let _permit = self.semaphore.try_acquire()
            .map_err(|_| anyhow::anyhow!("pool de conexoes SQLite esgotado"))?;

        let conn = open_readonly(&self.path)?;

        let ministros = query_distinct(&conn, "SELECT DISTINCT ministro FROM documents WHERE ministro IS NOT NULL ORDER BY ministro")?;
        let classes = query_distinct(&conn, "SELECT DISTINCT classe FROM documents WHERE classe IS NOT NULL ORDER BY classe")?;
        let tipos = query_distinct(&conn, "SELECT DISTINCT tipo FROM documents WHERE tipo IS NOT NULL ORDER BY tipo")?;
        let orgaos = query_distinct(&conn, "SELECT DISTINCT orgao_julgador FROM documents WHERE orgao_julgador IS NOT NULL ORDER BY orgao_julgador")?;

        Ok(FiltersResponse {
            ministros,
            classes,
            tipos,
            orgaos_julgadores: orgaos,
        })
    }

    /// Filtra chunk_ids aplicando criterios nos documentos pai.
    ///
    /// Retorna apenas os chunk_ids cujo documento atende todos os filtros fornecidos.
    pub fn filter_chunk_ids(
        &self,
        chunk_ids: &[String],
        filters: &SearchFilters,
    ) -> anyhow::Result<Vec<String>> {
        if chunk_ids.is_empty() || filters.is_empty() {
            return Ok(chunk_ids.to_vec());
        }

        let _permit = self.semaphore.try_acquire()
            .map_err(|_| anyhow::anyhow!("pool de conexoes SQLite esgotado"))?;

        let conn = open_readonly(&self.path)?;

        // Construir WHERE clause dinamica
        let placeholders: Vec<&str> = vec!["?"; chunk_ids.len()];
        let mut sql = format!(
            "SELECT c.id FROM chunks c JOIN documents d ON c.doc_id = d.id WHERE c.id IN ({})",
            placeholders.join(",")
        );
        let mut params: Vec<Box<dyn rusqlite::types::ToSql>> = chunk_ids
            .iter()
            .map(|id| Box::new(id.clone()) as Box<dyn rusqlite::types::ToSql>)
            .collect();

        if let Some(ref ministro) = filters.ministro {
            sql.push_str(" AND d.ministro = ?");
            params.push(Box::new(ministro.clone()));
        }
        if let Some(ref tipo) = filters.tipo {
            sql.push_str(" AND d.tipo = ?");
            params.push(Box::new(tipo.clone()));
        }
        if let Some(ref classe) = filters.classe {
            sql.push_str(" AND d.classe = ?");
            params.push(Box::new(classe.clone()));
        }
        if let Some(ref processo_like) = filters.processo_like {
            sql.push_str(" AND d.processo LIKE ?");
            params.push(Box::new(processo_like.clone()));
        }
        if let Some(ref orgao) = filters.orgao_julgador {
            sql.push_str(" AND d.orgao_julgador = ?");
            params.push(Box::new(orgao.clone()));
        }
        if let Some(ref data_from) = filters.data_from {
            sql.push_str(" AND d.data_publicacao >= ?");
            params.push(Box::new(data_from.clone()));
        }
        if let Some(ref data_to) = filters.data_to {
            sql.push_str(" AND d.data_publicacao <= ?");
            params.push(Box::new(data_to.clone()));
        }

        let param_refs: Vec<&dyn rusqlite::types::ToSql> =
            params.iter().map(|p| p.as_ref()).collect();

        let mut stmt = conn.prepare(&sql)?;
        let filtered: Vec<String> = stmt
            .query_map(param_refs.as_slice(), |row| row.get(0))?
            .collect::<Result<Vec<_>, _>>()?;

        Ok(filtered)
    }

    /// Busca chunks adjacentes ao chunk dado, para expansao de contexto.
    ///
    /// Retorna tuplas `(chunk_index, content, secao)` dos chunks vizinhos
    /// dentro de `window` posicoes, excluindo o chunk central.
    pub fn get_adjacent_chunks(
        &self,
        doc_id: &str,
        chunk_index: i64,
        window: usize,
    ) -> anyhow::Result<Vec<(i64, String, Option<String>)>> {
        let _permit = self
            .semaphore
            .try_acquire()
            .map_err(|_| anyhow::anyhow!("pool de conexoes SQLite esgotado"))?;

        let conn = open_readonly(&self.path)?;
        let from = (chunk_index - window as i64).max(0);
        let to = chunk_index + window as i64;

        let mut stmt = conn.prepare(
            "SELECT chunk_index, content, secao FROM chunks
             WHERE doc_id = ? AND chunk_index >= ? AND chunk_index <= ?
             AND chunk_index != ?
             ORDER BY chunk_index",
        )?;

        let rows = stmt.query_map(
            rusqlite::params![doc_id, from, to, chunk_index],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
        )?;

        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    /// Conta total de documentos no banco.
    pub fn document_count(&self) -> anyhow::Result<u64> {
        let _permit = self.semaphore.try_acquire()
            .map_err(|_| anyhow::anyhow!("pool de conexoes SQLite esgotado"))?;

        let conn = open_readonly(&self.path)?;
        let count: i64 = conn.query_row("SELECT count(*) FROM documents", [], |row| row.get(0))?;
        Ok(count as u64)
    }

    /// Verifica se o banco esta acessivel.
    pub fn health_check(&self) -> bool {
        open_readonly(&self.path)
            .and_then(|conn| {
                conn.query_row("SELECT 1", [], |_| Ok(()))
                    .map_err(Into::into)
            })
            .is_ok()
    }
}

/// Abre conexao SQLite em modo read-only.
fn open_readonly(path: &str) -> anyhow::Result<Connection> {
    let conn = Connection::open_with_flags(
        path,
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    )?;
    Ok(conn)
}

/// Executa query que retorna uma coluna de strings.
fn query_distinct(conn: &Connection, sql: &str) -> anyhow::Result<Vec<String>> {
    let mut stmt = conn.prepare(sql)?;
    let values: Vec<String> = stmt
        .query_map([], |row| row.get(0))?
        .collect::<Result<Vec<_>, _>>()?;
    Ok(values)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    #[ignore]
    fn test_open_readonly() {
        let store = MetadataStore::open("db/stj-vec.db", 2);
        assert!(store.is_ok(), "falha ao abrir: {:?}", store.err());
    }

    #[test]
    #[ignore]
    fn test_get_filter_values() {
        let store = MetadataStore::open("db/stj-vec.db", 2)
            .expect("falha ao abrir banco");
        let filters = store.get_filter_values().expect("falha ao buscar filtros");
        assert!(!filters.ministros.is_empty(), "ministros vazio");
        assert!(!filters.tipos.is_empty(), "tipos vazio");
        assert!(!filters.classes.is_empty(), "classes vazio");
    }
}
