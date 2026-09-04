import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { jsonError, withErrorHandling } from "@/lib/api-helpers";
import { wordsFromText } from "@/lib/aggregate";
import { getIO } from "@/lib/socket-server";
import { sessionRoom, SOCKET_EVENTS, type ResponseAddedPayload } from "@/lib/socket-events";
import type { ResponseValue } from "@/types/slides";

const bodySchema = z.object({
  participantId: z.string().min(1),
  slideId: z.string().min(1),
  // Raw shapes coming from the participant UI; normalized per slide type below.
  choices: z.array(z.number().int()).optional(), // poll
  rating: z.number().optional(), // rating_scale
  text: z.string().max(2000).optional(), // word_cloud / open_text
});

export async function POST(req: Request) {
  return withErrorHandling(async () => {
    const body = bodySchema.parse(await req.json());

    const participant = await prisma.participant.findUnique({ where: { id: body.participantId } });
    if (!participant) return jsonError("Unknown participant — please rejoin.", 404);

    const slide = await prisma.sessionSlide.findUnique({ where: { id: body.slideId } });
    if (!slide || slide.sessionId !== participant.sessionId) {
      return jsonError("This question is no longer available.", 404);
    }

    const session = await prisma.session.findUnique({ where: { id: participant.sessionId } });
    if (!session || session.status !== "live") {
      return jsonError("This session isn't accepting responses right now.", 409);
    }

    let value: ResponseValue;
    switch (slide.type) {
      case "poll": {
        const options = (slide.config as { options?: string[] }).options ?? [];
        const choices = (body.choices ?? []).filter((i) => i >= 0 && i < options.length);
        if (choices.length === 0) return jsonError("Pick at least one option.", 422);
        value = { choices };
        break;
      }
      case "rating_scale": {
        const cfg = slide.config as { min?: number; max?: number };
        const min = cfg.min ?? 1;
        const max = cfg.max ?? 5;
        if (typeof body.rating !== "number" || body.rating < min || body.rating > max) {
          return jsonError(`Rating must be between ${min} and ${max}.`, 422);
        }
        value = { rating: body.rating };
        break;
      }
      case "word_cloud": {
        const text = body.text?.trim();
        if (!text) return jsonError("Enter a word or short phrase.", 422);
        const maxWords = (slide.config as { maxWords?: number }).maxWords ?? 3;
        value = { words: wordsFromText(text, maxWords) };
        break;
      }
      case "open_text": {
        const text = body.text?.trim();
        if (!text) return jsonError("Enter a response.", 422);
        value = { text };
        break;
      }
      default:
        return jsonError("Unsupported slide type.", 400);
    }

    await prisma.response.upsert({
      where: { slideId_participantId: { slideId: slide.id, participantId: participant.id } },
      create: {
        sessionId: session.id,
        slideId: slide.id,
        participantId: participant.id,
        value: value as object,
      },
      update: { value: value as object, submittedAt: new Date() },
    });

    const participantCount = await prisma.response.count({ where: { slideId: slide.id } });

    const io = getIO();
    if (io) {
      const payload: ResponseAddedPayload = { sessionId: session.id, slideId: slide.id, participantCount };
      io.to(sessionRoom(session.id)).emit(SOCKET_EVENTS.RESPONSE_ADDED, payload);
    }

    return NextResponse.json({ ok: true });
  });
}
