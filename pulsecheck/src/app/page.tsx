import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between px-6 py-5 max-w-5xl mx-auto w-full">
        <div className="flex items-center gap-2 font-display text-lg font-extrabold">
          <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-or to-teal flex items-center justify-center text-ink text-xs">
            PC
          </span>
          PulseCheck
        </div>
        <nav className="flex items-center gap-3 text-sm">
          <Link href="/login" className="btn btn-ghost btn-sm">
            Moderator login
          </Link>
        </nav>
      </header>

      <section className="flex-1 flex flex-col items-center justify-center text-center px-6 py-16 gap-8">
        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal/10 border border-teal/25 text-teal text-xs font-semibold">
          Built for Botswana&apos;s ad, PR &amp; research industry
        </span>
        <h1 className="font-display text-4xl sm:text-5xl font-extrabold leading-tight max-w-2xl">
          Live audience insights for{" "}
          <span className="bg-gradient-to-r from-or to-teal bg-clip-text text-transparent">
            concept tests, ad recall &amp; brand pulses
          </span>
        </h1>
        <p className="text-cream/60 max-w-lg">
          Run live polls, word clouds, and ratings in the room or in the field — mobile-first
          and built to stay usable on 3G. No app to install, no login for participants.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Link href="/j" className="btn btn-primary">
            Join a session
          </Link>
          <Link href="/signup" className="btn btn-ghost">
            Create a moderator account
          </Link>
        </div>
      </section>

      <footer className="text-center text-xs text-cream/30 py-6">
        PulseCheck — part of the MediaPulse BW intelligence suite
      </footer>
    </main>
  );
}
