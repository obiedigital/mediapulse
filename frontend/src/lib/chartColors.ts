// Categorical hues are assigned to entities (brands, publications, ...) in
// fixed, first-seen order and never re-cycled when a filter changes the
// visible set — see the dataviz skill's categorical-color rule.
const SERIES_VARS = [
  "--series-1", "--series-2", "--series-3", "--series-4",
  "--series-5", "--series-6", "--series-7", "--series-8",
]

const assigned = new Map<string, string>()

export function colorForEntity(name: string): string {
  if (!assigned.has(name)) {
    const idx = assigned.size % SERIES_VARS.length
    assigned.set(name, `var(${SERIES_VARS[idx]})`)
  }
  return assigned.get(name)!
}

export function sentimentColor(sentiment: string | null): string {
  switch (sentiment) {
    case "positive":
      return "var(--status-good)"
    case "negative":
      return "var(--status-critical)"
    default:
      return "var(--ink-muted)"
  }
}

export function threatColor(tag: string | null): string {
  switch (tag) {
    case "opportunity":
      return "var(--status-good)"
    case "risk":
      return "var(--status-critical)"
    default:
      return "var(--status-warning)"
  }
}
