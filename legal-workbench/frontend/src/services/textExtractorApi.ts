import axios from 'axios';
import { fetch as tauriFetch } from '@tauri-apps/plugin-http';
import type {
  ExtractOptions,
  JobSubmitResponse,
  JobStatusResponse,
  ExtractionResult,
} from '@/types/textExtractor';
import { lteLogger } from '@/utils/lteLogger';
import { getApiBaseUrl, isTauri } from '@/lib/tauri';

const API_BASE_URL = `${getApiBaseUrl()}/api/text/api/v1`;

// Axios instance for web browser
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

    if (!error.response && error.message === 'Network Error') {
      lteLogger.error('CORS or Network Error - verifique:', {
        url,
        baseURL: error.config?.baseURL,
        hint: 'Pode ser CORS bloqueado ou servidor inacessível',
      });
    } else {
      lteLogger.error(`API Error: ${error.config?.method?.toUpperCase() || 'GET'} ${url}`, {
        status,
        message: error.message,
        data: error.response?.data,
      });
    }

    return Promise.reject(error);
  }
);

/**
 * HTTP client que usa Tauri plugin-http no desktop e axios no browser.
 * O plugin-http contorna limitações do WebKitGTK com CORS/fetch.
 */
async function httpRequest<T>(
  method: 'GET' | 'POST',
  path: string,
  options?: {
    body?: FormData | Record<string, unknown>;
    headers?: Record<string, string>;
  }
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;

  if (isTauri()) {
    // Usar Tauri HTTP plugin (contorna limitações WebKitGTK)
    lteLogger.request(method, url, options?.body);

    try {
      const response = await tauriFetch(url, {
        method,
        body: options?.body instanceof FormData ? options.body : JSON.stringify(options?.body),
        headers: options?.headers,
      });

      if (!response.ok) {
        const errorData = await response.text();
        lteLogger.error(`Tauri HTTP Error: ${method} ${url}`, {
          status: response.status,
          data: errorData,
        });
        throw new Error(`HTTP ${response.status}: ${errorData}`);
      }

      const data = await response.json();
      lteLogger.response(method, url, response.status, data);
      return data as T;
    } catch (error) {
      lteLogger.error(`Tauri fetch error: ${method} ${url}`, error);
      throw error;
    }
  } else {
    // Usar axios no browser
    if (method === 'GET') {
      const response = await api.get<T>(path);
      return response.data;
    } else {
      const response = await api.post<T>(path, options?.body, {
        headers: options?.headers,
      });
      return response.data;
    }
  }
}

export const textExtractorApi = {
  /**
   * Submit extraction job
   */
  submitJob: async (file: File, options: ExtractOptions): Promise<JobSubmitResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('engine', options.engine);
    formData.append('gpu_mode', options.gpuMode);
    formData.append('use_gemini', String(options.useGemini));

    const optionsPayload = {
      margins: options.margins,
      ignore_terms: options.ignoreTerms,
    };
    formData.append('options', JSON.stringify(optionsPayload));

    return httpRequest<JobSubmitResponse>('POST', '/extract', {
      body: formData,
      headers: {
        // FormData sets Content-Type automatically with boundary
      },
    });
  },

  /**
   * Poll job status
   */
  getJobStatus: async (jobId: string): Promise<JobStatusResponse> => {
    return httpRequest<JobStatusResponse>('GET', `/jobs/${jobId}`);
  },

  /**
   * Get extraction results
   */
  getJobResult: async (jobId: string): Promise<ExtractionResult> => {
    return httpRequest<ExtractionResult>('GET', `/jobs/${jobId}/result`);
  },

  /**
   * Health check - retorna status do servidor
   */
  healthCheck: async (): Promise<{ ok: boolean; status?: string; error?: string }> => {
    try {
      const baseUrl = API_BASE_URL.replace('/api/v1', '');
      const url = `${baseUrl}/health`;

      if (isTauri()) {
        const response = await tauriFetch(url, { method: 'GET' });
        if (response.ok) {
          const data = (await response.json()) as { status: string };
          return { ok: true, status: data.status };
        }
        return { ok: false, error: `HTTP ${response.status}` };
      } else {
        const response = await axios.get<{ status: string }>(url, { timeout: 5000 });
        return { ok: response.status === 200, status: response.data.status };
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      return { ok: false, error: message };
    }
  },
};
