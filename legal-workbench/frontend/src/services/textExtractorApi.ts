import axios from 'axios';
import type {
  ExtractOptions,
  JobSubmitResponse,
  JobStatusResponse,
  ExtractionResult,
} from '@/types/textExtractor';
import { lteLogger } from '@/utils/lteLogger';
import { getApiBaseUrl } from '@/lib/tauri';

const API_BASE_URL = `${getApiBaseUrl()}/api/text/api/v1`;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    const url = `${config.baseURL || ''}${config.url || ''}`;
    lteLogger.request(config.method?.toUpperCase() || 'GET', url, config.data);
    return config;
  },
  (error) => {
    lteLogger.error('Request interceptor error', error);
    return Promise.reject(error);
  }
);

// Response interceptor for logging
api.interceptors.response.use(
  (response) => {
    const url = `${response.config.baseURL || ''}${response.config.url || ''}`;
    lteLogger.response(
      response.config.method?.toUpperCase() || 'GET',
      url,
      response.status,
      response.data
    );
    return response;
  },
  (error) => {
    const url = `${error.config?.baseURL || ''}${error.config?.url || ''}`;
    const status = error.response?.status || 0;
    lteLogger.error(`API Error: ${error.config?.method?.toUpperCase() || 'GET'} ${url}`, {
      status,
      message: error.message,
      data: error.response?.data,
    });
    return Promise.reject(error);
  }
);

export const textExtractorApi = {
  /**
   * Submit extraction job
   */
  submitJob: async (file: File, options: ExtractOptions): Promise<JobSubmitResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('engine', options.engine);
    formData.append('use_gemini', String(options.useGemini));

    // Send options as JSON string
    const optionsPayload = {
      margins: options.margins,
      ignore_terms: options.ignoreTerms,
    };
    formData.append('options', JSON.stringify(optionsPayload));

    const response = await api.post<JobSubmitResponse>('/extract', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  /**
   * Poll job status
   */
  getJobStatus: async (jobId: string): Promise<JobStatusResponse> => {
    const response = await api.get<JobStatusResponse>(`/jobs/${jobId}`);
    return response.data;
  },

  /**
   * Get extraction results
   */
  getJobResult: async (jobId: string): Promise<ExtractionResult> => {
    const response = await api.get<ExtractionResult>(`/jobs/${jobId}/result`);
    return response.data;
  },

  /**
   * Health check
   */
  healthCheck: async (): Promise<{ status: string }> => {
    const response = await api.get<{ status: string }>('/health');
    return response.data;
  },
};
