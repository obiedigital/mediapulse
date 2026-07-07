interface StatTileProps {
  label: string
  value: string | number
  caption?: string
  tone?: "default" | "good" | "warning" | "critical"
}

const TONE_CLASSES: Record<string, string> = {
  default: "text-ink-primary",
  good: "text-status-good",
  warning: "text-status-warning",
  critical: "text-status-critical",
}

export function StatTile({ label, value, caption, tone = "default" }: StatTileProps) {
  return (
    <div className="rounded-xl border border-gridline bg-surface-card p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-ink-muted">{label}</div>
      <div className={`mt-1.5 text-3xl font-semibold ${TONE_CLASSES[tone]}`}>{value}</div>
      {caption && <div className="mt-1 text-xs text-ink-secondary">{caption}</div>}
    </div>
  )
}
