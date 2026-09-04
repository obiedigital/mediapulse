"use client";

import { useState } from "react";

export interface SlideDraft {
  type: "poll" | "word_cloud" | "rating_scale" | "open_text";
  config: Record<string, unknown>;
}

const TYPE_OPTIONS: { value: SlideDraft["type"]; label: string }[] = [
  { value: "poll", label: "Poll (single/multi choice)" },
  { value: "word_cloud", label: "Word cloud" },
  { value: "rating_scale", label: "Rating scale" },
  { value: "open_text", label: "Open text" },
];

export default function SlideForm({
  initial,
  onSave,
  onCancel,
  busy,
}: {
  initial?: SlideDraft;
  onSave: (draft: SlideDraft) => void;
  onCancel: () => void;
  busy?: boolean;
}) {
  const [type, setType] = useState<SlideDraft["type"]>(initial?.type ?? "poll");
  const cfg = initial?.config ?? {};

  const [question, setQuestion] = useState((cfg.question as string) ?? (cfg.prompt as string) ?? "");
  const [options, setOptions] = useState<string[]>((cfg.options as string[]) ?? ["", ""]);
  const [multi, setMulti] = useState(Boolean(cfg.multi));
  const [min, setMin] = useState((cfg.min as number) ?? 1);
  const [max, setMax] = useState((cfg.max as number) ?? 5);
  const [minLabel, setMinLabel] = useState((cfg.minLabel as string) ?? "");
  const [maxLabel, setMaxLabel] = useState((cfg.maxLabel as string) ?? "");
  const [maxWords, setMaxWords] = useState((cfg.maxWords as number) ?? 3);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    let config: Record<string, unknown>;
    switch (type) {
      case "poll":
        config = { question, options: options.map((o) => o.trim()).filter(Boolean), multi };
        break;
      case "word_cloud":
        config = { prompt: question, maxWords };
        break;
      case "rating_scale":
        config = { question, min: Number(min), max: Number(max), minLabel, maxLabel };
        break;
      case "open_text":
        config = { prompt: question };
        break;
    }
    onSave({ type, config });
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-3">
      <div className="flex flex-col gap-1">
        <label className="label">Slide type</label>
        <select className="input" value={type} onChange={(e) => setType(e.target.value as SlideDraft["type"])}>
          {TYPE_OPTIONS.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="label">{type === "word_cloud" || type === "open_text" ? "Prompt" : "Question"}</label>
        <input className="input" required value={question} onChange={(e) => setQuestion(e.target.value)} />
      </div>

      {type === "poll" && (
        <div className="flex flex-col gap-2">
          <label className="label">Options</label>
          {options.map((opt, i) => (
            <div key={i} className="flex gap-2">
              <input
                className="input"
                required
                value={opt}
                onChange={(e) => setOptions(options.map((o, j) => (j === i ? e.target.value : o)))}
                placeholder={`Option ${i + 1}`}
              />
              {options.length > 2 && (
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => setOptions(options.filter((_, j) => j !== i))}
                >
                  ✕
                </button>
              )}
            </div>
          ))}
          <button type="button" className="btn btn-ghost btn-sm self-start" onClick={() => setOptions([...options, ""])}>
            + Add option
          </button>
          <label className="flex items-center gap-2 text-sm text-cream/60">
            <input type="checkbox" checked={multi} onChange={(e) => setMulti(e.target.checked)} />
            Allow selecting more than one option
          </label>
        </div>
      )}

      {type === "rating_scale" && (
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <label className="label">Min</label>
            <input className="input" type="number" value={min} onChange={(e) => setMin(Number(e.target.value))} />
          </div>
          <div className="flex flex-col gap-1">
            <label className="label">Max</label>
            <input className="input" type="number" value={max} onChange={(e) => setMax(Number(e.target.value))} />
          </div>
          <div className="flex flex-col gap-1">
            <label className="label">Min label (optional)</label>
            <input className="input" value={minLabel} onChange={(e) => setMinLabel(e.target.value)} placeholder="e.g. Not likely" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="label">Max label (optional)</label>
            <input className="input" value={maxLabel} onChange={(e) => setMaxLabel(e.target.value)} placeholder="e.g. Very likely" />
          </div>
        </div>
      )}

      {type === "word_cloud" && (
        <div className="flex flex-col gap-1 max-w-[160px]">
          <label className="label">Max words / participant</label>
          <input className="input" type="number" min={1} max={5} value={maxWords} onChange={(e) => setMaxWords(Number(e.target.value))} />
        </div>
      )}

      <div className="flex gap-2 mt-1">
        <button className="btn btn-primary" type="submit" disabled={busy}>
          Save
        </button>
        <button type="button" className="btn btn-ghost" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}
