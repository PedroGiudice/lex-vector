import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Loader2 } from 'lucide-react';

/**
 * CCuiThinkingBlock - Collapsible thinking/reasoning display
 *
 * Features:
 * - Toggle open/close with chevron icon
 * - Streaming indicator with spinner
 * - Duration display when complete
 * - Visual hierarchy with border-l
 *
 * @param {Object} props
 * @param {string} props.content - The thinking/reasoning content
 * @param {boolean} props.isStreaming - Whether content is currently streaming
 * @param {string} props.label - Label to display (default: "Thinking")
 * @param {number} props.duration - Duration in milliseconds (shown when complete)
 */
const CCuiThinkingBlock = ({
  content,
  isStreaming = false,
  label = 'Thinking',
  duration = null
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleOpen = () => {
    setIsOpen(!isOpen);
  };

  const formatDuration = (ms) => {
    if (!ms) return '';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  return (
    <div className="my-4 border-l-2 border-ccui-accent pl-4">
      {/* Header - clickable to toggle */}
      <button
        onClick={toggleOpen}
        className="flex items-center gap-2 w-full text-left group hover:opacity-80 transition-opacity"
        aria-expanded={isOpen}
        aria-label={`${isOpen ? 'Collapse' : 'Expand'} thinking block`}
      >
        {/* Chevron icon */}
        {isOpen ? (
          <ChevronDown className="w-4 h-4 text-ccui-text-secondary flex-shrink-0" />
        ) : (
          <ChevronRight className="w-4 h-4 text-ccui-text-secondary flex-shrink-0" />
        )}

        {/* Label */}
        <span className="text-sm font-medium text-ccui-text-secondary">
          {label}
        </span>

        {/* Streaming spinner or duration */}
        {isStreaming ? (
          <Loader2 className="w-3.5 h-3.5 text-ccui-accent animate-spin" />
        ) : duration ? (
          <span className="text-xs text-ccui-text-tertiary">
            {formatDuration(duration)}
          </span>
        ) : null}
      </button>

      {/* Content - collapsible */}
      {isOpen && (
        <div className="mt-2 text-sm text-ccui-text-secondary whitespace-pre-wrap leading-relaxed">
          {content}
          {isStreaming && (
            <span className="inline-block w-1.5 h-4 ml-1 bg-ccui-accent animate-pulse" />
          )}
        </div>
      )}
    </div>
  );
};

export default CCuiThinkingBlock;
