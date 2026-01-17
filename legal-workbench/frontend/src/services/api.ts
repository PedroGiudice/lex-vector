import axios, { AxiosInstance } from 'axios';
import type {
  UploadResponse,
  SaveTemplateRequest,
  Template,
  PatternMatch,
  TemplateDetails,
} from '@/types';

const API_BASE = '/api/doc/api/v1/builder';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    // CRITICAL: Use axios directly, NOT this.client
    // this.client has default Content-Type: application/json which corrupts FormData
    // Browser must set Content-Type with correct multipart boundary automatically
    const response = await axios.post<UploadResponse>(
      `${API_BASE}/upload`,
      formData
      // No headers - browser sets Content-Type: multipart/form-data; boundary=...
    );

    return response.data;
  }

  async detectPatterns(text: string): Promise<PatternMatch[]> {
    interface PatternResponse {
      matches: Array<{
        pattern_type: string;
        start: number;
        end: number;
        value: string;
        suggested_field: string;
      }>;
      pattern_types_found: string[];
    }
    const response = await this.client.post<PatternResponse>('/patterns', { text });
    // Map API response to PatternMatch format expected by frontend
    return response.data.matches.map((m) => ({
      pattern: m.pattern_type,
      text: m.value,
      start: m.start,
      end: m.end,
      confidence: 1.0, // API doesn't return confidence, default to 1
      paragraphIndex: 0, // Default to 0, will be updated by caller if needed
    }));
  }

  async saveTemplate(data: SaveTemplateRequest): Promise<{ templateId: string }> {
    // Map frontend camelCase to backend snake_case
    const payload = {
      template_name: data.name,
      document_id: data.documentId,
      annotations: data.annotations,
      description: data.description,
    };
    const response = await this.client.post<{ template_id: string }>('/save', payload);
    return { templateId: response.data.template_id };
  }

  async getTemplates(): Promise<Template[]> {
    const response = await this.client.get<{ templates: Template[]; count: number }>('/templates');
    return response.data.templates;
  }

  async getTemplateDetails(templateId: string): Promise<TemplateDetails> {
    const response = await this.client.get<TemplateDetails>(`/templates/${templateId}`);
    return response.data;
  }

  async deleteTemplate(templateId: string): Promise<void> {
    await this.client.delete(`/templates/${templateId}`);
  }

  async assembleDocument(data: {
    template_path: string;
    data: Record<string, string>;
    output_filename?: string;
    auto_normalize?: boolean;
  }): Promise<{
    success: boolean;
    output_path: string;
    download_url: string;
    filename: string;
    message: string;
  }> {
    // Use main API endpoint, not builder
    const response = await axios.post('/api/doc/api/v1/assemble', data);
    return response.data;
  }
}

export const api = new ApiService();
