"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AGE_BANDS, BW_REGIONS } from "@/types/slides";

export default function JoinPage() {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [showDemo, setShowDemo] = useState(false);
  const [ageBand, setAgeBand] = useState("");
  const [region, setRegion] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/join", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, ageBand: ageBand || undefined, region: region || undefined }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Couldn't join");
      try {
        localStorage.setItem(`pc_participant:${data.sessionId}`, data.participantId);
      } catch {
        // localStorage unavailable (private mode) — session still works, just won't
        // survive a refresh.
      }
      router.push(`/j/${data.sessionId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't join");
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-5">
      <form onSubmit={onSubmit} className="w-full max-w-xs flex flex-col gap-4 items-center text-center">
        <span className="w-10 h-10 rounded-lg bg-gradient-to-br from-or to-teal flex items-center justify-center text-ink text-xs font-bold">
          PC
        </span>
        <h1 className="font-display text-xl font-extrabold">Enter session code</h1>
        <input
          className="input text-center text-2xl tracking-[0.3em] font-display"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={6}
          required
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
          placeholder="000000"
          autoFocus
        />

        {!showDemo ? (
          <button type="button" className="text-xs text-cream/40 underline" onClick={() => setShowDemo(true)}>
            Add optional info (age band, region)
          </button>
        ) : (
          <div className="w-full flex flex-col gap-2 text-left">
            <select className="input" value={ageBand} onChange={(e) => setAgeBand(e.target.value)}>
              <option value="">Age band (optional)</option>
              {AGE_BANDS.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
            <select className="input" value={region} onChange={(e) => setRegion(e.target.value)}>
              <option value="">Region (optional)</option>
              {BW_REGIONS.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </div>
        )}

        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button className="btn btn-primary w-full" type="submit" disabled={loading || code.length !== 6}>
          {loading ? "Joining…" : "Join session"}
        </button>
      </form>
    </main>
  );
}
