import type { JurisprudenceResult } from '@/types';
import { OutcomeBadge } from './OutcomeBadge';

interface JurisprudenceResultCardProps {
  result: JurisprudenceResult;
}

export function JurisprudenceResultCard({
  result,
}: JurisprudenceResultCardProps) {
  return (
    <div className="card-terminal hover:border-terminal-accent/50 transition-all">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1">
          <h4 className="font-mono text-terminal-accent font-semibold">
            {result.processoNumero}
          </h4>
          <p className="text-sm text-terminal-muted mt-1">
            {result.orgaoJulgador} • {result.relator}
          </p>
        </div>
        <OutcomeBadge outcome={result.outcome} />
      </div>

      <p className="text-sm text-terminal-text leading-relaxed mb-3">
        {result.ementa}
      </p>

      <div className="flex items-center gap-3 text-xs text-terminal-muted">
        <span className="flex items-center gap-1">
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
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          {new Date(result.dataJulgamento).toLocaleDateString('pt-BR')}
        </span>
      </div>
    </div>
  );
}
