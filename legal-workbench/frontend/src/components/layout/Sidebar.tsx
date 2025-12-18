import React, { useState } from 'react';
import { Upload, FileText, Sparkles, LayoutTemplate, Plus } from 'lucide-react';
import { DropZone } from '@/components/upload/DropZone';
import { UploadProgress } from '@/components/upload/UploadProgress';
import { useDocumentUpload } from '@/hooks/useDocumentUpload';
import { useDocumentStore } from '@/store/documentStore';
import { PatternList } from '@/components/document/PatternList';
import { SaveTemplateModal } from '@/components/templates/SaveTemplateModal'; // Import SaveTemplateModal
import { TemplateList } from '@/components/templates/TemplateList'; // Import TemplateList

export function Sidebar() {
  const { uploadDocument, isUploading, uploadProgress } = useDocumentUpload();
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const documentId = useDocumentStore(state => state.documentId);
  const annotations = useDocumentStore(state => state.annotations); // Get annotations count

  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);

  const handleFileSelect = async (file: File) => {
    setSelectedFileName(file.name);
    try {
      await uploadDocument(file);
    } catch (error) {
      console.error('Upload error:', error);
      setSelectedFileName(null);
    }
  };

  return (
    <aside className="w-60 bg-gh-bg-secondary border-r border-gh-border-default flex flex-col">
      {/* Upload section */}
      <div className="p-4 border-b border-gh-border-default">
        <div className="flex items-center gap-2 mb-3">
          <Upload className="w-5 h-5 text-gh-accent-primary" />
          <h2 className="text-sm font-semibold text-gh-text-primary">Upload</h2>
        </div>

        {isUploading ? (
          <UploadProgress progress={uploadProgress} fileName={selectedFileName || undefined} />
        ) : (
          <DropZone onFileSelect={handleFileSelect} disabled={isUploading} />
        )}
      </div>

      {/* Detected patterns section */}
      {documentId && (
        <div className="p-4 border-b border-gh-border-default">
          <PatternList />
        </div>
      )}

      {/* Templates section */}
      <div className="p-4 border-b border-gh-border-default flex flex-col space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <LayoutTemplate className="w-5 h-5 text-gh-accent-primary" />
            <h2 className="text-sm font-semibold text-gh-text-primary">Templates</h2>
          </div>
          {documentId && annotations.length > 0 && ( // Only show save button if a document is loaded and has annotations
            <button
              onClick={() => setIsSaveModalOpen(true)}
              className="px-3 py-1 text-xs font-medium rounded-md bg-gh-accent-primary text-gh-text-primary hover:bg-opacity-90 transition-colors flex items-center gap-1"
              title="Save current annotations as a new template"
            >
              <Plus className="w-3 h-3" /> Save
            </button>
          )}
        </div>
        <TemplateList /> {/* Integrate TemplateList here */}
      </div>

      {/* Instructions */}
      <div className="flex-1 p-4 overflow-y-auto">
        <div className="flex items-center gap-2 mb-3">
          <FileText className="w-5 h-5 text-gh-accent-primary" />
          <h2 className="text-sm font-semibold text-gh-text-primary">
            How to Use
          </h2>
        </div>
        <ol className="space-y-3 text-xs text-gh-text-secondary">
          <li className="flex gap-2">
            <span className="flex-shrink-0 font-semibold text-gh-accent-primary">
              1.
            </span>
            <span>Upload a .docx document using the dropzone above</span>
          </li>
          <li className="flex gap-2">
            <span className="flex-shrink-0 font-semibold text-gh-accent-primary">
              2.
            </span>
            <span>Select text in the document viewer to create field annotations</span>
          </li>
          <li className="flex gap-2">
            <span className="flex-shrink-0 font-semibold text-gh-accent-primary">
              3.
            </span>
            <span>Enter a field name in snake_case (e.g., nome_autor)</span>
          </li>
          <li className="flex gap-2">
            <span className="flex-shrink-0 font-semibold text-gh-accent-primary">
              4.
            </span>
            <span>Review your annotations in the right panel</span>
          </li>
          <li className="flex gap-2">
            <span className="flex-shrink-0 font-semibold text-gh-accent-primary">
              5.
            </span>
            <span>Click "Save Template" when done</span>
          </li>
        </ol>
      </div>

      <SaveTemplateModal isOpen={isSaveModalOpen} onClose={() => setIsSaveModalOpen(false)} />
    </aside>
  );
}
