import { useSTJStore } from '@/store/stjStore';
import { ResultCard } from './ResultCard';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export function ResultsList() {
  const {
    results, total, loading, error,
    page, pageSize, setPage,
    selectedCase, loadCase
  } = useSTJStore();

  const totalPages = Math.ceil(total / pageSize);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-status-red p-8">
        {error}
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="text-center text-text-muted p-8">
        Nenhum resultado encontrado. Digite um termo de busca acima.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="text-sm text-text-muted">
        {total} resultado{total !== 1 ? 's' : ''} encontrado{total !== 1 ? 's' : ''}
      </div>

      <div className="space-y-3">
        {results.map((acordao) => (
          <ResultCard
            key={acordao.id}
            acordao={acordao}
            onClick={() => loadCase(acordao.id)}
            isSelected={selectedCase?.id === acordao.id}
          />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 pt-4">
          <button
            onClick={() => setPage(page - 1)}
            disabled={page === 0}
            className="p-2 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface-elevated"
          >
            <ChevronLeft size={20} />
          </button>
          <span className="text-sm text-text-muted">
            Página {page + 1} de {totalPages}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={page >= totalPages - 1}
            className="p-2 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface-elevated"
          >
            <ChevronRight size={20} />
          </button>
        </div>
      )}
    </div>
  );
}
