import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { useAuth } from '../../context/AuthContext';

const TITLES: Record<string, { title: string; subtitle?: string }> = {
  '/app': { title: 'Dashboard', subtitle: 'Good morning — here is what needs your attention today.' },
  '/app/documents': { title: 'Document Manager', subtitle: 'Every file, contract and record — searchable in one cabinet.' },
  '/app/scan': { title: 'Smart Scan', subtitle: 'Capture paperwork once. Docket classifies and files it for you.' },
  '/app/workflows': { title: 'Workflows', subtitle: 'Approval chains and automations running across your business.' },
  '/app/esignature': { title: 'eSignature & Forms', subtitle: 'Send for signature, build forms, track completion.' },
  '/app/reports': { title: 'Reports', subtitle: 'Volume, compliance and turnaround across every department.' },
  '/app/settings': { title: 'Settings', subtitle: 'Users, permissions, retention and compliance controls.' },
};

export function AppShell() {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) return <Navigate to="/login" replace />;

  const meta = TITLES[location.pathname] ?? { title: 'Docket' };

  return (
    <div className="flex h-screen w-full bg-paper text-ink">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar title={meta.title} subtitle={meta.subtitle} />
        <main className="flex-1 overflow-y-auto px-6 py-6 md:px-8 md:py-8">
          <div className="mx-auto max-w-[1240px]">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
