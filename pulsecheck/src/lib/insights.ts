import { prisma } from "./prisma";
import { aggregateSlide } from "./aggregate";
import type { SlideType } from "@/types/slides";

/**
 * Shared-layer write-back: when a session ends, summarize it into
 * insight_records so a future unified client dashboard can show it
 * alongside MediaPulse BW media-monitoring records for the same org.
 * (Phase 2 in the build brief — included here so the bridge table has a
 * real write path instead of sitting empty.)
 */
export async function writeSessionInsightRecord(sessionId: string) {
  const session = await prisma.session.findUnique({
    where: { id: sessionId },
    include: {
      slides: { orderBy: { order: "asc" } },
      participants: true,
      responses: true,
    },
  });
  if (!session) return null;

  const parts: string[] = [
    `${session.title} (${session.type.replace("_", " ")}) — ${session.participants.length} participant(s), ${session.slides.length} slide(s).`,
  ];

  for (const slide of session.slides) {
    const rows = session.responses
      .filter((r) => r.slideId === slide.id)
      .map((r) => ({ value: r.value, demographicTags: null }));
    const result = aggregateSlide(slide.type as SlideType, slide.config, rows);
    switch (result.type) {
      case "poll": {
        const top = [...result.options].sort((a, b) => b.count - a.count)[0];
        if (top && result.totalResponses > 0) {
          parts.push(`Poll "${(slide.config as { question?: string }).question ?? ""}": top answer "${top.label}" (${top.pct}%).`);
        }
        break;
      }
      case "rating_scale":
        if (result.totalResponses > 0) {
          parts.push(`Rating "${(slide.config as { question?: string }).question ?? ""}": average ${result.average}.`);
        }
        break;
      case "word_cloud": {
        const top = result.words.slice(0, 5).map((w) => w.text);
        if (top.length > 0) parts.push(`Word cloud top terms: ${top.join(", ")}.`);
        break;
      }
      case "open_text":
        if (result.totalResponses > 0) {
          parts.push(`Open text: ${result.totalResponses} response(s) collected.`);
        }
        break;
    }
  }

  return prisma.insightRecord.create({
    data: {
      orgId: session.orgId,
      source: "pulsecheck",
      recordType: "session_summary",
      summary: parts.join(" "),
      tags: { sessionType: session.type, slideCount: session.slides.length },
      linkedSessionId: session.id,
    },
  });
}
