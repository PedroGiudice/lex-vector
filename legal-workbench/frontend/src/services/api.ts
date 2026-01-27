import axios, { AxiosInstance } from 'axios';
import type {
  UploadResponse,
  SaveTemplateRequest,
  Template,
  PatternMatch,
  TemplateDetails,
} from '@/types';
import { getApiBaseUrl } from '@/lib/tauri';

const API_BASE = `${getApiBaseUrl()}/api/doc/api/v1/builder`;

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
    interface BackendUploadResponse {
      document_id: string;
      text_content: string;
      paragraphs: string[];
      metadata: Record<string, unknown>;
    }
    const response = await axios.post<BackendUploadResponse>(
      `${API_BASE}/upload`,
      formData
      // No headers - browser sets Content-Type: multipart/form-data; boundary=...
    );

    // Map backend snake_case to frontend camelCase
    return {
      documentId: response.data.document_id,
      textContent: response.data.text_content,
      paragraphs: response.data.paragraphs,
    };
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
    // Positions are already global (calculated in TipTapDocumentViewer using textContent.indexOf)
    const payload = {
      template_name: data.name,
      document_id: data.documentId,
      description: data.description,
      // Map annotation fields: fieldName->field_name, text->original_text
      // start/end are already global positions from the frontend
      annotations: data.annotations.map((a) => ({
        field_name: a.fieldName,
        original_text: a.text,
        start: a.start,
        end: a.end,
      })),
    };
    const response = await this.client.post<{ template_id: string }>('/save', payload);
    return { templateId: response.data.template_id };
  }

  async getTemplates(): Promise<Template[]> {
    interface BackendTemplate {
      id: string;
      name: string;
      description?: string;
      created_at: string;
      field_count: number;
    }
    const response = await this.client.get<{ templates: BackendTemplate[]; count: number }>(
      '/templates'
    );
    // Map backend snake_case to frontend camelCase
    return response.data.templates.map((t) => ({
      id: t.id,
      name: t.name,
      description: t.description,
      createdAt: t.created_at,
      fieldCount: t.field_count,
    }));
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
    const response = await axios.post(`${getApiBaseUrl()}/api/doc/api/v1/assemble`, data);
    return response.data;
  }
}

export const api = new ApiService();
