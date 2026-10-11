import { DurableObject } from "cloudflare:workers";
import type { Env } from "./index";
import {
  body,
  command,
  type Create,
  failure,
  Fault,
  hash,
  IDLE_MS,
  LOBBY_ACTIVITY_WRITE_MS,
  MAX_LOBBY_MS,
  SOCKET_ACTIVITY_MS,
  join,
  joinByCode,
  json,
  MAX_BYTES,
  parse,
  requireThat,
  secret,
  signal,
  TICKET_MS,
  token,
} from "./protocol";
import {
  apply,
  finish,
  invalidate,
  member,
  projection,
  DEFAULT_NETWORK_PROFILE,
  type State,
} from "./state";
import { normalizeInviteCode, validInviteCode } from "./invite_code";

interface Attachment {
  slot: 0 | 1;
  credential: string;
  connection: string;
  seq: number;
  window: number;
  count: number;
}

export class Room extends DurableObject<Env> {
  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    ctx.storage.sql.exec(
      "CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL)",
    );
    ctx.storage.sql.exec(
      "CREATE TABLE IF NOT EXISTS tickets (digest TEXT PRIMARY KEY, slot INTEGER NOT NULL, credential TEXT NOT NULL, expires INTEGER NOT NULL)",
    );
    ctx.storage.sql.exec(
      "CREATE TABLE IF NOT EXISTS rates (key TEXT PRIMARY KEY, window INTEGER NOT NULL, count INTEGER NOT NULL)",
    );
    // Survives hibernation. Read only while a request is already awake.
    ctx.storage.sql.exec(
      "CREATE TABLE IF NOT EXISTS relayed (id INTEGER PRIMARY KEY AUTOINCREMENT, negotiation TEXT NOT NULL, recipient INTEGER NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL, frame TEXT NOT NULL, UNIQUE (negotiation, kind, payload))",
    );
    ctx.setWebSocketAutoResponse(
      new WebSocketRequestResponsePair("ping", "pong"),
    );
  }
  private read(): State {
    const row = this.ctx.storage.sql
      .exec<{ value: string }>("SELECT value FROM state WHERE id=1")
      .toArray()[0];
    requireThat(row, "room_not_found", 404);
    const state = JSON.parse(row.value) as State;
    requireThat(state.schema === 1, "unsupported_state_schema", 503);
    return state;
  }
  private write(state: State): void {
    this.ctx.storage.sql.exec(
      "INSERT INTO state VALUES (1, ?) ON CONFLICT(id) DO UPDATE SET value=excluded.value",
      JSON.stringify(state),
    );
  }
  private live(): State {
    const state = this.read();
    requireThat(
      state.phase !== "closed" && state.leaseUntil > Date.now(),
      "room_closed",
      410,
    );
    if (state.phase === "preparing" && state.match!.deadline <= Date.now()) {
      finish(state, "start_timeout");
      state.revision++;
      this.write(state);
      this.broadcast(state);
    }
    requireThat(
      state.phase === "active" || state.lastActivity + IDLE_MS > Date.now(),
      "room_expired",
      410,
    );
    return state;
  }
  private slot(state: State, credential: string): 0 | 1 {
    const slot = state.members.findIndex(
      (seat) => seat?.credential === credential,
    );
    requireThat(slot !== -1, "unauthorized", 401);
    return slot as 0 | 1;
  }
  private rate(key: string, limit: number): void {
    const sql = this.ctx.storage.sql;
    const window = Math.floor(Date.now() / 60_000);
    sql.exec("DELETE FROM rates WHERE window < ?", window);
    const row = sql
      .exec<{ count: number }>("SELECT count FROM rates WHERE key=?", key)
      .toArray()[0];
    requireThat((row?.count ?? 0) < limit, "rate_limited", 429);
    sql.exec(
      "INSERT INTO rates VALUES (?, ?, 1) ON CONFLICT(key) DO UPDATE SET count=count+1",
      key,
      window,
    );
  }
  private async schedule(state: State): Promise<void> {
    if (state.phase === "closed") {
      await this.ctx.storage.deleteAlarm();
      return;
    }
    const now = Date.now();
    const heartbeatLive =
      this.socketHeartbeatRecent(now) ||
      state.lastActivity > now - SOCKET_ACTIVITY_MS;
    const socketsOpen = this.ctx.getWebSockets().length > 0;
    let deadline = state.lastActivity + IDLE_MS;
    if (state.phase === "active")
      deadline = heartbeatLive ? now + 5 * 60_000 : state.leaseUntil;
    else if (socketsOpen || heartbeatLive)
      deadline = Math.min(deadline, now + 5 * 60_000);
    if (state.phase === "preparing" && state.match)
      deadline = Math.min(deadline, state.match.deadline);
    if (state.phase === "lobby" && typeof state.createdAt === "number")
      deadline = Math.min(deadline, state.createdAt + MAX_LOBBY_MS);
    deadline = Math.min(deadline, state.leaseUntil);
    if (!(deadline > now)) {
      await this.ctx.storage.deleteAlarm();
      return;
    }
    await this.ctx.storage.setAlarm(deadline);
  }
  private closedMarker(state: State): State {
    return {
      schema: 1,
      id: state.id,
      creationHash: state.creationHash,
      inviteHash: "",
      shortInviteHash: null,
      compatibility: state.compatibility,
      revision: state.revision,
      setupRevision: state.setupRevision,
      members: [member("", ""), null],
      stage: state.stage,
      rules: state.rules,
      phase: "closed",
      match: null,
      lastResult: null,
      negotiation: null,
      lastActivity: 0,
      leaseUntil: 0,
      createdAt: state.createdAt,
    };
  }
  private async shutdown(state: State): Promise<void> {
    if (state.phase !== "closed") {
      state.phase = "closed";
      state.revision++;
    }
    this.broadcast(state);
    this.write(this.closedMarker(state));
    this.ctx.storage.sql.exec("DELETE FROM tickets");
    this.ctx.storage.sql.exec("DELETE FROM rates");
    this.ctx.storage.sql.exec("DELETE FROM relayed");
    await this.env.ADMISSION.getByName("global-v1").release(state.id);
    await this.ctx.storage.deleteAlarm();
  }
  private signalingFlags(state: State, ignore?: WebSocket): [boolean, boolean] {
    const flags: [boolean, boolean] = [false, false];
    for (const socket of this.ctx.getWebSockets()) {
      if (socket === ignore) continue;
      const attached = socket.deserializeAttachment() as Attachment | null;
      if (!attached) continue;
      const seat = state.members[attached.slot];
      if (
        seat &&
        seat.credential === attached.credential &&
        seat.connection === attached.connection
      )
        flags[attached.slot] = true;
    }
    return flags;
  }
  private present(state: State, ignore?: WebSocket): unknown {
    return projection(state, this.signalingFlags(state, ignore));
  }
  private broadcast(state: State, ignore?: WebSocket): void {
    const view = this.present(state, ignore);
    for (const socket of this.ctx.getWebSockets()) {
      if (socket === ignore) continue;
      const attached = socket.deserializeAttachment() as Attachment;
      const seat = state.members[attached.slot];
      if (
        state.phase === "closed" ||
        seat?.credential !== attached.credential ||
        seat.connection !== attached.connection
      ) {
        socket.close(1000, "membership_ended");
      } else this.send(socket, { type: "state", state: view });
    }
  }
  private send(socket: WebSocket, value: unknown): boolean {
    try {
      socket.send(JSON.stringify(value));
      return true;
    } catch {
      return false;
    }
  }
  private rememberRelayed(
    negotiationId: string,
    to: 0 | 1,
    kind: string,
    payload: string,
    frame: Record<string, unknown>,
  ): boolean {
    const sql = this.ctx.storage.sql;
    sql.exec("DELETE FROM relayed WHERE negotiation != ?", negotiationId);
    const duplicate = sql
      .exec<{ id: number }>(
        "SELECT id FROM relayed WHERE negotiation = ? AND kind = ? AND payload = ?",
        negotiationId,
        kind,
        payload,
      )
      .toArray()[0];
    // The same description must not bounce back to the other peer.
    if (duplicate) return false;
    const count =
      sql
        .exec<{ count: number }>(
          "SELECT COUNT(*) AS count FROM relayed WHERE negotiation = ?",
          negotiationId,
        )
        .toArray()[0]?.count ?? 0;
    if (count >= 64) {
      sql.exec(
        "DELETE FROM relayed WHERE id = (SELECT MIN(id) FROM relayed WHERE negotiation = ?)",
        negotiationId,
      );
    }
    sql.exec(
      "INSERT INTO relayed (negotiation, recipient, kind, payload, frame) VALUES (?, ?, ?, ?, ?)",
      negotiationId,
      to,
      kind,
      payload,
      JSON.stringify(frame),
    );
    return true;
  }
  private replayRelayed(
    socket: WebSocket,
    slot: 0 | 1,
    negotiationId: string | undefined,
  ): void {
    const sql = this.ctx.storage.sql;
    if (!negotiationId) {
      sql.exec("DELETE FROM relayed");
      return;
    }
    sql.exec("DELETE FROM relayed WHERE negotiation != ?", negotiationId);
    const rows = sql
      .exec<{ frame: string }>(
        "SELECT frame FROM relayed WHERE negotiation = ? AND recipient = ? ORDER BY id",
        negotiationId,
        slot,
      )
      .toArray();
    for (const row of rows) {
      try {
        this.send(socket, JSON.parse(row.frame));
      } catch {
        /* A corrupt row must not break the socket upgrade. */
      }
    }
  }
  async fetch(request: Request): Promise<Response> {
    try {
      const path = new URL(request.url).pathname;
      if (path === "/internal/create" && request.method === "POST") {
        const { input, id, fingerprint, leaseUntil, shortInviteHash } =
          await request.json<{
            input: Create;
            id: string;
            fingerprint: string;
            leaseUntil: number;
            shortInviteHash?: string;
          }>();
        const [credential, inviteHash] = await Promise.all([
          hash(input.sessionToken),
          hash(input.inviteToken),
        ]);
        const existing = this.ctx.storage.sql
          .exec<{ value: string }>("SELECT value FROM state WHERE id=1")
          .toArray()[0];
        if (existing) {
          const state = this.live();
          requireThat(state.creationHash === fingerprint, "conflicting_create");
          if (state.shortInviteHash === undefined && shortInviteHash) {
            state.shortInviteHash = shortInviteHash;
            this.write(state);
          }
          return json({ roomId: id, slot: 0, state: this.present(state) });
        }
        const state: State = {
          schema: 1,
          id,
          creationHash: fingerprint,
          inviteHash,
          shortInviteHash: shortInviteHash ?? null,
          compatibility: input.compatibility,
          revision: 1,
          setupRevision: 1,
          members: [member(credential, input.nickname), null],
          stage: "现世",
          rules: { time: 90, life: 1 },
          networkProfile: { ...DEFAULT_NETWORK_PROFILE },
          phase: "lobby",
          match: null,
          lastResult: null,
          negotiation: null,
          lastActivity: Date.now(),
          leaseUntil,
          createdAt: Date.now(),
        };
        this.write(state);
        await this.schedule(state);
        return json({ roomId: id, slot: 0, state: this.present(state) }, 201);
      }
      if (path === "/join" && request.method === "POST") {
        const input = parse(join, await body(request));
        const [credential, inviteHash] = await Promise.all([
          hash(input.sessionToken),
          hash(input.inviteToken),
        ]);
        const state = this.live();
        this.rate("join", 20);
        requireThat(state.inviteHash === inviteHash, "invalid_invite", 403);
        requireThat(
          JSON.stringify(input.compatibility) ===
            JSON.stringify(state.compatibility),
          "incompatible_build",
        );
        requireThat(state.phase === "lobby", "not_in_lobby");
        const existing = state.members.findIndex(
          (seat) => seat?.credential === credential,
        );
        if (existing !== -1)
          return json({
            roomId: state.id,
            slot: existing,
            state: this.present(state),
          });
        requireThat(!state.members[1], "room_full");
        state.members[1] = member(credential, input.nickname);
        invalidate(state);
        state.revision++;
        state.lastActivity = Date.now();
        this.write(state);
        this.broadcast(state);
        await this.schedule(state);
        return json(
          { roomId: state.id, slot: 1, state: this.present(state) },
          201,
        );
      }
      if (path === "/join-by-code" && request.method === "POST") {
        const input = parse(joinByCode, await body(request));
        requireThat(validInviteCode(input.code), "invalid_invite", 403);
        const [credential, codeHash] = await Promise.all([
          hash(input.sessionToken),
          hash(normalizeInviteCode(input.code)),
        ]);
        const state = this.live();
        this.rate("join", 20);
        requireThat(state.shortInviteHash === codeHash, "invalid_invite", 403);
        requireThat(
          JSON.stringify(input.compatibility) ===
            JSON.stringify(state.compatibility),
          "incompatible_build",
        );
        requireThat(state.phase === "lobby", "not_in_lobby");
        const existing = state.members.findIndex(
          (seat) => seat?.credential === credential,
        );
        if (existing === 1)
          return json({
            roomId: state.id,
            slot: 1,
            state: this.present(state),
          });
        requireThat(existing === -1, "invalid_invite", 403);
        requireThat(!state.members[1], "room_full");
        state.members[1] = member(credential, input.nickname);
        invalidate(state);
        state.revision++;
        state.lastActivity = Date.now();
        this.write(state);
        this.broadcast(state);
        await this.schedule(state);
        return json(
          { roomId: state.id, slot: 1, state: this.present(state) },
          201,
        );
      }
      if (path === "/socket" && request.method === "GET")
        return await this.upgradeSocket(request);
      const authorization = request.headers.get("Authorization") ?? "";
      requireThat(authorization.startsWith("Bearer "), "unauthorized", 401);
      const credential = await hash(parse(token, authorization.slice(7)));
      // Read after asynchronous hashing; no state transition spans an await.
      let state = this.live();
      const slot = this.slot(state, credential);
      if (path === "/state" && request.method === "GET")
        return json({ slot, state: this.present(state) });
      if (path === "/commands" && request.method === "POST") {
        const input = parse(command, await body(request));
        const requestHash = await hash(JSON.stringify(input));
        const inviteHash =
          input.operation.type === "reinvite"
            ? await hash(input.operation.inviteToken)
            : undefined;
        state = this.live();
        this.slot(state, credential);
        let seat = state.members[slot]!;
        this.rate("commands:" + slot, 120);
        if (input.seq === seat.seq) {
          requireThat(seat.lastCommand === requestHash, "conflicting_retry");
          if (input.operation.type === "reinvite") {
            const admission = this.env.ADMISSION.getByName("global-v1");
            const invite = await admission.prepareReinvite(
              state.id,
              requestHash,
              input.seq,
              state.leaseUntil,
            );
            if (state.shortInviteHash === undefined) {
              state.shortInviteHash = invite.digest;
              seat.lastReply = {
                acceptedSeq: input.seq,
                state: this.present(state),
                inviteCode: invite.code,
              };
              this.write(state);
            }
            requireThat(
              await admission.activateReinvite(
                state.id,
                requestHash,
                input.seq,
              ),
              "invite_code_unavailable",
              503,
            );
            const reply = seat.lastReply as Record<string, unknown>;
            requireThat(reply.inviteCode === invite.code, "invalid_state", 503);
          }
          return json(seat.lastReply);
        }
        requireThat(input.seq === seat.seq + 1, "invalid_sequence");
        let shortInvite: { code: string; digest: string } | undefined;
        if (input.operation.type === "reinvite") {
          requireThat(slot === 0, "owner_required", 403);
          requireThat(state.phase === "lobby", "not_in_lobby");
          shortInvite = await this.env.ADMISSION.getByName(
            "global-v1",
          ).prepareReinvite(state.id, requestHash, input.seq, state.leaseUntil);
          state = this.live();
          requireThat(
            this.slot(state, credential) === 0,
            "owner_required",
            403,
          );
          seat = state.members[0]!;
          if (input.seq === seat.seq) {
            requireThat(seat.lastCommand === requestHash, "conflicting_retry");
            requireThat(
              await this.env.ADMISSION.getByName("global-v1").activateReinvite(
                state.id,
                requestHash,
                input.seq,
              ),
              "invite_code_unavailable",
              503,
            );
            return json(seat.lastReply);
          }
          requireThat(input.seq === seat.seq + 1, "invalid_sequence");
          requireThat(state.phase === "lobby", "not_in_lobby");
        }
        const previousShortInvite = state.shortInviteHash ?? null;
        apply(state, slot, input, Date.now(), inviteHash, shortInvite?.digest);
        seat.seq = input.seq;
        seat.lastCommand = requestHash;
        const reply = {
          acceptedSeq: input.seq,
          state: this.present(state),
          ...(shortInvite ? { inviteCode: shortInvite.code } : {}),
        };
        seat.lastReply = reply;
        this.write(state);
        if (shortInvite) {
          requireThat(
            await this.env.ADMISSION.getByName("global-v1").activateReinvite(
              state.id,
              requestHash,
              input.seq,
            ),
            "invite_code_unavailable",
            503,
          );
        }
        if (
          input.operation.type === "leave" &&
          previousShortInvite &&
          state.phase !== "closed"
        )
          await this.env.ADMISSION.getByName("global-v1").revokeInviteCode(
            state.id,
            previousShortInvite,
          );
        if (input.operation.type === "leave" && state.phase === "closed") {
          await this.shutdown(state);
          return json(reply);
        }
        state = this.read();
        this.broadcast(state);
        await this.schedule(state);
        return json(reply);
      }
      if (path === "/ticket" && request.method === "POST") {
        this.rate("ticket:" + slot, 10);
        const ticket = secret();
        const ticketHash = await hash(ticket);
        state = this.live();
        this.slot(state, credential);
        this.ctx.storage.sql.exec(
          "DELETE FROM tickets WHERE expires <= ? OR slot = ?",
          Date.now(),
          slot,
        );
        this.ctx.storage.sql.exec(
          "INSERT INTO tickets VALUES (?, ?, ?, ?)",
          ticketHash,
          slot,
          credential,
          Date.now() + TICKET_MS,
        );
        return json({ ticket, expiresIn: TICKET_MS / 1000 });
      }
      if (path === "/ice" && request.method === "POST") {
        this.rate("ice:" + slot, 4);
        return await this.ice(state, slot);
      }
      throw new Fault(405, "method_not_allowed");
    } catch (error) {
      return failure(error);
    }
  }
  private async upgradeSocket(request: Request): Promise<Response> {
    requireThat(
      request.headers.get("Upgrade")?.toLowerCase() === "websocket",
      "websocket_required",
      426,
    );
    const protocols = (request.headers.get("Sec-WebSocket-Protocol") ?? "")
      .split(",")
      .map((value) => value.trim());
    requireThat(
      protocols.length === 2 && protocols[0] === "bvn.v1",
      "invalid_socket_protocol",
      400,
    );
    const ticketHash = await hash(parse(token, protocols[1]));
    const state = this.live();
    const ticket = this.ctx.storage.sql
      .exec<{ slot: 0 | 1; credential: string; expires: number }>(
        "DELETE FROM tickets WHERE digest = ? RETURNING slot, credential, expires",
        ticketHash,
      )
      .toArray()[0];
    requireThat(ticket && ticket.expires > Date.now(), "invalid_ticket", 401);
    requireThat(
      state.members[ticket.slot]?.credential === ticket.credential,
      "unauthorized",
      401,
    );
    const connection = crypto.randomUUID();
    state.members[ticket.slot]!.connection = connection;
    // A replacement closes the previous socket below. It must not drop an
    // in-flight negotiation: the new socket continues the same id.
    state.revision++;
    state.lastActivity = Date.now();
    this.write(state);
    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);
    this.ctx.acceptWebSocket(server);
    server.serializeAttachment({
      slot: ticket.slot,
      credential: ticket.credential,
      connection,
      seq: -1,
      window: 0,
      count: 0,
    } satisfies Attachment);
    this.broadcast(state);
    // The new socket did not see signals delivered to the connection it replaced.
    this.replayRelayed(server, ticket.slot, state.negotiation?.id);
    await this.schedule(state);
    return new Response(null, {
      status: 101,
      webSocket: client,
      headers: { "Sec-WebSocket-Protocol": "bvn.v1" },
    });
  }
  async webSocketMessage(
    socket: WebSocket,
    message: string | ArrayBuffer,
  ): Promise<void> {
    try {
      requireThat(
        typeof message === "string" &&
          new TextEncoder().encode(message).length <= MAX_BYTES,
        "message_too_large",
        413,
      );
      const state = this.live();
      const attached = socket.deserializeAttachment() as Attachment;
      const seat = state.members[attached.slot];
      requireThat(
        seat?.credential === attached.credential &&
          seat.connection === attached.connection,
        "unauthorized",
        401,
      );
      const window = Math.floor(Date.now() / 60_000);
      attached.count = attached.window === window ? attached.count + 1 : 1;
      attached.window = window;
      socket.serializeAttachment(attached);
      requireThat(attached.count <= 120, "rate_limited", 429);
      this.rate("signals", 240);
      const now = Date.now();
      const createdAt = state.createdAt ?? state.lastActivity;
      if (
        state.phase === "lobby" &&
        createdAt + MAX_LOBBY_MS > now &&
        now - state.lastActivity >= LOBBY_ACTIVITY_WRITE_MS
      ) {
        state.lastActivity = now;
        this.write(state);
        await this.schedule(state);
      }
      let decoded: unknown;
      try {
        decoded = JSON.parse(message);
      } catch {
        throw new Fault(400, "invalid_json");
      }
      const input = parse(signal, decoded);
      requireThat(input.seq > attached.seq, "invalid_sequence");
      const negotiation = state.negotiation;
      if (
        !negotiation ||
        negotiation.id !== input.negotiationId ||
        negotiation.epoch !== input.epoch ||
        negotiation.expires <= Date.now()
      ) {
        this.send(socket, {
          type: "error",
          error: "stale_negotiation",
          negotiationId: input.negotiationId,
        });
        return;
      }
      requireThat(input.epoch === (state.match?.epoch ?? null), "stale_epoch");
      requireThat(
        (input.kind !== "offer" || attached.slot === 0) &&
          (input.kind !== "answer" || attached.slot === 1),
        "invalid_signal_role",
        403,
      );
      attached.seq = input.seq;
      socket.serializeAttachment(attached);
      const peerSlot = attached.slot === 0 ? 1 : 0;
      const frame = { ...input, from: attached.slot };
      const fresh = this.rememberRelayed(
        negotiation.id,
        peerSlot,
        input.kind,
        input.payload,
        frame,
      );
      if (!fresh) {
        this.send(socket, {
          type: "signal_ack",
          seq: input.seq,
          delivered: true,
        });
        return;
      }
      let delivered = false;
      for (const peer of this.ctx.getWebSockets()) {
        const target = peer.deserializeAttachment() as Attachment;
        if (
          target.slot === peerSlot &&
          target.credential === state.members[peerSlot]?.credential &&
          target.connection === state.members[peerSlot]?.connection
        )
          delivered = this.send(peer, frame) || delivered;
      }
      this.send(socket, { type: "signal_ack", seq: input.seq, delivered });
    } catch (error) {
      this.send(socket, {
        type: "error",
        error: error instanceof Fault ? error.code : "internal_error",
      });
      if (
        !(error instanceof Fault) ||
        [401, 410, 413, 429].includes(error.status)
      )
        socket.close(1008, "protocol_error");
    }
  }
  webSocketClose(socket: WebSocket): void {
    // Transport loss is not a voluntary departure. A replacement already
    // broadcast while the new connection id was current; closing the old
    // socket must not broadcast again.
    try {
      const state = this.read();
      if (state.phase === "closed") return;
      const attached = socket.deserializeAttachment() as Attachment | null;
      const seat = attached ? state.members[attached.slot] : undefined;
      if (
        !attached ||
        !seat ||
        seat.credential !== attached.credential ||
        seat.connection !== attached.connection
      )
        return;
      this.broadcast(state, socket);
    } catch {
      /* The room row may already be gone. */
    }
  }
  webSocketError(socket: WebSocket): void {
    socket.close(1011, "socket_error");
  }
  private async ice(state: State, slot: 0 | 1): Promise<Response> {
    requireThat(
      this.env.TURN_KEY_ID && this.env.TURN_API_TOKEN,
      "turn_not_configured",
      503,
    );
    requireThat(
      /^[a-f0-9]{32}$/.test(this.env.TURN_KEY_ID),
      "turn_misconfigured",
      503,
    );
    const ttl = 4 * 60 * 60;
    let response: Response;
    try {
      response = await fetch(
        `https://rtc.live.cloudflare.com/v1/turn/keys/${this.env.TURN_KEY_ID}/credentials/generate-ice-servers`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${this.env.TURN_API_TOKEN}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ ttl }),
        },
      );
    } catch {
      throw new Fault(503, "turn_unavailable");
    }
    requireThat(response.ok, "turn_unavailable", 503);
    const issued = (await response.json()) as { iceServers?: unknown };
    requireThat(
      Array.isArray(issued.iceServers) && issued.iceServers.length > 0,
      "turn_unavailable",
      503,
    );
    // Revalidate membership after issuer work; revocation must win races.
    const current = this.live();
    requireThat(
      current.members[slot]?.credential === state.members[slot]?.credential,
      "unauthorized",
      401,
    );
    return json({ iceServers: issued.iceServers, expiresIn: ttl });
  }
  private socketHeartbeatRecent(now: number): boolean {
    return this.ctx.getWebSockets().some((socket) => {
      const last =
        this.ctx.getWebSocketAutoResponseTimestamp(socket)?.getTime() ?? 0;
      return last > now - SOCKET_ACTIVITY_MS;
    });
  }
  async alarm(): Promise<void> {
    let state = this.read();
    if (state.phase === "closed") {
      await this.ctx.storage.deleteAlarm();
      return;
    }
    const now = Date.now();
    let persist = false;
    if (typeof state.createdAt !== "number") {
      state.createdAt = state.lastActivity;
      persist = true;
    }
    let visible = false;
    if (state.phase === "preparing" && state.match!.deadline <= now) {
      finish(state, "start_timeout");
      state.revision++;
      persist = true;
      visible = true;
    }
    const lobbyExpired =
      state.phase === "lobby" && state.createdAt + MAX_LOBBY_MS <= now;
    // Ping is auto-answered and does not enter webSocketMessage. Read the
    // hibernated auto-response timestamp here, and only persist a change.
    if (
      state.phase === "lobby" &&
      !lobbyExpired &&
      this.socketHeartbeatRecent(now) &&
      now - state.lastActivity >= LOBBY_ACTIVITY_WRITE_MS
    ) {
      state.lastActivity = now;
      persist = true;
      visible = true;
    }
    const expired =
      lobbyExpired ||
      state.leaseUntil <= now ||
      (state.phase !== "active" && state.lastActivity + IDLE_MS <= now);
    if (expired) {
      await this.shutdown(state);
      return;
    }
    if (persist) this.write(state);
    const renewLease =
      state.phase !== "active" ||
      this.socketHeartbeatRecent(now) ||
      state.lastActivity > now - SOCKET_ACTIVITY_MS;
    if (renewLease) {
      const expires = await this.env.ADMISSION.getByName("global-v1").renew(
        state.id,
      );
      state = this.read();
      if (state.phase === "closed") {
        await this.ctx.storage.deleteAlarm();
        return;
      }
      if (!expires) {
        await this.shutdown(state);
        return;
      }
      if (state.leaseUntil !== expires) {
        state.leaseUntil = expires;
        this.write(state);
      }
    }
    if (visible) this.broadcast(state);
    await this.schedule(state);
  }
}
