// Text Extractor Types

export type ExtractionEngine = 'marker' | 'pdfplumber';
export type ExtractionStatus =
  | 'idle'
  | 'preflight'
  | 'configuring'
  | 'processing'
  | 'success'
  | 'error';
export type LogLevel = 'info' | 'warning' | 'error' | 'success';

export interface FileInfo {
  name: string;
  size: number;
  pages?: number;
  type: string;
}

export interface Margins {
  top: number;
  bottom: number;
  left: number;
  right: number;
}

export interface ExtractOptions {
  engine: ExtractionEngine;
  useGemini: boolean;
  margins: Margins;
  ignoreTerms: string[];
}

export interface JobSubmitResponse {
  job_id: string;
  status: string;
  estimated_completion?: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: string;
  progress: number;
  error_message?: string;
}

export interface ExtractedEntity {
  type: 'pessoa' | 'cpf' | 'cnpj' | 'data' | 'valor' | 'email' | 'telefone';
  value: string;
  count: number;
}

/**
 * Additional metadata from extraction (varies by engine/mode).
 * This is the `metadata` field from backend, NOT structured.
 */
export interface ExtractionMetadataExtra {
  file_size_bytes?: number;
  ocr_applied?: boolean;
  extraction_mode?: 'modal_gpu' | 'cpu' | 'pdfplumber';
  modal_gpu?: string;
  modal_processing_time?: number;
  native_pages?: number;
  ocr_pages?: number;
  [key: string]: unknown;
}

/**
 * Extraction result from backend.
 * Fields are at root level, NOT nested in metadata.
 */
export interface ExtractionResult {
  job_id: string;
  text: string;
  pages_processed: number;
  execution_time_seconds: number;
  engine_used: string;
  gemini_enhanced: boolean;
  metadata?: ExtractionMetadataExtra;
  entities?: ExtractedEntity[];
}

export interface LogEntry {
  id: string;
  timestamp: Date;
  message: string;
  level: LogLevel;
}

export interface TextExtractorState {
  // Upload
  file: File | null;
  fileInfo: FileInfo | null;

  // Config
  engine: ExtractionEngine;
  useGemini: boolean;
  margins: Margins;
  ignoreTerms: string[];

  // Job
  jobId: string | null;
  status: ExtractionStatus;
  progress: number;

  // Results
  result: ExtractionResult | null;

  // Console
  logs: LogEntry[];

  // Actions
  setFile: (file: File | null) => void;
  setEngine: (engine: ExtractionEngine) => void;
  setUseGemini: (useGemini: boolean) => void;
  setMargins: (margins: Margins) => void;
  setIgnoreTerms: (terms: string[]) => void;
  addIgnoreTerm: (term: string) => void;
  removeIgnoreTerm: (term: string) => void;
  loadPreset: (preset: 'lgpd' | 'court' | 'contract') => void;
  submitJob: () => Promise<void>;
  pollJob: () => Promise<void>;
  reset: () => void;
  addLog: (message: string, level?: LogLevel) => void;
  clearLogs: () => void;
}
