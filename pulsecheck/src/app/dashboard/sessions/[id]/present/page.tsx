import { notFound, redirect } from "next/navigation";
import { getSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import PresentView from "@/components/PresentView";

export default async function PresentSessionPage({ params }: { params: { id: string } }) {
  const auth = await getSession();
  if (!auth) redirect("/login");

  const session = await prisma.session.findUnique({ where: { id: params.id } });
  if (!session || session.orgId !== auth.orgId) notFound();

  const slides = await prisma.sessionSlide.findMany({
    where: { sessionId: session.id },
    orderBy: { order: "asc" },
  });

  return (
    <PresentView
      session={{
        id: session.id,
        title: session.title,
        status: session.status,
        activeSlideOrder: session.activeSlideOrder,
        joinCode: session.joinCode,
      }}
      slides={slides.map((s) => ({
        id: s.id,
        order: s.order,
        type: s.type,
        config: s.config as Record<string, unknown>,
      }))}
    />
  );
}
