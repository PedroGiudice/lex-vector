import React, { useCallback, useState } from 'react';
import { Upload, FileText, X, Sparkles, FolderOpen } from 'lucide-react';
import { useTextExtractorStore } from '@/store/textExtractorStore';
import { isTauri } from '@/lib/tauri';
import clsx from 'clsx';

export function UploadPanel() {
  const {
    file,
    fileInfo,
    status,
    useGemini,
    useScript,
    setFile,
    setFilePath,
    setUseGemini,
    setUseScript,
  } = useTextExtractorStore();
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

    try {
      const { open } = await import('@tauri-apps/plugin-dialog');
      const { readFile } = await import('@tauri-apps/plugin-fs');

      const path = await open({
        multiple: false,
        filters: [{ name: 'PDF', extensions: ['pdf'] }],
        title: 'Selecione o PDF',
      });

      if (path && typeof path === 'string') {
        console.log('[UploadPanel] Native dialog returned path:', path);
        const content = await readFile(path);
        const filename = path.split('/').pop() || 'document.pdf';
        const file = new File([content], filename, { type: 'application/pdf' });
        console.log('[UploadPanel] File created, setting both file and filePath');
        // Use getState() to avoid any potential closure issues with destructured setters
        const store = useTextExtractorStore.getState();
        store.setFile(file);
        store.setFilePath(path);
        console.log('[UploadPanel] Both setters called, verifying state...');
        // Verify immediately after setting
        const currentPath = useTextExtractorStore.getState().filePath;
        console.log('[UploadPanel] Verified filePath in store:', currentPath);
      }
    } catch (error) {
      console.error('Native file picker error:', error);
    }
  }, [isDisabled]);

  const handleClearFile = useCallback(() => {
    setFile(null);
    setFilePath(null);
  }, [setFile, setFilePath]);

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

        <label className="te-checkbox-label">
          <input
            type="checkbox"
            checked={useScript}
            onChange={(e) => setUseScript(e.target.checked)}
            disabled={isDisabled}
            className="te-checkbox"
          />
          <FileText size={14} className="te-icon-muted" />
          <span>Limpeza final (script)</span>
        </label>
      </div>
    </div>
  );
}

export default UploadPanel;
