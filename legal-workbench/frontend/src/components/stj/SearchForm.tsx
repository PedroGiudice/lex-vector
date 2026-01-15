import { useEffect } from 'react';
import { Search } from 'lucide-react';
import { useSTJStore } from '@/store/stjStore';

export function SearchForm() {
  const { searchTerm, setSearchTerm, search, loading, filters, setFilters, stats, loadStats } = useSTJStore();

  // Load stats on mount to populate orgao dropdown
  useEffect(() => {
    if (!stats) {
      loadStats();
    }
  }, [stats, loadStats]);

  // Get list of orgaos from stats
  const orgaoOptions = stats?.por_orgao ? Object.keys(stats.por_orgao).sort() : [];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    search();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="relative">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Buscar jurisprudência (min 3 caracteres)..."
          className="w-full bg-bg-input border border-border-default rounded-lg px-4 py-3 pl-10 text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-violet"
        />
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={18} />
      </div>

      <div className="flex gap-4">
        <select
          value={filters.dias}
          onChange={(e) => setFilters({ dias: Number(e.target.value) })}
          className="bg-bg-input border border-border-default rounded px-3 py-2 text-sm text-text-primary"
        >
          <option value={30}>Últimos 30 dias</option>
          <option value={90}>Últimos 90 dias</option>
          <option value={180}>Últimos 6 meses</option>
          <option value={365}>Último ano</option>
        </select>

        <select
          value={filters.campo}
          onChange={(e) => setFilters({ campo: e.target.value as 'ementa' | 'texto_integral' })}
          className="bg-bg-input border border-border-default rounded px-3 py-2 text-sm text-text-primary"
        >
          <option value="ementa">Buscar na ementa</option>
          <option value="texto_integral">Buscar no texto integral</option>
        </select>

        <select
          value={filters.orgao}
          onChange={(e) => setFilters({ orgao: e.target.value })}
          className="bg-bg-input border border-border-default rounded px-3 py-2 text-sm text-text-primary"
          aria-label="Filtrar por orgao julgador"
        >
          <option value="">Todos os orgaos</option>
          {orgaoOptions.map((orgao) => (
            <option key={orgao} value={orgao}>
              {orgao}
            </option>
          ))}
        </select>

        <button
          type="submit"
          disabled={loading || searchTerm.length < 3}
          className="px-6 py-2 bg-accent-violet text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent-violet/90 transition-colors"
        >
          {loading ? 'Buscando...' : 'Buscar'}
        </button>
      </div>
    </form>
  );
}
