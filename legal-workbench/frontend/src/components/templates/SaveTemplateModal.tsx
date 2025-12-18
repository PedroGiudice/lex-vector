import React, { useState } from 'react';
import { useDocumentStore } from '@/store/documentStore';
import { X, Save } from 'lucide-react';

interface SaveTemplateModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SaveTemplateModal({ isOpen, onClose }: SaveTemplateModalProps) {
  const [templateName, setTemplateName] = useState('');
  const [templateDescription, setTemplateDescription] = useState('');
  const saveTemplate = useDocumentStore((state) => state.saveTemplate);
  const addToast = useDocumentStore((state) => state.addToast);
  const annotations = useDocumentStore((state) => state.annotations);
  const documentId = useDocumentStore((state) => state.documentId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!templateName.trim()) {
      addToast('Template name cannot be empty', 'error');
      return;
    }
    if (!documentId) {
      addToast('No document loaded to save template from', 'error');
      return;
    }
    if (annotations.length === 0) {
      addToast('No annotations to save in the template', 'error');
      return;
    }

    try {
      await saveTemplate(templateName, templateDescription);
      addToast('Template saved successfully!', 'success');
      setTemplateName('');
      setTemplateDescription('');
      onClose();
    } catch (error) {
      console.error('Failed to save template:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gh-bg-primary bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-gh-bg-secondary border border-gh-border-default rounded-lg shadow-lg w-full max-w-md mx-4">
        <div className="flex justify-between items-center p-4 border-b border-gh-border-default">
          <h2 className="text-lg font-semibold text-gh-text-primary">Save Template</h2>
          <button onClick={onClose} className="text-gh-text-secondary hover:text-gh-text-primary">
            <X className="w-5 h-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label htmlFor="templateName" className="block text-sm font-medium text-gh-text-primary mb-1">
              Template Name
            </label>
            <input
              type="text"
              id="templateName"
              className="w-full px-3 py-2 rounded-md bg-gh-bg-primary border border-gh-border-default text-gh-text-primary focus:ring-gh-accent-primary focus:border-gh-accent-primary"
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              placeholder="e.g., Contract Analysis Template"
              required
            />
          </div>
          <div>
            <label htmlFor="templateDescription" className="block text-sm font-medium text-gh-text-primary mb-1">
              Description (Optional)
            </label>
            <textarea
              id="templateDescription"
              rows={3}
              className="w-full px-3 py-2 rounded-md bg-gh-bg-primary border border-gh-border-default text-gh-text-primary focus:ring-gh-accent-primary focus:border-gh-accent-primary resize-y"
              value={templateDescription}
              onChange={(e) => setTemplateDescription(e.target.value)}
              placeholder="A brief description of this template's purpose."
            ></textarea>
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium rounded-md text-gh-text-secondary hover:bg-gh-bg-tertiary transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium rounded-md bg-gh-accent-primary text-gh-text-primary hover:bg-opacity-90 transition-colors flex items-center gap-2"
            >
              <Save className="w-4 h-4" /> Save Template
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
