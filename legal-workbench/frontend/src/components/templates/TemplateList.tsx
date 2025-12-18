import React, { useEffect } from 'react';
import { useDocumentStore } from '@/store/documentStore';
import { TemplateCard } from './TemplateCard';
import { LayoutTemplate, Loader2 } from 'lucide-react';

export function TemplateList() {
  const templates = useDocumentStore((state) => state.templates);
  const fetchTemplates = useDocumentStore((state) => state.fetchTemplates);
  const isFetchingTemplates = useDocumentStore((state) => state.isFetchingTemplates);

  useEffect(() => {
    // Fetch templates when the component mounts
    fetchTemplates();
  }, [fetchTemplates]);

  if (isFetchingTemplates) {
    return (
      <div className="flex flex-col items-center justify-center p-4">
        <Loader2 className="w-8 h-8 text-gh-accent-primary animate-spin mb-4" />
        <p className="text-sm text-gh-text-secondary">Loading templates...</p>
      </div>
    );
  }

  if (templates.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-4 py-8">
        <LayoutTemplate className="w-12 h-12 text-gh-text-secondary mb-4" />
        <h3 className="text-md font-semibold text-gh-text-primary mb-2">
          No Templates Saved Yet
        </h3>
        <p className="text-xs text-gh-text-secondary max-w-md">
          Save your first template by annotating a document and clicking "Save Current as Template".
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <LayoutTemplate className="w-5 h-5 text-gh-accent-primary" />
        <h2 className="text-sm font-semibold text-gh-text-primary">Saved Templates</h2>
      </div>
      <div className="grid grid-cols-1 gap-3">
        {templates.map((template) => (
          <TemplateCard key={template.id} template={template} />
        ))}
      </div>
    </div>
  );
}
