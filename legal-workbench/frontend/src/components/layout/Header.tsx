import React from 'react';
import { FileText, Upload, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useDocumentStore } from '@/store/documentStore';

export function Header() {
  const documentId = useDocumentStore(state => state.documentId);
  const clearDocument = useDocumentStore(state => state.clearDocument);

  return (
    <header className="bg-gh-bg-secondary border-b border-gh-border-default px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="w-8 h-8 text-gh-accent-primary" />
          <div>
            <h1 className="text-xl font-bold text-gh-text-primary">
              Doc Assembler
            </h1>
            <p className="text-xs text-gh-text-secondary">Template Builder</p>
          </div>
        </div>

        {documentId && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearDocument}
            className="text-gh-text-secondary hover:text-gh-accent-danger"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Clear Document
          </Button>
        )}
      </div>
    </header>
  );
}
