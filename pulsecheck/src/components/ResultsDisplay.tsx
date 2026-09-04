"use client";

// Renders one slide's aggregated results. Deliberately hand-rolled
// bars/word-cloud instead of a charting library — this view only ever
// renders for a moderator (never shipped to the low-bandwidth participant
// bundle), but keeping it dependency-free keeps the whole app lean.

type SlideResult =
  | { type: "poll"; totalResponses: number; options: { label: string; count: number; pct: number }[] }
  | { type: "rating_scale"; totalResponses: number; average: number; distribution: { value: number; count: number }[] }
  | { type: "word_cloud"; totalResponses: number; words: { text: string; count: number }[] }
  | { type: "open_text"; totalResponses: number; responses: string[] };

const BAR_COLORS = ["#FF5C1A", "#00D4C8", "#A855F7", "#F59E0B", "#22C55E", "#FF8150", "#38BDF8"];

export default function ResultsDisplay({ result, big }: { result: SlideResult; big?: boolean }) {
  const labelSize = big ? "text-2xl" : "text-sm";
  const barHeight = big ? "h-10" : "h-6";

  if (result.type === "poll") {
    const max = Math.max(1, ...result.options.map((o) => o.count));
    return (
      <div className="flex flex-col gap-3 w-full">
        {result.options.map((opt, i) => (
          <div key={opt.label} className="flex flex-col gap-1">
            <div className={`flex justify-between ${labelSize} font-medium`}>
              <span>{opt.label}</span>
              <span className="text-cream/50">
                {opt.count} · {opt.pct}%
              </span>
            </div>
            <div className={`bg-s2 rounded-md overflow-hidden ${barHeight}`}>
              <div
                className={`${barHeight} rounded-md transition-all duration-500`}
                style={{
                  width: `${Math.max(2, (opt.count / max) * 100)}%`,
                  background: BAR_COLORS[i % BAR_COLORS.length],
                }}
              />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (result.type === "rating_scale") {
    const max = Math.max(1, ...result.distribution.map((d) => d.count));
    return (
      <div className="flex flex-col gap-4 w-full">
        <div className={`font-display font-extrabold ${big ? "text-6xl" : "text-3xl"} text-teal`}>
          {result.average}
          <span className={`text-cream/40 font-sans font-normal ${big ? "text-2xl" : "text-sm"} ml-2`}>average</span>
        </div>
        <div className="flex items-end gap-2 h-32">
          {result.distribution.map((d) => (
            <div key={d.value} className="flex flex-col items-center gap-1 flex-1">
              <div
                className="w-full rounded-t-md bg-or"
                style={{ height: `${Math.max(4, (d.count / max) * 100)}%` }}
              />
              <span className={`${labelSize} text-cream/50`}>{d.value}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (result.type === "word_cloud") {
    const max = Math.max(1, ...result.words.map((w) => w.count));
    if (result.words.length === 0) {
      return <p className="text-cream/30">Waiting for responses…</p>;
    }
    return (
      <div className="flex flex-wrap gap-x-4 gap-y-2 items-center justify-center py-6">
        {result.words.map((w, i) => {
          const scale = 0.6 + (w.count / max) * (big ? 2.4 : 1.6);
          return (
            <span
              key={w.text}
              style={{
                fontSize: `${scale}rem`,
                color: BAR_COLORS[i % BAR_COLORS.length],
              }}
              className="font-display font-extrabold leading-none"
              title={`${w.count} mention(s)`}
            >
              {w.text}
            </span>
          );
        })}
      </div>
    );
  }

  // open_text
  return (
    <div className="flex flex-col gap-2 max-h-[420px] overflow-y-auto">
      {result.responses.length === 0 && <p className="text-cream/30">Waiting for responses…</p>}
      {result.responses.map((text, i) => (
        <div key={i} className={`card px-4 py-3 ${big ? "text-xl" : "text-sm"}`}>
          {text}
        </div>
      ))}
    </div>
  );
}
