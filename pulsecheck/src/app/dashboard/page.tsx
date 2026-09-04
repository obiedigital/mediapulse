import Link from "next/link";
import { getSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import NewSessionForm from "@/components/NewSessionForm";

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-s3 text-cream/70",
  live: "bg-teal/15 text-teal",
  ended: "bg-cream/10 text-cream/40",
};

export default async function DashboardPage() {
  const session = await getSession();
  const sessions = session
    ? await prisma.session.findMany({
        where: { orgId: session.orgId },
        orderBy: { createdAt: "desc" },
        include: { _count: { select: { participants: true, slides: true } } },
      })
    : [];

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-extrabold">Sessions</h1>
      </div>

      <NewSessionForm />

      <div className="flex flex-col gap-3">
        {sessions.length === 0 && (
          <p className="text-cream/40 text-sm">No sessions yet — create your first one above.</p>
        )}
        {sessions.map((s) => (
          <Link
            key={s.id}
            href={`/dashboard/sessions/${s.id}/edit`}
            className="card p-4 flex items-center justify-between hover:border-line2 transition"
          >
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-semibold">{s.title}</h2>
                <span className={`pill text-[10px] px-2 py-0.5 rounded-full ${STATUS_STYLES[s.status]}`}>
                  {s.status}
                </span>
              </div>
              <p className="text-xs text-cream/40 mt-1">
                {s.type.replace("_", " ")} · code {s.joinCode} · {s._count.slides} slide(s) ·{" "}
                {s._count.participants} participant(s)
              </p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
