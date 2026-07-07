import { useEffect, useState } from "react"
import { apiGet } from "../lib/api"
import type { SourceHealth } from "../lib/types"

function formatDate(value: string | null): string {
  if (!value) return "never"
  return new Date(value).toLocaleString()
}

export function Admin() {
  const [sources, setSources] = useState<SourceHealth[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    apiGet<SourceHealth[]>("/admin/sources").then(setSources).catch((err) => setError(err.message))
  }, [])

  if (error) return <div className="text-status-critical">{error}</div>

  return (
    <div className="flex flex-col gap-5">
      <h1 className="text-2xl font-semibold tracking-tight">Source Health</h1>

      <div className="overflow-hidden rounded-xl border border-gridline bg-surface-card">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gridline text-xs uppercase tracking-wide text-ink-muted">
            <tr>
              <th className="px-4 py-3 font-medium">Source</th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Topic</th>
              <th className="px-4 py-3 font-medium">Last success</th>
              <th className="px-4 py-3 font-medium">Errors</th>
              <th className="px-4 py-3 font-medium">Last error</th>
            </tr>
          </thead>
          <tbody>
            {sources?.map((source) => (
              <tr key={source.id} className="border-b border-gridline last:border-0">
                <td className="px-4 py-3 font-medium">{source.name}</td>
                <td className="px-4 py-3 text-ink-secondary uppercase text-xs">{source.type}</td>
                <td className="px-4 py-3 text-ink-secondary">{source.topic_label}</td>
                <td className="px-4 py-3 text-ink-secondary">{formatDate(source.last_success_at)}</td>
                <td className={`px-4 py-3 font-medium ${source.consecutive_error_count > 0 ? "text-status-critical" : "text-status-good"}`}>
                  {source.consecutive_error_count}
                </td>
                <td className="max-w-xs truncate px-4 py-3 text-xs text-ink-muted" title={source.last_error ?? ""}>
                  {source.last_error ?? "—"}
                </td>
              </tr>
            ))}
            {sources && sources.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-ink-muted">
                  No sources configured for this tenant yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
