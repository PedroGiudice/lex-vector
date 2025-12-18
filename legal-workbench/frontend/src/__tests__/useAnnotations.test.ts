import { renderHook, act } from '@testing-library/react';
import { useAnnotations } from '@/hooks/useAnnotations';
import { useDocumentStore } from '@/store/documentStore';

// Mock the store
jest.mock('@/store/documentStore');

describe('useAnnotations Hook', () => {
  beforeEach(() => {
    // Reset store before each test
    (useDocumentStore as jest.Mock).mockReturnValue({
      annotations: [],
      addAnnotation: jest.fn(),
      removeAnnotation: jest.fn(),
      updateAnnotation: jest.fn(),
    });
  });

  it('validates field names correctly', () => {
    const { result } = renderHook(() => useAnnotations());

    // Valid field names
    expect(result.current.validateFieldName('nome_autor')).toEqual({ valid: true });
    expect(result.current.validateFieldName('data_assinatura')).toEqual({ valid: true });
    expect(result.current.validateFieldName('valor_total')).toEqual({ valid: true });

    // Invalid field names
    expect(result.current.validateFieldName('')).toEqual({
      valid: false,
      error: 'Field name cannot be empty',
    });

    expect(result.current.validateFieldName('NomeAutor')).toEqual({
      valid: false,
      error: 'Field name must be snake_case (lowercase, numbers, underscores)',
    });

    expect(result.current.validateFieldName('nome-autor')).toEqual({
      valid: false,
      error: 'Field name must be snake_case (lowercase, numbers, underscores)',
    });
  });

  it('checks for field name existence', () => {
    (useDocumentStore as jest.Mock).mockReturnValue({
      annotations: [
        { fieldName: 'nome_autor', text: 'John Doe', start: 0, end: 8, paragraphIndex: 0 },
      ],
      addAnnotation: jest.fn(),
      removeAnnotation: jest.fn(),
      updateAnnotation: jest.fn(),
    });

    const { result } = renderHook(() => useAnnotations());

    expect(result.current.fieldNameExists('nome_autor')).toBe(true);
    expect(result.current.fieldNameExists('outro_campo')).toBe(false);
  });

  it('gets annotations for specific paragraph', () => {
    (useDocumentStore as jest.Mock).mockReturnValue({
      annotations: [
        { fieldName: 'campo1', text: 'text1', start: 0, end: 5, paragraphIndex: 0 },
        { fieldName: 'campo2', text: 'text2', start: 0, end: 5, paragraphIndex: 1 },
        { fieldName: 'campo3', text: 'text3', start: 0, end: 5, paragraphIndex: 0 },
      ],
      addAnnotation: jest.fn(),
      removeAnnotation: jest.fn(),
      updateAnnotation: jest.fn(),
    });

    const { result } = renderHook(() => useAnnotations());

    const paragraph0Annotations = result.current.getAnnotationsForParagraph(0);
    expect(paragraph0Annotations).toHaveLength(2);
    expect(paragraph0Annotations[0].fieldName).toBe('campo1');
    expect(paragraph0Annotations[1].fieldName).toBe('campo3');
  });
});
