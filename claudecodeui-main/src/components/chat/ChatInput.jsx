import { useState, useRef } from 'react';
import { Send, Sparkles, History, Command } from 'lucide-react';

export default function ChatInput({
  onSend,
  onActionsClick,
  onHistoryClick,
  isProcessing,
  placeholder = "Describe your task or enter a command..."
}) {
  const [value, setValue] = useState('');
  const inputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (value.trim() && !isProcessing) {
      onSend(value.trim());
      setValue('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="border-t border-zinc-800 bg-zinc-900 p-4">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
        <div className="relative flex items-center">
          <div className="absolute left-3 text-orange-500">
            <Sparkles size={18} />
          </div>

          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isProcessing}
            className="w-full pl-10 pr-16 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 transition-colors"
          />

          <div className="absolute right-3 flex items-center gap-2">
            <button
              type="submit"
              disabled={!value.trim() || isProcessing}
              className="p-2 rounded-lg bg-zinc-700 hover:bg-zinc-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={16} className="text-zinc-300" />
            </button>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex justify-center gap-4 mt-3">
          <button
            type="button"
            onClick={onActionsClick}
            className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            <Command size={12} />
            Actions
          </button>
          <button
            type="button"
            onClick={onHistoryClick}
            className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            <History size={12} />
            History
          </button>
        </div>
      </form>
    </div>
  );
}
