import { act } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useDocumentStore } from '@/store/documentStore';
import type { FieldAnnotation, TextSelection, PatternMatch } from '@/types';

// Mock the api module
vi.mock('@/services/api', () => ({
  api: {
    uploadDocument: vi.fn(),
    detectPatterns: vi.fn(),
    saveTemplate: vi.fn(),
    getTemplates: vi.fn(),
    getTemplateDetails: vi.fn(),
  },
}));

// Reset store before each test
beforeEach(() => {
  const store = useDocumentStore.getState();
  // Reset to initial state
  act(() => {
    store.clearDocument();
    // Clear toasts manually
    const state = useDocumentStore.getState();
    state.toasts.forEach((toast) => store.removeToast(toast.id));
  });
});

describe('documentStore', () => {
  describe('initial state', () => {
    it('should have correct initial values', () => {
      const state = useDocumentStore.getState();

      expect(state.documentId).toBeNull();
      expect(state.textContent).toBe('');
      expect(state.paragraphs).toEqual([]);
      expect(state.isUploading).toBe(false);
      expect(state.uploadProgress).toBe(0);
      expect(state.annotations).toEqual([]);
      expect(state.selectedText).toBeNull();
      expect(state.detectedPatterns).toEqual([]);
    });

    it('should have empty templates list initially', () => {
      const state = useDocumentStore.getState();

      expect(state.templates).toEqual([]);
      expect(state.isFetchingTemplates).toBe(false);
      expect(state.isLoadingTemplate).toBe(false);
    });

    it('should have empty toasts initially', () => {
      const state = useDocumentStore.getState();

      expect(state.toasts).toEqual([]);
    });
  });

  describe('addAnnotation', () => {
    it('should add a new annotation', () => {
      const annotation: FieldAnnotation = {
        fieldName: 'testField',
        text: 'Sample text',
        start: 0,
        end: 11,
        paragraphIndex: 0,
      };

      act(() => {
        useDocumentStore.getState().addAnnotation(annotation);
      });

      const state = useDocumentStore.getState();
      expect(state.annotations).toContainEqual(annotation);
      expect(state.annotations).toHaveLength(1);
    });

    it('should not add duplicate field names', () => {
      const annotation: FieldAnnotation = {
        fieldName: 'duplicateField',
        text: 'First text',
        start: 0,
        end: 10,
        paragraphIndex: 0,
      };

      const duplicateAnnotation: FieldAnnotation = {
        fieldName: 'duplicateField',
        text: 'Second text',
        start: 20,
        end: 31,
        paragraphIndex: 1,
      };

      act(() => {
        useDocumentStore.getState().addAnnotation(annotation);
      });

      act(() => {
        useDocumentStore.getState().addAnnotation(duplicateAnnotation);
      });

      const state = useDocumentStore.getState();
      expect(state.annotations).toHaveLength(1);
      expect(state.annotations[0].text).toBe('First text');
    });

    it('should show success toast when adding annotation', () => {
      const annotation: FieldAnnotation = {
        fieldName: 'toastTest',
        text: 'Test',
        start: 0,
        end: 4,
        paragraphIndex: 0,
      };

      act(() => {
        useDocumentStore.getState().addAnnotation(annotation);
      });

      const state = useDocumentStore.getState();
      const successToast = state.toasts.find((t) => t.type === 'success');
      expect(successToast).toBeDefined();
      expect(successToast?.message).toContain('toastTest');
    });
  });

  describe('removeAnnotation', () => {
    it('should remove an existing annotation', () => {
      const annotation: FieldAnnotation = {
        fieldName: 'toRemove',
        text: 'Remove me',
        start: 0,
        end: 9,
        paragraphIndex: 0,
      };

      act(() => {
        useDocumentStore.getState().addAnnotation(annotation);
      });

      act(() => {
        useDocumentStore.getState().removeAnnotation('toRemove');
      });

      const state = useDocumentStore.getState();
      expect(state.annotations).toHaveLength(0);
    });

    it('should show info toast when removing annotation', () => {
      const annotation: FieldAnnotation = {
        fieldName: 'infoToast',
        text: 'Test',
        start: 0,
        end: 4,
        paragraphIndex: 0,
      };

      act(() => {
        useDocumentStore.getState().addAnnotation(annotation);
        // Clear previous toasts
        const toasts = useDocumentStore.getState().toasts;
        toasts.forEach((t) => useDocumentStore.getState().removeToast(t.id));
      });

      act(() => {
        useDocumentStore.getState().removeAnnotation('infoToast');
      });

      const state = useDocumentStore.getState();
      const infoToast = state.toasts.find((t) => t.type === 'info');
      expect(infoToast).toBeDefined();
      expect(infoToast?.message).toContain('infoToast');
    });
  });

  describe('updateAnnotation', () => {
    it('should update an existing annotation', () => {
      const original: FieldAnnotation = {
        fieldName: 'original',
        text: 'Original text',
        start: 0,
        end: 13,
        paragraphIndex: 0,
      };

      const updated: FieldAnnotation = {
        fieldName: 'updated',
        text: 'Updated text',
        start: 0,
        end: 12,
        paragraphIndex: 0,
      };

      act(() => {
        useDocumentStore.getState().addAnnotation(original);
      });

      act(() => {
        useDocumentStore.getState().updateAnnotation('original', updated);
      });

      const state = useDocumentStore.getState();
      expect(state.annotations).toHaveLength(1);
      expect(state.annotations[0].fieldName).toBe('updated');
    });

    it('should not update if new fieldName already exists', () => {
      const first: FieldAnnotation = {
        fieldName: 'first',
        text: 'First',
        start: 0,
        end: 5,
        paragraphIndex: 0,
      };

      const second: FieldAnnotation = {
        fieldName: 'second',
        text: 'Second',
        start: 10,
        end: 16,
        paragraphIndex: 0,
      };

      const conflicting: FieldAnnotation = {
        fieldName: 'second', // Same as existing
        text: 'Conflicting',
        start: 0,
        end: 11,
        paragraphIndex: 0,
      };

      act(() => {
        useDocumentStore.getState().addAnnotation(first);
        useDocumentStore.getState().addAnnotation(second);
      });

      act(() => {
        useDocumentStore.getState().updateAnnotation('first', conflicting);
      });

      const state = useDocumentStore.getState();
      expect(state.annotations).toHaveLength(2);
      // First annotation should remain unchanged
      expect(state.annotations.find((a) => a.fieldName === 'first')).toBeDefined();
    });
  });

  describe('setSelectedText', () => {
    it('should set selected text', () => {
      const selection: TextSelection = {
        text: 'Selected text',
        start: 5,
        end: 18,
        paragraphIndex: 1,
      };

      act(() => {
        useDocumentStore.getState().setSelectedText(selection);
      });

      const state = useDocumentStore.getState();
      expect(state.selectedText).toEqual(selection);
    });

    it('should clear selected text when set to null', () => {
      const selection: TextSelection = {
        text: 'Selected',
        start: 0,
        end: 8,
        paragraphIndex: 0,
      };

      act(() => {
        useDocumentStore.getState().setSelectedText(selection);
      });

      act(() => {
        useDocumentStore.getState().setSelectedText(null);
      });

      const state = useDocumentStore.getState();
      expect(state.selectedText).toBeNull();
    });
  });

  describe('clearDocument', () => {
    it('should reset document-related state', () => {
      const annotation: FieldAnnotation = {
        fieldName: 'test',
        text: 'Test',
        start: 0,
        end: 4,
        paragraphIndex: 0,
      };

      // Set up some state
      act(() => {
        const store = useDocumentStore.getState();
        store.addAnnotation(annotation);
        store.setSelectedText({ text: 'test', start: 0, end: 4, paragraphIndex: 0 });
      });

      act(() => {
        useDocumentStore.getState().clearDocument();
      });

      const state = useDocumentStore.getState();
      expect(state.documentId).toBeNull();
      expect(state.textContent).toBe('');
      expect(state.paragraphs).toEqual([]);
      expect(state.annotations).toEqual([]);
      expect(state.selectedText).toBeNull();
      expect(state.detectedPatterns).toEqual([]);
      expect(state.uploadProgress).toBe(0);
    });
  });

  describe('removeDetectedPattern', () => {
    it('should remove a specific pattern', () => {
      const pattern1: PatternMatch = {
        pattern: 'date',
        text: '01/01/2024',
        start: 0,
        end: 10,
        confidence: 0.9,
        paragraphIndex: 0,
      };

      const pattern2: PatternMatch = {
        pattern: 'cpf',
        text: '123.456.789-00',
        start: 20,
        end: 34,
        confidence: 0.95,
        paragraphIndex: 1,
      };

      // Manually set detected patterns
      act(() => {
        useDocumentStore.setState({ detectedPatterns: [pattern1, pattern2] });
      });

      act(() => {
        useDocumentStore.getState().removeDetectedPattern(pattern1);
      });

      const state = useDocumentStore.getState();
      expect(state.detectedPatterns).toHaveLength(1);
      expect(state.detectedPatterns[0]).toEqual(pattern2);
    });
  });

  describe('toasts', () => {
    it('should add a toast with auto-generated id', () => {
      act(() => {
        useDocumentStore.getState().addToast('Test message', 'success');
      });

      const state = useDocumentStore.getState();
      expect(state.toasts).toHaveLength(1);
      expect(state.toasts[0].message).toBe('Test message');
      expect(state.toasts[0].type).toBe('success');
      expect(state.toasts[0].id).toBeDefined();
    });

    it('should remove a toast by id', () => {
      act(() => {
        useDocumentStore.getState().addToast('To remove', 'info');
      });

      const toastId = useDocumentStore.getState().toasts[0].id;

      act(() => {
        useDocumentStore.getState().removeToast(toastId);
      });

      const state = useDocumentStore.getState();
      expect(state.toasts).toHaveLength(0);
    });

    it('should support different toast types', () => {
      act(() => {
        useDocumentStore.getState().addToast('Success', 'success');
        useDocumentStore.getState().addToast('Error', 'error');
        useDocumentStore.getState().addToast('Warning', 'warning');
        useDocumentStore.getState().addToast('Info', 'info');
      });

      const state = useDocumentStore.getState();
      expect(state.toasts).toHaveLength(4);
      expect(state.toasts.map((t) => t.type)).toEqual(['success', 'error', 'warning', 'info']);
    });
  });
});
