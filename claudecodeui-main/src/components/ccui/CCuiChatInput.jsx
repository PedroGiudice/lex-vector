import React, { useState, useRef, useEffect } from 'react';
import { Send, Terminal } from 'lucide-react';

/**
 * CCuiChatInput - Terminal-style chat input
 *
 * Features:
 * - Terminal icon with pulse animation
 * - Auto-resize textarea (max 120px)
 * - Enter to send (Shift+Enter for new line)
 * - Coral send button when content present
 * - Keyboard shortcuts hint
 *
 * @param {Object} props
 * @param {Function} props.onSend - Callback when message is sent
 * @param {boolean} props.disabled - Whether input is disabled
 * @param {string} props.placeholder - Placeholder text
 * @param {Function} props.onActionsClick - Callback for actions shortcut
 * @param {Function} props.onHistoryClick - Callback for history shortcut
 */
const CCuiChatInput = ({
  onSend,
  disabled = false,
  placeholder = 'Type your message...',
  onActionsClick,
  onHistoryClick
}) => {
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = 'auto';
    const newHeight = Math.min(textarea.scrollHeight, 120); // max 120px
    textarea.style.height = `${newHeight}px`;
  }, [value]);

  const handleSubmit = () => {
    if (!value.trim() || disabled) return;

    onSend(value);
    setValue('');

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    // Enter to send (not Shift+Enter)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }

    // Command/Ctrl shortcuts
    if (e.metaKey || e.ctrlKey) {
      if (e.key === 'k' && onActionsClick) {
        e.preventDefault();
        onActionsClick();
      }
    }

    // ArrowUp for history
    if (e.key === 'ArrowUp' && !value && onHistoryClick) {
      e.preventDefault();
      onHistoryClick();
    }
  };

  const hasContent = value.trim().length > 0;

  return (
    <div className="w-full">
      {/* Input container */}
      <div className="relative flex items-end gap-3 p-4 bg-ccui-bg-tertiary border border-ccui-border-tertiary rounded-lg">
        {/* Terminal icon */}
        <div className="flex-shrink-0 pb-2">
          <Terminal
            className={`w-5 h-5 text-ccui-text-secondary ${
              !disabled ? 'animate-pulse' : ''
            }`}
          />
        </div>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex-1 bg-transparent text-ccui-text-primary placeholder-ccui-text-tertiary resize-none outline-none text-sm leading-relaxed"
          style={{ maxHeight: '120px' }}
          aria-label="Chat message input"
        />

        {/* Send button */}
        <button
          onClick={handleSubmit}
          disabled={disabled || !hasContent}
          className={`flex-shrink-0 p-2 rounded transition-all ${
            hasContent && !disabled
              ? 'bg-ccui-accent text-white hover:opacity-90'
              : 'bg-ccui-bg-hover text-ccui-text-tertiary cursor-not-allowed'
          }`}
          aria-label="Send message"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>

      {/* Shortcuts hint */}
      <div className="flex items-center gap-4 mt-2 px-1 text-xs text-ccui-text-tertiary">
        {onActionsClick && (
          <span>
            <kbd className="px-1.5 py-0.5 bg-ccui-bg-hover border border-ccui-border-tertiary rounded text-xs">
              ⌘K
            </kbd>{' '}
            Actions
          </span>
        )}
        {onHistoryClick && (
          <span>
            <kbd className="px-1.5 py-0.5 bg-ccui-bg-hover border border-ccui-border-tertiary rounded text-xs">
              ↑
            </kbd>{' '}
            History
          </span>
        )}
        <span className="ml-auto">
          <kbd className="px-1.5 py-0.5 bg-ccui-bg-hover border border-ccui-border-tertiary rounded text-xs">
            Enter
          </kbd>{' '}
          Send
        </span>
      </div>
    </div>
  );
};

export default CCuiChatInput;
