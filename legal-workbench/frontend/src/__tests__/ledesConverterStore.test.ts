import { act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { useLedesConverterStore } from '@/store/ledesConverterStore';
import { ledesConverterApi } from '@/services/ledesConverterApi';

// Mock the API
vi.mock('@/services/ledesConverterApi', () => ({
  ledesConverterApi: {
    convertDocxToLedes: vi.fn(),
  },
  validateDocxFile: vi.fn((file: File) => {
    if (file.size > 10 * 1024 * 1024) {
      return { valid: false, error: 'File too large' };
    }
    if (!file.name.endsWith('.docx')) {
      return { valid: false, error: 'Invalid extension' };
    }
    return { valid: true };
  }),
}));

// Reset store before each test
beforeEach(() => {
  const store = useLedesConverterStore.getState();
  store.reset();
  vi.clearAllMocks();
});

describe('ledesConverterStore', () => {
  describe('initial state', () => {
    it('should have correct initial values', () => {
      const state = useLedesConverterStore.getState();

      expect(state.file).toBeNull();
      expect(state.status).toBe('idle');
      expect(state.uploadProgress).toBe(0);
      expect(state.ledesContent).toBeNull();
      expect(state.extractedData).toBeNull();
      expect(state.error).toBeNull();
      expect(state.retryCount).toBe(0);
    });
  });

  describe('setFile', () => {
    it('should set file when valid DOCX is provided', () => {
      const mockFile = new File(['test content'], 'invoice.docx', {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });

      act(() => {
        useLedesConverterStore.getState().setFile(mockFile);
      });

      const state = useLedesConverterStore.getState();
      expect(state.file).toBe(mockFile);
      expect(state.status).toBe('idle');
      expect(state.error).toBeNull();
    });

    it('should reject file larger than 10MB', () => {
      // Create a mock file larger than 10MB
      const largeFile = new File(
        [new ArrayBuffer(11 * 1024 * 1024)],
        'large.docx',
        { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }
      );

      act(() => {
        useLedesConverterStore.getState().setFile(largeFile);
      });

      const state = useLedesConverterStore.getState();
      expect(state.file).toBeNull();
      expect(state.status).toBe('error');
      expect(state.error).toBeTruthy();
    });

    it('should reject non-DOCX files', () => {
      const pdfFile = new File(['test'], 'document.pdf', {
        type: 'application/pdf',
      });

      act(() => {
        useLedesConverterStore.getState().setFile(pdfFile);
      });

      const state = useLedesConverterStore.getState();
      expect(state.file).toBeNull();
      expect(state.status).toBe('error');
      expect(state.error).toBeTruthy();
    });

    it('should clear state when null is provided', () => {
      const mockFile = new File(['test'], 'invoice.docx', {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });

      act(() => {
        useLedesConverterStore.getState().setFile(mockFile);
      });

      act(() => {
        useLedesConverterStore.getState().setFile(null);
      });

      const state = useLedesConverterStore.getState();
      expect(state.file).toBeNull();
      expect(state.status).toBe('idle');
      expect(state.ledesContent).toBeNull();
      expect(state.extractedData).toBeNull();
    });
  });

  describe('convertFile', () => {
    it('should successfully convert a valid file', async () => {
      const mockFile = new File(['test'], 'invoice.docx', {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });

      const mockResponse = {
        filename: 'invoice.docx',
        status: 'success' as const,
        ledes_content: 'INVOICE_DATE|INVOICE_NUMBER|CLIENT_ID|...',
        extracted_data: {
          invoice_date: '2024-01-15',
          invoice_number: 'INV-001',
          client_id: 'CLIENT123',
          matter_id: 'MATTER456',
          invoice_total: 5000.00,
          line_items: [],
        },
      };

      (ledesConverterApi.convertDocxToLedes as Mock).mockResolvedValue(mockResponse);

      act(() => {
        useLedesConverterStore.getState().setFile(mockFile);
      });

      await act(async () => {
        await useLedesConverterStore.getState().convertFile();
      });

      const state = useLedesConverterStore.getState();
      expect(state.status).toBe('success');
      expect(state.ledesContent).toBe(mockResponse.ledes_content);
      expect(state.extractedData).toEqual(mockResponse.extracted_data);
      expect(state.uploadProgress).toBe(100);
      expect(state.error).toBeNull();
    });

    it('should handle conversion errors', async () => {
      const mockFile = new File(['test'], 'invoice.docx', {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });

      (ledesConverterApi.convertDocxToLedes as Mock).mockRejectedValue(
        new Error('Conversion failed')
      );

      act(() => {
        useLedesConverterStore.getState().setFile(mockFile);
      });

      await act(async () => {
        await useLedesConverterStore.getState().convertFile();
      });

      const state = useLedesConverterStore.getState();
      expect(state.status).toBe('error');
      expect(state.error).toBeTruthy();
      expect(state.ledesContent).toBeNull();
    });

    it('should not convert when no file is selected', async () => {
      await act(async () => {
        await useLedesConverterStore.getState().convertFile();
      });

      const state = useLedesConverterStore.getState();
      expect(state.status).toBe('error');
      expect(state.error).toBe('No file selected for conversion.');
      expect(ledesConverterApi.convertDocxToLedes).not.toHaveBeenCalled();
    });

    it('should update progress during upload', async () => {
      const mockFile = new File(['test'], 'invoice.docx', {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });

      let progressCallback: ((progress: number) => void) | undefined;

      (ledesConverterApi.convertDocxToLedes as Mock).mockImplementation(
        (file, onProgress) => {
          progressCallback = onProgress;
          return new Promise((resolve) => {
            setTimeout(() => {
              resolve({
                filename: 'invoice.docx',
                status: 'success',
                ledes_content: 'test content',
              });
            }, 100);
          });
        }
      );

      act(() => {
        useLedesConverterStore.getState().setFile(mockFile);
      });

      const conversionPromise = act(async () => {
        await useLedesConverterStore.getState().convertFile();
      });

      // Simulate progress updates
      if (progressCallback) {
        act(() => {
          progressCallback!(50);
        });

        const midState = useLedesConverterStore.getState();
        expect(midState.uploadProgress).toBeGreaterThan(0);
      }

      await conversionPromise;

      const finalState = useLedesConverterStore.getState();
      expect(finalState.status).toBe('success');
    });
  });

  describe('downloadResult', () => {
    it('should create download link when content exists', () => {
      const mockFile = new File(['test'], 'invoice.docx', {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });

      const mockLedesContent = 'INVOICE_DATE|INVOICE_NUMBER|CLIENT_ID';

      // Setup state
      act(() => {
        useLedesConverterStore.setState({
          file: mockFile,
          ledesContent: mockLedesContent,
          status: 'success',
        });
      });

      // Mock DOM methods
      const createElementSpy = vi.spyOn(document, 'createElement');
      const appendChildSpy = vi.spyOn(document.body, 'appendChild');
      const removeChildSpy = vi.spyOn(document.body, 'removeChild');

      act(() => {
        useLedesConverterStore.getState().downloadResult();
      });

      expect(createElementSpy).toHaveBeenCalledWith('a');
      expect(appendChildSpy).toHaveBeenCalled();

      // Cleanup spies
      createElementSpy.mockRestore();
      appendChildSpy.mockRestore();
      removeChildSpy.mockRestore();
    });

    it('should not download when no content exists', () => {
      const createElementSpy = vi.spyOn(document, 'createElement');

      act(() => {
        useLedesConverterStore.getState().downloadResult();
      });

      expect(createElementSpy).not.toHaveBeenCalled();
      createElementSpy.mockRestore();
    });
  });

  describe('reset', () => {
    it('should reset state to initial values', () => {
      const mockFile = new File(['test'], 'invoice.docx', {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });

      act(() => {
        useLedesConverterStore.setState({
          file: mockFile,
          status: 'success',
          uploadProgress: 100,
          ledesContent: 'test content',
          extractedData: {
            invoice_date: '2024-01-15',
            invoice_number: 'INV-001',
            client_id: 'CLIENT123',
            matter_id: 'MATTER456',
            invoice_total: 5000.00,
            line_items: [],
          },
          error: null,
          retryCount: 2,
        });
      });

      act(() => {
        useLedesConverterStore.getState().reset();
      });

      const state = useLedesConverterStore.getState();
      expect(state.file).toBeNull();
      expect(state.status).toBe('idle');
      expect(state.uploadProgress).toBe(0);
      expect(state.ledesContent).toBeNull();
      expect(state.extractedData).toBeNull();
      expect(state.error).toBeNull();
      expect(state.retryCount).toBe(0);
    });
  });
});
