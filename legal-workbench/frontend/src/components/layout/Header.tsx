import React from 'react';
import { FileText, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useDocumentStore } from '@/store/documentStore';

export function Header() {
  const documentId = useDocumentStore((state) => state.documentId);
  const clearDocument = useDocumentStore((state) => state.clearDocument);

  return (
    <header className="bg-[#181825] border-b border-[#3f3f46] px-6 py-3 h-12 flex items-center">
      {' '}
      {/* Updated background, border, padding, and added height/flex for vertical alignment */}
      <div className="flex items-center justify-between w-full">
        {' '}
        {/* Added w-full */}
        <div className="flex items-center gap-3">
          <FileText className="w-6 h-6 text-[#3b82f6]" />{' '}
          {/* Adjusted icon size to 24px for 48px header */}
          <div>
            <h1 className="text-base font-bold text-[#e4e4e7]">
              {' '}
              {/* Adjusted text size to 16px (body UI default) */}
              Doc Assembler
            </h1>
            <p className="text-xs text-[#a1a1aa]">Template Builder</p>
          </div>
        </div>
        {documentId && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearDocument}
            className="text-[#a1a1aa] hover:text-[#ef4444]"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Clear Document
          </Button>
        )}
      </div>
    </header>
  );
}
