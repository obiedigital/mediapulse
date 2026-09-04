import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { requireSession } from "@/lib/auth";
import { generateJoinCode } from "@/lib/codegen";
import { withErrorHandling } from "@/lib/api-helpers";

const createSchema = z.object({
  title: z.string().trim().min(1, "Title is required").max(200),
  type: z
    .enum(["concept_test", "ad_recall", "brand_pulse", "focus_group", "custom"])
    .default("custom"),
});

export async function GET() {
  return withErrorHandling(async () => {
    const session = await requireSession();
    const sessions = await prisma.session.findMany({
      where: { orgId: session.orgId },
      orderBy: { createdAt: "desc" },
      include: { _count: { select: { participants: true, slides: true } } },
    });
    return NextResponse.json({ sessions });
  });
}

export async function POST(req: Request) {
  return withErrorHandling(async () => {
    const session = await requireSession();
    const body = createSchema.parse(await req.json());
    const joinCode = await generateJoinCode();

    const created = await prisma.session.create({
      data: {
        orgId: session.orgId,
        createdById: session.userId,
        title: body.title,
        type: body.type,
        joinCode,
      },
    });

    return NextResponse.json({ session: created }, { status: 201 });
  });
}
