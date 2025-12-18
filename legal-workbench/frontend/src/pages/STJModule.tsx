import { useEffect } from 'react';
import { useSTJStore } from '@/store/stjStore';
import { SearchForm } from '@/components/stj/SearchForm';
import { ResultsList } from '@/components/stj/ResultsList';
import { CaseDetail } from '@/components/stj/CaseDetail';
import { Scale, Database } from 'lucide-react';

export default function STJModule() {
  const { stats, loadStats } = useSTJStore();

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="h-14 border-b border-border-default bg-bg-panel-1 flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <Scale className="text-accent-violet" size={20} />
          <span className="text-accent-violet font-bold">STJ Dados Abertos</span>
        </div>
        {stats && (
          <div className="flex items-center gap-4 text-text-muted text-xs">
            <span className="flex items-center gap-1">
              <Database size={14} />
              {stats.total_acordaos.toLocaleString()} acórdãos
            </span>
            <span className="text-status-emerald">
              +{stats.ultimos_30_dias} nos últimos 30 dias
            </span>
          </div>
        )}
      </header>

      {/* Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel - Search */}
        <div className="w-1/2 border-r border-border-default flex flex-col">
          <div className="p-4 border-b border-border-default">
            <SearchForm />
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            <ResultsList />
          </div>
        </div>

        {/* Right Panel - Detail */}
        <div className="w-1/2 bg-surface-elevated">
          <CaseDetail />
        </div>
      </div>
    </div>
  );
}
