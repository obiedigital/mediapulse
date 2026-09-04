import { NextResponse } from "next/server";
import { ZodError } from "zod";
import { AuthError, getSession } from "./auth";
import { prisma } from "./prisma";

export function jsonError(message: string, status = 400) {
  return NextResponse.json({ error: message }, { status });
}

/** Wrap a route handler: turns AuthError/ZodError/not-found into clean HTTP responses. */
export function withErrorHandling(fn: () => Promise<Response>): Promise<Response> {
  return fn().catch((err) => {
    if (err instanceof AuthError) return jsonError("Not authenticated", 401);
    if (err instanceof ZodError) {
      return jsonError(err.errors.map((e) => e.message).join("; "), 422);
    }
    if (err instanceof NotFoundError) return jsonError(err.message, 404);
    if (err instanceof ForbiddenError) return jsonError(err.message, 403);
    console.error(err);
    return jsonError("Internal server error", 500);
  });
}

export class NotFoundError extends Error {}
export class ForbiddenError extends Error {}

/** Load a session by id and assert it belongs to the current moderator's org. */
export async function getOwnedSession(sessionId: string) {
  const session = await getSession();
  if (!session) throw new (await import("./auth")).AuthError("Not authenticated");

  const record = await prisma.session.findUnique({ where: { id: sessionId } });
  if (!record) throw new NotFoundError("Session not found");
  if (record.orgId !== session.orgId) throw new ForbiddenError("Session belongs to another organization");

  return { record, moderator: session };
}
