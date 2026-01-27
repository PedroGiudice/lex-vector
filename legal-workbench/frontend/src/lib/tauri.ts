/**
 * Tauri environment detection and utilities
 */

// API base URL for production backend
const PRODUCTION_API = 'http://64.181.162.38';

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
