/**
 * Tauri environment detection and utilities
 */

// API base URL for production backend
const PRODUCTION_API = 'http://100.114.203.28';

/**
 * Detect if running inside Tauri desktop app
 */
export function isTauri(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
}

/**
 * Get the appropriate API base URL
 * - Tauri: absolute URL to production server
 * - Web: relative URL (proxied by Vite/nginx)
 */
export function getApiBaseUrl(): string {
  if (isTauri()) {
    return PRODUCTION_API;
  }
  return '';
}

/**
 * Build full API URL for a given path
 */
export function buildApiUrl(path: string): string {
  const base = getApiBaseUrl();
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${normalizedPath}`;
}

/**
 * Open native file picker for PDF selection (Tauri only)
 * Returns null if not in Tauri or user cancels
 */
export async function selectPdfNative(): Promise<File | null> {
  if (!isTauri()) return null;

  try {
    const { open } = await import('@tauri-apps/plugin-dialog');
    const { readFile } = await import('@tauri-apps/plugin-fs');

    const path = await open({
      multiple: false,
      filters: [{ name: 'PDF', extensions: ['pdf'] }],
      title: 'Selecione o PDF',
    });

    if (path && typeof path === 'string') {
      const content = await readFile(path);
      const filename = path.split('/').pop() || 'document.pdf';
      return new File([content], filename, { type: 'application/pdf' });
    }
  } catch (error) {
    console.error('Native file picker error:', error);
  }

  return null;
}

/**
 * Save file using native Tauri dialog (Tauri only)
 * Returns true if saved successfully, false otherwise
 */
export async function saveFileNative(
  content: string,
  defaultFilename: string,
  filters: { name: string; extensions: string[] }[]
): Promise<boolean> {
  if (!isTauri()) return false;

  try {
    const { save } = await import('@tauri-apps/plugin-dialog');
    const { writeTextFile } = await import('@tauri-apps/plugin-fs');

    const path = await save({
      defaultPath: defaultFilename,
      filters,
      title: 'Salvar arquivo',
    });

    if (path) {
      await writeTextFile(path, content);
      return true;
    }
  } catch (error) {
    console.error('Native save error:', error);
  }

  return false;
}

/**
 * Upload PDF for extraction using native Tauri HTTP (bypasses WebKitGTK)
 * Returns job submission response or null if not in Tauri
 */
export interface NativeJobSubmitResponse {
  job_id: string;
  status: string;
  estimated_completion?: number;
  created_at?: string;
}

export interface NativeExtractOptions {
  margins?: { top: number; bottom: number; left: number; right: number };
  ignore_terms?: string[];
}

export async function uploadExtractionJobNative(
  filePath: string,
  engine: string,
  gpuMode: string,
  useGemini: boolean,
  useScript: boolean,
  options: NativeExtractOptions
): Promise<NativeJobSubmitResponse | null> {
  if (!isTauri()) return null;

  try {
    const { invoke } = await import('@tauri-apps/api/core');

    const result = await invoke<NativeJobSubmitResponse>('upload_extraction_job', {
      filePath,
      apiBaseUrl: PRODUCTION_API,
      engine,
      gpuMode,
      useGemini,
      useScript,
      optionsJson: JSON.stringify(options),
    });

    return result;
  } catch (error) {
    console.error('Native upload error:', error);
    throw error;
  }
}
