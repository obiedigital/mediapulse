// Shared event/channel names between server and client so both sides stay
// in sync without a magic-string typo somewhere.

/** Room a moderator's results view + big-screen mode join. */
export function sessionRoom(sessionId: string) {
  return `session:${sessionId}`;
}

export const SOCKET_EVENTS = {
  /** Client -> server: join the room for a session (moderator or participant). */
  JOIN_SESSION: "join_session",
  /** Server -> room: a new response was recorded (participant count + slide id). */
  RESPONSE_ADDED: "response_added",
  /** Server -> room: session status changed (draft/live/ended) or active slide changed. */
  SESSION_STATE: "session_state",
} as const;

export interface ResponseAddedPayload {
  sessionId: string;
  slideId: string;
  participantCount: number;
}

export interface SessionStatePayload {
  sessionId: string;
  status: "draft" | "live" | "ended";
  activeSlideOrder?: number | null;
}
