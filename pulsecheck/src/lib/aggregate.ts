import type {
  DemographicTags,
  OpenTextValue,
  PollConfig,
  PollValue,
  RatingScaleConfig,
  RatingValue,
  SlideType,
  WordCloudValue,
} from "@/types/slides";

export interface ResponseRow {
  value: unknown;
  demographicTags: unknown;
}

export interface SegmentFilter {
  key: keyof DemographicTags;
  value: string;
}

const STOPWORDS = new Set([
  "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be",
  "to", "of", "in", "on", "for", "it", "this", "that", "with", "as", "at",
  "i", "we", "you", "they", "he", "she", "very", "so", "just", "not",
]);

function tokenize(text: string, max = 3): string[] {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s'-]/g, " ")
    .split(/\s+/)
    .map((w) => w.trim())
    .filter((w) => w.length > 1 && !STOPWORDS.has(w))
    .slice(0, max);
}

function matchesSegment(tags: unknown, filter?: SegmentFilter): boolean {
  if (!filter) return true;
  const t = (tags ?? {}) as Record<string, unknown>;
  return t[filter.key] === filter.value;
}

export type SlideResult =
  | { type: "poll"; totalResponses: number; options: { label: string; count: number; pct: number }[] }
  | { type: "rating_scale"; totalResponses: number; average: number; distribution: { value: number; count: number }[] }
  | { type: "word_cloud"; totalResponses: number; words: { text: string; count: number }[] }
  | { type: "open_text"; totalResponses: number; responses: string[] };

export function aggregateSlide(
  slideType: SlideType,
  config: unknown,
  rows: ResponseRow[],
  segment?: SegmentFilter
): SlideResult {
  const filtered = rows.filter((r) => matchesSegment(r.demographicTags, segment));

  switch (slideType) {
    case "poll": {
      const cfg = config as PollConfig;
      const counts = cfg.options.map(() => 0);
      for (const row of filtered) {
        const v = row.value as PollValue;
        for (const idx of v?.choices ?? []) {
          if (counts[idx] !== undefined) counts[idx]++;
        }
      }
      const total = filtered.length;
      return {
        type: "poll",
        totalResponses: total,
        options: cfg.options.map((label, i) => ({
          label,
          count: counts[i],
          pct: total > 0 ? Math.round((counts[i] / total) * 1000) / 10 : 0,
        })),
      };
    }
    case "rating_scale": {
      const cfg = config as RatingScaleConfig;
      const dist: Record<number, number> = {};
      for (let v = cfg.min; v <= cfg.max; v++) dist[v] = 0;
      let sum = 0;
      let n = 0;
      for (const row of filtered) {
        const v = row.value as RatingValue;
        if (typeof v?.rating === "number" && dist[v.rating] !== undefined) {
          dist[v.rating]++;
          sum += v.rating;
          n++;
        }
      }
      return {
        type: "rating_scale",
        totalResponses: n,
        average: n > 0 ? Math.round((sum / n) * 100) / 100 : 0,
        distribution: Object.entries(dist).map(([value, count]) => ({
          value: Number(value),
          count,
        })),
      };
    }
    case "word_cloud": {
      const freq = new Map<string, number>();
      for (const row of filtered) {
        const v = row.value as WordCloudValue;
        for (const w of v?.words ?? []) {
          freq.set(w, (freq.get(w) ?? 0) + 1);
        }
      }
      const words = [...freq.entries()]
        .map(([text, count]) => ({ text, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 60);
      return { type: "word_cloud", totalResponses: filtered.length, words };
    }
    case "open_text": {
      const responses = filtered
        .map((row) => (row.value as OpenTextValue)?.text)
        .filter((t): t is string => Boolean(t && t.trim().length > 0));
      return { type: "open_text", totalResponses: filtered.length, responses };
    }
  }
}

/** Turn free text into cloud-ready word tokens (used when persisting a word_cloud response). */
export function wordsFromText(text: string, maxWords = 3): string[] {
  return tokenize(text, maxWords);
}
