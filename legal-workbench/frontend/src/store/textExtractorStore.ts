import { create } from 'zustand';
import { textExtractorApi } from '@/services/textExtractorApi';
import type { FileInfo, Margins, LogEntry, TextExtractorState } from '@/types/textExtractor';

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
    const { file, engine, useGemini, margins, ignoreTerms, addLog } = get();

    if (!file) {
      addLog('Error: No file selected', 'error');
      return;
    }

    set({ status: 'processing', progress: 0 });
    addLog(`Submitting extraction job...`, 'info');
    addLog(`Engine: ${engine}${useGemini ? ' + Gemini enhancement' : ''}`, 'info');

    try {
      const response = await textExtractorApi.submitJob(file, {
        engine,
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

    // Store interval reference for cleanup (timeout after 10 minutes)
    setTimeout(() => {
      clearInterval(pollInterval);
      const currentStatus = get().status;
      if (currentStatus === 'processing') {
        set({ status: 'error' });
        addLog('Job timed out after 10 minutes', 'error');
      }
    }, 600000);
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
}));

// Initialize with ready message
setTimeout(() => {
  useTextExtractorStore.getState().addLog('System initialized. Ready.', 'info');
}, 100);

export default useTextExtractorStore;
