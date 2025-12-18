import { useEffect } from 'react';
import { ToastContainer } from '@/components/ui/Toast';
import useTrelloStore from '@/store/trelloStore';
import { NavigationPanel } from '@/components/trello/NavigationPanel';
import { DataTable } from '@/components/trello/DataTable';
import { ActionsPanel } from '@/components/trello/ActionsPanel';

export default function TrelloModule() {
  const {
    boards,
    selectedBoardId,
    setSelectedBoardId,
    isLoading,
    error,
    lastSync,
    fetchInitialData,
  } = useTrelloStore();

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  const syncStatusColor = isLoading ? 'bg-status-yellow' : (error ? 'bg-status-red' : 'bg-status-emerald');
  const syncStatusText = isLoading ? 'Syncing...' : (error ? 'Sync failed' : 'Synced');
  const timeSinceLastSync = lastSync ? Math.floor((new Date().getTime() - lastSync.getTime()) / 1000) : null;

  return (
    <div className="flex flex-col h-full bg-bg-main text-text-primary">
      {/* Header - Top bar */}
      <header className="flex items-center justify-between px-4 py-2 border-b border-border-default bg-bg-panel-1 h-12">
        <div className="flex items-center space-x-3">
          <span className="text-accent-indigo font-bold text-base flex items-center gap-2">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-5 h-5">
              <path d="M12 3V5M12 19V21M3 12H5M19 12H21" strokeLinecap="round"/>
              <path d="M5.63604 5.63604L7.05025 7.05025M16.9497 16.9497L18.364 18.364" strokeLinecap="round"/>
              <path d="M5.63604 18.364L7.05025 16.9497M16.9497 7.05025L18.364 5.63604" strokeLinecap="round"/>
              <path d="M12 8L12 16" strokeLinecap="round"/>
            </svg>
            Trello Command Center
          </span>
          <span className="flex items-center space-x-2">
            <span className="text-text-muted text-xs uppercase tracking-wider">Board:</span>
            <select
              className="bg-bg-input border border-border-default rounded-sm px-2 py-1 text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-indigo cursor-pointer text-xs transition-colors"
              value={selectedBoardId || ''}
              onChange={(e) => setSelectedBoardId(e.target.value)}
              disabled={isLoading}
            >
              {boards.length === 0 && !isLoading && <option value="">No Boards Available</option>}
              {boards.map((board) => (
                <option key={board.id} value={board.id} className="bg-bg-panel-1 text-text-primary">
                  {board.name}
                </option>
              ))}
            </select>
          </span>
        </div>
        <div className="flex items-center space-x-3">
          {/* Sync Status Indicator */}
          <span className="flex items-center text-text-muted text-xs font-mono">
            <span className={`w-2 h-2 rounded-full ${syncStatusColor} mr-1.5`}></span>
            {syncStatusText} {timeSinceLastSync !== null && !isLoading && !error ? `${timeSinceLastSync}s ago` : ''}
          </span>
          <button
            className="text-text-muted hover:text-accent-indigo focus:outline-none focus:ring-1 focus:ring-accent-indigo rounded-sm p-1.5 transition-colors duration-200"
            title="Settings"
          >
            ⚙️
          </button>
        </div>
      </header>

      {/* Main Content Area - Three Panels */}
      <div className="flex flex-1 overflow-hidden">
        {/* Navigation Panel (Left) */}
        <NavigationPanel />

        {/* Data Table Panel (Center) */}
        <DataTable />

        {/* Actions Panel (Right) */}
        <ActionsPanel />
      </div>

      {/* Toast notifications */}
      <ToastContainer />
    </div>
  );
}
