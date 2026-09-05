# PulseCheck

Live audience-response and insights-capture platform for Botswana's advertising, PR, and
research industry — concept testing, ad recall, brand health pulses, and focus-group
facilitation. Built to share a data layer with MediaPulse BW so the two products can
eventually be sold as one intelligence suite.

## Stack

- **Frontend:** Next.js 14 (App Router), Tailwind CSS
- **Real-time:** polling (see [Real-time model](#real-time-model) below — this runs as
  standard Vercel serverless functions, no persistent server)
- **Backend:** Next.js API routes, PostgreSQL via Prisma
- **Auth:** email/password + signed session cookie (see [Auth](#auth) below)
- **PDF export:** pdfkit

## Getting started (local dev)

Prerequisites: Node 18+, a PostgreSQL database.

```bash
npm install
cp .env.example .env        # then edit DATABASE_URL / DIRECT_URL / AUTH_SECRET
npx prisma migrate dev      # on a fresh dev DB
npm run prisma:seed         # optional: creates a demo org, moderator, and session
npm run dev                 # next dev, on :3000
```

Demo login after seeding: `demo@pulsecheck.bw` / `password123`. Demo session join code:
`123456` (starts in `draft`; open the session and click **Go live** to activate it).

Production build/run locally: `npm run build && npm start` (standard `next build`/`next
start` — no custom server).

## Deploying (Vercel + Supabase)

1. **Create a Supabase project** (supabase.com) for the Postgres database. In *Project
   Settings → Database → Connection string* you'll find two URLs:
   - **Connection pooling** (port 6543, "Transaction" mode) → this is `DATABASE_URL`
   - **Direct connection** (port 5432) → this is `DIRECT_URL` (needed because pgbouncer's
     transaction mode doesn't support what `prisma migrate` needs)
2. **Set environment variables on the Vercel project**: `DATABASE_URL`, `DIRECT_URL`,
   `AUTH_SECRET` (a long random string — `openssl rand -base64 32` works).
3. **Deploy**: `vercel --prod` from the `pulsecheck/` directory (or connect the repo in
   the Vercel dashboard). The `build` script runs `prisma generate && prisma migrate
   deploy && next build`, so migrations apply automatically on every deploy.
4. **Seed demo data** (optional, one-time): run `npm run prisma:seed` locally with
   `DATABASE_URL`/`DIRECT_URL` pointed at the Supabase project (the seed script is
   idempotent — safe to re-run).

No other infra is needed — there's no separate real-time server to stand up.

## Data model — shared layer with MediaPulse BW

The schema (`prisma/schema.prisma`) is deliberately shaped to plug into MediaPulse BW
without a rebuild:

- **`org_id` is the tenant key on every table.** Sessions, participants, responses — all
  scoped to an `organizations` row the same way MediaPulse BW scopes its own tables.
- **`insight_records` is the bridge table.** Both products are meant to write summarized
  findings into it (`source: 'pulsecheck' | 'mediapulse'`), so a future unified client
  dashboard can show "what the media is saying" next to "what our audience actually
  said" from one query. The write path already works end-to-end here: ending a session
  (`PATCH /api/sessions/:id { status: "ended" }`) generates a `session_summary` record
  automatically (see `src/lib/insights.ts`). MediaPulse BW would write its own
  `article_summary`-type records into the same table using `linked_article_id`.

```
organizations → users, sessions
sessions → session_slides (ordered, jsonb config per type), participants, responses
responses → { slide_id, participant_id, value: jsonb }   -- shape depends on slide type
insight_records → { org_id, source, record_type, summary, tags, linked_session_id, linked_article_id }
```

Phase 3 (per the build brief) — a unified dashboard reading across both products' rows in
`insight_records`, and MediaPulse's classification pipeline tagging PulseCheck's
`open_text` responses with the same NLP model — is future work; the schema doesn't block
either.

## Auth

The build brief allows Clerk or Supabase Auth for moderator accounts. Neither is wired up
here because both need a live external project (an API key pair, a configured tenant)
that can't be provisioned inside this build. Instead, `src/lib/auth.ts` implements the
same *shape* — a `getSession()` you call server-side to get `{ userId, orgId, role }` —
with a small self-contained email/password + signed JWT cookie flow (bcrypt for hashing,
`jose` for signing). Every route reads the session through `getSession()` /
`requireSession()`, so swapping in Clerk or Supabase later means replacing this file plus
`/login` and `/signup`, not the rest of the app.

Participants never authenticate: joining a session with a 6-digit code creates a
`participants` row and hands back a `participantId`, which the participant's browser
keeps in `localStorage` (not a cookie — deliberately, so it survives being distinct per
device without server-side session state for anonymous users).

## Real-time model

There is no persistent server here — everything runs as stateless Next.js API routes, so
it deploys as-is to Vercel. "Live" updates work by short-interval polling instead of a
push connection:

- The moderator paces the session: `activeSlideOrder` on the `sessions` row says which
  slide is currently live. `PresentView` and the participant page each poll their
  relevant endpoint every 3 seconds (`/api/sessions/:id/results` and
  `/api/sessions/:id/public` respectively) and re-render on change.
- Aggregation (`src/lib/aggregate.ts`) runs server-side per request, including the
  demographic-segment filter, so the client never needs the raw response set — a poll is
  a small JSON payload, not a data dump.
- Practical effect: a moderator advancing a slide, or a participant's vote landing on the
  big screen, shows up within ~3 seconds rather than instantly. For a room-scale polling
  session this reads as "live" in practice.
- If sub-second push matters for a future deployment, the two poll loops (in
  `src/components/PresentView.tsx` and `src/app/j/[sessionId]/page.tsx`) are the only
  places that would need to change — swap them for a managed real-time service (Pusher,
  Ably) that works over serverless functions. A self-hosted Socket.io server (the
  original approach here) needs a persistent Node process and does **not** run on
  Vercel's serverless functions, which is why this deploy target uses polling instead.

## Low-bandwidth participant UI

The participant flow (`/j`, `/j/[sessionId]`) ships no charting library, no animation
library, and no rendering of aggregate results (that stays on the moderator's big-screen
view) — just the current slide and a form. Removing the Socket.io client (see above) also
dropped its shared bundle size further.

## Known limitations / what a production rollout should change

- **Auth**: swap `src/lib/auth.ts` for Clerk or Supabase Auth per the brief once a tenant
  is provisioned; add password-reset and email verification either way.
- **Real-time**: polling (~3s latency) rather than push — see above.
- **Next.js version**: pinned to `14.2.35` (the newest 14.x). Several Next.js advisories
  (Image Optimizer, i18n middleware, Server Actions edge cases) are only fully closed in
  15.x/16.x; none of the affected surfaces are in use here (`images.unoptimized: true`,
  no i18n, no edge middleware, no Server Actions), but a production deploy should budget
  time for the Next 15 migration (async `cookies()`/`headers()`/route `params`).
- **USSD/SMS join fallback** (Phase 2 in the brief) isn't built — it needs a telco/SMS
  gateway account.
- **Client-facing shareable report link** and **session templates** (Phase 2) aren't
  built; the PDF export covers the "share results" need for MVP.
