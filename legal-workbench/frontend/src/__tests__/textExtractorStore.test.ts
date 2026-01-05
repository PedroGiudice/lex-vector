import { act } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { useTextExtractorStore } from '@/store/textExtractorStore';

// Reset store before each test
beforeEach(() => {
  const store = useTextExtractorStore.getState();
  store.reset();
  store.clearLogs();
});

describe('textExtractorStore', () => {
  describe('initial state', () => {
    it('should have correct initial values', () => {
      const state = useTextExtractorStore.getState();

      expect(state.file).toBeNull();
      expect(state.fileInfo).toBeNull();
      expect(state.engine).toBe('marker');
      expect(state.useGemini).toBe(false);
      expect(state.status).toBe('idle');
      expect(state.progress).toBe(0);
      expect(state.result).toBeNull();
      expect(state.jobId).toBeNull();
    });

    it('should have default margins', () => {
      const state = useTextExtractorStore.getState();

      expect(state.margins).toEqual({
        top: 15,
        bottom: 20,
        left: 10,
        right: 10,
      });
    });

    it('should have LGPD preset terms loaded by default', () => {
      const state = useTextExtractorStore.getState();

      expect(state.ignoreTerms).toContain('Pagina X de Y');
      expect(state.ignoreTerms).toContain('TRIBUNAL DE JUSTICA');
      expect(state.ignoreTerms).toContain('Documento assinado digitalmente');
    });
  });

  describe('setFile', () => {
    it('should set file and fileInfo when valid file is provided', () => {
      const mockFile = new File(['test content'], 'test.pdf', {
        type: 'application/pdf',
      });

      act(() => {
        useTextExtractorStore.getState().setFile(mockFile);
      });

      const state = useTextExtractorStore.getState();
      expect(state.file).toBe(mockFile);
      expect(state.fileInfo).toEqual({
        name: 'test.pdf',
        size: mockFile.size,
        type: 'application/pdf',
      });
      expect(state.status).toBe('preflight');
    });

    it('should clear file when null is provided', () => {
      const mockFile = new File(['test content'], 'test.pdf', {
        type: 'application/pdf',
      });

      act(() => {
        useTextExtractorStore.getState().setFile(mockFile);
      });

      act(() => {
        useTextExtractorStore.getState().setFile(null);
      });

      const state = useTextExtractorStore.getState();
      expect(state.file).toBeNull();
      expect(state.fileInfo).toBeNull();
      expect(state.status).toBe('idle');
    });
  });

  describe('setEngine', () => {
    it('should update engine to marker', () => {
      act(() => {
        useTextExtractorStore.getState().setEngine('marker');
      });

      expect(useTextExtractorStore.getState().engine).toBe('marker');
    });

    it('should update engine to pdfplumber', () => {
      act(() => {
        useTextExtractorStore.getState().setEngine('pdfplumber');
      });

      expect(useTextExtractorStore.getState().engine).toBe('pdfplumber');
    });
  });

  describe('setUseGemini', () => {
    it('should toggle Gemini enhancement', () => {
      act(() => {
        useTextExtractorStore.getState().setUseGemini(true);
      });

      expect(useTextExtractorStore.getState().useGemini).toBe(true);

      act(() => {
        useTextExtractorStore.getState().setUseGemini(false);
      });

      expect(useTextExtractorStore.getState().useGemini).toBe(false);
    });
  });

  describe('setMargins', () => {
    it('should update margins', () => {
      const newMargins = { top: 25, bottom: 30, left: 15, right: 15 };

      act(() => {
        useTextExtractorStore.getState().setMargins(newMargins);
      });

      expect(useTextExtractorStore.getState().margins).toEqual(newMargins);
    });
  });

  describe('ignore terms management', () => {
    it('should add a new ignore term', () => {
      act(() => {
        useTextExtractorStore.getState().addIgnoreTerm('New Term');
      });

      expect(useTextExtractorStore.getState().ignoreTerms).toContain('New Term');
    });

    it('should not add duplicate terms', () => {
      const initialLength = useTextExtractorStore.getState().ignoreTerms.length;

      act(() => {
        useTextExtractorStore.getState().addIgnoreTerm('Pagina X de Y');
      });

      expect(useTextExtractorStore.getState().ignoreTerms.length).toBe(initialLength);
    });

    it('should not add empty terms', () => {
      const initialLength = useTextExtractorStore.getState().ignoreTerms.length;

      act(() => {
        useTextExtractorStore.getState().addIgnoreTerm('   ');
      });

      expect(useTextExtractorStore.getState().ignoreTerms.length).toBe(initialLength);
    });

    it('should remove an ignore term', () => {
      act(() => {
        useTextExtractorStore.getState().removeIgnoreTerm('Pagina X de Y');
      });

      expect(useTextExtractorStore.getState().ignoreTerms).not.toContain('Pagina X de Y');
    });

    it('should set all ignore terms', () => {
      const newTerms = ['Term A', 'Term B', 'Term C'];

      act(() => {
        useTextExtractorStore.getState().setIgnoreTerms(newTerms);
      });

      expect(useTextExtractorStore.getState().ignoreTerms).toEqual(newTerms);
    });
  });

  describe('loadPreset', () => {
    it('should load LGPD preset', () => {
      act(() => {
        useTextExtractorStore.getState().setIgnoreTerms([]);
      });

      act(() => {
        useTextExtractorStore.getState().loadPreset('lgpd');
      });

      const state = useTextExtractorStore.getState();
      expect(state.ignoreTerms).toContain('TRIBUNAL DE JUSTICA');
      expect(state.ignoreTerms).toContain('Documento assinado digitalmente');
    });

    it('should load court preset', () => {
      act(() => {
        useTextExtractorStore.getState().loadPreset('court');
      });

      const state = useTextExtractorStore.getState();
      expect(state.ignoreTerms).toContain('PODER JUDICIARIO');
      expect(state.ignoreTerms).toContain('MINISTERIO PUBLICO');
    });

    it('should load contract preset', () => {
      act(() => {
        useTextExtractorStore.getState().loadPreset('contract');
      });

      const state = useTextExtractorStore.getState();
      expect(state.ignoreTerms).toContain('Rubrica:');
      expect(state.ignoreTerms).toContain('Testemunhas:');
    });
  });

  describe('logs', () => {
    it('should add log entries', () => {
      act(() => {
        useTextExtractorStore.getState().addLog('Test message');
      });

      const state = useTextExtractorStore.getState();
      expect(state.logs.length).toBeGreaterThan(0);
      expect(state.logs[state.logs.length - 1].message).toBe('Test message');
    });

    it('should add log entries with different levels', () => {
      act(() => {
        useTextExtractorStore.getState().addLog('Error message', 'error');
      });

      const state = useTextExtractorStore.getState();
      const lastLog = state.logs[state.logs.length - 1];
      expect(lastLog.level).toBe('error');
    });

    it('should clear logs', () => {
      act(() => {
        useTextExtractorStore.getState().addLog('Test');
        useTextExtractorStore.getState().clearLogs();
      });

      expect(useTextExtractorStore.getState().logs).toHaveLength(0);
    });
  });

  describe('reset', () => {
    it('should reset state to initial values', () => {
      const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      act(() => {
        const store = useTextExtractorStore.getState();
        store.setFile(mockFile);
        store.setEngine('pdfplumber');
        store.setUseGemini(true);
      });

      act(() => {
        useTextExtractorStore.getState().reset();
      });

      const state = useTextExtractorStore.getState();
      expect(state.file).toBeNull();
      expect(state.fileInfo).toBeNull();
      expect(state.status).toBe('idle');
      expect(state.progress).toBe(0);
      expect(state.result).toBeNull();
      expect(state.jobId).toBeNull();
    });
  });
});
