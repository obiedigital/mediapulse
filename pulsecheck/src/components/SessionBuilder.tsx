"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import SlideForm, { type SlideDraft } from "@/components/SlideForm";

interface SlideItem {
  id: string;
  order: number;
  type: string;
  config: Record<string, unknown>;
}

interface SessionMeta {
  id: string;
  title: string;
  type: string;
  status: string;
  joinCode: string;
}

const SLIDE_LABEL: Record<string, string> = {
  poll: "Poll",
  word_cloud: "Word cloud",
  rating_scale: "Rating scale",
  open_text: "Open text",
};

function slideQuestion(config: Record<string, unknown>) {
  return (config.question as string) ?? (config.prompt as string) ?? "";
}

export default function SessionBuilder({
  session,
  initialSlides,
}: {
  session: SessionMeta;
  initialSlides: SlideItem[];
}) {
  const router = useRouter();
  const [slides, setSlides] = useState(initialSlides);
  const [status, setStatus] = useState(session.status);
  const [adding, setAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function refreshSlides() {
    const res = await fetch(`/api/sessions/${session.id}`);
    const data = await res.json();
    setSlides(data.slides);
  }

  async function addSlide(draft: SlideDraft) {
    setBusy(true);
    await fetch(`/api/sessions/${session.id}/slides`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(draft),
    });
    await refreshSlides();
    setAdding(false);
    setBusy(false);
  }

  async function updateSlide(slideId: string, draft: SlideDraft) {
    setBusy(true);
    await fetch(`/api/sessions/${session.id}/slides/${slideId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(draft),
    });
    await refreshSlides();
    setEditingId(null);
    setBusy(false);
  }

  async function deleteSlide(slideId: string) {
    if (!confirm("Delete this slide?")) return;
    setBusy(true);
    await fetch(`/api/sessions/${session.id}/slides/${slideId}`, { method: "DELETE" });
    await refreshSlides();
    setBusy(false);
  }

  async function move(slideId: string, dir: -1 | 1) {
    const sorted = [...slides].sort((a, b) => a.order - b.order);
    const idx = sorted.findIndex((s) => s.id === slideId);
    const swapIdx = idx + dir;
    if (swapIdx < 0 || swapIdx >= sorted.length) return;
    [sorted[idx], sorted[swapIdx]] = [sorted[swapIdx], sorted[idx]];
    const order = sorted.map((s) => s.id);
    setBusy(true);
    await fetch(`/api/sessions/${session.id}/slides`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order }),
    });
    await refreshSlides();
    setBusy(false);
  }

  async function setSessionStatus(next: string) {
    setBusy(true);
    const res = await fetch(`/api/sessions/${session.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: next }),
    });
    if (res.ok) setStatus(next);
    setBusy(false);
    if (next === "live") router.push(`/dashboard/sessions/${session.id}/present`);
  }

  const sortedSlides = [...slides].sort((a, b) => a.order - b.order);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link href="/dashboard" className="text-xs text-cream/40 hover:text-cream/70">
            ← All sessions
          </Link>
          <h1 className="font-display text-2xl font-extrabold mt-1">{session.title}</h1>
          <p className="text-sm text-cream/40 capitalize">{session.type.replace("_", " ")}</p>
        </div>
        <div className="card px-5 py-3 flex flex-col items-center">
          <span className="label">Join code</span>
          <span className="font-display text-3xl font-extrabold tracking-widest text-teal">
            {session.joinCode}
          </span>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {status === "draft" && (
          <button className="btn btn-primary" disabled={busy || slides.length === 0} onClick={() => setSessionStatus("live")}>
            Go live
          </button>
        )}
        {status === "live" && (
          <>
            <Link href={`/dashboard/sessions/${session.id}/present`} className="btn btn-primary">
              Open results / big screen
            </Link>
            <button className="btn btn-ghost" disabled={busy} onClick={() => setSessionStatus("ended")}>
              End session
            </button>
          </>
        )}
        {status === "ended" && (
          <Link href={`/dashboard/sessions/${session.id}/present`} className="btn btn-ghost">
            View results
          </Link>
        )}
        <a href={`/api/sessions/${session.id}/export`} className="btn btn-ghost" target="_blank" rel="noreferrer">
          Export PDF
        </a>
        {status === "draft" && slides.length === 0 && (
          <span className="text-xs text-cream/40">Add at least one slide before going live.</span>
        )}
      </div>

      <div className="flex flex-col gap-3">
        <h2 className="font-display text-lg font-bold">Slides</h2>
        {sortedSlides.map((slide, i) => (
          <div key={slide.id} className="card p-4">
            {editingId === slide.id ? (
              <SlideForm
                initial={{ type: slide.type as SlideDraft["type"], config: slide.config }}
                onCancel={() => setEditingId(null)}
                onSave={(draft) => updateSlide(slide.id, draft)}
                busy={busy}
              />
            ) : (
              <div className="flex items-start justify-between gap-4">
                <div>
                  <span className="label">
                    {i + 1}. {SLIDE_LABEL[slide.type] ?? slide.type}
                  </span>
                  <p className="text-sm mt-1">{slideQuestion(slide.config) || <em className="text-cream/30">No question set</em>}</p>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <button className="btn btn-ghost btn-sm" disabled={busy || i === 0} onClick={() => move(slide.id, -1)}>
                    ↑
                  </button>
                  <button
                    className="btn btn-ghost btn-sm"
                    disabled={busy || i === sortedSlides.length - 1}
                    onClick={() => move(slide.id, 1)}
                  >
                    ↓
                  </button>
                  <button className="btn btn-ghost btn-sm" disabled={busy} onClick={() => setEditingId(slide.id)}>
                    Edit
                  </button>
                  <button className="btn btn-ghost btn-sm" disabled={busy} onClick={() => deleteSlide(slide.id)}>
                    Delete
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}

        {adding ? (
          <div className="card p-4">
            <SlideForm onCancel={() => setAdding(false)} onSave={addSlide} busy={busy} />
          </div>
        ) : (
          <button className="btn btn-ghost self-start" onClick={() => setAdding(true)}>
            + Add slide
          </button>
        )}
      </div>
    </div>
  );
}
