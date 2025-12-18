import { useEffect } from 'react';
import { DocumentViewer } from '@/components/document/DocumentViewer';
import { AnnotationList } from '@/components/document/AnnotationList';
import { TemplateList } from '@/components/templates/TemplateList';
import { useDocumentStore } from '@/store/documentStore';
import { FileText, Upload } from 'lucide-react';
import { DropZone } from '@/components/upload/DropZone';

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-text-muted">
      <Upload size={48} className="mb-4 opacity-50" />
      <h2 className="text-lg font-medium mb-2">No Document Selected</h2>
      <p className="text-sm">Upload a document or select a template to get started</p>
    </div>
  );
}

export default function DocAssemblerModule() {
  const paragraphs = useDocumentStore(state => state.paragraphs);
  const templates = useDocumentStore(state => state.templates);
  const fetchTemplates = useDocumentStore(state => state.fetchTemplates);
  const uploadDocument = useDocumentStore(state => state.uploadDocument);
  const isUploading = useDocumentStore(state => state.isUploading);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const handleFileSelect = async (file: File) => {
    try {
      await uploadDocument(file);
    } catch (error) {
      console.error('Failed to upload document:', error);
    }
  };

  const hasDocument = paragraphs.length > 0;

  return (
    <div className="flex flex-col h-full bg-bg-main text-text-primary">
      {/* Header */}
      <header className="h-12 border-b border-border-default bg-bg-panel-1 flex items-center px-4">
        <FileText className="text-accent-violet mr-2" size={20} />
        <h1 className="text-lg font-bold text-accent-violet">Doc Assembler</h1>
        <div className="ml-auto text-text-muted text-xs">
          {templates.length} template{templates.length !== 1 ? 's' : ''} disponíve{templates.length !== 1 ? 'is' : 'l'}
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Upload & Templates */}
        <aside className="w-72 border-r border-border-default flex flex-col bg-bg-panel-1">
          <div className="p-4 border-b border-border-default">
            <h2 className="text-sm font-semibold text-text-muted mb-3 uppercase tracking-wide">Upload</h2>
            <DropZone
              onFileSelect={handleFileSelect}
              disabled={isUploading}
            />
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            <h2 className="text-sm font-semibold text-text-muted mb-3 uppercase tracking-wide">Templates</h2>
            <TemplateList />
          </div>
        </aside>

        {/* Center - Document Viewer */}
        <main className="flex-1 overflow-hidden">
          {hasDocument ? (
            <DocumentViewer />
          ) : (
            <EmptyState />
          )}
        </main>

        {/* Right Sidebar - Annotations */}
        <aside className="w-80 border-l border-border-default bg-surface-elevated">
          <div className="p-4 border-b border-border-default">
            <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wide">Annotations</h2>
          </div>
          <div className="overflow-y-auto h-full">
            <AnnotationList />
          </div>
        </aside>
      </div>
    </div>
  );
}
