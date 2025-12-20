import { ChevronDown, Sparkles } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

const models = [
  { id: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4', badge: 'Latest' },
  { id: 'claude-3-7-sonnet-20250219', name: 'Claude 3.7 Sonnet', badge: null },
  { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet', badge: null },
  { id: 'claude-opus-4-5-20251101', name: 'Claude Opus 4.5', badge: 'Most Capable' },
];

export default function ModelSelector({ currentModel, onModelChange }) {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef(null);
  const selected = models.find(m => m.id === currentModel) || models[0];

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpen(false);
      }
    }

    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [open]);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
      >
        <Sparkles size={14} className="text-orange-500" />
        <span className="text-sm text-zinc-300">{selected.name}</span>
        <ChevronDown size={14} className={`text-zinc-500 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute top-full right-0 mt-2 w-64 bg-zinc-800 rounded-lg border border-zinc-700 shadow-xl z-50">
          <div className="p-2">
            {models.map((model) => (
              <button
                key={model.id}
                onClick={() => {
                  onModelChange(model.id);
                  setOpen(false);
                }}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm flex items-center justify-between ${
                  model.id === currentModel
                    ? 'bg-zinc-700 text-white'
                    : 'text-zinc-400 hover:bg-zinc-700/50'
                }`}
              >
                <span>{model.name}</span>
                {model.badge && (
                  <span className="text-xs bg-orange-500/20 text-orange-400 px-1.5 py-0.5 rounded">
                    {model.badge}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
