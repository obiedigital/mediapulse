import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { createSessionToken, verifyPassword, sessionCookieOptions, SESSION_COOKIE_NAME } from "@/lib/auth";
import { jsonError, withErrorHandling } from "@/lib/api-helpers";

const bodySchema = z.object({
  email: z.string().trim().toLowerCase().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

export async function POST(req: Request) {
  return withErrorHandling(async () => {
    const body = bodySchema.parse(await req.json());

    const user = await prisma.user.findUnique({ where: { email: body.email } });
    if (!user || !(await verifyPassword(body.password, user.passwordHash))) {
      return jsonError("Invalid email or password", 401);
    }

    const token = await createSessionToken({ userId: user.id, orgId: user.orgId, role: user.role });
    const res = NextResponse.json({
      user: { id: user.id, name: user.name, email: user.email, role: user.role },
    });
    res.cookies.set(SESSION_COOKIE_NAME, token, sessionCookieOptions());
    return res;
  });
}
