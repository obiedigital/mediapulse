import { useState, type FormEvent } from "react"
import { Link, Navigate } from "react-router-dom"
import { useAuth } from "../lib/auth"
import { ApiError } from "../lib/api"
import "../marketing.css"

export function Login() {
  const { user, login, loading } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (!loading && user) return <Navigate to="/dashboard" replace />

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
    <div className="mp-marketing mp-auth-wrap">
      <div className="mp-card mp-auth-card">
        <div className="mp-auth-head">
          <span className="mp-logo-mark">MP</span>
          <div>
            <h1>Sign in to MediaPulse BW</h1>
            <p>Media intelligence dashboard</p>
          </div>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="mp-field">
            <label>Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@agency.bw"
              autoFocus
            />
          </div>
          <div className="mp-field">
            <label>Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>
          {error && <div className="mp-auth-error">{error}</div>}
          <button type="submit" disabled={submitting} className="mp-btn mp-btn-primary mp-btn-block">
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <div className="mp-auth-foot">
          <Link to="/">← Back to overview</Link>
        </div>
      </div>
    </div>
  )
}
