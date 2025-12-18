import React, { useCallback, useState } from 'react';
import { Upload, File } from 'lucide-react';
import clsx from 'clsx';

interface DropZoneProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  disabled?: boolean;
}

export function DropZone({ onFileSelect, accept = '.docx', disabled = false }: DropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragging(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      if (disabled) return;

      const files = Array.from(e.dataTransfer.files);
      const file = files[0];

      if (file && file.name.endsWith('.docx')) {
        onFileSelect(file);
      }
    },
    [onFileSelect, disabled]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        onFileSelect(file);
      }
      // Reset input value to allow selecting the same file again
      e.target.value = '';
    },
    [onFileSelect]
  );

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={clsx(
        'relative border-2 border-dashed rounded-lg p-8 transition-all',
        'flex flex-col items-center justify-center text-center',
        'min-h-[200px]',
        isDragging && !disabled
          ? 'border-gh-accent-primary bg-gh-highlight-bg'
          : 'border-gh-border-default bg-gh-bg-tertiary',
        disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-gh-accent-primary'
      )}
    >
      <input
        type="file"
        accept={accept}
        onChange={handleFileInput}
        disabled={disabled}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        aria-label="Upload document"
      />

      <div className="pointer-events-none">
        {isDragging ? (
          <File className="w-12 h-12 text-gh-accent-primary mb-4" />
        ) : (
          <Upload className="w-12 h-12 text-gh-text-secondary mb-4" />
        )}

        <h3 className="text-lg font-semibold text-gh-text-primary mb-2">
          {isDragging ? 'Drop your file here' : 'Upload Document'}
        </h3>

        <p className="text-sm text-gh-text-secondary mb-4">
          Drag and drop your .docx file here, or click to browse
        </p>

        <p className="text-xs text-gh-text-secondary">
          Maximum file size: 10MB
        </p>
      </div>
    </div>
  );
}
