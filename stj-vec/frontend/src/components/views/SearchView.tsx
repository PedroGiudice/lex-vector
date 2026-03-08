import { useCallback, useRef, useEffect, useMemo } from 'react';
import { useAppStore } from '@/store/app-store.ts';
import { useSearch } from '@/hooks/use-search.ts';
import { useDocument } from '@/hooks/use-document.ts';
import { FilterPanel } from '@/components/layout/FilterPanel.tsx';
import { MatchingLog } from '@/components/indicators/MatchingLog.tsx';
import { ScoreBar } from '@/components/indicators/ScoreBar.tsx';
import { Skeleton } from '@/components/indicators/Skeleton.tsx';
import { ApertureSpinner } from '@/components/indicators/ApertureSpinner.tsx';
import type { SearchResultItem } from '@/api/types.ts';

/* ========================================
   Helpers
   ======================================== */

function formatDate(dateStr: string): string {
  if (!dateStr) return '-';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('pt-BR');
  } catch {
    return dateStr;
  }
}

function tipoBadgeColor(tipo: string): React.CSSProperties {
  const t = tipo?.toLowerCase() ?? '';
  if (t.includes('acordao')) return { background: 'rgba(91,141,239,0.15)', color: '#7aa3f5' };
  if (t.includes('decisao')) return { background: 'rgba(74,222,128,0.12)', color: '#4ade80' };
  if (t.includes('despacho')) return { background: 'rgba(250,204,21,0.12)', color: '#facc15' };
  return { background: 'var(--color-accent-soft)', color: 'var(--color-text-secondary)' };
}

/* ========================================
   Result Card
   ======================================== */

interface ResultCardProps {
  result: SearchResultItem;
  isSelected: boolean;
  maxRrf: number;
  onClick: () => void;
}

const ResultCard: React.FC<ResultCardProps> = ({ result, isSelected, maxRrf, onClick }) => {
  const badge = tipoBadgeColor(result.tipo);

  return (
    <div
      onClick={onClick}
      className="mx-2 my-1 px-3 py-3 cursor-pointer"
      style={{
        borderRadius: 'var(--radius-md)',
        background: isSelected ? 'rgba(91,141,239,0.08)' : 'transparent',
        border: isSelected
          ? '1px solid rgba(91,141,239,0.3)'
          : '1px solid transparent',
        transition: 'all 0.15s ease',
      }}
      onMouseEnter={(e) => {
        if (!isSelected) e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
      }}
      onMouseLeave={(e) => {
        if (!isSelected) e.currentTarget.style.background = 'transparent';
      }}
    >
      {/* Header: processo + score */}
      <div className="flex items-center justify-between mb-1">
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
          {result.processo || 'Sem numero'}
        </span>
        <ScoreBar score={result.scores.rrf} maxScore={maxRrf} width={50} />
      </div>

      {/* Meta line */}
      <div className="flex items-center gap-2 mb-1.5 flex-wrap" style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
        <span>{result.ministro}</span>
        <span style={{ color: 'var(--color-border-card)' }}>|</span>
        <span>{result.orgao_julgador}</span>
        <span style={{ color: 'var(--color-border-card)' }}>|</span>
        <span>{formatDate(result.data_julgamento)}</span>
        <span
          style={{
            ...badge,
            fontSize: 9,
            fontWeight: 600,
            padding: '1px 6px',
            borderRadius: 3,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}
        >
          {result.tipo}
        </span>
      </div>

      {/* Content preview */}
      <div
        style={{
          fontSize: 12,
          color: 'var(--color-text-secondary)',
          lineHeight: 1.55,
          display: '-webkit-box',
          WebkitLineClamp: 3,
          WebkitBoxOrient: 'vertical' as const,
          overflow: 'hidden',
        }}
      >
        {result.content}
      </div>

      {/* Scores */}
      <div className="mt-1.5">
        <MatchingLog scores={result.scores} />
      </div>
    </div>
  );
};

/* ========================================
   Document Preview
   ======================================== */

interface DocumentPreviewProps {
  docId: string;
  matchedChunkId: string;
}

const DocumentPreview: React.FC<DocumentPreviewProps> = ({ docId, matchedChunkId }) => {
  const { data, isLoading } = useDocument(docId);
  const matchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (matchRef.current) {
      matchRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [data, matchedChunkId]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-4">
        <ApertureSpinner size={40} />
        <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>Carregando documento...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center py-12">
        <span style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>Documento nao encontrado</span>
      </div>
    );
  }

  const { document: doc, chunks } = data;

  return (
    <>
      {/* Document Header */}
      <div
        className="px-5 py-3"
        style={{
          borderBottom: '1px solid var(--color-border-subtle)',
          background: 'var(--color-bg-surface)',
        }}
      >
        <div className="flex items-center gap-3 mb-1">
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            {doc.processo}
          </span>
          <span
            style={{
              ...tipoBadgeColor(doc.tipo),
              fontSize: 9,
              fontWeight: 600,
              padding: '1px 6px',
              borderRadius: 3,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            {doc.tipo}
          </span>
        </div>
        <div className="flex items-center gap-3 flex-wrap" style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
          <span>{doc.classe}</span>
          <span style={{ color: 'var(--color-border-card)' }}>|</span>
          <span>{doc.ministro}</span>
          <span style={{ color: 'var(--color-border-card)' }}>|</span>
          <span>{doc.orgao_julgador}</span>
          <span style={{ color: 'var(--color-border-card)' }}>|</span>
          <span>Julgamento: {formatDate(doc.data_julgamento)}</span>
          <span style={{ color: 'var(--color-border-card)' }}>|</span>
          <span>Publicacao: {formatDate(doc.data_publicacao)}</span>
        </div>
        {doc.assuntos && (
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 4 }}>
            {doc.assuntos}
          </div>
        )}
        <div className="font-mono" style={{ fontSize: 10, color: 'var(--color-text-muted)', marginTop: 4 }}>
          {data.total_chunks} chunks
        </div>
      </div>

      {/* Chunks */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        <div className="flex flex-col gap-3">
          {chunks.map((chunk) => {
            const isMatch = chunk.id === matchedChunkId;
            return (
              <div
                key={chunk.id}
                ref={isMatch ? matchRef : undefined}
                className="px-3.5 py-3"
                style={{
                  fontSize: 13,
                  color: 'var(--color-text-primary)',
                  lineHeight: 1.65,
                  background: isMatch
                    ? 'rgba(91,141,239,0.08)'
                    : 'transparent',
                  borderRadius: 'var(--radius-md)',
                  border: isMatch
                    ? '1px solid rgba(91,141,239,0.25)'
                    : '1px solid transparent',
                  whiteSpace: 'pre-wrap' as const,
                  transition: 'all 0.2s ease',
                }}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <span
                    className="font-mono"
                    style={{
                      fontSize: 9,
                      fontWeight: 600,
                      color: isMatch ? 'var(--color-accent)' : 'var(--color-text-muted)',
                      letterSpacing: '0.04em',
                    }}
                  >
                    CHUNK {chunk.chunk_index}
                  </span>
                  {isMatch && (
                    <span
                      style={{
                        fontSize: 9,
                        fontWeight: 600,
                        color: 'var(--color-accent)',
                        background: 'var(--color-accent-soft)',
                        padding: '1px 6px',
                        borderRadius: 3,
                        letterSpacing: '0.04em',
                      }}
                    >
                      MATCH
                    </span>
                  )}
                  <span className="font-mono" style={{ fontSize: 9, color: 'var(--color-text-muted)' }}>
                    {chunk.token_count} tokens
                  </span>
                </div>
                {chunk.content}
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
};

/* ========================================
   Query Info Footer
   ======================================== */

interface QueryInfoFooterProps {
  embeddingMs: number;
  searchMs: number;
  metadataMs: number;
  totalMs: number;
  denseCandidates: number;
  sparseCandidates: number;
  resultCount: number;
}

const QueryInfoFooter: React.FC<QueryInfoFooterProps> = ({
  embeddingMs,
  searchMs,
  metadataMs,
  totalMs,
  denseCandidates,
  sparseCandidates,
  resultCount,
}) => (
  <div
    className="font-mono flex items-center gap-4 flex-wrap"
    style={{
      padding: '6px 16px',
      borderTop: '1px solid var(--color-border-subtle)',
      background: 'var(--color-bg-surface)',
      fontSize: 10,
      color: 'var(--color-text-muted)',
    }}
  >
    <span>embed: {embeddingMs}ms</span>
    <span>search: {searchMs}ms</span>
    <span>meta: {metadataMs}ms</span>
    <span style={{ color: 'var(--color-accent)', fontWeight: 600 }}>total: {totalMs}ms</span>
    <span style={{ color: 'var(--color-border-card)' }}>|</span>
    <span>dense: {denseCandidates}</span>
    <span>sparse: {sparseCandidates}</span>
    <span>results: {resultCount}</span>
  </div>
);

/* ========================================
   SearchView (main)
   ======================================== */

const LIMIT_OPTIONS = [10, 20, 50, 100];

const SearchView: React.FC = () => {
  const query = useAppStore((s) => s.query);
  const submittedQuery = useAppStore((s) => s.submittedQuery);
  const filters = useAppStore((s) => s.filters);
  const selectedChunkId = useAppStore((s) => s.selectedChunkId);
  const selectedDocId = useAppStore((s) => s.selectedDocId);
  const limit = useAppStore((s) => s.limit);
  const setQuery = useAppStore((s) => s.setQuery);
  const submitQuery = useAppStore((s) => s.submitQuery);
  const selectResult = useAppStore((s) => s.selectResult);
  const setLimit = useAppStore((s) => s.setLimit);

  const { data: searchData, isLoading: searching, isFetching } = useSearch(submittedQuery, filters, limit);

  const results = searchData?.results ?? [];
  const queryInfo = searchData?.query_info;

  const maxRrf = useMemo(() => {
    if (results.length === 0) return 0;
    return Math.max(...results.map((r) => r.scores.rrf));
  }, [results]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    submitQuery();
  }, [submitQuery]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitQuery();
    }
  }, [submitQuery]);

  return (
    <div className="flex flex-col h-screen view-enter">
      {/* Search Input */}
      <form
        onSubmit={handleSubmit}
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--color-border-subtle)',
          background: 'var(--color-bg-surface)',
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="flex items-center gap-3 px-4 py-3 flex-1"
            style={{
              background: 'var(--color-bg-input)',
              border: '1px solid var(--color-border-card)',
              borderRadius: 'var(--radius-md)',
              transition: 'border-color 0.2s, box-shadow 0.2s',
              boxShadow: submittedQuery
                ? '0 0 0 1px rgba(91,141,239,0.15), inset 0 1px 3px rgba(0,0,0,0.2)'
                : 'inset 0 1px 3px rgba(0,0,0,0.2)',
            }}
          >
            {isFetching ? (
              <ApertureSpinner size={20} />
            ) : (
              <span style={{
                width: 16, height: 16,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <span style={{
                  width: 7, height: 7, borderRadius: 2,
                  background: submittedQuery ? 'var(--color-accent)' : 'var(--color-text-muted)',
                  transition: 'background 0.2s',
                  boxShadow: submittedQuery ? '0 0 6px rgba(91,141,239,0.4)' : 'none',
                }} />
              </span>
            )}
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Buscar jurisprudencia do STJ..."
              style={{
                flex: 1,
                background: 'transparent',
                border: 'none',
                outline: 'none',
                fontSize: 15,
                color: 'var(--color-text-primary)',
                fontFamily: 'inherit',
                letterSpacing: '0.01em',
              }}
            />
            {submittedQuery && (
              <span className="font-mono" style={{
                fontSize: 11,
                color: 'var(--color-accent)',
                background: 'var(--color-accent-soft)',
                padding: '2px 8px',
                borderRadius: 3,
                fontWeight: 600,
              }}>
                {results.length}
              </span>
            )}
          </div>

          {/* Limit selector */}
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            style={{
              background: 'var(--color-bg-input)',
              border: '1px solid var(--color-border-card)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--color-text-secondary)',
              fontSize: 12,
              padding: '6px 8px',
              outline: 'none',
              fontFamily: 'inherit',
            }}
          >
            {LIMIT_OPTIONS.map((n) => (
              <option key={n} value={n}>{n} resultados</option>
            ))}
          </select>
        </div>
      </form>

      {/* Filter Panel */}
      <FilterPanel />

      {/* Main content area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Results List */}
        <div
          className="flex flex-col shrink-0 overflow-hidden"
          style={{
            width: 420,
            borderRight: '1px solid var(--color-border-subtle)',
          }}
        >
          <div className="flex-1 overflow-y-auto py-1">
            {searching ? (
              <div className="p-4 flex flex-col gap-3">
                <Skeleton height={80} />
                <Skeleton height={80} />
                <Skeleton height={80} />
                <Skeleton height={80} />
              </div>
            ) : results.length > 0 ? (
              results.map((result) => (
                <ResultCard
                  key={result.chunk_id}
                  result={result}
                  isSelected={result.chunk_id === selectedChunkId}
                  maxRrf={maxRrf}
                  onClick={() => selectResult(result.chunk_id, result.doc_id)}
                />
              ))
            ) : submittedQuery ? (
              <div className="flex flex-col items-center justify-center h-48 gap-4">
                <span style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>
                  Nenhum resultado para "{submittedQuery}"
                </span>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-48 gap-4">
                <ApertureSpinner size={48} />
                <div style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: 13, color: 'var(--color-text-secondary)', display: 'block' }}>
                    Busca vetorial hibrida
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 4, display: 'block' }}>
                    Dense + Sparse + RRF
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2, display: 'block' }}>
                    Digite e pressione Enter
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right: Document Preview */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {selectedDocId && selectedChunkId ? (
            <DocumentPreview docId={selectedDocId} matchedChunkId={selectedChunkId} />
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center gap-5" style={{ opacity: 0.6 }}>
              <ApertureSpinner size={64} />
              <span style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>
                Selecione um resultado para ver o documento
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Footer: Query Info */}
      {queryInfo && (
        <QueryInfoFooter
          embeddingMs={queryInfo.embedding_ms}
          searchMs={queryInfo.search_ms}
          metadataMs={queryInfo.metadata_ms}
          totalMs={queryInfo.total_ms}
          denseCandidates={queryInfo.dense_candidates}
          sparseCandidates={queryInfo.sparse_candidates}
          resultCount={results.length}
        />
      )}
    </div>
  );
};

export default SearchView;
