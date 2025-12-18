import React from 'react';
import { Loader2 } from 'lucide-react';

interface UploadProgressProps {
  progress: number;
  fileName?: string;
}

export function UploadProgress({ progress, fileName }: UploadProgressProps) {
  return (
    <div className="bg-gh-bg-tertiary border border-gh-border-default rounded-lg p-6">
      <div className="flex items-center gap-4 mb-4">
        <Loader2 className="w-6 h-6 text-gh-accent-primary animate-spin" />
        <div className="flex-1">
          <p className="text-sm font-medium text-gh-text-primary mb-1">
            {fileName ? `Uploading ${fileName}...` : 'Uploading document...'}
          </p>
          <p className="text-xs text-gh-text-secondary">
            Processing document and extracting text
          </p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gh-bg-secondary rounded-full h-2 overflow-hidden">
        <div
          className="bg-gh-accent-primary h-full transition-all duration-300 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      <p className="text-xs text-gh-text-secondary text-right mt-2">{progress}%</p>
    </div>
  );
}
