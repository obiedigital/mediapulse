"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { io, type Socket } from "socket.io-client";
import ResultsDisplay from "@/components/ResultsDisplay";
import { SOCKET_EVENTS, type ResponseAddedPayload, type SessionStatePayload } from "@/lib/socket-events";
import { AGE_BANDS, BW_REGIONS } from "@/types/slides";

interface SlideItem {
  id: string;
  order: number;
  type: string;
  config: Record<string, unknown>;
}

interface SessionMeta {
  id: string;
  title: string;
  status: string;
  activeSlideOrder: number | null;
  joinCode: string;
}

interface ResultsResponse {
  participantCount: number;
  results: {
    slideId: string;
    order: number;
    type: string;
    config: Record<string, unknown>;
    result: unknown;
  }[];
}

function slideQuestion(config: Record<string, unknown>) {
  return (config.question as string) ?? (config.prompt as string) ?? "";
}

export default function PresentView({ session: initialSession, slides }: { session: SessionMeta; slides: SlideItem[] }) {
  const [session, setSession] = useState(initialSession);
  const [data, setData] = useState<ResultsResponse | null>(null);
  const [viewOrder, setViewOrder] = useState(initialSession.activeSlideOrder ?? slides[0]?.order ?? 0);
  const [bigScreen, setBigScreen] = useState(false);
  const [segmentKey, setSegmentKey] = useState<"" | "age_band" | "region">("");
  const [segmentValue, setSegmentValue] = useState("");
  const socketRef = useRef<Socket | null>(null);

  const sorted = useMemo(() => [...slides].sort((a, b) => a.order - b.order), [slides]);
  const currentSlide = sorted.find((s) => s.order === viewOrder) ?? sorted[0];

  async function fetchResults() {
    const params = new URLSearchParams();
    if (currentSlide) params.set("slideId", currentSlide.id);
    if (segmentKey && segmentValue) {
      params.set("segmentKey", segmentKey);
      params.set("segmentValue", segmentValue);
    }
    const res = await fetch(`/api/sessions/${session.id}/results?${params.toString()}`);
    if (res.ok) setData(await res.json());
  }

  useEffect(() => {
    fetchResults();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentSlide?.id, segmentKey, segmentValue]);

  useEffect(() => {
    const socket = io({ path: "/socket.io" });
    socketRef.current = socket;
    socket.emit(SOCKET_EVENTS.JOIN_SESSION, session.id);

    socket.on(SOCKET_EVENTS.RESPONSE_ADDED, (payload: ResponseAddedPayload) => {
      if (payload.sessionId === session.id) fetchResults();
    });
    socket.on(SOCKET_EVENTS.SESSION_STATE, (payload: SessionStatePayload) => {
      if (payload.sessionId !== session.id) return;
      setSession((s) => ({ ...s, status: payload.status, activeSlideOrder: payload.activeSlideOrder ?? null }));
      if (payload.activeSlideOrder !== undefined && payload.activeSlideOrder !== null) {
        setViewOrder(payload.activeSlideOrder);
      }
    });

    return () => {
      socket.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session.id]);

  async function goToSlide(order: number) {
    setViewOrder(order);
    await fetch(`/api/sessions/${session.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ activeSlideOrder: order, status: "live" }),
    });
  }

  const idx = sorted.findIndex((s) => s.id === currentSlide?.id);
  const resultRow = data?.results.find((r) => r.slideId === currentSlide?.id);

  const content = (
    <div className="flex flex-col gap-6 w-full">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className={`font-display font-extrabold ${bigScreen ? "text-3xl" : "text-xl"}`}>{session.title}</h1>
          <p className="text-cream/40 text-sm">
            Join code <span className="text-teal font-semibold">{session.joinCode}</span> ·{" "}
            {data?.participantCount ?? 0} joined
          </p>
        </div>
        {!bigScreen && (
          <div className="flex items-center gap-2">
            <select
              className="input"
              value={segmentKey}
              onChange={(e) => {
                setSegmentKey(e.target.value as typeof segmentKey);
                setSegmentValue("");
              }}
            >
              <option value="">All respondents</option>
              <option value="age_band">Segment: age band</option>
              <option value="region">Segment: region</option>
            </select>
            {segmentKey && (
              <select className="input" value={segmentValue} onChange={(e) => setSegmentValue(e.target.value)}>
                <option value="">Choose…</option>
                {(segmentKey === "age_band" ? AGE_BANDS : BW_REGIONS).map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            )}
            <a href={`/api/sessions/${session.id}/export`} className="btn btn-ghost btn-sm" target="_blank" rel="noreferrer">
              Export PDF
            </a>
            <button className="btn btn-ghost btn-sm" onClick={() => setBigScreen(true)}>
              Big screen
            </button>
          </div>
        )}
        {bigScreen && (
          <button className="btn btn-ghost btn-sm" onClick={() => setBigScreen(false)}>
            Exit big screen
          </button>
        )}
      </div>

      {currentSlide ? (
        <div className={`card ${bigScreen ? "p-12 bg-ink border-none" : "p-6"} flex flex-col gap-4`}>
          <span className={`label ${bigScreen ? "text-base" : ""}`}>
            Slide {idx + 1} of {sorted.length}
          </span>
          <h2 className={`font-semibold ${bigScreen ? "text-4xl" : "text-lg"}`}>{slideQuestion(currentSlide.config)}</h2>
          {resultRow ? (
            <ResultsDisplay result={resultRow.result as never} big={bigScreen} />
          ) : (
            <p className="text-cream/30">Loading…</p>
          )}
        </div>
      ) : (
        <p className="text-cream/40">Add slides to this session first.</p>
      )}

      {!bigScreen && (
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            <button className="btn btn-ghost btn-sm" disabled={idx <= 0} onClick={() => goToSlide(sorted[idx - 1].order)}>
              ← Previous
            </button>
            <button
              className="btn btn-ghost btn-sm"
              disabled={idx < 0 || idx >= sorted.length - 1}
              onClick={() => goToSlide(sorted[idx + 1].order)}
            >
              Next →
            </button>
          </div>
          <Link href={`/dashboard/sessions/${session.id}/edit`} className="text-xs text-cream/40 hover:text-cream/70">
            Back to session builder
          </Link>
        </div>
      )}
    </div>
  );

  if (bigScreen) {
    return <div className="fixed inset-0 z-50 bg-ink text-cream p-10 overflow-y-auto">{content}</div>;
  }
  return content;
}
