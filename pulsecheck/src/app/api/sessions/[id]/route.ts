import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { getOwnedSession, withErrorHandling } from "@/lib/api-helpers";
import { writeSessionInsightRecord } from "@/lib/insights";
import { getIO } from "@/lib/socket-server";
import { sessionRoom, SOCKET_EVENTS, type SessionStatePayload } from "@/lib/socket-events";

export async function GET(_req: Request, { params }: { params: { id: string } }) {
  return withErrorHandling(async () => {
    const { record } = await getOwnedSession(params.id);
    const slides = await prisma.sessionSlide.findMany({
      where: { sessionId: record.id },
      orderBy: { order: "asc" },
    });
    return NextResponse.json({ session: record, slides });
  });
}

const patchSchema = z.object({
  title: z.string().trim().min(1).max(200).optional(),
  status: z.enum(["draft", "live", "ended"]).optional(),
  activeSlideOrder: z.number().int().nullable().optional(),
});

export async function PATCH(req: Request, { params }: { params: { id: string } }) {
  return withErrorHandling(async () => {
    const { record } = await getOwnedSession(params.id);
    const body = patchSchema.parse(await req.json());

    const data: Record<string, unknown> = {};
    if (body.title !== undefined) data.title = body.title;
    if (body.activeSlideOrder !== undefined) data.activeSlideOrder = body.activeSlideOrder;

    if (body.status !== undefined && body.status !== record.status) {
      data.status = body.status;
      if (body.status === "live" && !record.startedAt) data.startedAt = new Date();
      if (body.status === "ended") data.endedAt = new Date();
    }

    const updated = await prisma.session.update({ where: { id: record.id }, data });

    if (body.status === "ended") {
      await writeSessionInsightRecord(record.id);
    }

    const io = getIO();
    if (io && (body.status !== undefined || body.activeSlideOrder !== undefined)) {
      const payload: SessionStatePayload = {
        sessionId: updated.id,
        status: updated.status,
        activeSlideOrder: updated.activeSlideOrder,
      };
      io.to(sessionRoom(updated.id)).emit(SOCKET_EVENTS.SESSION_STATE, payload);
    }

    return NextResponse.json({ session: updated });
  });
}

export async function DELETE(_req: Request, { params }: { params: { id: string } }) {
  return withErrorHandling(async () => {
    const { record } = await getOwnedSession(params.id);
    await prisma.session.delete({ where: { id: record.id } });
    return NextResponse.json({ ok: true });
  });
}
