"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";

// No persistent socket on serverless hosting — poll for the host advancing
// the slide instead. A few seconds' lag is an acceptable tradeoff for a
// participant who's just about to tap a button anyway.
const POLL_INTERVAL_MS = 3000;

interface SlideItem {
  id: string;
  order: number;
  type: "poll" | "word_cloud" | "rating_scale" | "open_text";
  config: Record<string, unknown>;
}

interface PublicSession {
  id: string;
  title: string;
  status: "draft" | "live" | "ended";
  activeSlideOrder: number | null;
}

export default function ParticipantSessionPage() {
  const params = useParams<{ sessionId: string }>();
  const router = useRouter();
  const sessionId = params.sessionId;

  const [participantId, setParticipantId] = useState<string | null | undefined>(undefined);
  const [session, setSession] = useState<PublicSession | null>(null);
  const [slides, setSlides] = useState<SlideItem[]>([]);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const activeSlideOrderRef = useRef<number | null>(null);

  useEffect(() => {
    let stored: string | null = null;
    try {
      stored = localStorage.getItem(`pc_participant:${sessionId}`);
    } catch {
      stored = null;
    }
    if (!stored) {
      router.replace("/j");
      return;
    }
    setParticipantId(stored);
  }, [sessionId, router]);

  async function refreshSession() {
    const res = await fetch(`/api/sessions/${sessionId}/public`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.session.activeSlideOrder !== activeSlideOrderRef.current) {
      activeSlideOrderRef.current = data.session.activeSlideOrder;
      setSubmitted(false);
    }
    setSession(data.session);
    setSlides(data.slides);
  }

  useEffect(() => {
    refreshSession();
    const interval = setInterval(refreshSession, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  if (participantId === undefined) return null;

  if (!session) {
    return <Centered>Loading…</Centered>;
  }

  if (session.status === "draft") {
    return <Centered title={session.title}>Waiting for the host to start…</Centered>;
  }

  if (session.status === "ended") {
    return <Centered title={session.title}>Thanks for taking part! This session has ended.</Centered>;
  }

  const slide = slides.find((s) => s.order === session.activeSlideOrder);

  if (!slide) {
    return <Centered title={session.title}>Get ready — the next question is coming up…</Centered>;
  }

  if (submitted) {
    return <Centered title={session.title}>✓ Submitted. Waiting for the next question…</Centered>;
  }

  return (
    <main className="min-h-screen flex flex-col px-5 py-8 max-w-md mx-auto w-full">
      <p className="label mb-2">{session.title}</p>
      <SlideForm
        key={slide.id}
        slide={slide}
        onSubmit={async (value) => {
          setError(null);
          const res = await fetch("/api/responses", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ participantId, slideId: slide.id, ...value }),
          });
          const data = await res.json();
          if (!res.ok) {
            setError(data.error ?? "Couldn't submit — try again.");
            return;
          }
          setSubmitted(true);
        }}
        error={error}
      />
    </main>
  );
}

function Centered({ title, children }: { title?: string; children: React.ReactNode }) {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 text-center gap-2">
      {title && <p className="label">{title}</p>}
      <p className="text-cream/60">{children}</p>
    </main>
  );
}

function SlideForm({
  slide,
  onSubmit,
  error,
}: {
  slide: SlideItem;
  onSubmit: (value: { choices?: number[]; rating?: number; text?: string }) => Promise<void>;
  error: string | null;
}) {
  const [choices, setChoices] = useState<number[]>([]);
  const [rating, setRating] = useState<number | null>(null);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);

  const question = (slide.config.question as string) ?? (slide.config.prompt as string) ?? "";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSending(true);
    if (slide.type === "poll") await onSubmit({ choices });
    else if (slide.type === "rating_scale") await onSubmit({ rating: rating ?? undefined });
    else await onSubmit({ text });
    setSending(false);
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-5 flex-1">
      <h1 className="font-display text-2xl font-bold leading-snug">{question}</h1>

      {slide.type === "poll" && (
        <div className="flex flex-col gap-2">
          {((slide.config.options as string[]) ?? []).map((opt, i) => {
            const multi = Boolean(slide.config.multi);
            const active = choices.includes(i);
            return (
              <button
                type="button"
                key={i}
                onClick={() =>
                  setChoices((prev) =>
                    multi ? (active ? prev.filter((c) => c !== i) : [...prev, i]) : [i]
                  )
                }
                className={`btn ${active ? "btn-primary" : "btn-ghost"} justify-start text-left py-3`}
              >
                {opt}
              </button>
            );
          })}
        </div>
      )}

      {slide.type === "rating_scale" && (
        <div className="flex flex-col gap-2">
          <div className="flex justify-between text-xs text-cream/40">
            <span>{(slide.config.minLabel as string) ?? slide.config.min}</span>
            <span>{(slide.config.maxLabel as string) ?? slide.config.max}</span>
          </div>
          <div className="grid grid-cols-5 gap-2">
            {Array.from(
              { length: Number(slide.config.max ?? 5) - Number(slide.config.min ?? 1) + 1 },
              (_, i) => Number(slide.config.min ?? 1) + i
            ).map((v) => (
              <button
                type="button"
                key={v}
                onClick={() => setRating(v)}
                className={`btn ${rating === v ? "btn-primary" : "btn-ghost"} justify-center`}
              >
                {v}
              </button>
            ))}
          </div>
        </div>
      )}

      {slide.type === "word_cloud" && (
        <input
          className="input"
          required
          maxLength={40}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="One word or short phrase…"
          autoFocus
        />
      )}

      {slide.type === "open_text" && (
        <textarea
          className="input min-h-[120px]"
          required
          maxLength={1000}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type your answer…"
          autoFocus
        />
      )}

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <button
        className="btn btn-primary mt-auto"
        type="submit"
        disabled={
          sending ||
          (slide.type === "poll" && choices.length === 0) ||
          (slide.type === "rating_scale" && rating === null)
        }
      >
        {sending ? "Submitting…" : "Submit"}
      </button>
    </form>
  );
}
