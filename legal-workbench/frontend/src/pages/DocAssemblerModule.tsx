import { useEffect, useState } from 'react';
import { TipTapDocumentViewer } from '@/components/document/TipTapDocumentViewer';
import { FieldList } from '@/components/document/FieldList';
import { FieldEditorPanel } from '@/components/document/FieldEditorPanel';
import { TemplateList } from '@/components/templates/TemplateList';
import { useDocumentStore } from '@/store/documentStore';
import { FileText, Upload, Save, LayoutTemplate, Tag } from 'lucide-react';
import { DropZone } from '@/components/upload/DropZone';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { CollapsibleSection } from '@/components/ui/CollapsibleSection';

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
  const paragraphs = useDocumentStore((state) => state.paragraphs);
  const templates = useDocumentStore((state) => state.templates);
  const annotations = useDocumentStore((state) => state.annotations);
  const fetchTemplates = useDocumentStore((state) => state.fetchTemplates);
  const uploadDocument = useDocumentStore((state) => state.uploadDocument);
  const saveTemplate = useDocumentStore((state) => state.saveTemplate);
  const isUploading = useDocumentStore((state) => state.isUploading);

  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [isSaving, setIsSaving] = useState(false);

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

  const handleSaveTemplate = async () => {
    if (!templateName.trim()) {
      return;
    }

    setIsSaving(true);
    try {
      await saveTemplate(templateName);
      setIsSaveModalOpen(false);
      setTemplateName('');
    } catch (error) {
      console.error('Failed to save template:', error);
    } finally {
      setIsSaving(false);
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
          {templates.length} template{templates.length !== 1 ? 's' : ''} disponíve
          {templates.length !== 1 ? 'is' : 'l'}
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Upload, Templates, Fields */}
        <aside className="w-72 border-r border-border-default flex flex-col bg-bg-panel-1">
          {/* Upload - compact at top */}
          <CollapsibleSection
            title="Upload"
            icon={Upload}
            defaultExpanded={true}
            className="border-b border-border-default"
          >
            <DropZone onFileSelect={handleFileSelect} disabled={isUploading} compact />
          </CollapsibleSection>

          {/* Templates - main section, gets most space */}
          <CollapsibleSection
            title="Templates"
            icon={LayoutTemplate}
            badge={templates.length || undefined}
            defaultExpanded={true}
            className="flex-1 min-h-0 border-b border-border-default"
            contentClassName="overflow-y-auto max-h-[calc(100%-36px)]"
          >
            <TemplateList />
          </CollapsibleSection>

          {/* Campos criados - secondary section */}
          <CollapsibleSection
            title="Campos"
            icon={Tag}
            badge={annotations?.length || undefined}
            defaultExpanded={true}
            className="flex-shrink-0 max-h-48"
            contentClassName="overflow-y-auto max-h-32"
          >
            <FieldList />
          </CollapsibleSection>
        </aside>

        {/* Center - Document Viewer */}
        <main className="flex-1 overflow-hidden">
          {hasDocument ? <TipTapDocumentViewer /> : <EmptyState />}
        </main>

        {/* Right Sidebar - Field Editor Panel */}
        <aside className="w-80 border-l border-border-default bg-surface-elevated flex flex-col">
          <FieldEditorPanel />

          {/* Save Template Button - footer */}
          {annotations && annotations.length > 0 && (
            <div className="p-4 border-t border-border-default mt-auto">
              <Button variant="primary" className="w-full" onClick={() => setIsSaveModalOpen(true)}>
                <Save className="w-4 h-4 mr-2" />
                Salvar Template
              </Button>
            </div>
          )}
        </aside>
      </div>

      {/* Save Template Modal */}
      <Modal
        isOpen={isSaveModalOpen}
        onClose={() => !isSaving && setIsSaveModalOpen(false)}
        title="Salvar Template"
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsSaveModalOpen(false)} disabled={isSaving}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              onClick={handleSaveTemplate}
              disabled={!templateName.trim() || isSaving}
            >
              {isSaving ? 'Salvando...' : 'Salvar'}
            </Button>
          </>
        }
      >
        <Input
          label="Nome do Template"
          placeholder="ex: Contrato de Prestacao de Servicos"
          value={templateName}
          onChange={(e) => setTemplateName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && templateName.trim() && !isSaving) {
              handleSaveTemplate();
            }
          }}
          autoFocus
        />
      </Modal>
    </div>
  );
}
