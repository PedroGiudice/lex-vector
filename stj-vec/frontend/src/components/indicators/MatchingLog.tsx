import type { Scores } from '@/api/types.ts';

interface MatchingLogProps {
  scores: Scores;
}

function rankColor(rank: number): string {
  if (rank === 0) return 'var(--color-text-muted)';
  if (rank <= 5) return 'var(--color-score-high)';
  if (rank <= 20) return 'var(--color-score-mid)';
  return 'var(--color-text-muted)';
}

function formatRank(rank: number): string {
  return rank > 0 ? `#${rank}` : '-';
}

export const MatchingLog: React.FC<MatchingLogProps> = ({ scores }) => {
  return (
    <div
      className="font-mono flex items-center gap-1 flex-wrap"
      style={{ fontSize: 10, lineHeight: 1.4 }}
    >
      <span style={{ color: 'var(--color-text-muted)' }}>D:</span>
      <span style={{ color: rankColor(scores.dense_rank), fontWeight: 500 }}>
        {scores.dense.toFixed(3)}
      </span>
      <span style={{ color: rankColor(scores.dense_rank), fontSize: 9 }}>
        {formatRank(scores.dense_rank)}
      </span>

      <span style={{ color: 'var(--color-border-card)', margin: '0 2px' }}>|</span>

      <span style={{ color: 'var(--color-text-muted)' }}>S:</span>
      <span style={{ color: rankColor(scores.sparse_rank), fontWeight: 500 }}>
        {scores.sparse.toFixed(2)}
      </span>
      <span style={{ color: rankColor(scores.sparse_rank), fontSize: 9 }}>
        {formatRank(scores.sparse_rank)}
      </span>

      <span style={{ color: 'var(--color-border-card)', margin: '0 2px' }}>|</span>

      <span style={{ color: 'var(--color-text-muted)' }}>RRF:</span>
      <span style={{ color: 'var(--color-accent)', fontWeight: 600 }}>
        {scores.rrf.toFixed(4)}
      </span>
    </div>
  );
};

export default MatchingLog;
