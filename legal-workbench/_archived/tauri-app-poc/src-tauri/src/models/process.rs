use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessFolder {
    pub path: String,
    pub name: String,
    pub pdf_count: usize,
    pub total_size_bytes: u64,
    pub last_modified: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PdfFile {
    pub path: String,
    pub name: String,
    pub size_bytes: u64,
    pub last_modified: String,
    pub extracted_text: Option<String>,
    pub extraction_status: ExtractionStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ExtractionStatus {
    Pending,
    InProgress,
    Completed,
    Failed(String),
}
