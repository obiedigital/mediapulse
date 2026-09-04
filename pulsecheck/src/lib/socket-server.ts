import type { Server as IOServer } from "socket.io";

// The Socket.io server lives in the same Node process as Next.js (see
// server.ts) but is created outside of Next's request lifecycle. API route
// handlers reach it through this tiny singleton instead of importing
// server.ts directly (which would drag in the http.Server bootstrap).
const g = globalThis as unknown as { __pulsecheckIO?: IOServer };

export function setIO(io: IOServer) {
  g.__pulsecheckIO = io;
}

export function getIO(): IOServer | undefined {
  return g.__pulsecheckIO;
}
