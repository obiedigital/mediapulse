import { NextResponse } from "next/server";
import { z } from "zod";
import type { Prisma } from "@prisma/client";
import { prisma } from "@/lib/prisma";
import { getOwnedSession, withErrorHandling, NotFoundError } from "@/lib/api-helpers";

const patchSchema = z.object({
  config: z.record(z.unknown()).optional(),
  type: z.enum(["poll", "word_cloud", "rating_scale", "open_text"]).optional(),
});

async function loadSlide(sessionId: string, slideId: string) {
  const slide = await prisma.sessionSlide.findFirst({ where: { id: slideId, sessionId } });
  if (!slide) throw new NotFoundError("Slide not found");
  return slide;
}

export async function PATCH(
  req: Request,
  { params }: { params: { id: string; slideId: string } }
) {
  return withErrorHandling(async () => {
    const { record } = await getOwnedSession(params.id);
    await loadSlide(record.id, params.slideId);
    const body = patchSchema.parse(await req.json());

    const slide = await prisma.sessionSlide.update({
      where: { id: params.slideId },
      data: body as { type?: Prisma.SessionSlideUpdateInput["type"]; config?: Prisma.InputJsonValue },
    });
    return NextResponse.json({ slide });
  });
}

export async function DELETE(
  _req: Request,
  { params }: { params: { id: string; slideId: string } }
) {
  return withErrorHandling(async () => {
    const { record } = await getOwnedSession(params.id);
    await loadSlide(record.id, params.slideId);
    await prisma.sessionSlide.delete({ where: { id: params.slideId } });
    return NextResponse.json({ ok: true });
  });
}
