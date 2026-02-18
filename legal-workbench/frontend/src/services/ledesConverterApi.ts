import type {
  ConvertLedesResponse,
  LedesFileValidation,
  LedesMatter,
  LedesValidationResponse,
} from '@/types';

const isTauri =
  typeof window !== 'undefined' && !!(window as unknown as { __TAURI__?: unknown }).__TAURI__;
const API_BASE_URL = isTauri
  ? import.meta.env.VITE_LEDES_API_URL || 'http://localhost:8003'
  : '/api/ledes';

/** Native fetch for all environments.
 * tauriFetch (plugin-http/reqwest) hangs on Tailscale IPs and localhost on Windows.
 * Native fetch works via CSP connect-src whitelist + SSH reverse tunnel. */
const httpFetch = globalThis.fetch.bind(globalThis);

// Constants
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const VALID_MIME_TYPES = [
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/octet-stream', // Fallback for some browsers
];

/**
 * Validate a DOCX file before upload
 * @param file - File to validate
 * @returns Validation result with error message if invalid
 */
export const validateDocxFile = (file: File): LedesFileValidation => {
  // Validate file size (10MB limit)
  if (file.size > MAX_FILE_SIZE) {
    return {
      valid: false,
      error: `File size exceeds 10MB limit (${(file.size / 1024 / 1024).toFixed(2)}MB)`,
    };
  }

  // Validate MIME type (allow empty string for browser compatibility)
  if (!VALID_MIME_TYPES.includes(file.type) && file.type !== '') {
    return {
      valid: false,
      error: 'Invalid file type. Please upload a valid .docx file.',
    };
  }

  // Validate file extension as final check
  if (!file.name.toLowerCase().endsWith('.docx')) {
    return {
      valid: false,
      error: 'Invalid file extension. Please upload a .docx file.',
    };
  }

  return { valid: true };
};

/**
 * Sanitize filename to prevent XSS attacks when displaying
 * Converts potentially dangerous HTML characters to HTML entities
 * @param filename - Original filename
 * @returns Sanitized filename safe for display
 */
export const sanitizeFilename = (filename: string): string => {
  return filename.replace(/[<>"'&]/g, (char) => {
    const entities: Record<string, string> = {
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
      '&': '&amp;',
    };
    return entities[char] || char;
  });
};

/**
 * LEDES Converter API client
 * Provides methods for converting DOCX invoices to LEDES format
 */
export const ledesConverterApi = {
  /**
   * Check LEDES service health status
   * @returns Promise resolving to health status
   * @throws Error if service is unreachable
   */
  healthCheck: async (): Promise<{ status: string; service?: string }> => {
    const response = await httpFetch(`${API_BASE_URL}/health`);
    if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
    return response.json();
  },

  /**
   * Convert a DOCX invoice file to LEDES 1998B format
   * @param file - DOCX file to convert (max 10MB)
   * @param matterName - Optional matter name to associate with the conversion
   * @param onProgress - Optional progress callback (0-100 percent)
   * @returns Promise resolving to conversion result with LEDES content and extracted data
   * @throws Error if conversion fails or file is invalid
   */
  convertDocxToLedes: async (
    file: File,
    matterName?: string,
    _onProgress?: (progress: number) => void
  ): Promise<ConvertLedesResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    if (matterName) {
      formData.append('config', JSON.stringify({ matter_name: matterName }));
    }

    const response = await httpFetch(`${API_BASE_URL}/convert/docx-to-ledes`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error(`Conversion failed: ${response.status}`);
    return response.json();
  },

  /**
   * List all configured matters
   * @returns Promise resolving to array of matters
   */
  listMatters: async (): Promise<LedesMatter[]> => {
    const response = await httpFetch(`${API_BASE_URL}/matters`);
    if (!response.ok) throw new Error(`Failed to list matters: ${response.status}`);
    return response.json();
  },

  /**
   * Convert pasted text to LEDES 1998B format
   * @param text - Raw text content to convert
   * @param matterName - Optional matter name to associate with the conversion
   * @returns Promise resolving to conversion result with LEDES content
   */
  convertTextToLedes: async (text: string, matterName?: string): Promise<ConvertLedesResponse> => {
    const payload: { text: string; matter_name?: string } = { text };
    if (matterName) {
      payload.matter_name = matterName;
    }
    const response = await httpFetch(`${API_BASE_URL}/convert/text-to-ledes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`Text conversion failed: ${response.status}`);
    return response.json();
  },

  /**
   * Validate LEDES 1998B content
   * @param ledesContent - LEDES content string to validate
   * @returns Promise resolving to validation result
   */
  validateLedes: async (ledesContent: string): Promise<LedesValidationResponse> => {
    const formData = new FormData();
    formData.append('ledes_content', ledesContent);
    const response = await httpFetch(`${API_BASE_URL}/validate`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error(`Validation failed: ${response.status}`);
    return response.json();
  },
};

export default ledesConverterApi;
