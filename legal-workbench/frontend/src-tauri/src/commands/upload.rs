//! HTTP upload commands for text extraction.
//! Bypasses WebKitGTK limitations by using reqwest directly.

use crate::models::error::AppError;
use reqwest::multipart::{Form, Part};
use serde::{Deserialize, Serialize};
use std::path::Path;
use tokio::fs;

/// Response from job submission endpoint
#[derive(Debug, Serialize, Deserialize)]
pub struct JobSubmitResponse {
    pub job_id: String,
    pub status: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub estimated_completion: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub created_at: Option<String>,
}

/// Submit PDF extraction job via native HTTP (bypasses WebView)
#[tauri::command]
pub async fn upload_extraction_job(
    file_path: String,
    api_base_url: String,
    engine: String,
    gpu_mode: String,
    use_gemini: bool,
    use_script: bool,
    options_json: String,
) -> Result<JobSubmitResponse, AppError> {
    // Validate file exists
    let path = Path::new(&file_path);
    if !path.exists() {
        return Err(AppError::FileNotFound(file_path));
    }

    // Read file content
    let file_content = fs::read(&file_path).await?;
    let file_name = path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("document.pdf")
        .to_string();

    // Build multipart form
    let file_part = Part::bytes(file_content)
        .file_name(file_name)
        .mime_str("application/pdf")
        .map_err(|e| AppError::HttpError(e.to_string()))?;

    let form = Form::new()
        .part("file", file_part)
        .text("engine", engine)
        .text("gpu_mode", gpu_mode)
        .text("use_gemini", use_gemini.to_string())
        .text("use_script", use_script.to_string())
        .text("options", options_json);

    // Create client with timeout
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(60))
        .build()
        .map_err(|e| AppError::HttpError(e.to_string()))?;

    // Send request
    let url = format!("{}/api/text/api/v1/extract", api_base_url);
    let response = client
        .post(&url)
        .multipart(form)
        .send()
        .await?;

    // Check status
    let status = response.status();
    if !status.is_success() {
        let error_text = response.text().await.unwrap_or_default();
        return Err(AppError::HttpError(format!(
            "HTTP {}: {}",
            status.as_u16(),
            error_text
        )));
    }

    // Parse response
    let result: JobSubmitResponse = response.json().await?;
    Ok(result)
}
