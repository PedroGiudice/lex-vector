import { create } from 'zustand';
import { AxiosError } from 'axios';
import { ledesConverterApi, validateDocxFile } from '@/services/ledesConverterApi';
import type { LedesConversionStatus, LedesExtractedData, LedesConfig } from '@/types';

interface BatchResult {
  filename: string;
  status: 'success' | 'error';
  error?: string;
}

interface LedesConversionState {
  // File state
  file: File | null;

  // Batch mode
  files: File[];
  batchMode: boolean;
  batchResults: BatchResult[];

  // Conversion state
  status: LedesConversionStatus;
  uploadProgress: number;

  // Results
  ledesContent: string | null;
  extractedData: LedesExtractedData | null;

  // LEDES Config
  ledesConfig: LedesConfig | null;

  // Error handling
  error: string | null;
  retryCount: number;

  // Actions
  setFile: (file: File | null) => void;
  setFiles: (files: File[]) => void;
  setBatchMode: (enabled: boolean) => void;
  convertFile: () => Promise<void>;
  downloadResult: () => void;
  reset: () => void;
}

const MAX_RETRIES = 3;
const RETRY_DELAY_BASE = 1000; // 1 second

/**
 * Delay helper for retry logic
 */
const delay = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

export const useLedesConverterStore = create<LedesConversionState>((set, get) => ({
  // Initial state
  file: null,
  files: [],
  batchMode: false,
  batchResults: [],
  status: 'idle',
  uploadProgress: 0,
  ledesContent: null,
  extractedData: null,
  ledesConfig: null,
  error: null,
  retryCount: 0,

  setFile: (file) => {
    if (!file) {
      set({
        file: null,
        status: 'idle',
        error: null,
        ledesContent: null,
        extractedData: null,
        uploadProgress: 0,
        retryCount: 0,
      });
      return;
    }

    // Validate file before accepting
    set({ status: 'validating', error: null });

    const validation = validateDocxFile(file);
    if (!validation.valid) {
      set({
        status: 'error',
        error: validation.error || 'Invalid file',
        file: null,
      });
      return;
    }

    set({
      file,
      status: 'idle',
      ledesContent: null,
      extractedData: null,
      error: null,
      uploadProgress: 0,
      retryCount: 0,
    });
  },

  setFiles: (files: File[]) => {
    if (files.length === 0) {
      set({ files: [], batchMode: false, batchResults: [] });
      return;
    }
    // Validate all files
    const validFiles: File[] = [];
    for (const file of files) {
      const validation = validateDocxFile(file);
      if (validation.valid) {
        validFiles.push(file);
      }
    }
    set({
      files: validFiles,
      batchMode: validFiles.length > 1,
      status: 'idle',
      error: validFiles.length === 0 ? 'No valid files selected' : null,
    });
  },

  setBatchMode: (enabled: boolean) => set({ batchMode: enabled }),

  convertFile: async () => {
    const { file, retryCount, ledesConfig } = get();

    if (!file) {
      set({ status: 'error', error: 'No file selected for conversion.' });
      return;
    }

    set({
      status: 'uploading',
      ledesContent: null,
      extractedData: null,
      error: null,
      uploadProgress: 0,
    });

    try {
      const response = await ledesConverterApi.convertDocxToLedes(
        file,
        ledesConfig || undefined,
        (progress) => {
          // Upload phase: 0-50%
          set({ uploadProgress: Math.round(progress * 0.5) });
        }
      );

      // Processing phase: 50-100%
      set({ status: 'processing', uploadProgress: 75 });

      if (response.status === 'success' && response.ledes_content) {
        set({
          status: 'success',
          ledesContent: response.ledes_content,
          extractedData: response.extracted_data || null,
          uploadProgress: 100,
          retryCount: 0,
        });
      } else {
        set({
          status: 'error',
          error: response.message || 'Unknown conversion error.',
        });
      }
    } catch (error: unknown) {
      const isNetworkError =
        error instanceof Error &&
        (error.message.includes('Network') ||
          error.message.includes('timeout') ||
          error.message.includes('ECONNREFUSED'));

      if (isNetworkError && retryCount < MAX_RETRIES) {
        const newRetryCount = retryCount + 1;
        const retryDelay = RETRY_DELAY_BASE * Math.pow(2, retryCount);

        set({
          error: `Connection failed. Retrying (${newRetryCount}/${MAX_RETRIES})...`,
          retryCount: newRetryCount,
          uploadProgress: 0,
        });

        await delay(retryDelay);
        return get().convertFile();
      }

      // Extract meaningful error message from Axios response
      let errorMessage = 'Failed to convert file. Please try again.';

      if (error instanceof AxiosError && error.response?.data) {
        // FastAPI returns { detail: "..." }, other APIs may use { message: "..." }
        const data = error.response.data as { detail?: string; message?: string };
        errorMessage =
          data.detail || data.message || `HTTP ${error.response.status}: Request failed`;
        console.error('[LEDES] API Error:', error.response.status, data);
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      set({
        status: 'error',
        error: errorMessage,
      });
    }
  },

  downloadResult: () => {
    const { ledesContent, file } = get();

    if (!ledesContent || !file) {
      console.warn('Cannot download: missing content or file reference');
      return;
    }

    try {
      const blob = new Blob([ledesContent], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');

      const baseName = file.name.replace(/\.docx$/i, '');
      link.href = url;
      link.download = `${baseName}_LEDES.txt`;
      link.setAttribute('aria-label', `Download LEDES file: ${baseName}_LEDES.txt`);

      document.body.appendChild(link);
      link.click();

      // Cleanup with timeout to ensure download completes
      setTimeout(() => {
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      }, 100);
    } catch (error) {
      console.error('Download failed:', error);
      set({ error: 'Failed to download file. Please try again.' });
    }
  },

  reset: () =>
    set({
      file: null,
      files: [],
      batchMode: false,
      batchResults: [],
      status: 'idle',
      uploadProgress: 0,
      ledesContent: null,
      extractedData: null,
      ledesConfig: null,
      error: null,
      retryCount: 0,
    }),
}));
