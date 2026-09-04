import { notFound, redirect } from "next/navigation";
import { getSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import SessionBuilder from "@/components/SessionBuilder";

export default async function EditSessionPage({ params }: { params: { id: string } }) {
  const auth = await getSession();
  if (!auth) redirect("/login");

  const session = await prisma.session.findUnique({ where: { id: params.id } });
  if (!session || session.orgId !== auth.orgId) notFound();

  const slides = await prisma.sessionSlide.findMany({
    where: { sessionId: session.id },
    orderBy: { order: "asc" },
  });

  return (
    <SessionBuilder
      session={{
        id: session.id,
        title: session.title,
        type: session.type,
        status: session.status,
        joinCode: session.joinCode,
      }}
      initialSlides={slides.map((s) => ({
        id: s.id,
        order: s.order,
        type: s.type,
        config: s.config as Record<string, unknown>,
      }))}
    />
  );
}
