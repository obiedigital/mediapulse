import { useEffect, useMemo, useState } from "react"
import {
  Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts"
import { apiGet } from "../lib/api"
import type { SentimentTrendPoint, ShareOfVoice as ShareOfVoiceData } from "../lib/types"
import { colorForEntity } from "../lib/chartColors"

export function ShareOfVoice() {
  const [sov, setSov] = useState<ShareOfVoiceData | null>(null)
  const [trend, setTrend] = useState<SentimentTrendPoint[] | null>(null)
  const [selectedBrand, setSelectedBrand] = useState<string>("")
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      apiGet<ShareOfVoiceData>("/analytics/share-of-voice"),
      apiGet<SentimentTrendPoint[]>("/analytics/sentiment-trend"),
    ])
      .then(([s, t]) => {
        setSov(s)
        setTrend(t)
        const firstBrand = Array.from(new Set(t.map((p) => p.brand)))[0]
        if (firstBrand) setSelectedBrand(firstBrand)
      })
      .catch((err) => setError(err.message))
  }, [])

  const brands = useMemo(() => Array.from(new Set(sov?.points.map((p) => p.brand) ?? [])), [sov])

  const sovChartData = useMemo(() => {
    if (!sov) return []
    const byDate = new Map<string, Record<string, number | string>>()
    for (const point of sov.points) {
      const row = byDate.get(point.date) ?? { date: point.date }
      row[point.brand] = point.mentions
      byDate.set(point.date, row)
    }
    return Array.from(byDate.values()).sort((a, b) => (a.date as string).localeCompare(b.date as string))
  }, [sov])

  const trendChartData = useMemo(
    () => (trend ?? []).filter((p) => p.brand === selectedBrand).sort((a, b) => a.date.localeCompare(b.date)),
    [trend, selectedBrand],
  )

  if (error) return <div className="text-status-critical">{error}</div>
  if (!sov) return <div className="text-ink-muted">Loading…</div>

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Share of Voice</h1>
        <p className="text-sm text-ink-muted">{sov.methodology_note}</p>
      </div>

      <section className="rounded-xl border border-gridline bg-surface-card p-5">
        <h2 className="mb-4 text-sm font-semibold">Mentions over time, by brand</h2>
        {sovChartData.length === 0 ? (
          <div className="py-12 text-center text-sm text-ink-muted">No classified coverage in this period yet.</div>
        ) : (
          <ResponsiveContainer width="100%" height={340}>
            <LineChart data={sovChartData} margin={{ top: 4, right: 12, left: -12, bottom: 4 }}>
              <CartesianGrid stroke="var(--gridline)" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 12, fill: "var(--ink-muted)" }} axisLine={{ stroke: "var(--gridline)" }} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: "var(--ink-muted)" }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip contentStyle={{ background: "var(--surface-card)", border: "1px solid var(--gridline)", borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {brands.map((brand) => (
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
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold">Sentiment trend by brand</h2>
          <select
            value={selectedBrand}
            onChange={(e) => setSelectedBrand(e.target.value)}
            className="rounded-lg border border-gridline bg-transparent px-2 py-1 text-sm outline-none focus:border-brand"
          >
            {Array.from(new Set((trend ?? []).map((p) => p.brand))).map((brand) => (
              <option key={brand} value={brand}>{brand}</option>
            ))}
          </select>
        </div>
        {trendChartData.length === 0 ? (
          <div className="py-12 text-center text-sm text-ink-muted">No per-brand sentiment data for this brand yet.</div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={trendChartData} margin={{ top: 4, right: 12, left: -12, bottom: 4 }}>
              <CartesianGrid stroke="var(--gridline)" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 12, fill: "var(--ink-muted)" }} axisLine={{ stroke: "var(--gridline)" }} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: "var(--ink-muted)" }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip contentStyle={{ background: "var(--surface-card)", border: "1px solid var(--gridline)", borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="positive" name="Positive" stackId="s" fill="var(--status-good)" />
              <Bar dataKey="neutral" name="Neutral" stackId="s" fill="var(--ink-muted)" />
              <Bar dataKey="negative" name="Negative" stackId="s" fill="var(--status-critical)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </section>
    </div>
  )
}
