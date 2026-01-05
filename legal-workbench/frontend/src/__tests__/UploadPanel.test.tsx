import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { UploadPanel } from '@/components/text-extractor/UploadPanel';
import { useTextExtractorStore } from '@/store/textExtractorStore';

// Reset store before each test
beforeEach(() => {
  act(() => {
    const store = useTextExtractorStore.getState();
    store.reset();
    store.clearLogs();
  });
});

describe('UploadPanel', () => {
  describe('initial render', () => {
    it('should render the panel with correct header', () => {
      render(<UploadPanel />);

      expect(screen.getByText('[UPLOAD]')).toBeInTheDocument();
      expect(screen.getByText('#STEP-1')).toBeInTheDocument();
    });

    it('should show dropzone when no file is selected', () => {
      render(<UploadPanel />);

      expect(screen.getByText('> DROP_PDF_HERE')).toBeInTheDocument();
      expect(screen.getByText('| // Drag file or click to browse')).toBeInTheDocument();
      expect(screen.getByText('Supported: .pdf (max 50MB)')).toBeInTheDocument();
    });

    it('should have an accessible file input', () => {
      render(<UploadPanel />);

      const fileInput = screen.getByLabelText('Upload PDF document');
      expect(fileInput).toBeInTheDocument();
      expect(fileInput).toHaveAttribute('accept', '.pdf,application/pdf');
    });
  });

  describe('file selection', () => {
    it('should accept PDF files via file input', async () => {
      render(<UploadPanel />);

      const file = new File(['test content'], 'document.pdf', {
        type: 'application/pdf',
      });

      const fileInput = screen.getByLabelText('Upload PDF document');

      await act(async () => {
        fireEvent.change(fileInput, { target: { files: [file] } });
      });

      const state = useTextExtractorStore.getState();
      expect(state.file).toBeTruthy();
      expect(state.fileInfo?.name).toBe('document.pdf');
    });

    it('should show file preview after selection', async () => {
      const { rerender } = render(<UploadPanel />);

      const file = new File(['test content'], 'contract.pdf', {
        type: 'application/pdf',
      });

      const fileInput = screen.getByLabelText('Upload PDF document');

      await act(async () => {
        fireEvent.change(fileInput, { target: { files: [file] } });
      });

      // Re-render to show file preview
      rerender(<UploadPanel />);

      expect(screen.getByText('contract.pdf')).toBeInTheDocument();
    });
  });

  describe('drag and drop', () => {
    it('should have visual feedback on dragover', async () => {
      const { container } = render(<UploadPanel />);

      const dropzone = container.querySelector('.te-dropzone');
      expect(dropzone).toBeInTheDocument();

      await act(async () => {
        fireEvent.dragOver(dropzone as Element, {
          dataTransfer: { files: [] },
        });
      });

      expect(dropzone).toHaveClass('te-dropzone--active');
    });

    it('should remove visual feedback on dragleave', async () => {
      const { container } = render(<UploadPanel />);

      const dropzone = container.querySelector('.te-dropzone');

      await act(async () => {
        fireEvent.dragOver(dropzone as Element, {
          dataTransfer: { files: [] },
        });
      });

      await act(async () => {
        fireEvent.dragLeave(dropzone as Element);
      });

      expect(dropzone).not.toHaveClass('te-dropzone--active');
    });
  });

  describe('Gemini toggle', () => {
    it('should render Gemini enhancement checkbox', () => {
      render(<UploadPanel />);

      expect(
        screen.getByText('Use Gemini enhancement (slower, cleaner output)')
      ).toBeInTheDocument();
    });

    it('should toggle Gemini enhancement', async () => {
      render(<UploadPanel />);

      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).not.toBeChecked();

      await act(async () => {
        fireEvent.click(checkbox);
      });

      expect(useTextExtractorStore.getState().useGemini).toBe(true);
    });
  });

  describe('file removal', () => {
    it('should clear file when remove button is clicked', async () => {
      // First, set a file
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      await act(async () => {
        useTextExtractorStore.getState().setFile(file);
      });

      render(<UploadPanel />);

      const removeButton = screen.getByLabelText('Remove file');
      expect(removeButton).toBeInTheDocument();

      await act(async () => {
        fireEvent.click(removeButton);
      });

      expect(useTextExtractorStore.getState().file).toBeNull();
    });
  });
});
