import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { apiGet } from "../lib/api"
import { useAuth } from "../lib/auth"
import type { Brief, KPI } from "../lib/types"

function greeting() {
  const hour = new Date().getHours()
  if (hour < 12) return "Good morning"
  if (hour < 18) return "Good afternoon"
  return "Good evening"
}

export function ClientPortal() {
  const { user } = useAuth()
  const [kpi, setKpi] = useState<KPI | null>(null)
  const [latestBrief, setLatestBrief] = useState<Brief | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([apiGet<KPI>("/analytics/kpis"), apiGet<Brief[]>("/briefs?limit=1")])
      .then(([k, briefs]) => {
        setKpi(k)
        setLatestBrief(briefs[0] ?? null)
      })
      .catch((err) => setError(err.message))
  }, [])

  if (error) return <div className="text-status-critical">{error}</div>
  if (!kpi) return <div className="text-ink-muted">Loading…</div>

  const firstName = user?.name?.split(" ")[0] ?? "there"

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-8">
      <div>
        <p className="text-sm text-ink-muted">
          {greeting()}, {firstName}
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">Here's how coverage looks</h1>
        <p className="mt-1 text-sm text-ink-muted">
          {kpi.period_start} to {kpi.period_end} · {kpi.total_articles} stories tracked
        </p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-2xl border border-gridline bg-surface-card p-5 text-center">
          <div className="text-4xl font-bold text-status-good">{kpi.opportunity_count}</div>
          <div className="mt-1 text-sm font-medium text-ink-secondary">Opportunities</div>
        </div>
        <div className="rounded-2xl border border-gridline bg-surface-card p-5 text-center">
          <div className="text-4xl font-bold text-status-warning">{kpi.monitor_count}</div>
          <div className="mt-1 text-sm font-medium text-ink-secondary">Worth watching</div>
        </div>
        <div className="rounded-2xl border border-gridline bg-surface-card p-5 text-center">
          <div className="text-4xl font-bold text-status-critical">{kpi.risk_count}</div>
          <div className="mt-1 text-sm font-medium text-ink-secondary">Risks</div>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-gridline bg-surface-card">
        <div className="bg-brand/10 px-6 py-4">
          <span className="text-xs font-semibold tracking-wide text-brand uppercase">Today's brief</span>
        </div>
        {latestBrief ? (
          <div className="flex items-center justify-between gap-4 px-6 py-6">
            <div>
              <div className="text-lg font-semibold capitalize">{latestBrief.brief_type} brief</div>
              <div className="text-sm text-ink-muted">
                {new Date(latestBrief.period_start).toLocaleDateString()} –{" "}
                {new Date(latestBrief.period_end).toLocaleDateString()}
              </div>
            </div>
            <Link
              to="/briefs"
              className="shrink-0 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-black transition-opacity hover:opacity-90"
            >
              Read brief
            </Link>
          </div>
        ) : (
          <div className="px-6 py-8 text-center text-sm text-ink-muted">
            Your first Daily Brief will appear here once it's generated.
          </div>
        )}
      </div>

      <p className="text-center text-xs text-ink-muted">
        Want the full analyst view — story feed, share of voice, Ask MediaPulse? That's available to your
        strategist team.
      </p>
    </div>
  )
}
