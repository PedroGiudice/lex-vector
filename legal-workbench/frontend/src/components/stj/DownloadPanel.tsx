import { useState, useCallback, useEffect, useMemo } from 'react';
import {
  Download,
  Calendar,
  Building,
  Play,
  Square,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { useSTJStore } from '@/store/stjStore';
import type { SyncPeriod, SyncParams } from '@/services/stjApi';

/**
 * DownloadPanel Component
 *
 * Provides a UI for triggering bulk retroactive downloads from STJ.
 * Features period selection (preset or custom), optional orgao filtering,
 * progress tracking with real-time status updates, and cancel functionality.
 *
 * @example
 * // Usage in parent component:
 * import { DownloadPanel } from '@/components/stj/DownloadPanel';
 *
 * function STJModule() {
 *   return (
 *     <div>
 *       <DownloadPanel />
 *     </div>
 *   );
 * }
 */

// Period options for radio buttons
const PERIOD_OPTIONS: { value: SyncPeriod; label: string }[] = [
  { value: '30', label: 'Ultimos 30 dias' },
  { value: '90', label: 'Ultimos 90 dias' },
  { value: '365', label: 'Ultimos 365 dias' },
  { value: 'desde_2022', label: 'Desde 2022 (completo)' },
  { value: 'custom', label: 'Periodo personalizado' },
];

interface DownloadPanelProps {
  className?: string;
}

export function DownloadPanel({ className = '' }: DownloadPanelProps) {
  // Local state for form inputs
  const [selectedPeriod, setSelectedPeriod] = useState<SyncPeriod>('30');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [selectedOrgaos, setSelectedOrgaos] = useState<string[]>([]);
  const [showOrgaoFilter, setShowOrgaoFilter] = useState(false);

  // Store state
  const {
    syncStatus,
    isSyncing,
    syncProgress,
    syncError,
    startSync,
    cancelSync,
    resetSyncState,
    stats,
    loadStats,
  } = useSTJStore();

  // Load stats on mount to get available orgaos
  useEffect(() => {
    if (!stats) {
      loadStats();
    }
  }, [stats, loadStats]);

  // Get available orgaos from stats dynamically
  const availableOrgaos = useMemo(() => {
    if (!stats?.por_orgao) {
      return [];
    }
    return Object.entries(stats.por_orgao)
      .sort((a, b) => b[1] - a[1]) // Sort by count descending
      .map(([orgao, count]) => ({
        value: orgao,
        label: `${orgao} (${count})`,
      }));
  }, [stats]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Don't reset if still syncing - let it continue in background
    };
  }, []);

  // Handle orgao checkbox toggle
  const handleOrgaoToggle = useCallback((orgao: string) => {
    setSelectedOrgaos((prev) =>
      prev.includes(orgao)
        ? prev.filter((o) => o !== orgao)
        : [...prev, orgao]
    );
  }, []);

  // Handle form submission
  const handleStartDownload = useCallback(async () => {
    const params: SyncParams = {
      period: selectedPeriod,
    };

    // Add custom dates if selected
    if (selectedPeriod === 'custom') {
      if (!customStartDate || !customEndDate) {
        return; // Validation - don't proceed without dates
      }
      params.dataInicio = customStartDate;
      params.dataFim = customEndDate;
    }

    // Add orgao filter if any selected
    if (selectedOrgaos.length > 0) {
      params.orgaos = selectedOrgaos;
    }

    await startSync(params);
  }, [selectedPeriod, customStartDate, customEndDate, selectedOrgaos, startSync]);

  // Check if form is valid
  const isFormValid = useCallback(() => {
    if (selectedPeriod === 'custom') {
      return customStartDate && customEndDate && customStartDate <= customEndDate;
    }
    return true;
  }, [selectedPeriod, customStartDate, customEndDate]);

  // Get status icon and color
  const getStatusDisplay = useCallback(() => {
    switch (syncStatus) {
      case 'idle':
        return { icon: null, color: 'text-text-muted', label: 'Pronto para iniciar' };
      case 'downloading':
        return { icon: <Loader2 className="animate-spin" size={16} />, color: 'text-accent-indigo', label: 'Baixando dados...' };
      case 'processing':
        return { icon: <RefreshCw className="animate-spin" size={16} />, color: 'text-status-yellow', label: 'Processando...' };
      case 'complete':
        return { icon: <CheckCircle size={16} />, color: 'text-status-emerald', label: 'Concluido!' };
      case 'error':
        return { icon: <XCircle size={16} />, color: 'text-status-red', label: 'Erro' };
      default:
        return { icon: null, color: 'text-text-muted', label: 'Desconhecido' };
    }
  }, [syncStatus]);

  const statusDisplay = getStatusDisplay();

  return (
    <div
      className={`bg-bg-panel-1 border border-border-default rounded-lg p-4 ${className}`}
      role="region"
      aria-label="Download Massivo"
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Download className="text-accent-indigo" size={20} />
        <h3 className="text-text-primary font-semibold">Download Massivo</h3>
      </div>

      {/* Period Selection */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <Calendar className="text-text-muted" size={14} />
          <span className="text-text-secondary text-sm font-medium">Periodo</span>
        </div>

        <div className="space-y-2" role="radiogroup" aria-label="Selecionar periodo">
          {PERIOD_OPTIONS.map((option) => (
            <label
              key={option.value}
              className="flex items-center gap-2 cursor-pointer group"
            >
              <input
                type="radio"
                name="period"
                value={option.value}
                checked={selectedPeriod === option.value}
                onChange={(e) => setSelectedPeriod(e.target.value as SyncPeriod)}
                disabled={isSyncing}
                className="w-4 h-4 text-accent-indigo bg-bg-input border-border-default focus:ring-accent-indigo focus:ring-offset-bg-main"
                aria-describedby={option.value === 'custom' ? 'custom-dates-hint' : undefined}
              />
              <span className="text-text-primary text-sm group-hover:text-accent-indigo-light transition-colors">
                {option.label}
              </span>
            </label>
          ))}
        </div>

        {/* Custom Date Pickers */}
        {selectedPeriod === 'custom' && (
          <div className="mt-3 ml-6 flex gap-3" id="custom-dates-hint">
            <div className="flex-1">
              <label htmlFor="start-date" className="text-text-muted text-xs block mb-1">
                Data inicio
              </label>
              <input
                id="start-date"
                type="date"
                value={customStartDate}
                onChange={(e) => setCustomStartDate(e.target.value)}
                disabled={isSyncing}
                max={customEndDate || undefined}
                className="w-full bg-bg-input border border-border-default rounded px-2 py-1.5 text-text-primary text-sm focus:outline-none focus:ring-1 focus:ring-accent-indigo disabled:opacity-50"
              />
            </div>
            <div className="flex-1">
              <label htmlFor="end-date" className="text-text-muted text-xs block mb-1">
                Data fim
              </label>
              <input
                id="end-date"
                type="date"
                value={customEndDate}
                onChange={(e) => setCustomEndDate(e.target.value)}
                disabled={isSyncing}
                min={customStartDate || undefined}
                max={new Date().toISOString().split('T')[0]}
                className="w-full bg-bg-input border border-border-default rounded px-2 py-1.5 text-text-primary text-sm focus:outline-none focus:ring-1 focus:ring-accent-indigo disabled:opacity-50"
              />
            </div>
          </div>
        )}
      </div>

      {/* Orgao Filter (Collapsible) */}
      <div className="mb-4">
        <button
          type="button"
          onClick={() => setShowOrgaoFilter(!showOrgaoFilter)}
          disabled={isSyncing}
          className="flex items-center gap-2 text-text-secondary text-sm hover:text-text-primary transition-colors disabled:opacity-50"
          aria-expanded={showOrgaoFilter}
          aria-controls="orgao-filter-section"
        >
          <Building size={14} />
          <span>Filtrar por orgao (opcional)</span>
          <span className="text-text-muted">
            {selectedOrgaos.length > 0 && `(${selectedOrgaos.length} selecionados)`}
          </span>
        </button>

        {showOrgaoFilter && (
          <div
            id="orgao-filter-section"
            className="mt-2 ml-6 grid grid-cols-2 gap-2"
            role="group"
            aria-label="Selecionar orgaos"
          >
            {availableOrgaos.map((orgao) => (
              <label
                key={orgao.value}
                className="flex items-center gap-2 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selectedOrgaos.includes(orgao.value)}
                  onChange={() => handleOrgaoToggle(orgao.value)}
                  disabled={isSyncing}
                  className="w-3.5 h-3.5 text-accent-indigo bg-bg-input border-border-default rounded focus:ring-accent-indigo"
                />
                <span className="text-text-secondary text-xs">{orgao.label}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 mb-4">
        {!isSyncing ? (
          <button
            type="button"
            onClick={handleStartDownload}
            disabled={!isFormValid()}
            className="flex items-center gap-2 px-4 py-2 bg-accent-indigo text-white rounded-lg font-medium hover:bg-accent-indigo-light transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-describedby="download-status"
          >
            <Play size={16} />
            Iniciar Download
          </button>
        ) : (
          <button
            type="button"
            onClick={cancelSync}
            className="flex items-center gap-2 px-4 py-2 bg-status-red text-white rounded-lg font-medium hover:bg-status-red/80 transition-colors"
          >
            <Square size={16} />
            Cancelar
          </button>
        )}

        {syncStatus === 'complete' || syncStatus === 'error' ? (
          <button
            type="button"
            onClick={resetSyncState}
            className="flex items-center gap-2 px-4 py-2 bg-bg-panel-2 text-text-primary rounded-lg hover:bg-border-default transition-colors"
          >
            <RefreshCw size={16} />
            Nova Sincronizacao
          </button>
        ) : null}
      </div>

      {/* Progress Section */}
      <div
        id="download-status"
        className="border-t border-border-default pt-4"
        role="status"
        aria-live="polite"
      >
        {/* Status Label */}
        <div className={`flex items-center gap-2 mb-3 ${statusDisplay.color}`}>
          {statusDisplay.icon}
          <span className="text-sm font-medium">{statusDisplay.label}</span>
          {syncProgress.message && (
            <span className="text-text-muted text-xs ml-2">
              {syncProgress.message}
            </span>
          )}
        </div>

        {/* Progress Bar */}
        {isSyncing && syncProgress.percent !== undefined && (
          <div className="mb-3">
            <div className="h-2 bg-bg-panel-2 rounded-full overflow-hidden">
              <div
                className="h-full bg-accent-indigo transition-all duration-300 ease-out"
                style={{ width: `${Math.min(syncProgress.percent, 100)}%` }}
                role="progressbar"
                aria-valuenow={syncProgress.percent}
                aria-valuemin={0}
                aria-valuemax={100}
              />
            </div>
            <div className="flex justify-between text-text-muted text-xs mt-1">
              <span>{syncProgress.percent.toFixed(1)}%</span>
              {syncProgress.currentPage !== undefined && syncProgress.totalPages !== undefined && (
                <span>
                  Pagina {syncProgress.currentPage} de {syncProgress.totalPages}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Stats Grid */}
        {(isSyncing || syncStatus === 'complete' || syncStatus === 'error') && (
          <div className="grid grid-cols-5 gap-2">
            <StatItem
              label="Baixados"
              value={syncProgress.downloaded}
              color="text-accent-indigo"
            />
            <StatItem
              label="Processados"
              value={syncProgress.processed}
              color="text-status-yellow"
            />
            <StatItem
              label="Inseridos"
              value={syncProgress.inserted}
              color="text-status-emerald"
            />
            <StatItem
              label="Duplicados"
              value={syncProgress.duplicates}
              color="text-text-muted"
            />
            <StatItem
              label="Erros"
              value={syncProgress.errors}
              color={syncProgress.errors > 0 ? 'text-status-red' : 'text-text-muted'}
            />
          </div>
        )}

        {/* Error Message */}
        {syncError && (
          <div className="mt-3 flex items-start gap-2 p-3 bg-status-red/10 border border-status-red/30 rounded-lg">
            <AlertCircle className="text-status-red flex-shrink-0 mt-0.5" size={16} />
            <p className="text-status-red text-sm">{syncError}</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Helper component for stats display
interface StatItemProps {
  label: string;
  value: number;
  color: string;
}

function StatItem({ label, value, color }: StatItemProps) {
  return (
    <div className="text-center">
      <div className={`text-lg font-mono font-semibold ${color}`}>
        {value.toLocaleString()}
      </div>
      <div className="text-text-muted text-xxs uppercase tracking-wide">
        {label}
      </div>
    </div>
  );
}

export default DownloadPanel;
