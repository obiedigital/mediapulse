import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderOpen,
  ScanLine,
  Workflow,
  FileSignature,
  BarChart3,
  Settings,
  FolderCog,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Avatar } from '../ui/Avatar';

const NAV = [
  {
    label: 'Overview',
    items: [{ to: '/app', label: 'Dashboard', icon: LayoutDashboard, end: true }],
  },
  {
    label: 'Cabinet',
    items: [
      { to: '/app/documents', label: 'Document Manager', icon: FolderOpen },
      { to: '/app/scan', label: 'Smart Scan', icon: ScanLine, badge: 3 },
    ],
  },
  {
    label: 'Automate',
    items: [
      { to: '/app/workflows', label: 'Workflows', icon: Workflow, badge: 2 },
      { to: '/app/esignature', label: 'eSignature & Forms', icon: FileSignature },
    ],
  },
  {
    label: 'Manage',
    items: [
      { to: '/app/reports', label: 'Reports', icon: BarChart3 },
      { to: '/app/settings', label: 'Settings', icon: Settings },
    ],
  },
];

export function Sidebar() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <aside className="hidden md:flex w-[228px] shrink-0 flex-col bg-navy-950 text-white/80 overflow-y-auto scrollbar-none">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gold-500">
          <FolderCog size={17} className="text-navy-950" />
        </div>
        <span className="font-display text-[15px] font-extrabold text-white">Filed</span>
      </div>

      <div className="mx-4 mb-4 rounded-xl bg-white/5 p-3">
        <p className="text-[10px] font-semibold uppercase tracking-wide text-white/40">Cabinet</p>
        <p className="mt-0.5 text-[13px] font-semibold text-white">{user.org}</p>
        <p className="mt-1 text-[10.5px] text-gold-400 font-medium">Growth Plan · 184.6 GB used</p>
      </div>

      <nav className="flex-1 px-3 pb-4">
        {NAV.map((group) => (
          <div key={group.label} className="mb-4">
            <p className="px-2 mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-white/35">{group.label}</p>
            {group.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={'end' in item ? item.end : false}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 rounded-lg px-2.5 py-2 mb-0.5 text-[12.5px] font-medium transition-colors ${
                    isActive ? 'bg-gold-500 text-navy-950 font-semibold' : 'text-white/65 hover:bg-white/8 hover:text-white'
                  }`
                }
              >
                <item.icon size={15} />
                <span className="flex-1">{item.label}</span>
                {'badge' in item && item.badge && (
                  <span className="rounded-full bg-danger-600 px-1.5 py-px text-[9.5px] font-bold text-white">{item.badge}</span>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="mx-3 mb-4 flex items-center gap-2.5 rounded-xl border border-white/10 p-3">
        <Avatar initials={user.initials} color={user.color} size={30} />
        <div className="min-w-0">
          <p className="truncate text-[12.5px] font-semibold text-white">{user.name}</p>
          <p className="truncate text-[10.5px] text-white/40">{user.role} · {user.department}</p>
        </div>
      </div>
    </aside>
  );
}
