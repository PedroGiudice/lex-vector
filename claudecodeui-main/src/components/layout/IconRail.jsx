import { MessageSquare, FolderOpen, Search, Settings, Terminal, GitBranch } from 'lucide-react';

const navItems = [
  { id: 'chat', icon: MessageSquare, label: 'Chat' },
  { id: 'files', icon: FolderOpen, label: 'Files' },
  { id: 'search', icon: Search, label: 'Search' },
  { id: 'terminal', icon: Terminal, label: 'Terminal' },
  { id: 'git', icon: GitBranch, label: 'Git' },
];

export default function IconRail({ activeTab, onTabChange, onSettingsClick }) {
  return (
    <div className="w-12 bg-zinc-950 border-r border-zinc-800 flex flex-col items-center py-3">
      {/* Navigation Icons */}
      <div className="flex flex-col gap-1">
        {navItems.map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            onClick={() => onTabChange(id)}
            className={`p-2.5 rounded-lg transition-colors ${
              activeTab === id
                ? 'bg-zinc-800 text-white'
                : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900'
            }`}
            title={label}
          >
            <Icon size={20} />
          </button>
        ))}
      </div>

      {/* Settings at bottom */}
      <div className="mt-auto">
        <button
          onClick={onSettingsClick}
          className="p-2.5 rounded-lg text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900 transition-colors"
          title="Settings"
        >
          <Settings size={20} />
        </button>
      </div>
    </div>
  );
}
