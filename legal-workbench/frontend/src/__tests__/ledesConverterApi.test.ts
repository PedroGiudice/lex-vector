import { describe, it, expect } from 'vitest';
import { validateDocxFile, sanitizeFilename } from '@/services/ledesConverterApi';

describe('ledesConverterApi utilities', () => {
  describe('validateDocxFile', () => {
    it('should accept valid DOCX files', () => {
      const validFile = new File(['test content'], 'invoice.docx', {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });

      const result = validateDocxFile(validFile);
      expect(result.valid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it('should reject files larger than 10MB', () => {
      const largeFile = new File(
        [new ArrayBuffer(11 * 1024 * 1024)],
        'large.docx',
        { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }
      );

      const result = validateDocxFile(largeFile);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('10MB limit');
    });

    it('should reject files without .docx extension', () => {
      const pdfFile = new File(['test content'], 'document.pdf', {
        type: 'application/pdf',
      });

      const result = validateDocxFile(pdfFile);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid file');
    });

    it('should reject files with invalid MIME type', () => {
      const textFile = new File(['test content'], 'document.docx', {
        type: 'text/plain',
      });

      const result = validateDocxFile(textFile);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('file type');
    });

    it('should accept files with empty MIME type (browser fallback)', () => {
      const fileWithEmptyType = new File(['test content'], 'invoice.docx', {
        type: '',
      });

      const result = validateDocxFile(fileWithEmptyType);
      expect(result.valid).toBe(true);
    });

    it('should accept files with octet-stream MIME type', () => {
      const octetStreamFile = new File(['test content'], 'invoice.docx', {
        type: 'application/octet-stream',
      });

      const result = validateDocxFile(octetStreamFile);
      expect(result.valid).toBe(true);
    });

    it('should be case-insensitive for file extensions', () => {
      const uppercaseFile = new File(['test'], 'INVOICE.DOCX', {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });

      const result = validateDocxFile(uppercaseFile);
      expect(result.valid).toBe(true);
    });
  });

  describe('sanitizeFilename', () => {
    it('should not modify safe filenames', () => {
      const safeFilename = 'invoice_2024_01_15.docx';
      const result = sanitizeFilename(safeFilename);
      expect(result).toBe(safeFilename);
    });

    it('should escape < character', () => {
      const filename = 'file<script>.docx';
      const result = sanitizeFilename(filename);
      expect(result).toBe('file&lt;script&gt;.docx');
    });

    it('should escape > character', () => {
      const filename = 'file>script.docx';
      const result = sanitizeFilename(filename);
      expect(result).toBe('file&gt;script.docx');
    });

    it('should escape " character', () => {
      const filename = 'file"test".docx';
      const result = sanitizeFilename(filename);
      expect(result).toBe('file&quot;test&quot;.docx');
    });

    it('should escape \' character', () => {
      const filename = "file'test'.docx";
      const result = sanitizeFilename(filename);
      expect(result).toBe('file&#39;test&#39;.docx');
    });

    it('should escape & character', () => {
      const filename = 'file&test.docx';
      const result = sanitizeFilename(filename);
      expect(result).toBe('file&amp;test.docx');
    });

    it('should escape multiple special characters', () => {
      const filename = '<script>alert("XSS");</script>';
      const result = sanitizeFilename(filename);
      expect(result).toBe('&lt;script&gt;alert(&quot;XSS&quot;);&lt;/script&gt;');
    });

    it('should preserve other special characters', () => {
      const filename = 'invoice_2024-01-15 (copy).docx';
      const result = sanitizeFilename(filename);
      expect(result).toBe('invoice_2024-01-15 (copy).docx');
    });
  });
});
