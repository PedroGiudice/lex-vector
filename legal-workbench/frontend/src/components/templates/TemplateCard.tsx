import React from 'react';
import { Template } from '@/types';
import { useDocumentStore } from '@/store/documentStore';
import { Calendar, Layers, Loader2 } from 'lucide-react';

// Simple date formatter without date-fns dependency
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

interface TemplateCardProps {
  template: Template;
  onUse?: () => void;
}

export function TemplateCard({ template, onUse }: TemplateCardProps) {
  const loadTemplate = useDocumentStore((state) => state.loadTemplate);
  const isLoadingTemplate = useDocumentStore((state) => state.isLoadingTemplate);

  const handleLoadTemplate = async () => {
    if (isLoadingTemplate) return; // Prevent multiple clicks
    try {
      await loadTemplate(template.id);
      // Toast message handled by store
    } catch (error) {
      // Error handled by store
    }
  };

  return (
    <div className="bg-gh-bg-tertiary border border-gh-border-default rounded-lg p-3 flex flex-col hover:border-gh-accent-primary transition-colors duration-200">
      <h3 className="text-sm font-semibold text-gh-text-primary mb-1 truncate">{template.name}</h3>
      {template.description && (
        <p className="text-xs text-gh-text-secondary line-clamp-2 mb-2">{template.description}</p>
      )}
      <div className="flex items-center text-xs text-gh-text-secondary gap-3 mt-auto">
        <div className="flex items-center gap-1" title="Number of fields">
          <Layers className="w-3 h-3 text-gh-accent-primary" />
          <span>{template.fieldCount} fields</span>
        </div>
        <div className="flex items-center gap-1" title="Created on">
          <Calendar className="w-3 h-3 text-gh-accent-success" />
          <span>{formatDate(template.createdAt)}</span>
        </div>
      </div>
      <div className="mt-3 flex gap-2">
        <button
          onClick={handleLoadTemplate}
          disabled={isLoadingTemplate}
          className="flex-1 bg-gh-bg-secondary text-gh-text-primary py-1.5 rounded text-xs font-medium hover:bg-gh-border-default transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoadingTemplate ? (
            <>
              <Loader2 className="w-3 h-3 animate-spin" /> Loading...
            </>
          ) : (
            'Carregar'
          )}
        </button>
        {onUse && (
          <button
            onClick={onUse}
            className="flex-1 bg-gh-accent-primary text-gh-text-primary py-1.5 rounded text-xs font-medium hover:bg-opacity-90 transition-colors flex items-center justify-center"
          >
            Usar
          </button>
        )}
      </div>
    </div>
  );
}
