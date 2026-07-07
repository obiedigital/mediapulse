import { useEffect, useMemo, useState } from "react"
import {
  CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
  Bar, BarChart,
} from "recharts"
import { apiGet } from "../lib/api"
import type { KPI, ShareOfVoice, TopicMixPoint } from "../lib/types"
import { StatTile } from "../components/StatTile"
import { colorForEntity } from "../lib/chartColors"

export function Overview() {
  const [kpi, setKpi] = useState<KPI | null>(null)
  const [sov, setSov] = useState<ShareOfVoice | null>(null)
  const [topicMix, setTopicMix] = useState<TopicMixPoint[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      apiGet<KPI>("/analytics/kpis"),
      apiGet<ShareOfVoice>("/analytics/share-of-voice"),
      apiGet<TopicMixPoint[]>("/analytics/topic-mix"),
    ])
      .then(([k, s, t]) => {
        setKpi(k)
        setSov(s)
        setTopicMix(t)
      })
      .catch((err) => setError(err.message))
  }, [])

  const topicMixRows = useMemo(
    () =>
      (topicMix ?? []).map((point) => ({
        ...point,
        label: point.category ? `${point.topic_label} · ${point.category}` : point.topic_label,
      })),
    [topicMix],
  )

  const sovSeries = useMemo(() => {
    if (!sov) return { data: [], brands: [] as string[] }
    const brands = Array.from(new Set(sov.points.map((p) => p.brand)))
    const byDate = new Map<string, Record<string, number | string>>()
    for (const point of sov.points) {
      const row = byDate.get(point.date) ?? { date: point.date }
      row[point.brand] = point.mentions
      byDate.set(point.date, row)
    }
    return { data: Array.from(byDate.values()).sort((a, b) => (a.date as string).localeCompare(b.date as string)), brands }
  }, [sov])

  if (error) return <div className="text-status-critical">{error}</div>
  if (!kpi) return <div className="text-ink-muted">Loading…</div>

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Overview</h1>
        <p className="text-sm text-ink-muted">
          {kpi.period_start} to {kpi.period_end}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatTile label="Total coverage" value={kpi.total_articles} />
        <StatTile label="Classified" value={kpi.classified_count} />
        <StatTile label="Pending analysis" value={kpi.pending_count} />
        <StatTile
          label="Errors"
          value={kpi.error_count}
          tone={kpi.error_count > 0 ? "critical" : "default"}
        />
        <StatTile
          label="Opportunities"
          value={kpi.opportunity_count}
          tone="good"
        />
        <StatTile label="Monitor" value={kpi.monitor_count} tone="warning" />
        <StatTile
          label="Risks"
          value={kpi.risk_count}
          tone={kpi.risk_count > 0 ? "critical" : "default"}
        />
        <StatTile
          label="Avg. relevance"
          value={kpi.avg_relevance !== null ? kpi.avg_relevance.toFixed(2) : "—"}
        />
      </div>

      <section className="rounded-xl border border-gridline bg-surface-card p-5">
        <h2 className="mb-1 text-sm font-semibold">Share of voice</h2>
        <p className="mb-4 text-xs text-ink-muted">{sov?.methodology_note}</p>
        {sovSeries.data.length === 0 ? (
          <div className="py-12 text-center text-sm text-ink-muted">No classified coverage in this period yet.</div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={sovSeries.data} margin={{ top: 4, right: 12, left: -12, bottom: 4 }}>
              <CartesianGrid stroke="var(--gridline)" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 12, fill: "var(--ink-muted)" }} axisLine={{ stroke: "var(--gridline)" }} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: "var(--ink-muted)" }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip
                contentStyle={{ background: "var(--surface-card)", border: "1px solid var(--gridline)", borderRadius: 8, fontSize: 12 }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {sovSeries.brands.map((brand) => (
                <Line
                  key={brand}
                  type="monotone"
                  dataKey={brand}
                  name={brand}
                  stroke={colorForEntity(brand)}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </section>

      <section className="rounded-xl border border-gridline bg-surface-card p-5">
        <h2 className="mb-4 text-sm font-semibold">Topic mix</h2>
        {!topicMix || topicMix.length === 0 ? (
          <div className="py-12 text-center text-sm text-ink-muted">No coverage in this period yet.</div>
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(160, topicMix.length * 44)}>
            <BarChart data={topicMixRows} layout="vertical" margin={{ top: 4, right: 24, left: 12, bottom: 4 }}>
              <CartesianGrid stroke="var(--gridline)" horizontal={false} />
              <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12, fill: "var(--ink-muted)" }} axisLine={false} tickLine={false} />
              <YAxis
                type="category"
                dataKey="label"
                width={200}
                tick={{ fontSize: 12, fill: "var(--ink-secondary)" }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{ background: "var(--surface-card)", border: "1px solid var(--gridline)", borderRadius: 8, fontSize: 12 }}
              />
              <Bar dataKey="count" fill="var(--series-1)" radius={[0, 4, 4, 0]} maxBarSize={20} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </section>
    </div>
  )
}
