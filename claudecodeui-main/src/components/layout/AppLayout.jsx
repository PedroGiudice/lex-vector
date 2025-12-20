import IconRail from './IconRail';
import ChatSidebar from './ChatSidebar';

export default function AppLayout({
  children,
  activeTab,
  onTabChange,
  sidebarOpen,
  onToggleSidebar,
  onSettingsClick,
  selectedProject,
  sessions,
  selectedSessionId,
  onSelectSession,
  onNewChat
}) {
  return (
    <div className="h-screen flex bg-zinc-950">
      {/* Icon Rail - Always visible */}
      <IconRail
        activeTab={activeTab}
        onTabChange={onTabChange}
        onSettingsClick={onSettingsClick}
      />

      {/* Collapsible Sidebar */}
      {sidebarOpen && (
        <ChatSidebar
          selectedProject={selectedProject}
          sessions={sessions}
          selectedSessionId={selectedSessionId}
          onSelectSession={onSelectSession}
          onNewChat={onNewChat}
          onClose={() => onToggleSidebar(false)}
        />
      )}

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0">
        {children}
      </main>
    </div>
  );
}
