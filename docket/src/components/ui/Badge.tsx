import type { ReactNode } from 'react';
import clsx from 'clsx';

type Tone = 'navy' | 'gold' | 'ok' | 'warn' | 'danger' | 'info' | 'neutral';

const tones: Record<Tone, string> = {
  navy: 'bg-navy-100 text-navy-800',
  gold: 'bg-gold-100 text-gold-600',
  ok: 'bg-ok-100 text-ok-600',
  warn: 'bg-warn-100 text-warn-600',
  danger: 'bg-danger-100 text-danger-600',
  info: 'bg-info-100 text-info-600',
  neutral: 'bg-paper-dim text-ink/60',
};

export function Badge({ tone = 'neutral', children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <span className={clsx('inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold', tones[tone], className)}>
      {children}
    </span>
  );
}
