/**
 * TypeScript interfaces matching Rust models from src-tauri
 */

// Process folder from filesystem scan
export interface ProcessFolder {
  path: string;
  name: string;
  pdf_count: number;
  total_size_bytes: number;
  last_modified: string; // ISO 8601
}

// PDF file metadata
export interface PdfFile {
  path: string;
  name: string;
  size_bytes: number;
  last_modified: string; // ISO 8601
  extracted_text: string | null;
  extraction_status: ExtractionStatus;
}

// Extraction status enum (matches Rust enum serialization)
export type ExtractionStatus = 'Pending' | 'InProgress' | 'Completed' | { Failed: string };

// Cache entry structure
export interface CachedResult {
  file_hash: string;
  file_path: string;
  api_response: string;
  backend_url: string;
  cached_at: number; // Unix timestamp
}

// Command result types
export interface TauriCommands {
  list_process_folders: (args: { rootPath: string }) => Promise<ProcessFolder[]>;
  list_pdfs_in_folder: (args: { folderPath: string }) => Promise<PdfFile[]>;
  init_cache: () => Promise<void>;
  get_cached_result: (args: { fileHash: string }) => Promise<string | null>;
  save_cached_result: (args: {
    fileHash: string;
    filePath: string;
    apiResponse: string;
    backendUrl: string;
  }) => Promise<void>;
  hash_file: (args: { filePath: string }) => Promise<string>;
}

// Error type from Tauri commands
export interface TauriError {
  message: string;
  code?: string;
}
