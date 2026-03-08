interface ScoreBarProps {
  /** Score value (0 to maxScore) */
  score: number;
  /** Maximum score in the result set, for normalization */
  maxScore: number;
  width?: number;
}

function scoreColor(normalized: number): string {
  if (normalized >= 0.8) return 'var(--color-score-high)';
  if (normalized >= 0.5) return 'var(--color-score-mid)';
  return 'var(--color-text-muted)';
}

export const ScoreBar: React.FC<ScoreBarProps> = ({ score, maxScore, width = 60 }) => {
  const normalized = maxScore > 0 ? score / maxScore : 0;

  return (
    <div className="flex items-center gap-2">
      <span
        className="font-mono"
        style={{
          fontSize: 11,
          fontWeight: 500,
          color: scoreColor(normalized),
          minWidth: 38,
        }}
      >
        {score.toFixed(4)}
      </span>
      <div
        style={{
          width,
          height: 2,
          borderRadius: 1,
          backgroundColor: 'var(--color-border-subtle)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${normalized * 100}%`,
            height: '100%',
            borderRadius: 1,
            backgroundColor: scoreColor(normalized),
            animation: 'score-fill 0.4s ease-out',
          }}
        />
      </div>
    </div>
  );
};

export default ScoreBar;
