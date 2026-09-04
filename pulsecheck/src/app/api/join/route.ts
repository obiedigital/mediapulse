import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { jsonError, withErrorHandling } from "@/lib/api-helpers";

const bodySchema = z.object({
  code: z
    .string()
    .trim()
    .regex(/^\d{6}$/, "Enter the 6-digit code"),
  ageBand: z.string().trim().max(20).optional(),
  region: z.string().trim().max(60).optional(),
  deviceFingerprint: z.string().trim().max(200).optional(),
});

export async function POST(req: Request) {
  return withErrorHandling(async () => {
    const body = bodySchema.parse(await req.json());

    const session = await prisma.session.findUnique({ where: { joinCode: body.code } });
    if (!session || session.status === "ended") {
      return jsonError("That code isn't active. Check with your host.", 404);
    }

    const participant = await prisma.participant.create({
      data: {
        sessionId: session.id,
        joinCode: body.code,
        deviceFingerprint: body.deviceFingerprint,
        demographicTags: {
          ...(body.ageBand ? { age_band: body.ageBand } : {}),
          ...(body.region ? { region: body.region } : {}),
        },
      },
    });

    return NextResponse.json({
      participantId: participant.id,
      sessionId: session.id,
      title: session.title,
      status: session.status,
    });
  });
}
