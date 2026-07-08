import { Link } from "react-router-dom"
import "../marketing.css"

const FEATURES = [
  {
    icon: "◈",
    title: "AI classification",
    body: "Claude reads every article and tags sentiment, entities and brand mentions per-tenant — no keyword lists to maintain.",
  },
  {
    icon: "▤",
    title: "Layout-aware ingestion",
    body: "Print PDFs are segmented by column and font-size heuristics, with a vision-model fallback for pages that defeat text extraction.",
  },
  {
    icon: "✎",
    title: "Daily Brief",
    body: "A synthesized, agency-register brief lands in your inbox every morning as HTML and PDF — no analyst required to assemble it.",
  },
  {
    icon: "◎",
    title: "Ask MediaPulse",
    body: "Ask plain-language questions about the last 90 days of coverage and get answers grounded in the actual corpus, with citations.",
  },
  {
    icon: "▲",
    title: "Alerts",
    body: "Negative sentiment spikes, competitor launches, regulator announcements and volume anomalies surface the moment they're detected.",
  },
  {
    icon: "▣",
    title: "Client portal",
    body: "A read-only, zero-data-plumbing view for stakeholders who just want the brief and the numbers — not the newsroom underneath it.",
  },
]

const METRICS = [
  { num: "24/7", label: "unattended monitoring" },
  { num: "<15m", label: "classification cadence" },
  { num: "4", label: "alert types watched" },
  { num: "90d", label: "corpus window for Ask" },
]

export function Landing() {
  return (
    <div className="mp-marketing">
      <header className="mp-nav">
        <div className="mp-nav-inner">
          <div className="mp-logo">
            <span className="mp-logo-mark">MP</span>
            <span className="mp-brandmark">MediaPulse BW</span>
          </div>
          <Link to="/login" className="mp-btn mp-btn-primary">
            Sign in
          </Link>
        </div>
      </header>

      <section className="mp-hero">
        <div>
          <span className="mp-eyebrow">AI media intelligence · Botswana</span>
          <h1>
            Know what's being<br />said about you, <span className="mp-grad-text">before it spreads</span>.
          </h1>
          <p>
            MediaPulse BW ingests print, online and broadcast coverage, classifies it with
            Claude, and turns it into a brief your team can act on — every single day,
            without a newsroom.
          </p>
          <div className="mp-hero-ctas">
            <Link to="/login" className="mp-btn mp-btn-primary">
              Sign in to your dashboard
            </Link>
            <a href="#features" className="mp-btn mp-btn-ghost">
              See how it works
            </a>
          </div>
        </div>
        <div>
          <div className="mp-card mp-signal-card">
            <div className="mp-signal-top">
              <div>
                <span className="mp-num">12</span>
                <div className="mp-muted" style={{ fontSize: 12.5 }}>
                  new stories today
                </div>
              </div>
              <span className="mp-pill mp-pill-risk">Risk</span>
            </div>
            <div className="mp-muted" style={{ fontSize: 13.5 }}>
              Orange Money outage coverage spiking across 3 outlets
            </div>
          </div>
          <div className="mp-card mp-signal-card">
            <div className="mp-signal-top">
              <div>
                <span className="mp-num">+18%</span>
                <div className="mp-muted" style={{ fontSize: 12.5 }}>
                  share of voice, week over week
                </div>
              </div>
              <span className="mp-pill mp-pill-opportunity">Opportunity</span>
            </div>
            <div className="mp-muted" style={{ fontSize: 13.5 }}>
              Network expansion story picked up nationally
            </div>
          </div>
          <div className="mp-card mp-signal-card" style={{ marginBottom: 0 }}>
            <div className="mp-signal-top">
              <div>
                <span className="mp-num">1</span>
                <div className="mp-muted" style={{ fontSize: 12.5 }}>
                  regulator announcement flagged
                </div>
              </div>
              <span className="mp-pill mp-pill-monitor">Monitor</span>
            </div>
            <div className="mp-muted" style={{ fontSize: 13.5 }}>
              BOCRA statement on spectrum allocation
            </div>
          </div>
        </div>
      </section>

      <div className="mp-metrics-band">
        {METRICS.map((m) => (
          <div className="mp-metric" key={m.label}>
            <span className="mp-num">{m.num}</span>
            <span>{m.label}</span>
          </div>
        ))}
      </div>

      <section className="mp-section" id="features">
        <div className="mp-section-head">
          <span className="mp-eyebrow">The pipeline</span>
          <h2>From raw coverage to a brief you can act on</h2>
          <p>
            Every piece runs unattended: ingestion, classification, synthesis and delivery,
            scoped per tenant with your house style and brand list baked in.
          </p>
        </div>
        <div className="mp-feat-grid">
          {FEATURES.map((f) => (
            <div className="mp-card mp-feat-cell" key={f.title}>
              <div className="mp-feat-icon">{f.icon}</div>
              <h4>{f.title}</h4>
              <p>{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mp-footer-cta">
        <h2>Ready to see your coverage?</h2>
        <p>Sign in with your MediaPulse BW account to open your dashboard.</p>
        <Link to="/login" className="mp-btn mp-btn-primary">
          Sign in
        </Link>
      </section>

      <footer className="mp-footer">MediaPulse BW · media intelligence for Orange Botswana</footer>
    </div>
  )
}
