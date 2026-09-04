import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { createSessionToken, hashPassword, sessionCookieOptions, SESSION_COOKIE_NAME } from "@/lib/auth";
import { jsonError, withErrorHandling } from "@/lib/api-helpers";

const bodySchema = z.object({
  orgName: z.string().trim().min(2, "Organization name is too short").max(120),
  name: z.string().trim().min(1, "Name is required").max(120),
  email: z.string().trim().toLowerCase().email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

export async function POST(req: Request) {
  return withErrorHandling(async () => {
    const body = bodySchema.parse(await req.json());

    const existing = await prisma.user.findUnique({ where: { email: body.email } });
    if (existing) return jsonError("An account with that email already exists", 409);

    const passwordHash = await hashPassword(body.password);

    const { org, user } = await prisma.$transaction(async (tx) => {
      const org = await tx.organization.create({ data: { name: body.orgName } });
      const user = await tx.user.create({
        data: {
          orgId: org.id,
          name: body.name,
          email: body.email,
          passwordHash,
          role: "owner",
        },
      });
      return { org, user };
    });

    const token = await createSessionToken({ userId: user.id, orgId: org.id, role: user.role });
    const res = NextResponse.json({
      user: { id: user.id, name: user.name, email: user.email, role: user.role },
      org: { id: org.id, name: org.name },
    });
    res.cookies.set(SESSION_COOKIE_NAME, token, sessionCookieOptions());
    return res;
  });
}
