import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { getOwnedSession, withErrorHandling } from "@/lib/api-helpers";
import { aggregateSlide, type SegmentFilter } from "@/lib/aggregate";
import type { DemographicTags, SlideType } from "@/types/slides";

export async function GET(req: Request, { params }: { params: { id: string } }) {
  return withErrorHandling(async () => {
    const { record } = await getOwnedSession(params.id);
    const url = new URL(req.url);
    const slideId = url.searchParams.get("slideId");
    const segmentKey = url.searchParams.get("segmentKey") as keyof DemographicTags | null;
    const segmentValue = url.searchParams.get("segmentValue");
    const segment: SegmentFilter | undefined =
      segmentKey && segmentValue ? { key: segmentKey, value: segmentValue } : undefined;

    const slides = await prisma.sessionSlide.findMany({
      where: { sessionId: record.id, ...(slideId ? { id: slideId } : {}) },
      orderBy: { order: "asc" },
    });

    const responses = await prisma.response.findMany({
      where: { sessionId: record.id },
      include: { participant: { select: { demographicTags: true } } },
    });

    const participantCount = await prisma.participant.count({ where: { sessionId: record.id } });

    const results = slides.map((slide) => {
      const rows = responses
        .filter((r) => r.slideId === slide.id)
        .map((r) => ({ value: r.value, demographicTags: r.participant.demographicTags }));
      return {
        slideId: slide.id,
        order: slide.order,
        type: slide.type,
        config: slide.config,
        result: aggregateSlide(slide.type as SlideType, slide.config, rows, segment),
      };
    });

    return NextResponse.json({
      sessionId: record.id,
      status: record.status,
      activeSlideOrder: record.activeSlideOrder,
      participantCount,
      results,
    });
  });
}
