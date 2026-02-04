import axios, { AxiosProgressEvent } from 'axios';
import type { ConvertLedesResponse, LedesFileValidation } from '@/types';
import { getApiBaseUrl } from '@/lib/tauri';

// Use Tailscale IP for Tauri, relative URL for web
const API_BASE_URL = `${getApiBaseUrl()}/api/ledes`;

// Constants
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const VALID_MIME_TYPES = [
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/octet-stream', // Fallback for some browsers
];

// Batch processing types
export interface LedesExtractedData {
  invoice_number?: string;
  invoice_date?: string;
  total_amount?: number;
  client_name?: string;
  matter_name?: string;
  line_items?: Array<{
    date?: string;
    description?: string;
    hours?: number;
    rate?: number;
    amount?: number;
  }>;
}

export interface BatchFileResult {
  filename: string;
  status: 'success' | 'error';
  error?: string;
  extracted_data?: LedesExtractedData;
  ledes_content?: string;
}

export interface BatchConversionResponse {
  total_files: number;
  successful: number;
  failed: number;
  results: BatchFileResult[];
  consolidated_content?: string;
}

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
    const response = await axios.get(`${API_BASE_URL}/health`);
    return response.data;
  },

  /**
   * Convert a DOCX invoice file to LEDES 1998B format
   * @param file - DOCX file to convert (max 10MB)
   * @param config - Optional LEDES configuration (law_firm_id, client_id, matter_id, etc.)
   * @param onProgress - Optional progress callback (0-100 percent)
   * @returns Promise resolving to conversion result with LEDES content and extracted data
   * @throws Error if conversion fails or file is invalid
   */
  convertDocxToLedes: async (
    file: File,
    config?: {
      lawFirmId: string;
      lawFirmName: string;
      clientId: string;
      clientName?: string;
      matterId: string;
      matterName?: string;
      unitCost?: number;
      timekeeperId?: string;
      timekeeperName?: string;
      timekeeperClassification?: string;
      billingStartDate?: string;
      billingEndDate?: string;
      taskCode?: string;
      activityCode?: string;
    },
    onProgress?: (progress: number) => void
  ): Promise<ConvertLedesResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    // Add config as JSON string if provided
    if (config) {
      const configPayload = {
        law_firm_id: config.lawFirmId,
        law_firm_name: config.lawFirmName,
        client_id: config.clientId,
        client_name: config.clientName || '',
        matter_id: config.matterId,
        matter_name: config.matterName || '',
        // Timekeeper and billing fields
        unit_cost: config.unitCost || 300.0,
        timekeeper_id: config.timekeeperId || 'CMR',
        timekeeper_name: config.timekeeperName || 'RODRIGUES, CARLOS MAGNO',
        timekeeper_classification: config.timekeeperClassification || 'PARTNR',
        // Billing period (YYYYMMDD format)
        billing_start_date: config.billingStartDate || '',
        billing_end_date: config.billingEndDate || '',
        // UTBMS codes
        task_code: config.taskCode || 'L100',
        activity_code: config.activityCode || 'A103',
      };
      formData.append('config', JSON.stringify(configPayload));
    }

    const response = await axios.post<ConvertLedesResponse>(
      `${API_BASE_URL}/convert/docx-to-ledes`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent: AxiosProgressEvent) => {
          if (progressEvent.total && onProgress) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(percentCompleted);
          }
        },
        timeout: 30000, // 30 second timeout for large files
      }
    );

    return response.data;
  },

  /**
   * Convert multiple DOCX files to LEDES format (batch processing)
   * @param files - Array of DOCX files to convert (max 10MB each)
   * @param config - Optional LEDES configuration
   * @param consolidate - Whether to consolidate all results into a single file
   * @param onProgress - Optional progress callback (0-100 percent)
   * @returns Promise resolving to batch conversion results
   * @throws Error if conversion fails
   */
  convertBatch: async (
    files: File[],
    config?: {
      lawFirmId: string;
      lawFirmName: string;
      clientId: string;
      clientName?: string;
      matterId: string;
      matterName?: string;
      unitCost?: number;
      timekeeperId?: string;
      timekeeperName?: string;
      timekeeperClassification?: string;
      billingStartDate?: string;
      billingEndDate?: string;
      taskCode?: string;
      activityCode?: string;
    },
    consolidate: boolean = false,
    onProgress?: (progress: number) => void
  ): Promise<BatchConversionResponse> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    if (config) {
      const configPayload = {
        law_firm_id: config.lawFirmId,
        law_firm_name: config.lawFirmName,
        client_id: config.clientId,
        client_name: config.clientName || '',
        matter_id: config.matterId,
        matter_name: config.matterName || '',
        unit_cost: config.unitCost || 300.0,
        timekeeper_id: config.timekeeperId || '',
        timekeeper_name: config.timekeeperName || '',
        timekeeper_classification: config.timekeeperClassification || '',
        billing_start_date: config.billingStartDate || '',
        billing_end_date: config.billingEndDate || '',
        task_code: config.taskCode || 'L100',
        activity_code: config.activityCode || 'A103',
      };
      formData.append('config', JSON.stringify(configPayload));
    }

    formData.append('consolidate', String(consolidate));

    const response = await axios.post<BatchConversionResponse>(
      `${API_BASE_URL}/convert/batch`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent: AxiosProgressEvent) => {
          if (progressEvent.total && onProgress) {
            onProgress(Math.round((progressEvent.loaded * 100) / progressEvent.total));
          }
        },
        timeout: 120000, // 2 minutes for batch
      }
    );

    return response.data;
  },
};

export default ledesConverterApi;
