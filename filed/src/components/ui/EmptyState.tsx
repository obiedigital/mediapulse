import type { ReactNode } from 'react';

export function EmptyState({ icon, title, subtitle, action }: { icon: ReactNode; title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-6">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-navy-50 text-navy-700">{icon}</div>
      <h4 className="font-display text-base font-bold text-ink">{title}</h4>
      {subtitle && <p className="mt-1.5 max-w-sm text-[13px] text-ink/55">{subtitle}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
