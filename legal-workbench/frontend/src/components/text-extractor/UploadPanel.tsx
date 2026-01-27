import React, { useCallback, useState } from 'react';
import { Upload, FileText, X, Sparkles, FolderOpen } from 'lucide-react';
import { useTextExtractorStore } from '@/store/textExtractorStore';
import { isTauri, selectPdfNative } from '@/lib/tauri';
import clsx from 'clsx';

export function UploadPanel() {
  const { file, fileInfo, status, useGemini, setFile, setUseGemini } = useTextExtractorStore();
  const [isDragging, setIsDragging] = useState(false);

  const isDisabled = status === 'processing';

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (!isDisabled) {
        setIsDragging(true);
      }
    },
    [isDisabled]
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      if (isDisabled) return;

      const files = Array.from(e.dataTransfer.files);
      const pdfFile = files.find((f) => f.type === 'application/pdf' || f.name.endsWith('.pdf'));

      if (pdfFile) {
        setFile(pdfFile);
      }
    },
    [isDisabled, setFile]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile) {
        setFile(selectedFile);
      }
      e.target.value = '';
    },
    [setFile]
  );

  const handleNativeSelect = useCallback(async () => {
    if (isDisabled) return;
    const selectedFile = await selectPdfNative();
    if (selectedFile) {
      setFile(selectedFile);
    }
  }, [isDisabled, setFile]);

  const handleClearFile = useCallback(() => {
    setFile(null);
  }, [setFile]);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  return (
    <div className="te-panel">
      <div className="te-panel-header">
        <span className="te-panel-label">[UPLOAD]</span>
        <span className="te-panel-step">#STEP-1</span>
      </div>
      <div className="te-panel-content">
        {!file ? (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={clsx(
              'te-dropzone',
              isDragging && 'te-dropzone--active',
              isDisabled && 'te-dropzone--disabled'
            )}
          >
            <input
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileInput}
              disabled={isDisabled}
              className="te-dropzone-input"
              aria-label="Upload PDF document"
            />

            <div className="te-dropzone-content">
              <div className="te-dropzone-icon">
                <span className="te-icon-bracket">[ &gt; ]</span>
                <span className="te-icon-label">PDF</span>
              </div>
              <div className="te-dropzone-arrow">
                <FileText size={24} className="te-icon-muted" />
                <span className="te-arrow">-&gt;</span>
                <Upload size={24} className="te-icon-accent" />
              </div>
              <div className="te-dropzone-text">
                <span className="te-command">&gt; DROP_PDF_HERE</span>
                <span className="te-comment">| // Drag file or click to browse</span>
              </div>
              <p className="te-hint">Supported: .pdf (max 50MB)</p>
              {isTauri() && (
                <button
                  type="button"
                  onClick={handleNativeSelect}
                  disabled={isDisabled}
                  className="te-btn-native"
                >
                  <FolderOpen size={16} />
                  <span>Selecionar arquivo</span>
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="te-file-preview">
            <div className="te-file-info">
              <FileText size={32} className="te-icon-accent" />
              <div className="te-file-details">
                <span className="te-file-name">{fileInfo?.name}</span>
                <span className="te-file-size">{fileInfo && formatFileSize(fileInfo.size)}</span>
              </div>
              <button
                type="button"
                onClick={handleClearFile}
                disabled={isDisabled}
                className="te-btn-icon"
                aria-label="Remove file"
              >
                <X size={18} />
              </button>
            </div>
          </div>
        )}

        <label className="te-checkbox-label">
          <input
            type="checkbox"
            checked={useGemini}
            onChange={(e) => setUseGemini(e.target.checked)}
            disabled={isDisabled}
            className="te-checkbox"
          />
          <Sparkles size={14} className="te-icon-muted" />
          <span>Use Gemini enhancement (slower, cleaner output)</span>
        </label>
      </div>
    </div>
  );
}

export default UploadPanel;
