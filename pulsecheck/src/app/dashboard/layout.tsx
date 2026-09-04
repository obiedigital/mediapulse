import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import LogoutButton from "@/components/LogoutButton";
import Link from "next/link";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession();
  if (!session) redirect("/login");

  const user = await prisma.user.findUnique({
    where: { id: session.userId },
    include: { org: true },
  });
  if (!user) redirect("/login");

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-line">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2 font-display text-lg font-extrabold">
            <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-or to-teal flex items-center justify-center text-ink text-xs">
              PC
            </span>
            PulseCheck
          </Link>
          <div className="flex items-center gap-4 text-sm text-cream/60">
            <span>{user.org.name}</span>
            <span className="text-cream/30">·</span>
            <span>{user.name}</span>
            <LogoutButton />
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-8">{children}</main>
    </div>
  );
}
