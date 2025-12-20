import ModelSelector from './ModelSelector';
import { PanelLeft, Search, MoreHorizontal } from 'lucide-react';

export default function ChatHeader({
  currentModel,
  onModelChange,
  onToggleSidebar,
  projectName
}) {
  return (
    <div className="h-12 border-b border-zinc-800 bg-zinc-900 px-4 flex items-center justify-between">
      {/* Left: Toggle sidebar */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-lg text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800 transition-colors"
          title="Toggle sidebar"
        >
          <PanelLeft size={18} />
        </button>

        {projectName && (
          <span className="text-sm text-zinc-400 font-medium">
            {projectName}
          </span>
        )}
      </div>

      {/* Right: Model selector and actions */}
      <div className="flex items-center gap-2">
        <ModelSelector
          currentModel={currentModel}
          onModelChange={onModelChange}
        />

        <button
          className="p-2 rounded-lg text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800 transition-colors"
          title="Search"
        >
          <Search size={18} />
        </button>

        <button
          className="p-2 rounded-lg text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800 transition-colors"
          title="More options"
        >
          <MoreHorizontal size={18} />
        </button>
      </div>
    </div>
  );
}
