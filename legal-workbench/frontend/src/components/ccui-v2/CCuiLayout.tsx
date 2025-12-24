import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  Files,
  Search,
  SlidersHorizontal,
  Sun,
  Plus,
  Folder,
  Cpu,
  X,
  Settings,
  GitBranch,
  Zap,
  Sparkles,
  Clock,
  Edit,
  Layout,
  LucideIcon
} from 'lucide-react';
import CCuiFileTree from './CCuiFileTree';
import CCuiChatInterface from './CCuiChatInterface';

interface SidebarIconProps {
  icon: LucideIcon;
  active: boolean;
  onClick: () => void;
  tooltip: string;
}

const SidebarIcon: React.FC<SidebarIconProps> = ({ icon: Icon, active, onClick, tooltip }) => (
  <button
    onClick={onClick}
    title={tooltip}
    className={`w-full p-4 flex justify-center transition-all duration-200 relative group ${active ? 'text-[#e3e1de]' : 'text-[#b5b5b5] hover:text-[#e3e1de]'}`}
  >
    <Icon className="w-6 h-6" strokeWidth={1.5} />
    {active && <div className="absolute left-0 top-3 bottom-3 w-0.5 bg-[#d97757] rounded-r-full shadow-[0_0_8px_rgba(217,119,87,0.8)]"></div>}
  </button>
);

interface StatusBarItemProps {
  icon?: LucideIcon;
  label?: string;
  color?: string;
  active?: boolean;
}

const StatusBarItem: React.FC<StatusBarItemProps> = ({ icon: Icon, label, color = "text-[#b5b5b5]", active }) => (
  <div className={`flex items-center gap-2 px-3 py-1 ${active ? 'bg-[#1a1a1a] rounded' : ''} cursor-pointer hover:text-[#e3e1de] transition-colors`}>
    {Icon && <Icon className={`w-4 h-4 ${color}`} />}
    {label && <span className="text-sm font-mono text-[#b5b5b5] group-hover:text-[#e3e1de]">{label}</span>}
  </div>
);

type SidebarView = 'history' | 'explorer' | 'search' | 'settings';

export default function CCuiLayout() {
  const [sidebarView, setSidebarView] = useState<SidebarView>('history');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [time, setTime] = useState(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));

  useEffect(() => {
    const interval = setInterval(() => {
      setTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col h-screen w-full bg-[#000000] text-[#e3e1de] font-sans overflow-hidden selection:bg-[#d97757]/30">

      {/* --- HEADER --- */}
      <header className="flex-none h-14 bg-[#000000] flex items-center justify-between px-6 z-50 select-none border-b border-[#27272a]">
        <div className="flex items-center gap-6">
          {/* Window Controls */}
          <div className="flex gap-2.5 group cursor-pointer opacity-90 hover:opacity-100 transition-opacity">
            <div className="w-3.5 h-3.5 rounded-full bg-[#FF5F56] border border-[#E0443E]"></div>
            <div className="w-3.5 h-3.5 rounded-full bg-[#FFBD2E] border border-[#DEA123]"></div>
            <div className="w-3.5 h-3.5 rounded-full bg-[#27C93F] border border-[#1AAB29]"></div>
          </div>

          {/* Project Path */}
          <div className="flex items-center gap-2.5 text-base font-medium text-[#b5b5b5] hover:text-[#e3e1de] transition-colors cursor-pointer ml-4">
            <Folder className="w-4.5 h-4.5 text-[#b5b5b5]" />
            <span>~/project-root</span>
          </div>
        </div>

        <div className="flex items-center gap-5">
          <div className="flex items-center gap-2.5 px-3 py-1.5 rounded bg-[#1a1a1a] border border-[#27272a] hover:border-[#d97757] transition-colors cursor-pointer">
            <Cpu className="w-4 h-4 text-[#d97757]" />
            <span className="text-sm font-mono text-[#e3e1de] tracking-wide">Claude Code Wrapper</span>
          </div>
          <Search className="w-5 h-5 text-[#b5b5b5] hover:text-[#d97757] cursor-pointer transition-colors" />
          <Settings
            className="w-5 h-5 text-[#b5b5b5] hover:text-[#d97757] cursor-pointer transition-colors"
            onClick={() => setIsSettingsOpen(true)}
          />
        </div>
      </header>

      {/* --- MAIN LAYOUT --- */}
      <div className="flex-1 flex overflow-hidden">

        {/* ICON RAIL */}
        <aside className="w-20 bg-[#000000] border-r border-[#27272a] flex flex-col items-center py-6 z-50">
          <SidebarIcon icon={MessageSquare} active={sidebarView === 'history'} onClick={() => setSidebarView('history')} tooltip="Chats" />
          <SidebarIcon icon={Files} active={sidebarView === 'explorer'} onClick={() => setSidebarView('explorer')} tooltip="Explorer" />
          <SidebarIcon icon={Search} active={sidebarView === 'search'} onClick={() => setSidebarView('search')} tooltip="Search" />
          <SidebarIcon icon={SlidersHorizontal} active={sidebarView === 'settings'} onClick={() => setSidebarView('settings')} tooltip="Controls" />

          <div className="mt-auto mb-6">
            <SidebarIcon icon={Sun} active={false} onClick={() => { }} tooltip="Theme" />
          </div>
        </aside>

        {/* SIDEBAR PANEL */}
        <aside className="w-80 bg-[#050505] border-r border-[#27272a] flex flex-col z-40">
          {sidebarView === 'history' && (
            <div className="flex flex-col h-full">
              <div className="h-14 flex items-center justify-between px-5 border-b border-[#27272a]">
                <span className="text-sm font-bold text-[#b5b5b5] tracking-widest">CHATS</span>
                <Edit className="w-4.5 h-4.5 text-[#b5b5b5] hover:text-[#e3e1de] cursor-pointer" />
              </div>
              <div className="p-5">
                <button className="w-full flex items-center justify-center gap-3 py-3 rounded bg-[#111] border border-[#27272a] hover:border-[#d97757] hover:text-[#d97757] text-[#b5b5b5] text-sm font-medium transition-all group">
                  <Plus className="w-4 h-4" />
                  <span>New Chat</span>
                </button>
              </div>
              <div className="flex-1 flex flex-col items-center justify-center text-[#666] p-8 text-center">
                <MessageSquare className="w-14 h-14 mb-4 text-[#222]" />
                <span className="text-base font-medium text-[#888]">No recent history</span>
                <span className="text-sm text-[#555] mt-2">Start a conversation to see it here</span>
              </div>
            </div>
          )}

          {sidebarView === 'explorer' && (
            <div className="flex flex-col h-full">
              <div className="h-14 flex items-center px-5 border-b border-[#27272a]">
                <span className="text-sm font-bold text-[#b5b5b5] tracking-widest">EXPLORER</span>
              </div>
              <div className="flex-1 overflow-y-auto p-4">
                <CCuiFileTree />
              </div>
            </div>
          )}

          {['search', 'settings'].includes(sidebarView) && (
            <div className="flex flex-col items-center justify-center h-full text-[#333]">
              <Layout className="w-14 h-14 mb-4 text-[#1a1a1a]" />
              <span className="text-base text-[#666]">View not implemented</span>
            </div>
          )}
        </aside>

        {/* MAIN CONTENT */}
        <main className="flex-1 flex flex-col relative bg-[#000000]">
          <CCuiChatInterface />
        </main>
      </div>

      {/* --- STATUS BAR --- */}
      <footer className="flex-none h-10 bg-[#050505] border-t border-[#27272a] flex items-center justify-between px-5 select-none">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2.5">
            <div className="w-3 h-3 rounded-full bg-green-500 shadow-[0_0_6px_rgba(34,197,94,0.6)] animate-pulse"></div>
            <span className="text-sm font-mono text-[#b5b5b5] font-bold tracking-wide">READY</span>
          </div>
          <StatusBarItem icon={Zap} label="0% ctx" />
          <StatusBarItem icon={Sparkles} label="Claude 3.7 Sonnet" color="text-[#d97757]" active />
          <StatusBarItem icon={GitBranch} label="main" />
        </div>

        <div className="flex items-center gap-8">
          <StatusBarItem label="UTF-8" />
          <StatusBarItem label="TypeScript" />
          <div className="flex items-center gap-2.5 text-[#b5b5b5]">
            <Clock className="w-4 h-4" />
            <span className="text-sm font-mono font-medium">{time}</span>
          </div>
        </div>
      </footer>

      {/* Settings Modal Overlay */}
      {isSettingsOpen && (
        <div className="absolute inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-center justify-center animate-in fade-in duration-200">
          <div className="w-[520px] bg-[#0a0a0a] border border-[#27272a] rounded-xl shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#27272a] bg-[#0f0f0f]">
              <span className="text-lg font-bold text-[#e3e1de]">Settings</span>
              <button onClick={() => setIsSettingsOpen(false)} className="text-[#666] hover:text-[#e3e1de]"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-8">
              <div className="space-y-6">
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-bold text-[#b5b5b5] uppercase tracking-wide">API Endpoint</label>
                  <input type="text" value="https://api.claudecode.dev/v1" className="w-full bg-[#050505] border border-[#27272a] rounded px-4 py-3 text-base text-[#b5b5b5] focus:border-[#d97757] focus:outline-none focus:ring-1 focus:ring-[#d97757]/50 transition-all" readOnly />
                </div>
              </div>
            </div>
            <div className="bg-[#0f0f0f] px-6 py-4 border-t border-[#27272a] flex justify-end">
              <button onClick={() => setIsSettingsOpen(false)} className="px-6 py-2 rounded bg-[#d97757] text-black text-sm font-bold hover:bg-[#ff8c69] transition-colors">
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
