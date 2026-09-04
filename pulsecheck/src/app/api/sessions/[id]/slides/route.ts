import { NextResponse } from "next/server";
import { z } from "zod";
import type { Prisma } from "@prisma/client";
import { prisma } from "@/lib/prisma";
import { getOwnedSession, withErrorHandling } from "@/lib/api-helpers";

const slideSchema = z.object({
  type: z.enum(["poll", "word_cloud", "rating_scale", "open_text"]),
  config: z.record(z.unknown()),
});

export async function POST(req: Request, { params }: { params: { id: string } }) {
  return withErrorHandling(async () => {
    const { record } = await getOwnedSession(params.id);
    const body = slideSchema.parse(await req.json());

    const last = await prisma.sessionSlide.findFirst({
      where: { sessionId: record.id },
      orderBy: { order: "desc" },
    });
    const order = (last?.order ?? -1) + 1;

    const slide = await prisma.sessionSlide.create({
      data: { sessionId: record.id, type: body.type, config: body.config as Prisma.InputJsonValue, order },
    });

    return NextResponse.json({ slide }, { status: 201 });
  });
}

const reorderSchema = z.object({
  order: z.array(z.string()).min(1), // slide ids in desired order
});

export async function PATCH(req: Request, { params }: { params: { id: string } }) {
  return withErrorHandling(async () => {
    const { record } = await getOwnedSession(params.id);
    const body = reorderSchema.parse(await req.json());

    // Two-phase update: the (sessionId, order) unique constraint is checked
    // per-statement, so writing final order values directly can collide with
    // another row's current order mid-transaction. Push everything out of
    // range first, then assign final positions.
    await prisma.$transaction([
      ...body.order.map((slideId, index) =>
        prisma.sessionSlide.updateMany({
          where: { id: slideId, sessionId: record.id },
          data: { order: 100000 + index },
        })
      ),
      ...body.order.map((slideId, index) =>
        prisma.sessionSlide.updateMany({
          where: { id: slideId, sessionId: record.id },
          data: { order: index },
        })
      ),
    ]);

    const slides = await prisma.sessionSlide.findMany({
      where: { sessionId: record.id },
      orderBy: { order: "asc" },
    });
    return NextResponse.json({ slides });
  });
}
