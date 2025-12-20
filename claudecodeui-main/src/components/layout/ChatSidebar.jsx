import { Plus, Pencil, MoreHorizontal } from 'lucide-react';
import { groupSessionsByDate, formatTime } from '../../utils/dateUtils';

export default function ChatSidebar({
  selectedProject,
  sessions,
  selectedSessionId,
  onSelectSession,
  onNewChat,
  onClose
}) {
  const groupedSessions = groupSessionsByDate(sessions || []);

  return (
    <div className="w-64 bg-zinc-900 border-r border-zinc-800 flex flex-col">
      {/* Project Header */}
      <div className="p-3 border-b border-zinc-800 flex items-center gap-2">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          <div className="w-3 h-3 rounded-full bg-green-500" />
        </div>
        <span className="text-sm text-zinc-400 truncate flex-1">
          {selectedProject?.displayName || '~/project'}
        </span>
      </div>

      {/* Chats Header */}
      <div className="px-3 py-2 flex items-center justify-between">
        <span className="text-xs font-medium text-zinc-500 uppercase tracking-wider">
          Chats
        </span>
        <div className="flex gap-1">
          <button className="p-1 text-zinc-500 hover:text-zinc-300 rounded">
            <Pencil size={14} />
          </button>
          <button className="p-1 text-zinc-500 hover:text-zinc-300 rounded">
            <MoreHorizontal size={14} />
          </button>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="px-3 pb-2">
        <button
          onClick={onNewChat}
          className="w-full py-2 px-3 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm text-zinc-300 flex items-center justify-center gap-2 transition-colors"
        >
          <Plus size={16} />
          New Chat
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto px-2">
        {Object.entries(groupedSessions).map(([group, groupSessions]) => (
          <div key={group} className="mb-4">
            <div className="px-2 py-1 text-xs font-medium text-zinc-600 uppercase tracking-wider">
              {group}
            </div>
            {groupSessions.map((session) => (
              <button
                key={session.id}
                onClick={() => onSelectSession(session)}
                className={`w-full text-left px-2 py-2 rounded-lg mb-0.5 transition-colors ${
                  selectedSessionId === session.id
                    ? 'bg-zinc-800 text-white'
                    : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200'
                }`}
              >
                <div className="text-sm truncate font-medium">
                  {session.title || 'New Chat'}
                </div>
                <div className="text-xs text-zinc-600">
                  {formatTime(session.lastModified)}
                </div>
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
