import { useState, type FormEvent } from "react"
import { Navigate } from "react-router-dom"
import { useAuth } from "../lib/auth"
import { ApiError } from "../lib/api"

export function Login() {
  const { user, login, loading } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (!loading && user) return <Navigate to="/" replace />

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-page px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand text-base font-bold text-black">
            MP
          </span>
          <div className="text-center">
            <div className="text-lg font-semibold tracking-tight">MediaPulse BW</div>
            <div className="text-sm text-ink-muted">Media intelligence dashboard</div>
          </div>
        </div>
        <form
          onSubmit={handleSubmit}
          className="rounded-xl border border-gridline bg-surface-card p-6 shadow-sm"
        >
          <label className="mb-1 block text-xs font-medium text-ink-secondary">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mb-4 w-full rounded-lg border border-gridline bg-transparent px-3 py-2 text-sm outline-none focus:border-brand"
            placeholder="you@agency.bw"
          />
          <label className="mb-1 block text-xs font-medium text-ink-secondary">Password</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mb-4 w-full rounded-lg border border-gridline bg-transparent px-3 py-2 text-sm outline-none focus:border-brand"
            placeholder="••••••••"
          />
          {error && <div className="mb-4 text-sm text-status-critical">{error}</div>}
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-brand py-2 text-sm font-semibold text-black transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  )
}
