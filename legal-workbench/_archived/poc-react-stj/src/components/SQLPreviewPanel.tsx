import type { SQLPreview } from '@/types';

interface SQLPreviewPanelProps {
  preview: SQLPreview;
}

export function SQLPreviewPanel({ preview }: SQLPreviewPanelProps) {
  return (
    <div className="card-terminal">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-terminal-accent font-mono">
          [SQL PREVIEW]
        </h3>
        <span className="badge-info">
          ~{preview.estimatedResults.toLocaleString()} resultados
        </span>
      </div>

      <div className="bg-black/40 rounded border border-terminal-border p-4 overflow-x-auto">
        <pre className="font-mono text-sm text-terminal-text whitespace-pre">
          <code>{preview.query}</code>
        </pre>
      </div>

      <div className="mt-4 flex items-center gap-2 text-xs text-terminal-muted">
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <span>Preview atualizado em tempo real conforme seus filtros</span>
      </div>
    </div>
  );
}
