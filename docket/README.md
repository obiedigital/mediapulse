# Docket — the paperless office platform for South African business

A product concept and interactive demo inspired by [Digital Cabinet](https://www.digitalcabinet.co.za/)
(a Cape Town / Johannesburg document-management and workflow-automation SaaS). This is an
**original, standalone brand** — not a copy of Digital Cabinet's site or code — built to show what a
modern take on the same product category (cloud document management, smart scanning, workflow
automation, eSignature) could look like, seeded with realistic South African sample data.

All data (the "Rand Auto Group" tenant, documents, users, workflow instances, signature requests,
testimonials, pricing) is fictional demo content for this prototype.

## Stack

- React 19 + TypeScript + Vite
- React Router for the marketing site / login / app shell
- Tailwind CSS v4 (CSS-first theme in `src/index.css`)
- Recharts for dashboard & report charts
- lucide-react for icons

## Structure

```
src/
  types.ts               Domain types (documents, workflows, signatures, …)
  data/mockData.ts        All seed/demo data for the "Rand Auto Group" tenant
  context/                AuthContext (demo login) + ToastContext
  components/
    ui/                   Button, Card, Badge, Modal, Progress, Avatar, EmptyState
    layout/                Sidebar, Topbar, AppShell (protected route)
    marketing/             Landing page Nav + Footer
  pages/
    marketing/Landing.tsx  Public site: hero, modules, industries, how-it-works,
                            testimonials, pricing, CTA
    auth/Login.tsx          Demo role picker + manual sign-in form
    app/                    Dashboard, DocumentManager, SmartScan, Workflows,
                            ESignature, Reports, Settings
```

## Product modules

- **Document Manager** — folder tree, search/filter, document detail modal, upload flow,
  compliance tags (POPIA / FICA / FSCA).
- **Smart Scan** — capture sources (mobile, network scanner, email, bulk upload) and a live
  capture simulator that queues → processes → classifies → files a document.
- **Workflows** — approval-chain visualizer with step types (approval / condition /
  notification / form) and an active-instances list you can approve/reject.
- **eSignature & Forms** — signature request tracking per signer, plus a form-template library.
- **Reports** — volume, compliance and workflow-throughput charts.
- **Settings** — users & roles, retention rules, compliance toggles, integrations, billing.

## Getting started

```bash
npm install
npm run dev       # http://localhost:5173
npm run build     # type-check + production build to dist/
```

Sign in via any of the four demo role cards on `/login` (Admin, Manager, Staff × 2) — no real
credentials required. The session persists in `localStorage` only, for this browser.
