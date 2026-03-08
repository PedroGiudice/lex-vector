interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = 14,
  className = '',
}) => {
  return (
    <div
      className={className}
      style={{
        width,
        height,
        borderRadius: 'var(--radius-sm)',
        background: `linear-gradient(
          90deg,
          var(--color-bg-card) 25%,
          var(--color-bg-card-hover) 50%,
          var(--color-bg-card) 75%
        )`,
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.5s ease-in-out infinite',
      }}
    />
  );
};

export default Skeleton;
