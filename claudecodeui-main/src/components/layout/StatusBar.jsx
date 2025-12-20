import { Circle } from 'lucide-react';

export default function StatusBar({
  status = 'ready',
  contextUsage = 0,
  model = 'Claude 3.7 Sonnet'
}) {
  const statusColors = {
    ready: 'text-green-500',
    processing: 'text-yellow-500',
    error: 'text-red-500',
    connecting: 'text-blue-500'
  };

  const statusLabels = {
    ready: 'Ready',
    processing: 'Processing',
    error: 'Error',
    connecting: 'Connecting'
  };

  return (
    <div className="h-6 bg-zinc-950 border-t border-zinc-800 px-4 flex items-center justify-between text-xs">
      {/* Left: Status */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <Circle
            size={8}
            className={`${statusColors[status] || statusColors.ready} fill-current`}
          />
          <span className="text-zinc-400 uppercase">
            {statusLabels[status] || status}
          </span>
        </div>

        {contextUsage > 0 && (
          <div className="flex items-center gap-1.5 text-zinc-500">
            <span className="text-yellow-500">↑</span>
            <span>{contextUsage}% ctx</span>
          </div>
        )}
      </div>

      {/* Center: Model indicator */}
      <div className="text-zinc-500">
        {model}
      </div>

      {/* Right: Extras */}
      <div className="flex items-center gap-4 text-zinc-500">
        <span>UTF-8</span>
        <span>{new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        })}</span>
      </div>
    </div>
  );
}
