import type { Outcome } from '@/types';

interface OutcomeBadgeProps {
  outcome: Outcome;
}

const outcomeConfig = {
  provido: {
    label: 'PROVIDO',
    className: 'badge-success',
  },
  desprovido: {
    label: 'DESPROVIDO',
    className: 'badge-danger',
  },
  parcial: {
    label: 'PARCIAL',
    className: 'badge-warning',
  },
} as const;

export function OutcomeBadge({ outcome }: OutcomeBadgeProps) {
  const config = outcomeConfig[outcome];

  return <span className={config.className}>{config.label}</span>;
}
