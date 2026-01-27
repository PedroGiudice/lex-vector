use crate::models::AppError;
use rusqlite::{Connection, params};
use sha2::{Sha256, Digest};
use std::io::Read;
use std::path::PathBuf;
use tauri::Manager;

fn get_db_path(app: &tauri::AppHandle) -> PathBuf {
    app.path().app_data_dir().unwrap().join("cache.db")
}

#[tauri::command]
pub async fn init_cache(app: tauri::AppHandle) -> Result<(), AppError> {
    let db_path = get_db_path(&app);
    if let Some(parent) = db_path.parent() {
        std::fs::create_dir_all(parent)?;
    }

    let conn = Connection::open(&db_path)?;
    conn.execute(
        "CREATE TABLE IF NOT EXISTS api_cache (
            file_hash TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            api_response TEXT NOT NULL,
            backend_url TEXT NOT NULL,
            cached_at INTEGER NOT NULL
        )",
        [],
    )?;
    Ok(())
}

#[tauri::command]
pub async fn get_cached_result(
    app: tauri::AppHandle,
    file_hash: String,
) -> Result<Option<String>, AppError> {
    let db_path = get_db_path(&app);
    let conn = Connection::open(&db_path)?;

    let result: Result<String, _> = conn.query_row(
        "SELECT api_response FROM api_cache WHERE file_hash = ?",
        params![file_hash],
        |row| row.get(0),
    );

    Ok(result.ok())
}

#[tauri::command]
pub async fn save_cached_result(
    app: tauri::AppHandle,
    file_hash: String,
    file_path: String,
    api_response: String,
    backend_url: String,
) -> Result<(), AppError> {
    let db_path = get_db_path(&app);
    let conn = Connection::open(&db_path)?;

    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs();

    conn.execute(
        "INSERT OR REPLACE INTO api_cache (file_hash, file_path, api_response, backend_url, cached_at)
         VALUES (?, ?, ?, ?, ?)",
        params![file_hash, file_path, api_response, backend_url, now as i64],
    )?;

    Ok(())
}

#[tauri::command]
pub async fn hash_file(file_path: String) -> Result<String, AppError> {
    let mut file = std::fs::File::open(&file_path)?;
    let mut hasher = Sha256::new();
    let mut buffer = [0u8; 8192];

    loop {
        let bytes_read = file.read(&mut buffer)?;
        if bytes_read == 0 {
            break;
        }
        hasher.update(&buffer[..bytes_read]);
    }

    Ok(format!("{:x}", hasher.finalize()))
}
