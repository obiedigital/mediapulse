// Custom server: Next.js request handling + a Socket.io server sharing the
// same HTTP server/port. This is what lets the moderator's results view and
// big-screen mode get pushed updates instead of polling.
import { createServer } from "http";
import next from "next";
import { Server } from "socket.io";
import { setIO } from "./src/lib/socket-server";
import { SOCKET_EVENTS } from "./src/lib/socket-events";

const dev = process.env.NODE_ENV !== "production";
const port = Number(process.env.PORT) || 3000;

const app = next({ dev });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const httpServer = createServer((req, res) => handle(req, res));

  const io = new Server(httpServer, {
    path: "/socket.io",
    // Keep the participant-facing payloads tiny: polling fallback stays
    // available for flaky 3G, but we don't ship extra transports/config.
    cors: { origin: "*" },
  });

  io.on("connection", (socket) => {
    socket.on(SOCKET_EVENTS.JOIN_SESSION, (sessionId: string) => {
      if (typeof sessionId === "string" && sessionId.length > 0) {
        socket.join(`session:${sessionId}`);
      }
    });
  });

  setIO(io);

  httpServer.listen(port, () => {
    console.log(`> PulseCheck ready on http://localhost:${port}`);
  });
});
