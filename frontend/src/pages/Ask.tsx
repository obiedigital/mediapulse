import { useState, type FormEvent } from "react"
import { Link } from "react-router-dom"
import { apiPost, ApiError } from "../lib/api"
import type { AskResponse } from "../lib/types"

interface Turn {
  question: string
  answer: string
  citations: AskResponse["citations"]
  error?: string
}

export function Ask() {
  const [question, setQuestion] = useState("")
  const [turns, setTurns] = useState<Turn[]>([])
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const q = question.trim()
    if (!q || loading) return
    setLoading(true)
    setQuestion("")
    try {
      const result = await apiPost<AskResponse>("/ask", { question: q })
      setTurns((prev) => [...prev, { question: q, answer: result.answer, citations: result.citations }])
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Something went wrong"
      setTurns((prev) => [...prev, { question: q, answer: "", citations: [], error: message }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Ask MediaPulse</h1>
        <p className="text-sm text-ink-muted">
          Ask a question over your monitored coverage — answers cite the stored articles used.
        </p>
      </div>

      <div className="flex flex-col gap-4">
        {turns.length === 0 && (
          <div className="rounded-xl border border-dashed border-gridline p-10 text-center text-sm text-ink-muted">
            Try: &ldquo;How did coverage of Orange Money compare to Smega this quarter?&rdquo;
          </div>
        )}
        {turns.map((turn, i) => (
          <div key={i} className="rounded-xl border border-gridline bg-surface-card p-5">
            <div className="mb-2 text-sm font-semibold text-ink-primary">{turn.question}</div>
            {turn.error ? (
              <div className="text-sm text-status-critical">{turn.error}</div>
            ) : (
              <>
                <p className="text-sm leading-relaxed text-ink-secondary">{turn.answer}</p>
                {turn.citations.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {turn.citations.map((c) => (
                      <Link
                        key={c.article_id}
                        to={`/feed/${c.article_id}`}
                        className="rounded-full border border-gridline px-2.5 py-1 text-xs text-ink-secondary hover:border-brand hover:text-brand"
                      >
                        {c.title}
                      </Link>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        ))}
        {loading && <div className="text-sm text-ink-muted">Thinking…</div>}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about your coverage…"
          className="flex-1 rounded-lg border border-gridline bg-transparent px-3 py-2 text-sm outline-none focus:border-brand"
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-black disabled:opacity-50"
        >
          Ask
        </button>
      </form>
    </div>
  )
}
