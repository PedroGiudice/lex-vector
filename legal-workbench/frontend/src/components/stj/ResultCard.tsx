import { Calendar, User, Building } from 'lucide-react';
import type { AcordaoSummary } from '@/services/stjApi';

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
        <span className={`text-xs px-2 py-0.5 rounded ${
          acordao.tipo_decisao === 'Acórdão'
            ? 'bg-status-emerald/20 text-status-emerald'
            : 'bg-status-yellow/20 text-status-yellow'
        }`}>
          {acordao.tipo_decisao || 'N/A'}
        </span>
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
