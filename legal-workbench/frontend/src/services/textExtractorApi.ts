import type {
  ExtractOptions,
  JobSubmitResponse,
  JobStatusResponse,
  ExtractionResult,
} from '@/types/textExtractor';
import { lteLogger } from '@/utils/lteLogger';
import { getApiBaseUrl, isTauri, tauriFetchFormData, tauriFetch } from '@/lib/tauri';

const API_BASE_URL = `${getApiBaseUrl()}/api/text/api/v1`;

/**
 * Make HTTP request using Tauri plugin (when in Tauri) or fetch (browser)
 * This bypasses WebKitGTK's broken pipe issues on Linux
 */
async function makeRequest<T>(url: string, options: RequestInit = {}): Promise<T> {
  const fullUrl = `${API_BASE_URL}${url}`;

  lteLogger.request(options.method || 'GET', fullUrl, options.body);

  try {
    const response = await tauriFetch(fullUrl, options);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      lteLogger.error(`API Error: ${options.method || 'GET'} ${fullUrl}`, {
        status: response.status,
        data: errorData,
      });
      throw new Error(`HTTP ${response.status}: ${JSON.stringify(errorData)}`);
    }

    const data = await response.json();
    lteLogger.response(options.method || 'GET', fullUrl, response.status, data);
    return data as T;
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    lteLogger.error(`Request failed: ${options.method || 'GET'} ${fullUrl}`, {
      message,
      hint: isTauri() ? 'Using Tauri HTTP plugin' : 'Using native fetch',
    });
    throw error;
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
    formData.append('use_script', String(options.useScript));

    // Send options as JSON string
    const optionsPayload = {
      margins: options.margins,
      ignore_terms: options.ignoreTerms,
    };
    formData.append('options', JSON.stringify(optionsPayload));

    const fullUrl = `${API_BASE_URL}/extract`;

    lteLogger.request('POST', fullUrl, { file: file.name, options });

    try {
      const response = await tauriFetchFormData(fullUrl, formData);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        lteLogger.error(`API Error: POST ${fullUrl}`, {
          status: response.status,
          data: errorData,
        });
        throw new Error(`HTTP ${response.status}: ${JSON.stringify(errorData)}`);
      }

      const data = await response.json();
      lteLogger.response('POST', fullUrl, response.status, data);
      return data as JobSubmitResponse;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      lteLogger.error(`Submission failed: ${fullUrl}`, {
        message,
        hint: isTauri() ? 'Using Tauri HTTP plugin' : 'Using native fetch',
      });
      throw error;
    }
  },

  /**
   * Poll job status
   */
  getJobStatus: async (jobId: string): Promise<JobStatusResponse> => {
    return makeRequest<JobStatusResponse>(`/jobs/${jobId}`);
  },

  /**
   * Get extraction results
   */
  getJobResult: async (jobId: string): Promise<ExtractionResult> => {
    return makeRequest<ExtractionResult>(`/jobs/${jobId}/result`);
  },

  /**
   * Health check - retorna status do servidor
   */
  healthCheck: async (): Promise<{ ok: boolean; status?: string; error?: string }> => {
    try {
      // Health check está em /api/text/health, não em /api/v1/health
      const baseUrl = API_BASE_URL.replace('/api/v1', '');
      const response = await tauriFetch(`${baseUrl}/health`);

      if (response.ok) {
        const data = await response.json();
        return { ok: true, status: data.status };
      }
      return { ok: false, error: `HTTP ${response.status}` };
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      return { ok: false, error: message };
    }
  },
};
