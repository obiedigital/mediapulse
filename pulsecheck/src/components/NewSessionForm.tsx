"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const TYPES = [
  { value: "concept_test", label: "Concept test" },
  { value: "ad_recall", label: "Ad recall" },
  { value: "brand_pulse", label: "Brand health pulse" },
  { value: "focus_group", label: "Focus group" },
  { value: "custom", label: "Custom" },
];

export default function NewSessionForm() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [type, setType] = useState("custom");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) {
    return (
      <button className="btn btn-primary self-start" onClick={() => setOpen(true)}>
        + New session
      </button>
    );
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, type }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Could not create session");
      router.push(`/dashboard/sessions/${data.session.id}/edit`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create session");
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="card p-5 flex flex-col gap-3 max-w-md">
      <div className="flex flex-col gap-1">
        <label className="label">Session title</label>
        <input
          className="input"
          required
          autoFocus
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Q3 concept test — Beverage Brand X"
        />
      </div>
      <div className="flex flex-col gap-1">
        <label className="label">Type</label>
        <select className="input" value={type} onChange={(e) => setType(e.target.value)}>
          {TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </div>
      {error && <p className="text-red-400 text-sm">{error}</p>}
      <div className="flex gap-2">
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? "Creating…" : "Create session"}
        </button>
        <button type="button" className="btn btn-ghost" onClick={() => setOpen(false)}>
          Cancel
        </button>
      </div>
    </form>
  );
}
