import { useState, useMemo } from 'react';
import type { LegalDomain, TriggerWord, QueryParams } from '@/types';
import {
  LEGAL_DOMAINS,
  TRIGGER_WORDS,
  QUERY_TEMPLATES,
} from '@/utils/mockData';
import {
  useJurisprudenceQuery,
  useSQLPreview,
} from '@/hooks/useJurisprudenceQuery';
import { SQLPreviewPanel } from './SQLPreviewPanel';
import { JurisprudenceResultCard } from './JurisprudenceResultCard';

export function STJQueryBuilder() {
  const [domain, setDomain] = useState<LegalDomain | null>(null);
  const [selectedTriggerWords, setSelectedTriggerWords] = useState<
    TriggerWord[]
  >([]);
  const [onlyAcordaos, setOnlyAcordaos] = useState(false);

  const queryParams: QueryParams = useMemo(
    () => ({
      domain,
      triggerWords: selectedTriggerWords,
      onlyAcordaos,
    }),
    [domain, selectedTriggerWords, onlyAcordaos]
  );

  const sqlPreview = useSQLPreview(queryParams);
  const { data: results, isLoading, error } = useJurisprudenceQuery(queryParams);

  const handleTriggerWordToggle = (word: TriggerWord) => {
    setSelectedTriggerWords((prev) =>
      prev.includes(word)
        ? prev.filter((w) => w !== word)
        : [...prev, word]
    );
  };

  const applyTemplate = (templateId: string) => {
    const template = QUERY_TEMPLATES.find((t) => t.id === templateId);
    if (!template) return;

    if (template.domain) setDomain(template.domain);
    if (template.triggerWords) setSelectedTriggerWords(template.triggerWords);
    setOnlyAcordaos(template.onlyAcordaos);
  };

  const clearFilters = () => {
    setDomain(null);
    setSelectedTriggerWords([]);
    setOnlyAcordaos(false);
  };

  return (
    <div className="min-h-screen bg-terminal-bg p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <header className="border-b border-terminal-border pb-6">
          <h1 className="text-3xl font-bold text-terminal-accent font-mono mb-2">
            [STJ JURISPRUDENCE LAB]
          </h1>
          <p className="text-terminal-muted">
            Query Builder com Preview SQL em Tempo Real
          </p>
        </header>

        {/* Template Quick Buttons */}
        <div className="card-terminal">
          <h2 className="text-sm font-semibold text-terminal-text mb-3 font-mono">
            [TEMPLATES RÁPIDOS]
          </h2>
          <div className="flex flex-wrap gap-2">
            {QUERY_TEMPLATES.map((template) => (
              <button
                key={template.id}
                onClick={() => applyTemplate(template.id)}
                className="btn-terminal"
                title={template.description}
              >
                {template.name}
              </button>
            ))}
            <button
              onClick={clearFilters}
              className="px-4 py-2 bg-terminal-danger/10 border border-terminal-danger/30
                         text-terminal-danger font-mono text-sm rounded
                         hover:bg-terminal-danger/20 hover:border-terminal-danger/50
                         transition-all duration-200"
            >
              Limpar Filtros
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Legal Domain */}
          <div className="card-terminal">
            <label className="block text-sm font-semibold text-terminal-text mb-3 font-mono">
              [DOMÍNIO JURÍDICO]
            </label>
            <select
              className="select-terminal"
              value={domain || ''}
              onChange={(e) =>
                setDomain(e.target.value ? (e.target.value as LegalDomain) : null)
              }
            >
              <option value="">Todos os domínios</option>
              {LEGAL_DOMAINS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          {/* Somente Acórdãos Toggle */}
          <div className="card-terminal">
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-sm font-semibold text-terminal-text font-mono">
                [TIPO DE DOCUMENTO]
              </span>
              <div className="flex items-center gap-3">
                {onlyAcordaos && (
                  <span className="badge-warning text-xs">
                    FILTRO ATIVO
                  </span>
                )}
                <div className="relative">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={onlyAcordaos}
                    onChange={(e) => setOnlyAcordaos(e.target.checked)}
                  />
                  <div
                    className="w-14 h-7 bg-terminal-border rounded-full peer
                               peer-checked:bg-terminal-accent/30
                               peer-focus:ring-2 peer-focus:ring-terminal-accent/50
                               transition-all duration-200"
                  ></div>
                  <div
                    className="absolute left-1 top-1 w-5 h-5 bg-terminal-muted rounded-full
                               peer-checked:translate-x-7 peer-checked:bg-terminal-accent
                               transition-all duration-200"
                  ></div>
                </div>
              </div>
            </label>
            <p className="text-xs text-terminal-muted mt-2">
              {onlyAcordaos
                ? 'Exibindo apenas acórdãos'
                : 'Todos os tipos de documentos'}
            </p>
          </div>
        </div>

        {/* Trigger Words */}
        <div className="card-terminal">
          <h2 className="text-sm font-semibold text-terminal-text mb-3 font-mono">
            [PALAVRAS-GATILHO]
            {selectedTriggerWords.length > 0 && (
              <span className="ml-2 text-terminal-accent">
                ({selectedTriggerWords.length} selecionadas)
              </span>
            )}
          </h2>
          <div className="flex flex-wrap gap-2">
            {TRIGGER_WORDS.map((word) => {
              const isSelected = selectedTriggerWords.includes(word);
              return (
                <button
                  key={word}
                  onClick={() => handleTriggerWordToggle(word)}
                  className={`px-3 py-1.5 rounded border font-mono text-sm transition-all
                    ${
                      isSelected
                        ? 'bg-terminal-accent/20 border-terminal-accent text-terminal-accent'
                        : 'bg-terminal-bg border-terminal-border text-terminal-muted hover:border-terminal-accent/50'
                    }`}
                >
                  {word}
                </button>
              );
            })}
          </div>
        </div>

        {/* SQL Preview */}
        <SQLPreviewPanel preview={sqlPreview} />

        {/* Results Section */}
        <div className="card-terminal">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-terminal-accent font-mono">
              [RESULTADOS]
            </h2>
            {results && (
              <span className="badge-info">{results.length} encontrados</span>
            )}
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-terminal-accent border-t-transparent rounded-full animate-spin mb-4"></div>
              <p className="text-terminal-muted font-mono text-sm">
                Processando query...
              </p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="bg-terminal-danger/10 border border-terminal-danger/30 rounded p-4">
              <p className="text-terminal-danger font-mono text-sm">
                Erro ao executar query: {(error as Error).message}
              </p>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !error && (!results || results.length === 0) && (
            <div className="text-center py-12">
              <svg
                className="w-16 h-16 mx-auto mb-4 text-terminal-muted opacity-50"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p className="text-terminal-muted font-mono">
                {domain || selectedTriggerWords.length > 0
                  ? 'Nenhum resultado encontrado para os filtros aplicados'
                  : 'Selecione filtros para executar a busca'}
              </p>
            </div>
          )}

          {/* Results List */}
          {results && results.length > 0 && (
            <div className="space-y-4">
              {results.map((result) => (
                <JurisprudenceResultCard key={result.id} result={result} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
