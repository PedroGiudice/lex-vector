use crate::models::{AppError, PdfFile, ProcessFolder, ExtractionStatus};
use std::fs;
use std::path::Path;
use chrono::{DateTime, Utc};

#[tauri::command]
pub async fn list_process_folders(root_path: String) -> Result<Vec<ProcessFolder>, AppError> {
    let path = Path::new(&root_path);
    if !path.is_dir() {
        return Err(AppError::InvalidDirectory(root_path));
    }

    let mut folders = Vec::new();
    for entry in fs::read_dir(path)? {
        let entry = entry?;
        let entry_path = entry.path();
        if entry_path.is_dir() {
            let pdf_count = count_pdfs(&entry_path);
            let metadata = entry.metadata()?;

            folders.push(ProcessFolder {
                path: entry_path.to_string_lossy().to_string(),
                name: entry.file_name().to_string_lossy().to_string(),
                pdf_count,
                total_size_bytes: calculate_dir_size(&entry_path),
                last_modified: format_time(metadata.modified()?),
            });
        }
    }

    folders.sort_by(|a, b| b.last_modified.cmp(&a.last_modified));
    Ok(folders)
}

#[tauri::command]
pub async fn list_pdfs_in_folder(folder_path: String) -> Result<Vec<PdfFile>, AppError> {
    let path = Path::new(&folder_path);
    if !path.is_dir() {
        return Err(AppError::InvalidDirectory(folder_path));
    }

    let mut pdfs = Vec::new();
    collect_pdfs_recursive(path, &mut pdfs)?;
    pdfs.sort_by(|a, b| a.name.cmp(&b.name));
    Ok(pdfs)
}

fn count_pdfs(dir: &Path) -> usize {
    walkdir::WalkDir::new(dir)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| e.path().extension().map_or(false, |ext| ext == "pdf"))
        .count()
}

fn calculate_dir_size(dir: &Path) -> u64 {
    walkdir::WalkDir::new(dir)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter_map(|e| e.metadata().ok())
        .filter(|m| m.is_file())
        .map(|m| m.len())
        .sum()
}

fn collect_pdfs_recursive(dir: &Path, pdfs: &mut Vec<PdfFile>) -> Result<(), AppError> {
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();

        if path.is_dir() {
            collect_pdfs_recursive(&path, pdfs)?;
        } else if path.extension().map_or(false, |ext| ext == "pdf") {
            let metadata = entry.metadata()?;
            pdfs.push(PdfFile {
                path: path.to_string_lossy().to_string(),
                name: entry.file_name().to_string_lossy().to_string(),
                size_bytes: metadata.len(),
                last_modified: format_time(metadata.modified()?),
                extracted_text: None,
                extraction_status: ExtractionStatus::Pending,
            });
        }
    }
    Ok(())
}

fn format_time(time: std::time::SystemTime) -> String {
    let datetime: DateTime<Utc> = time.into();
    datetime.format("%Y-%m-%dT%H:%M:%SZ").to_string()
}
