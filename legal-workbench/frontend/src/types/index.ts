export interface FieldAnnotation {
  fieldName: string;
  text: string;
  start: number;
  end: number;
  paragraphIndex: number;
}

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
