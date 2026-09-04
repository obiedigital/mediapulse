import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { withErrorHandling, NotFoundError } from "@/lib/api-helpers";

/**
 * Unauthenticated, participant-facing view of a session: just enough to
 * render the current slide. No response counts, no other participants'
 * data — that stays behind the moderator's /results endpoint.
 */
export async function GET(_req: Request, { params }: { params: { id: string } }) {
  return withErrorHandling(async () => {
    const session = await prisma.session.findUnique({ where: { id: params.id } });
    if (!session) throw new NotFoundError("Session not found");

    const slides = await prisma.sessionSlide.findMany({
      where: { sessionId: session.id },
      orderBy: { order: "asc" },
      select: { id: true, order: true, type: true, config: true },
    });

    return NextResponse.json({
      session: {
        id: session.id,
        title: session.title,
        status: session.status,
        activeSlideOrder: session.activeSlideOrder,
      },
      slides,
    });
  });
}
