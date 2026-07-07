import { useEffect, useState } from "react"
import { apiGet } from "../lib/api"
import type { Brief } from "../lib/types"

export function Briefs() {
  const [briefs, setBriefs] = useState<Brief[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    apiGet<Brief[]>("/briefs").then(setBriefs).catch((err) => setError(err.message))
  }, [])

  if (error) return <div className="text-status-critical">{error}</div>

  return (
    <div className="flex flex-col gap-5">
      <h1 className="text-2xl font-semibold tracking-tight">Daily Brief Archive</h1>

      {briefs && briefs.length === 0 && (
        <div className="rounded-xl border border-dashed border-gridline p-10 text-center text-sm text-ink-muted">
          No briefs have been generated yet. Automated Daily Brief generation lands in a later milestone —
          check back once the first brief has run.
        </div>
      )}

      {briefs && briefs.length > 0 && (
        <div className="flex flex-col gap-2">
          {briefs.map((brief) => (
            <div key={brief.id} className="flex items-center justify-between rounded-xl border border-gridline bg-surface-card p-4">
              <div>
                <div className="text-sm font-medium capitalize">{brief.brief_type} brief</div>
                <div className="text-xs text-ink-muted">
                  {new Date(brief.period_start).toLocaleDateString()} – {new Date(brief.period_end).toLocaleDateString()}
                </div>
              </div>
              <span className="text-xs capitalize text-ink-secondary">{brief.status}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
