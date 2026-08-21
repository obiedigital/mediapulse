export function ProgressBar({ value, tone = 'navy' }: { value: number; tone?: 'navy' | 'gold' | 'ok' | 'danger' }) {
  const colors: Record<string, string> = {
    navy: 'bg-navy-700',
    gold: 'bg-gold-500',
    ok: 'bg-ok-600',
    danger: 'bg-danger-600',
  };
  return (
    <div className="h-1.5 w-full rounded-full bg-paper-dim overflow-hidden">
      <div className={`h-full rounded-full ${colors[tone]}`} style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
    </div>
  );
}
