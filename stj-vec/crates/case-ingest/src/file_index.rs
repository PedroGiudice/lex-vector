use std::path::Path;

use anyhow::{Context, Result};
use rusqlite::Connection;

/// Record representing a tracked file in the index.
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct FileRecord {
    pub path: String,
    pub mtime: i64,
    pub hash_md5: String,
    pub status: String,
}

/// File index backed by a `SQLite` table.
///
/// Tracks which files have been indexed, their modification time, and content hash.
pub struct FileIndex<'a> {
    conn: &'a Connection,
}

#[allow(dead_code)]
impl<'a> FileIndex<'a> {
    /// Creates a new `FileIndex`, initializing the table if it does not exist.
    ///
    /// # Errors
    ///
    /// Returns an error if the table creation SQL fails.
    pub fn new(conn: &'a Connection) -> Result<Self> {
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS file_index (
                path     TEXT PRIMARY KEY,
                mtime    INTEGER NOT NULL,
                hash_md5 TEXT NOT NULL,
                status   TEXT NOT NULL DEFAULT 'indexed'
            );",
        )
        .context("failed to create file_index table")?;
        Ok(Self { conn })
    }

    /// Gets a file record by path.
    ///
    /// # Errors
    ///
    /// Returns an error if the query fails.
    pub fn get(&self, path: &str) -> Result<Option<FileRecord>> {
        let mut stmt = self
            .conn
            .prepare("SELECT path, mtime, hash_md5, status FROM file_index WHERE path = ?1")?;
        let mut rows = stmt.query_map([path], |row| {
            Ok(FileRecord {
                path: row.get(0)?,
                mtime: row.get(1)?,
                hash_md5: row.get(2)?,
                status: row.get(3)?,
            })
        })?;
        match rows.next() {
            Some(row) => Ok(Some(row?)),
            None => Ok(None),
        }
    }

    /// Inserts or updates a file record.
    ///
    /// # Errors
    ///
    /// Returns an error if the upsert fails.
    pub fn upsert(&self, path: &str, mtime: i64, hash: &str) -> Result<()> {
        self.conn.execute(
            "INSERT INTO file_index (path, mtime, hash_md5, status)
             VALUES (?1, ?2, ?3, 'indexed')
             ON CONFLICT(path) DO UPDATE SET mtime = ?2, hash_md5 = ?3, status = 'indexed'",
            rusqlite::params![path, mtime, hash],
        )?;
        Ok(())
    }

    /// Removes a file record by path.
    ///
    /// # Errors
    ///
    /// Returns an error if the delete fails.
    pub fn remove(&self, path: &str) -> Result<()> {
        self.conn
            .execute("DELETE FROM file_index WHERE path = ?1", [path])?;
        Ok(())
    }

    /// Returns all file records in the index.
    ///
    /// # Errors
    ///
    /// Returns an error if the query fails.
    pub fn all(&self) -> Result<Vec<FileRecord>> {
        let mut stmt = self
            .conn
            .prepare("SELECT path, mtime, hash_md5, status FROM file_index")?;
        let rows = stmt.query_map([], |row| {
            Ok(FileRecord {
                path: row.get(0)?,
                mtime: row.get(1)?,
                hash_md5: row.get(2)?,
                status: row.get(3)?,
            })
        })?;
        let mut records = Vec::new();
        for row in rows {
            records.push(row?);
        }
        Ok(records)
    }
}

/// Computes the MD5 hash of a file's contents.
///
/// # Errors
///
/// Returns an error if the file cannot be read.
pub fn compute_file_hash(path: &Path) -> Result<String> {
    let content =
        std::fs::read(path).with_context(|| format!("failed to read {}", path.display()))?;
    let digest = md5::compute(content);
    Ok(format!("{digest:x}"))
}

/// Returns the file modification time as a Unix timestamp in seconds.
///
/// # Errors
///
/// Returns an error if the file metadata cannot be read.
pub fn get_mtime(path: &Path) -> Result<i64> {
    let metadata = std::fs::metadata(path)
        .with_context(|| format!("failed to get metadata for {}", path.display()))?;
    let mtime = metadata
        .modified()
        .context("modified time not available")?
        .duration_since(std::time::UNIX_EPOCH)
        .context("system time before unix epoch")?;
    #[allow(clippy::cast_possible_wrap)]
    let secs = mtime.as_secs() as i64;
    Ok(secs)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::NamedTempFile;

    #[test]
    fn test_file_index_crud() {
        let conn = Connection::open_in_memory().unwrap();
        let idx = FileIndex::new(&conn).unwrap();

        // Insert
        idx.upsert("/tmp/test.pdf", 1000, "abc123").unwrap();
        let rec = idx.get("/tmp/test.pdf").unwrap().unwrap();
        assert_eq!(rec.path, "/tmp/test.pdf");
        assert_eq!(rec.mtime, 1000);
        assert_eq!(rec.hash_md5, "abc123");
        assert_eq!(rec.status, "indexed");

        // Update
        idx.upsert("/tmp/test.pdf", 2000, "def456").unwrap();
        let rec = idx.get("/tmp/test.pdf").unwrap().unwrap();
        assert_eq!(rec.mtime, 2000);
        assert_eq!(rec.hash_md5, "def456");

        // All
        idx.upsert("/tmp/other.pdf", 3000, "ghi789").unwrap();
        let all = idx.all().unwrap();
        assert_eq!(all.len(), 2);

        // Delete
        idx.remove("/tmp/test.pdf").unwrap();
        assert!(idx.get("/tmp/test.pdf").unwrap().is_none());
        assert_eq!(idx.all().unwrap().len(), 1);
    }

    #[test]
    fn test_compute_file_hash() {
        let mut file = NamedTempFile::new().unwrap();
        let content = b"hello world";
        file.write_all(content).unwrap();
        file.flush().unwrap();

        let hash = compute_file_hash(file.path()).unwrap();
        let expected = format!("{:x}", md5::compute(content));
        assert_eq!(hash, expected);
    }
}
