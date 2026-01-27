use serde::Serialize;
use thiserror::Error;

#[derive(Debug, Error, Serialize)]
pub enum AppError {
    #[error("Arquivo nao encontrado: {0}")]
    FileNotFound(String),

    #[error("Permissao negada: {0}")]
    PermissionDenied(String),

    #[error("Diretorio invalido: {0}")]
    InvalidDirectory(String),

    #[error("Erro de IO: {0}")]
    IoError(String),

    #[error("Erro de banco: {0}")]
    DatabaseError(String),
}

impl From<std::io::Error> for AppError {
    fn from(err: std::io::Error) -> Self {
        match err.kind() {
            std::io::ErrorKind::NotFound => AppError::FileNotFound(err.to_string()),
            std::io::ErrorKind::PermissionDenied => AppError::PermissionDenied(err.to_string()),
            _ => AppError::IoError(err.to_string()),
        }
    }
}

impl From<rusqlite::Error> for AppError {
    fn from(err: rusqlite::Error) -> Self {
        AppError::DatabaseError(err.to_string())
    }
}
