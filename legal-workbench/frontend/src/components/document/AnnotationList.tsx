import React, { useState } from 'react';
import { Edit2, Trash2, Save, FileText } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { useAnnotations } from '@/hooks/useAnnotations';
import { useDocumentStore } from '@/store/documentStore';

export function AnnotationList() {
  const { annotations, removeAnnotation } = useAnnotations();
  const saveTemplate = useDocumentStore(state => state.saveTemplate);

  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [isSaving, setIsSaving] = useState(false);

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

  return (
    <div className="h-full flex flex-col bg-gh-bg-secondary border-l border-gh-border-default">
      {/* Header */}
      <div className="px-4 py-4 border-b border-gh-border-default">
        <h2 className="text-lg font-semibold text-gh-text-primary flex items-center gap-2">
          <FileText className="w-5 h-5" />
          Annotations
        </h2>
        <p className="text-xs text-gh-text-secondary mt-1">
          {annotations.length} field{annotations.length !== 1 ? 's' : ''} created
        </p>
      </div>

      {/* Annotation list */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {annotations.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-sm text-gh-text-secondary">
              No annotations yet. Select text in the document to create fields.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {annotations.map(annotation => (
              <div
                key={annotation.fieldName}
                className="bg-gh-bg-tertiary border border-gh-border-default rounded-lg p-3 hover:border-gh-accent-primary transition-colors"
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <code className="text-sm font-mono text-gh-accent-primary">
                    {annotation.fieldName}
                  </code>
                  <button
                    onClick={() => removeAnnotation(annotation.fieldName)}
                    className="text-gh-text-secondary hover:text-gh-accent-danger transition-colors"
                    aria-label={`Delete ${annotation.fieldName}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-xs text-gh-text-secondary line-clamp-2">
                  "{annotation.text}"
                </p>
                <p className="text-xs text-gh-text-secondary mt-1">
                  Paragraph {annotation.paragraphIndex + 1}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer with Save button */}
      {annotations.length > 0 && (
        <div className="px-4 py-4 border-t border-gh-border-default">
          <Button
            variant="primary"
            className="w-full"
            onClick={() => setIsSaveModalOpen(true)}
          >
            <Save className="w-4 h-4 mr-2" />
            Save Template
          </Button>
        </div>
      )}

      {/* Save Template Modal */}
      <Modal
        isOpen={isSaveModalOpen}
        onClose={() => !isSaving && setIsSaveModalOpen(false)}
        title="Save Template"
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => setIsSaveModalOpen(false)}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSaveTemplate}
              disabled={!templateName.trim() || isSaving}
            >
              {isSaving ? 'Saving...' : 'Save'}
            </Button>
          </>
        }
      >
        <Input
          label="Template Name"
          placeholder="e.g., Contrato de Prestação de Serviços"
          value={templateName}
          onChange={e => setTemplateName(e.target.value)}
          onKeyDown={e => {
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
