import { create } from 'zustand';
import { api } from '@/services/api';
import type { FieldAnnotation, PatternMatch, TextSelection, Toast, Template, TemplateDetails } from '@/types';

interface DocumentState {
  // Document state
  documentId: string | null;
  textContent: string;
  paragraphs: string[];
  isUploading: boolean;
  uploadProgress: number;

  // Annotations state
  annotations: FieldAnnotation[];
  selectedText: TextSelection | null;
  detectedPatterns: PatternMatch[];

  // Templates state
  templates: Template[];
  isFetchingTemplates: boolean;
  isLoadingTemplate: boolean;

  // UI state
  toasts: Toast[];

  // Actions
  uploadDocument: (file: File) => Promise<void>;
  addAnnotation: (annotation: FieldAnnotation) => void;
  removeAnnotation: (fieldName: string) => void;
  updateAnnotation: (oldFieldName: string, newAnnotation: FieldAnnotation) => void;
  setSelectedText: (selection: TextSelection | null) => void;
  saveTemplate: (name: string, description?: string) => Promise<void>;
  clearDocument: () => void;
  detectPatterns: (text: string) => Promise<void>;
  removeDetectedPattern: (patternToRemove: PatternMatch) => void;
  fetchTemplates: () => Promise<void>;
  loadTemplate: (templateId: string) => Promise<void>;
  addToast: (message: string, type: Toast['type']) => void;
  removeToast: (id: string) => void;
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  // Initial state
  documentId: null,
  textContent: '',
  paragraphs: [],
  isUploading: false,
  uploadProgress: 0,
  annotations: [],
  selectedText: null,
  detectedPatterns: [],
  templates: [],
  isFetchingTemplates: false,
  isLoadingTemplate: false,
  toasts: [],

  // Upload document
  uploadDocument: async (file: File) => {
    set({ isUploading: true, uploadProgress: 0, detectedPatterns: [], annotations: [] });
    try {
      const response = await api.uploadDocument(file);

      set({
        documentId: response.documentId,
        textContent: response.textContent,
        paragraphs: response.paragraphs,
        isUploading: false,
        uploadProgress: 100,
        annotations: [],
      });

      get().detectPatterns(response.textContent);
      get().addToast('Document uploaded successfully', 'success');
    } catch (error) {
      set({ isUploading: false, uploadProgress: 0 });
      get().addToast('Failed to upload document', 'error');
      throw error;
    }
  },

  // Add annotation
  addAnnotation: (annotation: FieldAnnotation) => {
    const { annotations } = get();

    if (annotations.some(a => a.fieldName === annotation.fieldName)) {
      get().addToast('Field name already exists', 'error');
      return;
    }

    set({ annotations: [...annotations, annotation] });
    get().addToast(`Field \"${annotation.fieldName}\" created`, 'success');
  },

  // Remove annotation
  removeAnnotation: (fieldName: string) => {
    set(state => ({
      annotations: state.annotations.filter(a => a.fieldName !== fieldName),
    }));
    get().addToast(`Field \"${fieldName}\" removed`, 'info');
  },

  // Update annotation
  updateAnnotation: (oldFieldName: string, newAnnotation: FieldAnnotation) => {
    const { annotations } = get();

    if (oldFieldName !== newAnnotation.fieldName &&
        annotations.some(a => a.fieldName === newAnnotation.fieldName)) {
      get().addToast('Field name already exists', 'error');
      return;
    }

    set(state => ({
      annotations: state.annotations.map(a =>
        a.fieldName === oldFieldName ? newAnnotation : a
      ),
    }));
    get().addToast(`Field \"${newAnnotation.fieldName}\" updated`, 'success');
  },

  // Set selected text
  setSelectedText: (selection: TextSelection | null) => {
    set({ selectedText: selection });
  },

  // Save template
  saveTemplate: async (name: string, description?: string) => {
    const { documentId, annotations } = get();

    if (!documentId) {
      get().addToast('No document loaded', 'error');
      return;
    }

    if (annotations.length === 0) {
      get().addToast('No fields annotated', 'error');
      return;
    }

    try {
      await api.saveTemplate({ name, documentId, annotations, description });
      get().addToast(`Template \"${name}\" saved successfully`, 'success');
      get().fetchTemplates();
    } catch (error) {
      get().addToast('Failed to save template', 'error');
      throw error;
    }
  },

  // Clear document
  clearDocument: () => {
    set({
      documentId: null,
      textContent: '',
      paragraphs: [],
      annotations: [],
      selectedText: null,
      detectedPatterns: [],
      uploadProgress: 0,
    });
  },

  // Detect patterns
  detectPatterns: async (text: string) => {
    try {
      const patterns = await api.detectPatterns(text);
      set({ detectedPatterns: patterns });
    } catch (error) {
      console.error('Failed to detect patterns:', error);
    }
  },

  // Remove a detected pattern from the list
  removeDetectedPattern: (patternToRemove: PatternMatch) => {
    set(state => ({
      detectedPatterns: state.detectedPatterns.filter(
        (p) =>
          !(p.pattern === patternToRemove.pattern &&
            p.text === patternToRemove.text &&
            p.start === patternToRemove.start &&
            p.end === patternToRemove.end &&
            p.paragraphIndex === patternToRemove.paragraphIndex)
      ),
    }));
  },

  // Fetch templates
  fetchTemplates: async () => {
    set({ isFetchingTemplates: true });
    try {
      const templates = await api.getTemplates();
      set({ templates, isFetchingTemplates: false });
    } catch (error) {
      console.error('Failed to fetch templates:', error);
      get().addToast('Failed to load templates', 'error');
      set({ isFetchingTemplates: false });
    }
  },

  // Load template
  loadTemplate: async (templateId: string) => {
    set({ isLoadingTemplate: true });
    try {
      const templateDetails = await api.getTemplateDetails(templateId); 
      set({
        annotations: templateDetails.annotations,
        selectedText: null,
        detectedPatterns: [], // Clear detected patterns as they might not apply to new annotations
        isLoadingTemplate: false,
      });
      get().addToast('Template loaded successfully', 'success');
    } catch (error) {
      console.error('Failed to load template:', error);
      get().addToast('Failed to load template', 'error');
      set({ isLoadingTemplate: false });
    }
  },

  // Add toast notification
  addToast: (message: string, type: Toast['type']) => {
    const id = Math.random().toString(36).substring(7);
    const toast: Toast = { id, message, type };

    set(state => ({ toasts: [...state.toasts, toast] }));

    // Auto-remove after 5 seconds
    setTimeout(() => {
      get().removeToast(id);
    }, 5000);
  },

  // Remove toast
  removeToast: (id: string) => {
    set(state => ({
      toasts: state.toasts.filter(t => t.id !== id),
    }));
  },
}));
