import { sentimentColor, threatColor } from "../lib/chartColors"

function Dot({ color }: { color: string }) {
  return (
    <span
      className="inline-block h-2 w-2 rounded-full shrink-0"
      style={{ backgroundColor: color }}
    />
  )
}

export function SentimentBadge({ sentiment }: { sentiment: string | null }) {
  if (!sentiment) {
    return <span className="text-xs text-ink-muted">Pending analysis</span>
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-gridline px-2 py-0.5 text-xs font-medium capitalize text-ink-secondary">
      <Dot color={sentimentColor(sentiment)} />
      {sentiment}
    </span>
  )
}

export function ThreatBadge({ tag }: { tag: string | null }) {
  if (!tag) {
    return <span className="text-xs text-ink-muted">—</span>
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-gridline px-2 py-0.5 text-xs font-medium capitalize text-ink-secondary">
      <Dot color={threatColor(tag)} />
      {tag}
    </span>
  )
}

export function StatusPill({ status }: { status: string }) {
  const label = status.replace(/_/g, " ")
  const tone =
    status === "error" ? "text-status-critical" :
    status === "needs_review" ? "text-status-warning" :
    status === "classified" ? "text-status-good" :
    "text-ink-muted"
  return <span className={`text-xs font-medium capitalize ${tone}`}>{label}</span>
}
