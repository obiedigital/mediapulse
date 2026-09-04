import { prisma } from "./prisma";

/** Generate a 6-digit numeric join code with no leading zero, unique among active sessions. */
export async function generateJoinCode(): Promise<string> {
  for (let attempt = 0; attempt < 25; attempt++) {
    const code = String(Math.floor(100000 + Math.random() * 900000));
    const existing = await prisma.session.findUnique({ where: { joinCode: code } });
    if (!existing) return code;
  }
  throw new Error("Could not generate a unique join code, please retry.");
}
