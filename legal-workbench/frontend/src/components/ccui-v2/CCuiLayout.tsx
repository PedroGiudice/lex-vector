import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  Files,
  Search,
  SlidersHorizontal,
  Plus,
  Folder,
  X,
  Settings,
  GitBranch,
  Clock,
  Edit,
  Layout,
  LucideIcon,
  Scale,
  Activity,
  Wifi,
  WifiOff,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import CCuiFileTree from './CCuiFileTree';
import CCuiChatInterface from './CCuiChatInterface';
import { useWebSocket } from './contexts/WebSocketContext';

/**
 * CCui v2 Layout -- "Sala de Operacoes Juridica"
 *
 * Estetica: editorial escuro com tons terrosos organicos.
 * Instrument Serif para titulos, Geist Mono para dados.
 * Terracota (#a0603a) como accent primario, ocre queimado (#b85a30) para acoes.
 * Grade sutil em tom de argila, atmosfera de escritorio de mogno.
 */

interface SidebarIconProps {
  icon: LucideIcon;
  active: boolean;
  onClick: () => void;
  tooltip: string;
  badge?: number;
}

const SidebarIcon: React.FC<SidebarIconProps> = ({
  icon: Icon,
  active,
  onClick,
  tooltip,
  badge,
}) => (
  <button
    onClick={onClick}
    title={tooltip}
    aria-label={tooltip}
    className={`
      relative w-full flex justify-center items-center py-3 transition-all duration-200
      ${active ? 'text-[#a0603a]' : 'text-[#4a3d28] hover:text-[#7a6545]'}
    `}
  >
    <Icon className="w-[17px] h-[17px]" strokeWidth={1.4} />
    {active && <div className="absolute left-0 inset-y-1.5 w-[2px] bg-[#a0603a] rounded-r-full" />}
    {badge !== undefined && badge > 0 && (
      <div className="absolute top-1.5 right-2 w-1.5 h-1.5 rounded-full bg-[#b85a30]" />
    )}
  </button>
);

type SidebarView = 'history' | 'explorer' | 'search' | 'settings';

export default function CCuiLayout() {
  const [sidebarView, setSidebarView] = useState<SidebarView>('history');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [time, setTime] = useState(
    new Date().toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  );
  const { connectionStatus } = useWebSocket();

  useEffect(() => {
    const interval = setInterval(() => {
      setTime(
        new Date().toLocaleTimeString('pt-BR', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        })
      );
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
        e.preventDefault();
        setSidebarCollapsed((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const isOnline = connectionStatus === 'connected';

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist+Mono:wght@300;400;500;600&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300;1,9..40,400&display=swap');

        .lv-root {
          font-family: 'DM Sans', system-ui, sans-serif;
          background: #0d0a08;
          background-image:
            linear-gradient(rgba(160,96,58,0.018) 1px, transparent 1px),
            linear-gradient(90deg, rgba(160,96,58,0.018) 1px, transparent 1px);
          background-size: 48px 48px;
        }

        .lv-serif { font-family: 'Instrument Serif', Georgia, serif; }
        .lv-mono { font-family: 'Geist Mono', 'JetBrains Mono', monospace; }

        .lv-scrollbar::-webkit-scrollbar { width: 3px; }
        .lv-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .lv-scrollbar::-webkit-scrollbar-thumb { background: #2a2218; border-radius: 1px; }
        .lv-scrollbar::-webkit-scrollbar-thumb:hover { background: #3a301f; }

        .lv-section-label {
          font-family: 'Geist Mono', monospace;
          font-size: 9px;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          color: #5a4a32;
        }

        .lv-tag {
          font-family: 'Geist Mono', monospace;
          font-size: 8px;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: #4a3d28;
          padding: 2px 6px;
          border: 1px solid rgba(160,96,58,0.12);
          background: rgba(160,96,58,0.04);
        }

        @keyframes lv-breathe {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        .lv-breathe { animation: lv-breathe 3s ease-in-out infinite; }

        @keyframes lv-slide-in {
          from { opacity: 0; transform: translateX(-6px); }
          to { opacity: 1; transform: translateX(0); }
        }
        .lv-slide-in { animation: lv-slide-in 0.2s ease-out; }

        .lv-noise::before {
          content: '';
          position: absolute;
          inset: 0;
          opacity: 0.02;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
          pointer-events: none;
          z-index: 0;
        }
      `}</style>

      <div className="lv-root lv-noise flex flex-col h-full w-full text-[#c0a880] overflow-hidden select-none relative">
        {/* === HEADER === */}
        <header className="flex-none h-10 bg-[#0d0a08]/95 border-b border-[#231d15] flex items-center justify-between px-4 z-50 backdrop-blur-sm">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Scale className="w-3.5 h-3.5 text-[#a0603a]" strokeWidth={1.4} />
              <span className="lv-serif text-[15px] text-[#a0603a] tracking-wide italic">
                Lex Vector
              </span>
              <span className="lv-mono text-[8px] tracking-[0.15em] text-[#3a301f] ml-0.5">
                / CCUI
              </span>
            </div>

            <div className="h-3.5 w-px bg-[#231d15]" />

            <div className="flex items-center gap-1.5 cursor-pointer group">
              <Folder
                className="w-3 h-3 text-[#3e3222] group-hover:text-[#7a6545] transition-colors"
                strokeWidth={1.4}
              />
              <span className="lv-mono text-[10px] text-[#3e3222] group-hover:text-[#5a4a32] transition-colors">
                lex-vector
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 border border-[#231d15] bg-[#141009]">
            <div
              className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-[#5a7a3a] lv-breathe' : 'bg-[#8a3028]'}`}
            />
            <span className="lv-mono text-[9px] tracking-[0.15em] text-[#5a4a32]">CLAUDE CODE</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarCollapsed((prev) => !prev)}
              className="text-[#3e3222] hover:text-[#7a6545] transition-colors"
              title="Toggle sidebar (Ctrl+B)"
              aria-label="Toggle sidebar"
            >
              {sidebarCollapsed ? (
                <ChevronRight className="w-3.5 h-3.5" strokeWidth={1.4} />
              ) : (
                <ChevronLeft className="w-3.5 h-3.5" strokeWidth={1.4} />
              )}
            </button>
            <Settings
              className="w-3.5 h-3.5 text-[#3e3222] hover:text-[#7a6545] cursor-pointer transition-colors"
              strokeWidth={1.4}
              onClick={() => setIsSettingsOpen(true)}
            />
          </div>
        </header>

        {/* === LAYOUT PRINCIPAL === */}
        <div className="flex-1 flex overflow-hidden">
          <aside className="w-11 bg-[#0d0a08] border-r border-[#231d15] flex flex-col items-center py-2 z-50 flex-none">
            <SidebarIcon
              icon={MessageSquare}
              active={sidebarView === 'history'}
              onClick={() => setSidebarView('history')}
              tooltip="Sessoes"
            />
            <SidebarIcon
              icon={Files}
              active={sidebarView === 'explorer'}
              onClick={() => setSidebarView('explorer')}
              tooltip="Arquivos"
            />
            <SidebarIcon
              icon={Search}
              active={sidebarView === 'search'}
              onClick={() => setSidebarView('search')}
              tooltip="Busca"
            />
            <SidebarIcon
              icon={SlidersHorizontal}
              active={sidebarView === 'settings'}
              onClick={() => setSidebarView('settings')}
              tooltip="Controles"
            />
          </aside>

          {!sidebarCollapsed && (
            <aside className="w-56 bg-[#110e0b] border-r border-[#231d15] flex flex-col z-40 flex-none lv-slide-in">
              {sidebarView === 'history' && (
                <div className="flex flex-col h-full">
                  <div className="flex items-center justify-between px-3 py-2.5 border-b border-[#231d15]">
                    <span className="lv-section-label">Sessoes</span>
                    <Edit
                      className="w-3 h-3 text-[#3e3222] hover:text-[#7a6545] cursor-pointer transition-colors"
                      strokeWidth={1.4}
                    />
                  </div>

                  <div className="p-2">
                    <button
                      className="
                      w-full flex items-center gap-2 px-3 py-2
                      border border-[#231d15] hover:border-[#a0603a]/25
                      text-[#4a3d28] hover:text-[#a0603a]
                      lv-mono text-[9px] tracking-[0.12em]
                      transition-all duration-200
                    "
                    >
                      <Plus className="w-3 h-3" strokeWidth={1.8} />
                      <span>NOVA SESSAO</span>
                    </button>
                  </div>

                  <div className="flex-1 flex flex-col items-center justify-center px-3 text-center">
                    <div className="w-7 h-7 border border-[#231d15] flex items-center justify-center mb-2">
                      <MessageSquare className="w-3 h-3 text-[#2a2218]" strokeWidth={1.4} />
                    </div>
                    <span className="lv-mono text-[9px] text-[#2e2519]">SEM HISTORICO</span>
                  </div>
                </div>
              )}

              {sidebarView === 'explorer' && (
                <div className="flex flex-col h-full">
                  <div className="flex items-center px-3 py-2.5 border-b border-[#231d15]">
                    <span className="lv-section-label">Arquivos</span>
                  </div>
                  <div className="flex-1 overflow-y-auto lv-scrollbar p-1.5">
                    <CCuiFileTree />
                  </div>
                </div>
              )}

              {['search', 'settings'].includes(sidebarView) && (
                <div className="flex flex-col items-center justify-center h-full">
                  <Layout className="w-4 h-4 text-[#251f16] mb-1.5" strokeWidth={1} />
                  <span className="lv-mono text-[9px] text-[#2e2519]">EM BREVE</span>
                </div>
              )}
            </aside>
          )}

          <main className="flex-1 flex flex-col relative overflow-hidden">
            <CCuiChatInterface />
          </main>
        </div>

        {/* === STATUS BAR === */}
        <footer className="flex-none h-6 bg-[#0d0a08]/95 border-t border-[#231d15] flex items-center justify-between px-3 z-50 backdrop-blur-sm">
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-1.5">
              {isOnline ? (
                <Wifi className="w-2.5 h-2.5 text-[#5a7a3a]" strokeWidth={1.5} />
              ) : (
                <WifiOff className="w-2.5 h-2.5 text-[#8a3028]" strokeWidth={1.5} />
              )}
              <span
                className={`lv-mono text-[8px] tracking-[0.12em] ${isOnline ? 'text-[#5a7a3a]' : 'text-[#8a3028]'}`}
              >
                {isOnline ? 'ONLINE' : 'OFFLINE'}
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              <Activity className="w-2.5 h-2.5 text-[#a0603a]" strokeWidth={1.5} />
              <span className="lv-mono text-[8px] text-[#a0603a]">Opus 4.5</span>
            </div>

            <div className="flex items-center gap-1.5">
              <GitBranch className="w-2.5 h-2.5 text-[#3e3222]" strokeWidth={1.5} />
              <span className="lv-mono text-[8px] text-[#3e3222]">main</span>
            </div>
          </div>

          <div className="flex items-center gap-5">
            <span className="lv-mono text-[8px] text-[#2e2519]">UTF-8</span>
            <div className="flex items-center gap-1.5">
              <Clock className="w-2.5 h-2.5 text-[#3e3222]" strokeWidth={1.5} />
              <span className="lv-mono text-[8px] text-[#3e3222]">{time}</span>
            </div>
          </div>
        </footer>
      </div>

      {/* === MODAL CONFIGURACOES === */}
      {isSettingsOpen && (
        <div className="fixed inset-0 z-[200] bg-black/80 backdrop-blur-sm flex items-center justify-center">
          <div className="w-[440px] bg-[#110e0b] border border-[#231d15] shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-[#231d15]">
              <div className="flex items-center gap-2">
                <Settings className="w-3 h-3 text-[#a0603a]" strokeWidth={1.4} />
                <span className="lv-mono text-[10px] tracking-[0.15em] text-[#7a6545]">
                  CONFIGURACOES
                </span>
              </div>
              <button
                onClick={() => setIsSettingsOpen(false)}
                className="text-[#3e3222] hover:text-[#7a6545] transition-colors"
                aria-label="Fechar"
              >
                <X className="w-3.5 h-3.5" strokeWidth={1.4} />
              </button>
            </div>

            <div className="p-5 space-y-4">
              <div className="space-y-1.5">
                <label className="lv-section-label block">Endpoint</label>
                <input
                  type="text"
                  defaultValue="wss://localhost/ws"
                  className="
                    w-full bg-[#141009] border border-[#231d15]
                    focus:border-[#a0603a]/25 focus:outline-none
                    px-3 py-2 lv-mono text-[11px] text-[#7a6545]
                    transition-colors duration-200
                  "
                  readOnly
                />
              </div>
            </div>

            <div className="px-4 py-3 border-t border-[#231d15] flex justify-end">
              <button
                onClick={() => setIsSettingsOpen(false)}
                className="
                  px-4 py-1.5 border border-[#a0603a]/25 hover:border-[#a0603a]/50
                  lv-mono text-[9px] tracking-[0.12em] text-[#a0603a]
                  hover:bg-[#a0603a]/5 transition-all duration-200
                "
              >
                CONFIRMAR
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
