import React, { useState, useCallback, ReactNode } from 'react';
import { ChevronDown, ChevronRight, LucideIcon } from 'lucide-react';
import clsx from 'clsx';

interface CollapsibleSectionProps {
  title: string;
  icon?: LucideIcon;
  badge?: string | number;
  children: ReactNode;
  defaultExpanded?: boolean;
  className?: string;
  contentClassName?: string;
}

export function CollapsibleSection({
  title,
  icon: Icon,
  badge,
  children,
  defaultExpanded = true,
  className,
  contentClassName,
}: CollapsibleSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const toggleExpanded = useCallback(() => {
    setIsExpanded((prev) => !prev);
  }, []);

  return (
    <div className={clsx('flex flex-col', className)}>
      {/* Header - clickable */}
      <button
        type="button"
        onClick={toggleExpanded}
        className={clsx(
          'flex items-center gap-2 px-4 py-2 w-full text-left',
          'hover:bg-bg-panel-2 transition-colors',
          'focus:outline-none focus:ring-1 focus:ring-inset focus:ring-accent-violet'
        )}
        aria-expanded={isExpanded}
      >
        {/* Chevron */}
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-text-muted flex-shrink-0" />
        ) : (
          <ChevronRight className="w-4 h-4 text-text-muted flex-shrink-0" />
        )}

        {/* Icon (optional) */}
        {Icon && <Icon className="w-4 h-4 text-text-muted flex-shrink-0" />}

        {/* Title */}
        <span className="text-sm font-semibold text-text-muted uppercase tracking-wide flex-1 truncate">
          {title}
        </span>

        {/* Badge (optional) */}
        {badge !== undefined && badge !== '' && (
          <span className="text-xs text-text-muted bg-bg-panel-2 px-1.5 py-0.5 rounded">
            {badge}
          </span>
        )}
      </button>

      {/* Content - collapsible */}
      {isExpanded && <div className={clsx('px-4 pb-3', contentClassName)}>{children}</div>}
    </div>
  );
}
