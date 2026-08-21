import { Link } from 'react-router-dom';
import {
  FolderOpen,
  ScanLine,
  Workflow,
  FileSignature,
  ShieldCheck,
  Car,
  Users,
  Umbrella,
  Landmark,
  ArrowRight,
  Check,
  Star,
  Smartphone,
  Mail,
  Printer,
  Sparkles,
} from 'lucide-react';
import { Nav } from '../../components/marketing/Nav';
import { Footer } from '../../components/marketing/Footer';

const MODULES = [
  {
    icon: FolderOpen,
    title: 'Document Manager',
    desc: 'Every contract, invoice and record in one searchable cloud cabinet — with folders, tags, versioning and granular permissions.',
    span: true,
  },
  {
    icon: ScanLine,
    title: 'Smart Scan',
    desc: 'Scan from mobile, network scanner or email. Filed reads and classifies each document into the right folder automatically.',
  },
  {
    icon: Workflow,
    title: 'Workflow Automation',
    desc: 'Approval chains, conditional routing and email notifications — no more paper trails chasing signatures.',
  },
  {
    icon: FileSignature,
    title: 'eSignature & Forms',
    desc: 'Build branded forms, capture submissions, and send documents for legally binding eSignature in minutes.',
  },
  {
    icon: ShieldCheck,
    title: 'Compliance & Retention',
    desc: 'POPIA, FICA and FSCA-aligned retention rules, audit trails and consent registers built in.',
    span: true,
  },
];

const INDUSTRIES = [
  { icon: Car, name: 'Automotive Dealerships', desc: 'Deal files, FICA packs, RICA and trade-in paperwork filed the moment a sale closes.' },
  { icon: Users, name: 'HR & Payroll', desc: 'Contracts, payslips and leave forms — signed, filed and POPIA-compliant automatically.' },
  { icon: Umbrella, name: 'Insurance & Broking', desc: 'Claims intake and policy documents routed through FSCA-aligned approval workflows.' },
  { icon: Landmark, name: 'Finance & SARS', desc: 'Supplier invoices, VAT returns and audit packs organised and instantly retrievable.' },
];

const STEPS = [
  { n: '01', icon: Smartphone, title: 'Capture', desc: 'Snap a photo, scan a batch, or forward an email — paperwork enters the cabinet from anywhere.' },
  { n: '02', icon: Sparkles, title: 'Classify', desc: 'Filed reads each document and files it into the right folder with the right tags, automatically.' },
  { n: '03', icon: Workflow, title: 'Automate', desc: 'Approval workflows route documents to the right person, with reminders until it is actioned.' },
  { n: '04', icon: FileSignature, title: 'Close out', desc: 'Send for eSignature, archive on schedule, and pull audit-ready reports in one click.' },
];

const TESTIMONIALS = [
  {
    quote: 'We went from a filing room full of deal jackets to a fully searchable cabinet. FICA packs that took 20 minutes to find now take ten seconds.',
    name: 'Johan Pretorius',
    role: 'Dealership Operations Manager, Rand Auto Group',
  },
  {
    quote: 'Onboarding used to mean printing an offer letter, chasing a signature, then scanning it back in. Now the whole thing happens before lunch.',
    name: 'Thandiwe Nkosi',
    role: 'HR Business Partner, Rand Auto Group',
  },
  {
    quote: 'Our POPIA audit went from a two-week scramble to a report we exported in an afternoon. The retention rules just work.',
    name: 'Naledi Mokoena',
    role: 'IT & Compliance Lead, Rand Auto Group',
  },
];

const PRICING = [
  {
    tier: 'Starter',
    price: 'R690',
    note: 'per user / month',
    features: ['Up to 10 users', '50 GB document storage', 'Smart Scan (mobile + email)', '2 active workflows', 'Standard support'],
  },
  {
    tier: 'Business',
    price: 'R1,190',
    note: 'per user / month',
    featured: true,
    features: [
      'Up to 100 users',
      '500 GB document storage',
      'Smart Scan + network scanner intake',
      'Unlimited workflows & eSignature',
      'POPIA / FICA compliance suite',
      'Priority support',
    ],
  },
  {
    tier: 'Enterprise',
    price: 'Custom',
    note: 'volume pricing',
    features: ['Unlimited users & storage', 'Custom workflow development', 'Dedicated compliance officer', 'SSO & audit API', 'Onboarding & migration team'],
  },
];

export function Landing() {
  return (
    <div className="bg-paper">
      <Nav />

      {/* HERO */}
      <section className="mx-auto grid max-w-[1240px] grid-cols-1 items-center gap-12 px-5 pb-16 pt-16 md:grid-cols-[1.1fr_0.9fr] md:px-8 md:pt-24">
        <div>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-gold-500/30 bg-gold-50 px-3.5 py-1.5 text-[12px] font-semibold text-gold-600">
            🇿🇦 South Africa's paperless office platform
          </div>
          <h1 className="font-display text-[38px] font-extrabold leading-[1.08] tracking-tight text-ink md:text-[54px]">
            Every document.
            <br />
            Filed, signed<span className="text-gold-500">, </span>
            <span className="bg-gradient-to-r from-navy-800 to-gold-600 bg-clip-text text-transparent">automatically.</span>
          </h1>
          <p className="mt-5 max-w-lg text-[15.5px] leading-relaxed text-ink/60">
            Filed scans, classifies and files every contract, invoice and form your business handles — then routes it
            for approval and signature, so nothing sits in a tray or an inbox again.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              to="/login"
              className="inline-flex items-center gap-2 rounded-xl bg-navy-800 px-5 py-3.5 text-[14px] font-semibold text-white hover:bg-navy-700 transition-colors"
            >
              See the platform <ArrowRight size={16} />
            </Link>
            <a
              href="#how"
              className="inline-flex items-center gap-2 rounded-xl border border-line bg-surface px-5 py-3.5 text-[14px] font-semibold text-ink hover:bg-navy-50 transition-colors"
            >
              How it works
            </a>
          </div>
          <div className="mt-9 flex items-center gap-3">
            <div className="flex -space-x-2">
              {['NM', 'JP', 'TN', 'RW'].map((i) => (
                <div key={i} className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-paper bg-navy-100 text-[10.5px] font-bold text-navy-800">
                  {i}
                </div>
              ))}
            </div>
            <span className="text-[12.5px] text-ink/50">Trusted by dealerships, brokers and HR teams across SA</span>
          </div>
        </div>

        <div className="rounded-2xl border border-line bg-surface p-3 shadow-2xl shadow-navy-900/10">
          <div className="flex items-center gap-1.5 rounded-t-xl bg-paper-dim px-3 py-2.5">
            <span className="h-2.5 w-2.5 rounded-full bg-line" />
            <span className="h-2.5 w-2.5 rounded-full bg-line" />
            <span className="h-2.5 w-2.5 rounded-full bg-line" />
            <span className="ml-2 flex-1 rounded bg-surface px-2.5 py-1 text-center text-[10.5px] text-ink/40">app.filed.co.za/documents</span>
          </div>
          <div className="p-4">
            <div className="mb-3 flex items-center justify-between">
              <span className="font-display text-[13px] font-bold text-ink">FICA & RICA</span>
              <span className="text-[10.5px] text-ink/40">212 documents</span>
            </div>
            {[
              { name: 'ID Copy - W. Botha.jpg', tag: 'Scanned 2 min ago', tone: 'gold' },
              { name: 'FICA Pack - S. Naidoo.pdf', tag: 'Pending review', tone: 'warn' },
              { name: 'Deal File - VW Polo - B. Khumalo.pdf', tag: 'Signed & filed', tone: 'ok' },
              { name: 'Trade-In Valuation - Ford Ranger.pdf', tag: 'Filed', tone: 'navy' },
            ].map((r) => (
              <div key={r.name} className="mb-2 flex items-center gap-3 rounded-lg border border-line-soft bg-paper px-3 py-2.5">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-navy-50 text-navy-700">
                  <FolderOpen size={14} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[12px] font-medium text-ink">{r.name}</p>
                  <p className="text-[10.5px] text-ink/45">{r.tag}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CAPTURE STRIP */}
      <div className="border-y border-line bg-navy-950 py-5">
        <div className="mx-auto flex max-w-[1240px] flex-wrap items-center justify-center gap-x-10 gap-y-3 px-5 text-[12.5px] font-semibold text-white/50 md:px-8">
          <span className="flex items-center gap-2"><Smartphone size={14} /> Mobile capture</span>
          <span className="flex items-center gap-2"><Printer size={14} /> Network scanners</span>
          <span className="flex items-center gap-2"><Mail size={14} /> Email import</span>
          <span className="flex items-center gap-2"><ScanLine size={14} /> Bulk digitisation</span>
          <span className="flex items-center gap-2"><ShieldCheck size={14} /> POPIA / FICA / FSCA aligned</span>
        </div>
      </div>

      {/* MODULES */}
      <section id="platform" className="mx-auto max-w-[1240px] px-5 py-20 md:px-8">
        <div className="mb-10 max-w-xl">
          <div className="mb-3 inline-block rounded-full bg-navy-100 px-3 py-1 text-[11.5px] font-semibold text-navy-800">The platform</div>
          <h2 className="font-display text-[30px] font-extrabold tracking-tight text-ink md:text-[34px]">One cabinet, four modules.</h2>
          <p className="mt-2.5 text-[14.5px] leading-relaxed text-ink/55">
            Filed replaces the filing room, the fax machine and the approvals-by-email chain with one connected system.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {MODULES.map((m) => (
            <div
              key={m.title}
              className={`flex flex-col justify-end rounded-2xl border border-line bg-surface p-6 min-h-[180px] hover:border-navy-600/30 transition-colors ${
                m.span ? 'lg:col-span-1' : ''
              }`}
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-gold-100 text-gold-600">
                <m.icon size={19} />
              </div>
              <h4 className="font-display text-[15.5px] font-bold text-ink">{m.title}</h4>
              <p className="mt-1.5 text-[13px] leading-relaxed text-ink/55">{m.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* METRICS BAND */}
      <div className="border-y border-line bg-surface">
        <div className="mx-auto grid max-w-[1240px] grid-cols-2 gap-6 px-5 py-12 md:grid-cols-4 md:px-8">
          {[
            ['2.1M+', 'Pages scanned monthly'],
            ['47', 'Reams of paper saved / month*'],
            ['5.4 hrs', 'Avg. approval turnaround'],
            ['99.9%', 'Uptime, hosted in ZA'],
          ].map(([num, label]) => (
            <div key={label} className="text-center">
              <div className="font-display text-[32px] font-extrabold bg-gradient-to-r from-navy-800 to-gold-600 bg-clip-text text-transparent md:text-[38px]">
                {num}
              </div>
              <div className="mt-1 text-[12px] text-ink/50">{label}</div>
            </div>
          ))}
        </div>
        <p className="mx-auto max-w-[1240px] px-5 pb-6 text-[10.5px] text-ink/35 md:px-8">*Illustrative figures for demo tenant "Rand Auto Group".</p>
      </div>

      {/* INDUSTRIES */}
      <section id="industries" className="mx-auto max-w-[1240px] px-5 py-20 md:px-8">
        <div className="mb-10 max-w-xl">
          <div className="mb-3 inline-block rounded-full bg-gold-100 px-3 py-1 text-[11.5px] font-semibold text-gold-600">Built for SA business</div>
          <h2 className="font-display text-[30px] font-extrabold tracking-tight text-ink md:text-[34px]">Industries that run on paperwork.</h2>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {INDUSTRIES.map((ind) => (
            <div key={ind.name} className="rounded-2xl border border-line bg-surface p-6">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-navy-100 text-navy-800">
                <ind.icon size={19} />
              </div>
              <h4 className="font-display text-[14.5px] font-bold text-ink">{ind.name}</h4>
              <p className="mt-1.5 text-[12.5px] leading-relaxed text-ink/55">{ind.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how" className="bg-navy-950 py-20">
        <div className="mx-auto max-w-[1240px] px-5 md:px-8">
          <div className="mb-10 max-w-xl">
            <div className="mb-3 inline-block rounded-full bg-white/10 px-3 py-1 text-[11.5px] font-semibold text-gold-400">How it works</div>
            <h2 className="font-display text-[30px] font-extrabold tracking-tight text-white md:text-[34px]">From paper tray to filed, in minutes.</h2>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((s) => (
              <div key={s.n} className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
                <span className="text-[12px] font-bold text-gold-400">{s.n}</span>
                <div className="my-4 flex h-10 w-10 items-center justify-center rounded-xl bg-white/10 text-white">
                  <s.icon size={18} />
                </div>
                <h4 className="font-display text-[15px] font-bold text-white">{s.title}</h4>
                <p className="mt-1.5 text-[12.5px] leading-relaxed text-white/50">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section className="mx-auto max-w-[1240px] px-5 py-20 md:px-8">
        <div className="mb-10 max-w-xl">
          <div className="mb-3 inline-block rounded-full bg-navy-100 px-3 py-1 text-[11.5px] font-semibold text-navy-800">Customer stories</div>
          <h2 className="font-display text-[30px] font-extrabold tracking-tight text-ink md:text-[34px]">Illustrative customer feedback.</h2>
          <p className="mt-2.5 text-[13px] text-ink/45">Sample quotes from the "Rand Auto Group" demo tenant used throughout this preview.</p>
        </div>
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
          {TESTIMONIALS.map((t) => (
            <div key={t.name} className="rounded-2xl border border-line bg-surface p-6">
              <div className="mb-3 flex gap-0.5 text-gold-500">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star key={i} size={13} fill="currentColor" strokeWidth={0} />
                ))}
              </div>
              <p className="text-[13.5px] leading-relaxed text-ink">“{t.quote}”</p>
              <div className="mt-5 flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-navy-100 text-[12px] font-bold text-navy-800">
                  {t.name.split(' ').map((p) => p[0]).join('')}
                </div>
                <div>
                  <p className="text-[12.5px] font-semibold text-ink">{t.name}</p>
                  <p className="text-[11px] text-ink/45">{t.role}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" className="border-t border-line bg-surface py-20">
        <div className="mx-auto max-w-[1240px] px-5 md:px-8">
          <div className="mb-10 max-w-xl">
            <div className="mb-3 inline-block rounded-full bg-gold-100 px-3 py-1 text-[11.5px] font-semibold text-gold-600">Pricing</div>
            <h2 className="font-display text-[30px] font-extrabold tracking-tight text-ink md:text-[34px]">Simple, per-user pricing.</h2>
            <p className="mt-2.5 text-[13.5px] text-ink/55">All plans include unlimited document types, POPIA-aligned retention and ZA-hosted storage.</p>
          </div>
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
            {PRICING.map((p) => (
              <div
                key={p.tier}
                className={`relative rounded-2xl border p-7 ${
                  p.featured ? 'border-gold-500 bg-gradient-to-b from-gold-50 to-surface' : 'border-line bg-paper'
                }`}
              >
                {p.featured && (
                  <span className="absolute -top-3 right-6 rounded-full bg-gold-500 px-3 py-1 text-[10.5px] font-bold text-navy-950">Most popular</span>
                )}
                <p className="text-[13px] font-semibold text-ink/50">{p.tier}</p>
                <p className="mt-1 font-display text-[32px] font-extrabold text-ink">
                  {p.price} <span className="text-[13px] font-medium text-ink/45">{p.note}</span>
                </p>
                <ul className="my-6 flex flex-col gap-2.5">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-[13px] text-ink/65">
                      <Check size={14} className="mt-0.5 shrink-0 text-ok-600" /> {f}
                    </li>
                  ))}
                </ul>
                <Link
                  to="/login"
                  className={`block rounded-lg px-4 py-3 text-center text-[13px] font-semibold transition-colors ${
                    p.featured ? 'bg-navy-800 text-white hover:bg-navy-700' : 'border border-line text-ink hover:bg-navy-50'
                  }`}
                >
                  Start free trial
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative overflow-hidden py-24 text-center">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_30%,rgba(217,164,65,0.16),transparent_60%)]" />
        <div className="relative mx-auto max-w-2xl px-5">
          <h2 className="font-display text-[32px] font-extrabold tracking-tight text-ink md:text-[38px]">Ready to close the filing room?</h2>
          <p className="mt-3 text-[14.5px] text-ink/55">See the full demo cabinet — documents, workflows and eSignature, pre-loaded with sample data.</p>
          <Link
            to="/login"
            className="mt-8 inline-flex items-center gap-2 rounded-xl bg-navy-800 px-6 py-3.5 text-[14px] font-semibold text-white hover:bg-navy-700 transition-colors"
          >
            Explore the platform <ArrowRight size={16} />
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
}
