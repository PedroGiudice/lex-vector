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
