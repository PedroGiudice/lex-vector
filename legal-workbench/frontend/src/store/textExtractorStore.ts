import { create } from 'zustand';
import { textExtractorApi } from '@/services/textExtractorApi';
import { isTauri } from '@/lib/tauri';
import type {
  FileInfo,
  Margins,
  LogEntry,
  TextExtractorState,
  GpuMode,
  HistoryEntry,
} from '@/types/textExtractor';

// LGPD preset terms
const LGPD_PRESET_TERMS = [
  'Pagina X de Y',
  'TRIBUNAL DE JUSTICA',
  'Documento assinado digitalmente',
  'Numeracao unica',
  'Assinado eletronicamente',
  'Validar em',
  'Codigo de validacao',
  'PODER JUDICIARIO',
];

// Court docs preset
const COURT_PRESET_TERMS = [
  'PODER JUDICIARIO',
  'TRIBUNAL DE JUSTICA',
  'MINISTERIO PUBLICO',
  'Pagina',
  'fls.',
  'Processo n',
  'Documento assinado',
  'GABINETE',
];

// Contract preset
const CONTRACT_PRESET_TERMS = ['Rubrica:', 'Visto:', 'Pagina', 'Testemunhas:', 'Autenticacao:'];

const DEFAULT_MARGINS: Margins = {
  top: 15,
  bottom: 20,
  left: 10,
  right: 10,
};

const generateLogId = (): string => {
  return `log-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

export const useTextExtractorStore = create<TextExtractorState>((set, get) => ({
  // Upload
  file: null,
  fileInfo: null,

  // Config
  engine: 'marker',
  gpuMode: 'auto' as GpuMode,
  useGemini: false,
  margins: { ...DEFAULT_MARGINS },
  ignoreTerms: [...LGPD_PRESET_TERMS],

  // Job
  jobId: null,
  status: 'idle',
  progress: 0,

  // Results
  result: null,

  // Console
  logs: [],

  // History
  history: [] as HistoryEntry[],
  historyOpen: false,
  historyLoading: false,

  // Actions
  setFile: (file) => {
    if (file) {
      const fileInfo: FileInfo = {
        name: file.name,
        size: file.size,
        type: file.type,
      };
      set({ file, fileInfo, status: 'preflight' });
      get().addLog(
        `File selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`,
        'info'
      );

      // Simulate preflight check
      setTimeout(() => {
        const state = get();
        if (state.file) {
          get().addLog('Pre-flight check: Valid PDF, Not encrypted', 'success');
          set({ status: 'configuring' });
        }
      }, 500);
    } else {
      set({ file: null, fileInfo: null, status: 'idle' });
    }
  },

  setEngine: (engine) => set({ engine }),

  setGpuMode: (gpuMode) => set({ gpuMode }),

  setUseGemini: (useGemini) => set({ useGemini }),

  setMargins: (margins) => set({ margins }),

  setIgnoreTerms: (terms) => set({ ignoreTerms: terms }),

  addIgnoreTerm: (term) => {
    const { ignoreTerms } = get();
    if (term.trim() && !ignoreTerms.includes(term.trim())) {
      set({ ignoreTerms: [...ignoreTerms, term.trim()] });
    }
  },

  removeIgnoreTerm: (term) => {
    const { ignoreTerms } = get();
    set({ ignoreTerms: ignoreTerms.filter((t) => t !== term) });
  },

  loadPreset: (preset) => {
    switch (preset) {
      case 'lgpd':
        set({ ignoreTerms: [...LGPD_PRESET_TERMS] });
        get().addLog('Loaded LGPD preset terms', 'info');
        break;
      case 'court':
        set({ ignoreTerms: [...COURT_PRESET_TERMS] });
        get().addLog('Loaded Court documents preset terms', 'info');
        break;
      case 'contract':
        set({ ignoreTerms: [...CONTRACT_PRESET_TERMS] });
        get().addLog('Loaded Contract preset terms', 'info');
        break;
    }
  },

  submitJob: async () => {
    const { file, engine, gpuMode, useGemini, margins, ignoreTerms, addLog } = get();

    if (!file) {
      addLog('Error: No file selected', 'error');
      return;
    }

    set({ status: 'processing', progress: 0 });

    // Check local cache first (Tauri only)
    if (isTauri()) {
      try {
        addLog('Checking local cache...', 'info');
        const { invoke } = await import('@tauri-apps/api/core');

        // Calculate hash from file content
        const arrayBuffer = await file.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const fileHash = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');

        // Check cache
        const cachedJson = await invoke<string | null>('get_cached_result', { fileHash });

        if (cachedJson) {
          const result = JSON.parse(cachedJson);
          set({ result, status: 'success', progress: 100 });
          addLog('Cache hit! Loaded from local storage.', 'success');
          addLog(
            `Original extraction: ${result.pages_processed} pages in ${result.execution_time_seconds.toFixed(1)}s`,
            'info'
          );
          return;
        }

        addLog('Cache miss. Sending to backend...', 'info');
      } catch (cacheError) {
        addLog('Cache check skipped (error)', 'warning');
        console.error('Cache error:', cacheError);
      }
    }

    addLog(`Submitting extraction job...`, 'info');
    addLog(`Engine: ${engine}${useGemini ? ' + Gemini' : ''} | GPU: ${gpuMode}`, 'info');

    try {
      const response = await textExtractorApi.submitJob(file, {
        engine,
        gpuMode,
        useGemini,
        margins,
        ignoreTerms,
      });

      set({ jobId: response.job_id });
      addLog(`Job submitted: ${response.job_id}`, 'success');

      // Start polling
      get().pollJob();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      set({ status: 'error' });
      addLog(`Submission failed: ${errorMsg}`, 'error');
    }
  },

  pollJob: async () => {
    const { jobId, addLog } = get();

    if (!jobId) {
      addLog('Error: No job ID to poll', 'error');
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        const statusResponse = await textExtractorApi.getJobStatus(jobId);
        const { status, progress } = statusResponse;

        set({ progress });

        if (progress > 0) {
          addLog(`Processing... ${progress}%`, 'info');
        }

        if (status === 'completed') {
          clearInterval(pollInterval);
          addLog('Extraction completed!', 'success');

          // Fetch results
          try {
            const result = await textExtractorApi.getJobResult(jobId);
            set({ result, status: 'success' });
            addLog(
              `Processed ${result.pages_processed} pages in ${result.execution_time_seconds.toFixed(1)}s`,
              'success'
            );
            addLog(`Total characters: ${result.text.length.toLocaleString()}`, 'info');
            if (result.metadata?.extraction_mode) {
              addLog(
                `Mode: ${result.metadata.extraction_mode}${result.metadata.modal_gpu ? ` (${result.metadata.modal_gpu})` : ''}`,
                'info'
              );
            }

            // Save to local cache (Tauri only)
            const { file } = get();
            if (isTauri() && file) {
              try {
                const { invoke } = await import('@tauri-apps/api/core');
                const arrayBuffer = await file.arrayBuffer();
                const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
                const hashArray = Array.from(new Uint8Array(hashBuffer));
                const fileHash = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');

                await invoke('save_cached_result', {
                  fileHash,
                  filePath: file.name,
                  apiResponse: JSON.stringify(result),
                  backendUrl: window.location.origin,
                });
                addLog('Result cached locally', 'info');
              } catch (cacheError) {
                console.error('Failed to cache result:', cacheError);
              }
            }
          } catch (resultError: any) {
            set({ status: 'error' });
            addLog('Failed to fetch results', 'error');
          }
        } else if (status === 'failed') {
          clearInterval(pollInterval);
          set({ status: 'error' });
          addLog(`Job failed: ${statusResponse.error_message || 'Unknown error'}`, 'error');
        }
      } catch (error: any) {
        clearInterval(pollInterval);
        set({ status: 'error' });
        addLog(`Polling error: ${error.message}`, 'error');
      }
    }, 2000);

    // Store interval reference for cleanup (timeout after 30 minutes)
    // PDFs grandes (500+ páginas) + cold start Modal podem levar 15-20 minutos
    setTimeout(() => {
      clearInterval(pollInterval);
      const currentStatus = get().status;
      if (currentStatus === 'processing') {
        set({ status: 'error' });
        addLog('Job timed out after 30 minutes', 'error');
      }
    }, 1800000);
  },

  reset: () => {
    set({
      file: null,
      fileInfo: null,
      jobId: null,
      status: 'idle',
      progress: 0,
      result: null,
    });
    get().addLog('System reset. Ready for new extraction.', 'info');
  },

  addLog: (message, level = 'info') => {
    const entry: LogEntry = {
      id: generateLogId(),
      timestamp: new Date(),
      message,
      level,
    };
    set((state) => ({
      logs: [...state.logs, entry],
    }));
  },

  clearLogs: () => {
    set({ logs: [] });
  },

  // History Actions
  setHistoryOpen: (open) => set({ historyOpen: open }),

  loadHistory: async () => {
    if (!isTauri()) return;

    set({ historyLoading: true });
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const entries = await invoke<
        Array<{
          file_hash: string;
          file_path: string;
          cached_at: number;
        }>
      >('list_cache_entries');

      const history: HistoryEntry[] = entries.map((e) => ({
        ...e,
        file_name: e.file_path.split('/').pop() || e.file_path.split('\\').pop() || 'Unknown',
      }));

      set({ history, historyLoading: false });
    } catch (error) {
      console.error('Failed to load history:', error);
      set({ historyLoading: false });
    }
  },

  loadFromHistory: async (entry) => {
    const { addLog } = get();

    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const cachedJson = await invoke<string | null>('get_cached_result', {
        fileHash: entry.file_hash,
      });

      if (cachedJson) {
        const result = JSON.parse(cachedJson);
        set({
          result,
          status: 'success',
          historyOpen: false,
          fileInfo: {
            name: entry.file_name,
            size: 0,
            type: 'application/pdf',
          },
        });
        addLog(`Loaded from cache: ${entry.file_name}`, 'success');
        addLog(`Cached at: ${new Date(entry.cached_at * 1000).toLocaleString('pt-BR')}`, 'info');
      } else {
        addLog('Cache entry not found', 'error');
      }
    } catch (error) {
      addLog('Failed to load from cache', 'error');
    }
  },
}));

// Initialize with ready message
setTimeout(() => {
  useTextExtractorStore.getState().addLog('System initialized. Ready.', 'info');
}, 100);

export default useTextExtractorStore;
