import { Sparkles } from 'lucide-react';

export default function ThinkingIndicator({ message = "Thinking..." }) {
  return (
    <div className="flex items-center gap-3 py-4">
      {/* Avatar */}
      <div className="w-8 h-8 rounded-full bg-orange-500/10 flex items-center justify-center flex-shrink-0">
        <Sparkles size={16} className="text-orange-500 animate-pulse" />
      </div>

      {/* Thinking message with animated dots */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-zinc-400">{message}</span>
        <div className="flex gap-1">
          <span className="w-1.5 h-1.5 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-1.5 h-1.5 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-1.5 h-1.5 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}
