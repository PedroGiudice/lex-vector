export interface FieldAnnotation {
  fieldName: string;
  text: string;
  start: number;
  end: number;
  paragraphIndex: number;
  color: string; // Hex color for visual identification
}

// Input type for creating annotations (color is assigned automatically by the store)
export type FieldAnnotationInput = Omit<FieldAnnotation, 'color'>;

export interface PatternMatch {
  pattern: string;
  text: string;
  start: number;
  end: number;
  confidence: number;
  paragraphIndex: number;
}

export interface TextSelection {
  text: string;
  start: number;
  end: number;
  paragraphIndex: number;
}

export interface UploadResponse {
  documentId: string;
  textContent: string;
  paragraphs: string[];
}

export interface SaveTemplateRequest {
  name: string;
  documentId: string;
  annotations: FieldAnnotation[];
  description?: string; // Added optional description
}

export interface Template {
  id: string;
  name: string;
  description?: string; // Added optional description to Template interface as well
  createdAt: string;
  fieldCount: number;
}

export interface TemplateDetails extends Template {
  annotations: FieldAnnotation[]; // Assuming template details include annotations
}

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

// LEDES Converter Types
export type LedesConversionStatus =
  | 'idle'
  | 'validating'
  | 'uploading'
  | 'processing'
  | 'success'
  | 'error';

export interface LedesConfig {
  lawFirmId: string;
  lawFirmName: string;
  clientId: string;
  clientName?: string;
  matterId: string;
  matterName?: string;
}

export interface LedesExtractedData {
  invoice_date: string;
  invoice_number: string;
  client_id: string;
  matter_id: string;
  invoice_total: number;
  line_items: Array<{
    description: string;
    amount: number;
  }>;
}

export interface ConvertLedesResponse {
  filename: string;
  status: 'success' | 'error';
  message?: string;
  ledes_content?: string;
  extracted_data?: LedesExtractedData;
}

export interface LedesFileValidation {
  valid: boolean;
  error?: string;
}

// Doc Assembler Types
export interface AssembleRequest {
  template_path: string;
  data: Record<string, string>;
  output_filename?: string;
  auto_normalize?: boolean;
}

export interface AssembleResponse {
  success: boolean;
  output_path: string;
  download_url: string;
  filename: string;
  message: string;
}

export interface TemplateField {
  name: string;
  value: string;
  category?: string;
}
