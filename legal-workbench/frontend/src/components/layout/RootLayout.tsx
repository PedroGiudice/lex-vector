import { Outlet, NavLink } from 'react-router-dom';
import { LayoutDashboard, Kanban, FileText, Scale } from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Hub' },
  { to: '/trello', icon: Kanban, label: 'Trello' },
  { to: '/doc-assembler', icon: FileText, label: 'Doc Assembler' },
  { to: '/stj', icon: Scale, label: 'STJ' },
];

export function RootLayout() {
  return (
    <div className="flex h-screen w-screen bg-bg-main text-text-primary">
      {/* Sidebar */}
      <aside className="w-16 bg-bg-panel-1 border-r border-border-default flex flex-col items-center py-4">
        <div className="text-accent-indigo font-bold text-xl mb-8">LW</div>
        <nav className="flex flex-col gap-2">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `p-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-accent-indigo/20 text-accent-indigo'
                    : 'text-text-muted hover:text-text-primary hover:bg-surface-elevated'
                }`
              }
              title={label}
            >
              <Icon size={20} />
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
