import { Calendar, User, Building, Gavel } from 'lucide-react';
import type { AcordaoSummary } from '@/services/stjApi';

/**
 * Get badge style based on resultado_julgamento value
 */
function getResultadoBadgeStyle(resultado?: string): { bg: string; text: string } {
  if (!resultado) {
    return { bg: 'bg-text-muted/20', text: 'text-text-muted' };
  }

  const lower = resultado.toLowerCase();

  if (lower.includes('provido') && !lower.includes('nao') && !lower.includes('desprovido')) {
    return { bg: 'bg-status-emerald/20', text: 'text-status-emerald' };
  }
  if (lower.includes('desprovido') || lower.includes('nao provido') || lower.includes('improvido')) {
    return { bg: 'bg-status-red/20', text: 'text-status-red' };
  }
  if (lower.includes('parcial')) {
    return { bg: 'bg-status-yellow/20', text: 'text-status-yellow' };
  }

  return { bg: 'bg-accent-indigo/20', text: 'text-accent-indigo' };
}

interface ResultCardProps {
  acordao: AcordaoSummary;
  onClick: () => void;
  isSelected: boolean;
}

export function ResultCard({ acordao, onClick, isSelected }: ResultCardProps) {
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('pt-BR');
  };

  return (
    <div
      onClick={onClick}
      className={`p-4 border rounded-lg cursor-pointer transition-all ${
        isSelected
          ? 'border-accent-violet bg-accent-violet/10'
          : 'border-border-default bg-surface-elevated hover:border-accent-violet/50'
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <span className="text-accent-violet font-mono text-sm">
          {acordao.numero_processo}
        </span>
        <div className="flex items-center gap-2">
          {acordao.resultado_julgamento && (
            <span className={`text-xs px-2 py-0.5 rounded flex items-center gap-1 ${
              getResultadoBadgeStyle(acordao.resultado_julgamento).bg
            } ${getResultadoBadgeStyle(acordao.resultado_julgamento).text}`}>
              <Gavel size={10} />
              {acordao.resultado_julgamento}
            </span>
          )}
          <span className={`text-xs px-2 py-0.5 rounded ${
            acordao.tipo_decisao === 'Acordao'
              ? 'bg-status-emerald/20 text-status-emerald'
              : 'bg-status-yellow/20 text-status-yellow'
          }`}>
            {acordao.tipo_decisao || 'N/A'}
          </span>
        </div>
      </div>

      <p className="text-text-primary text-sm line-clamp-3 mb-3">
        {acordao.ementa || 'Ementa não disponível'}
      </p>

      <div className="flex items-center gap-4 text-text-muted text-xs">
        <span className="flex items-center gap-1">
          <User size={12} />
          {acordao.relator || 'N/A'}
        </span>
        <span className="flex items-center gap-1">
          <Building size={12} />
          {acordao.orgao_julgador || 'N/A'}
        </span>
        <span className="flex items-center gap-1">
          <Calendar size={12} />
          {formatDate(acordao.data_julgamento)}
        </span>
      </div>
    </div>
  );
}
