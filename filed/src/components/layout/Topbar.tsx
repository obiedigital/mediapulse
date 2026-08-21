import { useState } from 'react';
import { Bell, Search, LogOut, ChevronDown } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Avatar } from '../ui/Avatar';
import { demoUsers } from '../../data/mockData';

export function Topbar({ title, subtitle }: { title: string; subtitle?: string }) {
  const { user, login, logout } = useAuth();
  const navigate = useNavigate();
  const [switcherOpen, setSwitcherOpen] = useState(false);
  if (!user) return null;

  return (
    <header className="flex h-16 shrink-0 items-center justify-between gap-4 border-b border-line bg-surface/95 backdrop-blur px-6">
      <div className="min-w-0">
        <h1 className="font-display text-[18px] font-bold text-ink truncate">{title}</h1>
        {subtitle && <p className="text-[12px] text-ink/50 truncate">{subtitle}</p>}
      </div>

      <div className="hidden lg:flex flex-1 max-w-sm items-center gap-2 rounded-lg border border-line bg-paper px-3 py-2 text-[12.5px] text-ink/45">
        <Search size={14} />
        <span>Search documents, workflows, people…</span>
        <kbd className="ml-auto rounded bg-paper-dim px-1.5 py-0.5 text-[10px] text-ink/50">⌘K</kbd>
      </div>

      <div className="flex items-center gap-4 shrink-0">
        <button className="relative text-ink/50 hover:text-ink">
          <Bell size={18} />
          <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-danger-600" />
        </button>

        <div className="relative">
          <button
            onClick={() => setSwitcherOpen((s) => !s)}
            className="flex items-center gap-2 rounded-lg border border-line px-2 py-1.5 hover:bg-paper"
          >
            <Avatar initials={user.initials} color={user.color} size={26} />
            <div className="hidden sm:block text-left">
              <p className="text-[12px] font-semibold text-ink leading-tight">{user.name}</p>
              <p className="text-[10.5px] text-ink/45 leading-tight">{user.role}</p>
            </div>
            <ChevronDown size={14} className="text-ink/40" />
          </button>

          {switcherOpen && (
            <div className="absolute right-0 top-full mt-2 w-64 rounded-xl border border-line bg-surface p-2 shadow-xl z-50">
              <p className="px-2 py-1.5 text-[10px] font-semibold uppercase tracking-wide text-ink/40">Switch demo role</p>
              {demoUsers.map((u) => (
                <button
                  key={u.id}
                  onClick={() => {
                    login(u.id);
                    setSwitcherOpen(false);
                  }}
                  className={`flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-left hover:bg-paper ${
                    u.id === user.id ? 'bg-navy-50' : ''
                  }`}
                >
                  <Avatar initials={u.initials} color={u.color} size={26} />
                  <div className="min-w-0">
                    <p className="truncate text-[12px] font-semibold text-ink">{u.name}</p>
                    <p className="truncate text-[10.5px] text-ink/45">{u.role} · {u.department}</p>
                  </div>
                </button>
              ))}
              <div className="my-1.5 border-t border-line" />
              <button
                onClick={() => {
                  logout();
                  navigate('/login');
                }}
                className="flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-left text-[12.5px] font-medium text-danger-600 hover:bg-danger-100/50"
              >
                <LogOut size={14} /> Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
