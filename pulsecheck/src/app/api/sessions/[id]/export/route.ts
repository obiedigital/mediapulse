import { prisma } from "@/lib/prisma";
import { getOwnedSession, withErrorHandling } from "@/lib/api-helpers";
import { buildSessionPdf } from "@/lib/pdf";

export async function GET(_req: Request, { params }: { params: { id: string } }) {
  return withErrorHandling(async () => {
    const { record } = await getOwnedSession(params.id);

    const [slides, responses, participantCount] = await Promise.all([
      prisma.sessionSlide.findMany({ where: { sessionId: record.id }, orderBy: { order: "asc" } }),
      prisma.response.findMany({
        where: { sessionId: record.id },
        include: { participant: { select: { id: true, demographicTags: true } } },
        orderBy: { submittedAt: "asc" },
      }),
      prisma.participant.count({ where: { sessionId: record.id } }),
    ]);

    const pdf = await buildSessionPdf(
      { ...record, participantCount },
      slides,
      responses
    );

    return new Response(new Uint8Array(pdf), {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="${record.title.replace(/[^a-z0-9]+/gi, "-")}-results.pdf"`,
      },
    });
  });
}
