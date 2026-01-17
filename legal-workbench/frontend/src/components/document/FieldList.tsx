import React from 'react';
import { Trash2 } from 'lucide-react';
import { useAnnotations } from '@/hooks/useAnnotations';

export function FieldList() {
  const { annotations, removeAnnotation } = useAnnotations();

  if (annotations.length === 0) {
    return (
      <div className="text-center py-6">
        <p className="text-xs text-text-muted">Nenhum campo criado ainda</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {annotations.map((annotation) => (
        <div
          key={annotation.fieldName}
          className="flex items-center gap-2 p-2 rounded-lg bg-bg-panel-1 border border-border-default hover:border-accent-violet transition-colors group"
        >
          {/* Indicador de cor */}
          <div
            className="w-3 h-3 rounded-full flex-shrink-0"
            style={{ backgroundColor: annotation.color }}
          />

          {/* Nome do campo */}
          <code className="text-xs font-mono text-text-primary flex-1 truncate">
            {annotation.fieldName}
          </code>

          {/* Botao delete */}
          <button
            onClick={() => removeAnnotation(annotation.fieldName)}
            className="opacity-0 group-hover:opacity-100 text-text-muted hover:text-status-red transition-all"
            aria-label={`Remover ${annotation.fieldName}`}
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      ))}
    </div>
  );
}
