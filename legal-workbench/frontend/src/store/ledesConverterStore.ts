import { create } from 'zustand';
import { ledesConverterApi, validateDocxFile } from '@/services/ledesConverterApi';
import type {
  LedesConversionStatus,
  LedesExtractedData,
  LedesMatter,
  LedesValidationIssue,
} from '@/types';

type ActiveTab = 'upload' | 'text';

interface LedesConversionState {
  // Tab state
  activeTab: ActiveTab;

  // File state (upload tab)
  file: File | null;

  // Text state (text tab)
  textInput: string;

  // Matter selection
  matters: LedesMatter[];
  selectedMatter: string | null;
  mattersLoading: boolean;

  // Conversion state
  status: LedesConversionStatus;
  uploadProgress: number;

  // Results
  ledesContent: string | null;
  extractedData: LedesExtractedData | null;

  // Validation
  validationIssues: LedesValidationIssue[];

  // Error handling
  error: string | null;
  retryCount: number;

  // Actions
  setActiveTab: (tab: ActiveTab) => void;
  setFile: (file: File | null) => void;
  setTextInput: (text: string) => void;
  selectMatter: (matterName: string | null) => void;
  loadMatters: () => Promise<void>;
  convertFile: () => Promise<void>;
  convertText: () => Promise<void>;
  validateResult: () => Promise<void>;
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
  activeTab: 'upload',
  file: null,
  textInput: '',
  matters: [],
  selectedMatter: null,
  mattersLoading: false,
  status: 'idle',
  uploadProgress: 0,
  ledesContent: null,
  extractedData: null,
  validationIssues: [],
  error: null,
  retryCount: 0,

  setActiveTab: (tab) =>
    set({
      activeTab: tab,
      status: 'idle',
      error: null,
      ledesContent: null,
      extractedData: null,
      validationIssues: [],
    }),

  setTextInput: (text) => set({ textInput: text }),

  selectMatter: (matterName) => set({ selectedMatter: matterName }),

  loadMatters: async () => {
    set({ mattersLoading: true });
    try {
      const matters = await ledesConverterApi.listMatters();
      set({ matters, mattersLoading: false });
    } catch (error) {
      console.error('Failed to load matters:', error);
      set({ mattersLoading: false });
    }
  },

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

  convertFile: async () => {
    const { file, retryCount, selectedMatter } = get();

    if (!file) {
      set({ status: 'error', error: 'No file selected for conversion.' });
      return;
    }

    set({
      status: 'uploading',
      ledesContent: null,
      extractedData: null,
      validationIssues: [],
      error: null,
      uploadProgress: 0,
    });

    try {
      const response = await ledesConverterApi.convertDocxToLedes(
        file,
        selectedMatter || undefined,
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
        // Auto-validate after successful conversion
        get().validateResult();
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

      const errorMessage =
        error instanceof Error ? error.message : 'Failed to convert file. Please try again.';

      set({
        status: 'error',
        error: errorMessage,
      });
    }
  },

  convertText: async () => {
    const { textInput, selectedMatter } = get();

    if (!textInput.trim()) {
      set({ status: 'error', error: 'No text provided.' });
      return;
    }

    set({
      status: 'processing',
      ledesContent: null,
      extractedData: null,
      validationIssues: [],
      error: null,
    });

    try {
      const response = await ledesConverterApi.convertTextToLedes(
        textInput,
        selectedMatter || undefined
      );

      if (response.status === 'success') {
        set({
          status: 'success',
          ledesContent: response.ledes_content,
          extractedData: response.extracted_data,
        });
        // Auto-validate
        get().validateResult();
      } else {
        set({
          status: 'error',
          error: response.message || 'Text conversion failed.',
        });
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to convert text.';
      set({ status: 'error', error: errorMessage });
    }
  },

  validateResult: async () => {
    const { ledesContent } = get();
    if (!ledesContent) return;

    try {
      const result = await ledesConverterApi.validateLedes(ledesContent);
      set({ validationIssues: result.issues });
    } catch (error) {
      console.error('Validation failed:', error);
    }
  },

  downloadResult: () => {
    const { ledesContent, file, extractedData } = get();

    if (!ledesContent) {
      console.warn('Cannot download: missing content');
      return;
    }

    try {
      const blob = new Blob([ledesContent], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');

      const baseName = file
        ? file.name.replace(/\.docx$/i, '')
        : `LEDES_${extractedData?.invoice_number || 'output'}`;
      link.href = url;
      link.download = `${baseName}_LEDES.txt`;

      document.body.appendChild(link);
      link.click();

      setTimeout(() => {
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      }, 100);
    } catch (error) {
      console.error('Download failed:', error);
      set({ error: 'Failed to download file.' });
    }
  },

  reset: () =>
    set({
      file: null,
      textInput: '',
      status: 'idle',
      uploadProgress: 0,
      ledesContent: null,
      extractedData: null,
      validationIssues: [],
      error: null,
      retryCount: 0,
    }),
}));
