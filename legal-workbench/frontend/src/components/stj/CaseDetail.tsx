import { useSTJStore } from '@/store/stjStore';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { X, ExternalLink, Calendar, User, Building, Scale, FileText, Gavel } from 'lucide-react';

export function CaseDetail() {
  const { selectedCase, loadingCase, loadCase } = useSTJStore();

  if (loadingCase) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!selectedCase) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-text-muted">
        <Scale size={48} className="mb-4 opacity-50" />
        <p>Selecione um acórdão para ver detalhes</p>
      </div>
    );
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('pt-BR');
  };

  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="flex items-start justify-between mb-4">
        <h2 className="text-lg font-bold text-accent-violet font-mono">
          {selectedCase.numero_processo}
        </h2>
        <button
          onClick={() => loadCase('')}
          className="p-1 hover:bg-surface-elevated rounded"
        >
          <X size={18} />
        </button>
      </div>

      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-text-muted flex items-center gap-1">
              <User size={14} /> Relator
            </span>
            <p className="text-text-primary">{selectedCase.relator || '-'}</p>
          </div>
          <div>
            <span className="text-text-muted flex items-center gap-1">
              <Building size={14} /> Orgao Julgador
            </span>
            <p className="text-text-primary">{selectedCase.orgao_julgador || '-'}</p>
          </div>
          <div>
            <span className="text-text-muted flex items-center gap-1">
              <Calendar size={14} /> Data Julgamento
            </span>
            <p className="text-text-primary">{formatDate(selectedCase.data_julgamento)}</p>
          </div>
          <div>
            <span className="text-text-muted flex items-center gap-1">
              <Calendar size={14} /> Data Publicacao
            </span>
            <p className="text-text-primary">{formatDate(selectedCase.data_publicacao)}</p>
          </div>
          <div>
            <span className="text-text-muted flex items-center gap-1">
              <FileText size={14} /> Classe Processual
            </span>
            <p className="text-text-primary">{selectedCase.classe_processual || '-'}</p>
          </div>
          <div>
            <span className="text-text-muted flex items-center gap-1">
              <Gavel size={14} /> Resultado
            </span>
            <p className="text-text-primary">{selectedCase.resultado_julgamento || '-'}</p>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-text-muted mb-2">Ementa</h3>
          <p className="text-text-primary text-sm bg-bg-panel-1 p-3 rounded-lg whitespace-pre-wrap">
            {selectedCase.ementa || 'Ementa não disponível'}
          </p>
        </div>

        {selectedCase.texto_integral && (
          <div>
            <h3 className="text-sm font-medium text-text-muted mb-2">Texto Integral</h3>
            <p className="text-text-primary text-sm bg-bg-panel-1 p-3 rounded-lg whitespace-pre-wrap max-h-96 overflow-y-auto">
              {selectedCase.texto_integral}
            </p>
          </div>
        )}

        {selectedCase.fonte_url && (
          <a
            href={selectedCase.fonte_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-accent-violet hover:underline text-sm"
          >
            <ExternalLink size={14} />
            Ver no site do STJ
          </a>
        )}
      </div>
    </div>
  );
}
