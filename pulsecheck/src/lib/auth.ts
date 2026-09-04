import { cookies } from "next/headers";
import { SignJWT, jwtVerify } from "jose";
import bcrypt from "bcryptjs";

// --- Moderator auth ---------------------------------------------------
//
// The build brief allows Clerk or Supabase Auth for moderator accounts.
// Neither is wired up here because both need a live external project
// (API keys, a configured tenant) that this build can't provision for
// you. Instead this is a small, self-contained email/password + signed
// session-cookie flow — same shape (a `session` you can read server-side
// to get { userId, orgId, role }), so swapping in Clerk/Supabase later
// means replacing this file and the /login, /signup routes, not the
// rest of the app. Every other route reads the session through
// `getSession()` / `requireSession()` below, so the swap is contained.

const COOKIE_NAME = "pc_session";
const SESSION_TTL_SECONDS = 60 * 60 * 24 * 30; // 30 days

function getSecretKey() {
  const secret = process.env.AUTH_SECRET;
  if (!secret || secret.length < 16) {
    throw new Error(
      "AUTH_SECRET is missing or too short. Set a long random value in .env (see .env.example)."
    );
  }
  return new TextEncoder().encode(secret);
}

export interface SessionPayload {
  userId: string;
  orgId: string;
  role: string;
}

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10);
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

export async function createSessionToken(payload: SessionPayload): Promise<string> {
  return new SignJWT({ ...payload })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(`${SESSION_TTL_SECONDS}s`)
    .sign(getSecretKey());
}

export async function verifySessionToken(token: string): Promise<SessionPayload | null> {
  try {
    const { payload } = await jwtVerify(token, getSecretKey());
    if (typeof payload.userId === "string" && typeof payload.orgId === "string") {
      return {
        userId: payload.userId,
        orgId: payload.orgId,
        role: typeof payload.role === "string" ? payload.role : "member",
      };
    }
    return null;
  } catch {
    return null;
  }
}

/** Read + verify the moderator session cookie in a server component or route handler. */
export async function getSession(): Promise<SessionPayload | null> {
  const token = cookies().get(COOKIE_NAME)?.value;
  if (!token) return null;
  return verifySessionToken(token);
}

export async function requireSession(): Promise<SessionPayload> {
  const session = await getSession();
  if (!session) {
    throw new AuthError("Not authenticated");
  }
  return session;
}

export class AuthError extends Error {}

export function sessionCookieOptions() {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    maxAge: SESSION_TTL_SECONDS,
  };
}

export const SESSION_COOKIE_NAME = COOKIE_NAME;
