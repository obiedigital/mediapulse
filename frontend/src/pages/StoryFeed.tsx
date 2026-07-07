import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { apiGet, downloadCsv } from "../lib/api"
import type { ArticleListResponse } from "../lib/types"
import { SentimentBadge, StatusPill, ThreatBadge } from "../components/Badges"

const PAGE_SIZE = 20

export function StoryFeed() {
  const [data, setData] = useState<ArticleListResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [offset, setOffset] = useState(0)
  const [search, setSearch] = useState("")
  const [sentiment, setSentiment] = useState("")
  const [status, setStatus] = useState("")

  const filters = { search: search || undefined, sentiment: sentiment || undefined, status: status || undefined }

  useEffect(() => {
    apiGet<ArticleListResponse>("/articles", { ...filters, limit: PAGE_SIZE, offset })
      .then(setData)
      .catch((err) => setError(err.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, sentiment, status, offset])

  function resetAndSet(setter: (v: string) => void) {
    return (v: string) => {
      setter(v)
      setOffset(0)
    }
  }

  if (error) return <div className="text-status-critical">{error}</div>

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Story Feed</h1>
        <button
          onClick={() => downloadCsv("/articles/export.csv", filters as Record<string, string>, "articles.csv")}
          className="rounded-lg border border-gridline px-3 py-1.5 text-sm font-medium hover:bg-gridline/30"
        >
          Export CSV
        </button>
      </div>

      <div className="flex flex-wrap gap-3">
        <input
          value={search}
          onChange={(e) => resetAndSet(setSearch)(e.target.value)}
          placeholder="Search titles…"
          className="rounded-lg border border-gridline bg-transparent px-3 py-1.5 text-sm outline-none focus:border-brand"
        />
        <select
          value={sentiment}
          onChange={(e) => resetAndSet(setSentiment)(e.target.value)}
          className="rounded-lg border border-gridline bg-transparent px-3 py-1.5 text-sm outline-none focus:border-brand"
        >
          <option value="">All sentiment</option>
          <option value="positive">Positive</option>
          <option value="neutral">Neutral</option>
          <option value="negative">Negative</option>
        </select>
        <select
          value={status}
          onChange={(e) => resetAndSet(setStatus)(e.target.value)}
          className="rounded-lg border border-gridline bg-transparent px-3 py-1.5 text-sm outline-none focus:border-brand"
        >
          <option value="">All statuses</option>
          <option value="new">New</option>
          <option value="classified">Classified</option>
          <option value="needs_review">Needs review</option>
          <option value="error">Error</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      <div className="overflow-hidden rounded-xl border border-gridline bg-surface-card">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gridline text-xs uppercase tracking-wide text-ink-muted">
            <tr>
              <th className="px-4 py-3 font-medium">Story</th>
              <th className="px-4 py-3 font-medium">Publication</th>
              <th className="px-4 py-3 font-medium">Date</th>
              <th className="px-4 py-3 font-medium">Sentiment</th>
              <th className="px-4 py-3 font-medium">Threat</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((item) => (
              <tr key={item.id} className="border-b border-gridline last:border-0 hover:bg-gridline/20">
                <td className="max-w-md px-4 py-3">
                  <Link to={`/feed/${item.id}`} className="font-medium text-ink-primary hover:text-brand">
                    {item.title}
                  </Link>
                  {item.pickup_count > 1 && (
                    <span className="ml-2 text-xs text-ink-muted">+{item.pickup_count - 1} pickups</span>
                  )}
                </td>
                <td className="px-4 py-3 text-ink-secondary">{item.publication}</td>
                <td className="px-4 py-3 text-ink-secondary">
                  {new Date(item.published_at).toLocaleDateString()}
                  {item.published_at_confidence === "low" && (
                    <span className="ml-1 text-status-warning" title="Low-confidence date">•</span>
                  )}
                </td>
                <td className="px-4 py-3"><SentimentBadge sentiment={item.sentiment_overall} /></td>
                <td className="px-4 py-3"><ThreatBadge tag={item.threat_tag} /></td>
                <td className="px-4 py-3"><StatusPill status={item.status} /></td>
              </tr>
            ))}
            {data && data.items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-ink-muted">
                  No stories match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {data && data.total > PAGE_SIZE && (
        <div className="flex items-center justify-between text-sm text-ink-secondary">
          <span>
            {offset + 1}–{Math.min(offset + PAGE_SIZE, data.total)} of {data.total}
          </span>
          <div className="flex gap-2">
            <button
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              className="rounded-lg border border-gridline px-3 py-1 disabled:opacity-40"
            >
              Previous
            </button>
            <button
              disabled={offset + PAGE_SIZE >= data.total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
              className="rounded-lg border border-gridline px-3 py-1 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
