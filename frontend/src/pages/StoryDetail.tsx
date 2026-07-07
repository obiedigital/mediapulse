import { useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { apiGet } from "../lib/api"
import type { ArticleDetail } from "../lib/types"
import { SentimentBadge, StatusPill, ThreatBadge } from "../components/Badges"

export function StoryDetail() {
  const { id } = useParams<{ id: string }>()
  const [article, setArticle] = useState<ArticleDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    apiGet<ArticleDetail>(`/articles/${id}`)
      .then(setArticle)
      .catch((err) => setError(err.message))
  }, [id])

  if (error) return <div className="text-status-critical">{error}</div>
  if (!article) return <div className="text-ink-muted">Loading…</div>

  const entityGroups = Object.entries(article.entities).filter(([, values]) => values.length > 0)

  return (
    <div className="flex flex-col gap-6">
      <Link to="/feed" className="text-sm text-ink-secondary hover:text-brand">
        ← Back to feed
      </Link>

      <div>
        <div className="mb-2 flex items-center gap-3 text-xs text-ink-muted">
          <span>{article.publication}</span>
          <span>·</span>
          <span>{new Date(article.published_at).toLocaleDateString()}</span>
          {article.published_at_confidence === "low" && (
            <span className="text-status-warning">low-confidence date</span>
          )}
          {article.byline && <><span>·</span><span>{article.byline}</span></>}
        </div>
        <h1 className="text-2xl font-semibold tracking-tight">{article.title}</h1>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <SentimentBadge sentiment={article.sentiment_overall} />
          <ThreatBadge tag={article.threat_tag} />
          <StatusPill status={article.status} />
          {article.category && (
            <span className="text-xs capitalize text-ink-muted">{article.category}</span>
          )}
          {article.url && (
            <a href={article.url} target="_blank" rel="noreferrer" className="text-xs text-brand hover:underline">
              Original source ↗
            </a>
          )}
        </div>
      </div>

      {article.summary_exec && (
        <section className="rounded-xl border border-gridline bg-surface-card p-5">
          <h2 className="mb-2 text-sm font-semibold">Executive summary</h2>
          <p className="text-sm text-ink-secondary">{article.summary_exec}</p>
        </section>
      )}

      {article.why_it_matters && (
        <section className="rounded-xl border border-gridline bg-surface-card p-5">
          <h2 className="mb-2 text-sm font-semibold">Why it matters</h2>
          <p className="text-sm text-ink-secondary">{article.why_it_matters}</p>
          {article.threat_rationale && (
            <p className="mt-2 text-xs text-ink-muted">{article.threat_rationale}</p>
          )}
        </section>
      )}

      {Object.keys(article.sentiment_by_brand).length > 0 && (
        <section className="rounded-xl border border-gridline bg-surface-card p-5">
          <h2 className="mb-3 text-sm font-semibold">Sentiment by brand</h2>
          <div className="flex flex-wrap gap-2">
            {Object.entries(article.sentiment_by_brand).map(([brand, sentiment]) => (
              <div key={brand} className="flex items-center gap-2 rounded-lg border border-gridline px-3 py-1.5">
                <span className="text-sm font-medium">{brand}</span>
                <SentimentBadge sentiment={sentiment} />
              </div>
            ))}
          </div>
        </section>
      )}

      {article.key_quotes.length > 0 && (
        <section className="rounded-xl border border-gridline bg-surface-card p-5">
          <h2 className="mb-3 text-sm font-semibold">Key quotes</h2>
          <ul className="flex flex-col gap-2">
            {article.key_quotes.map((quote, i) => (
              <li key={i} className="border-l-2 border-brand pl-3 text-sm italic text-ink-secondary">
                {quote}
              </li>
            ))}
          </ul>
        </section>
      )}

      {entityGroups.length > 0 && (
        <section className="rounded-xl border border-gridline bg-surface-card p-5">
          <h2 className="mb-3 text-sm font-semibold">Entities</h2>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
            {entityGroups.map(([kind, values]) => (
              <div key={kind}>
                <div className="mb-1 text-xs font-medium uppercase tracking-wide text-ink-muted">{kind}</div>
                <div className="text-sm text-ink-secondary">{values.join(", ")}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="rounded-xl border border-gridline bg-surface-card p-5">
        <h2 className="mb-3 text-sm font-semibold">Full text</h2>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink-secondary">{article.raw_text}</p>
      </section>
    </div>
  )
}
