import { useMemo } from 'react';
import { useDocumentStore } from '@/store/documentStore';
import type { FieldAnnotation } from '@/types';

export function useAnnotations() {
  const annotations = useDocumentStore(state => state.annotations || []); // Provide a default empty array
  const addAnnotation = useDocumentStore(state => state.addAnnotation);
  const removeAnnotation = useDocumentStore(state => state.removeAnnotation);
  const updateAnnotation = useDocumentStore(state => state.updateAnnotation);

  // Get annotations for a specific paragraph
  const getAnnotationsForParagraph = useMemo(() => {
    return (paragraphIndex: number): FieldAnnotation[] => {
      return annotations.filter(a => a.paragraphIndex === paragraphIndex);
    };
  }, [annotations]);

  // Check if a field name already exists
  const fieldNameExists = (fieldName: string): boolean => {
    return annotations.some(a => a.fieldName === fieldName);
  };

  // Validate field name (snake_case)
  const validateFieldName = (fieldName: string): { valid: boolean; error?: string } => {
    if (!fieldName.trim()) {
      return { valid: false, error: 'Field name cannot be empty' };
    }

    const snakeCasePattern = /^[a-z][a-z0-9_]*$/;
    if (!snakeCasePattern.test(fieldName)) {
      return {
        valid: false,
        error: 'Field name must be snake_case (lowercase, numbers, underscores)',
      };
    }

    if (fieldNameExists(fieldName)) {
      return { valid: false, error: 'Field name already exists' };
    }

    return { valid: true };
  };

  // Get annotation at specific position
  const getAnnotationAtPosition = (
    paragraphIndex: number,
    position: number
  ): FieldAnnotation | null => {
    return (
      annotations.find(
        a =>
          a.paragraphIndex === paragraphIndex &&
          position >= a.start &&
          position < a.end
      ) || null
    );
  };

  return {
    annotations,
    addAnnotation,
    removeAnnotation,
    updateAnnotation,
    getAnnotationsForParagraph,
    fieldNameExists,
    validateFieldName,
    getAnnotationAtPosition,
  };
}
