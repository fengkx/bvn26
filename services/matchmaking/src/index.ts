import { DurableObject } from "cloudflare:workers";
import {
  body,
  create,
  failure,
  Fault,
  hash,
  IDLE_MS,
  INVITE_TOMBSTONE_MS,
  json,
  joinByCode,
  parse,
  requireThat,
} from "./protocol";
import {
  generateInviteCode,
  normalizeInviteCode,
  validInviteCode,
} from "./invite_code";
export { Room } from "./room";
import type { Room } from "./room";

export interface Env {
  ROOMS: DurableObjectNamespace<Room>;
  ADMISSION: DurableObjectNamespace<Admission>;
  TURN_KEY_ID?: string;
  TURN_API_TOKEN?: string;
}

async function attachInviteCode(
  response: Response,
  inviteCode: string,
): Promise<Response> {
  if (!response.ok) return response;
  const value = (await response.json()) as Record<string, unknown>;
  return json({ ...value, inviteCode }, response.status);
}

export class Admission extends DurableObject<Env> {
  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    ctx.storage.sql.exec(
      "CREATE TABLE IF NOT EXISTS leases (id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, expires INTEGER NOT NULL)",
    );
    ctx.storage.sql.exec(
      "CREATE TABLE IF NOT EXISTS rates (key TEXT PRIMARY KEY, window INTEGER NOT NULL, count INTEGER NOT NULL)",
    );
    ctx.storage.sql.exec(
      "CREATE TABLE IF NOT EXISTS invite_codes (digest TEXT PRIMARY KEY, room_id TEXT NOT NULL, purpose TEXT NOT NULL, code TEXT NOT NULL, status TEXT NOT NULL, guest_hash TEXT, generation INTEGER NOT NULL, expires INTEGER NOT NULL, UNIQUE(room_id, purpose))",
    );
    ctx.storage.sql.exec(
      "CREATE TABLE IF NOT EXISTS invite_generations (room_id TEXT PRIMARY KEY, generation INTEGER NOT NULL)",
    );
    const inviteCodeColumns = ctx.storage.sql
      .exec<{ name: string }>("PRAGMA table_info(invite_codes)")
      .toArray();
    if (!inviteCodeColumns.some((column) => column.name === "generation"))
      ctx.storage.sql.exec(
        "ALTER TABLE invite_codes ADD COLUMN generation INTEGER NOT NULL DEFAULT 0",
      );
    const inviteRooms = ctx.storage.sql
      .exec<{ room_id: string; generation: number }>(
        "SELECT room_id, MAX(generation) AS generation FROM invite_codes WHERE status IN ('active', 'used') GROUP BY room_id",
      )
      .toArray();
    for (const room of inviteRooms)
      ctx.storage.sql.exec(
        "INSERT INTO invite_generations VALUES (?, ?) ON CONFLICT(room_id) DO UPDATE SET generation = MAX(generation, excluded.generation)",
        room.room_id,
        room.generation,
      );
  }
  rate(key: string, limit: number): boolean {
    const sql = this.ctx.storage.sql;
    const window = Math.floor(Date.now() / 60_000);
    sql.exec("DELETE FROM rates WHERE window < ?", window);
    const row = sql
      .exec<{ count: number }>("SELECT count FROM rates WHERE key = ?", key)
      .toArray()[0];
    if ((row?.count ?? 0) >= limit) return false;
    if (
      !row &&
      sql.exec<{ n: number }>("SELECT COUNT(*) n FROM rates").one().n >= 1024
    )
      return false;
    sql.exec(
      "INSERT INTO rates VALUES (?, ?, 1) ON CONFLICT(key) DO UPDATE SET count = count + 1",
      key,
      window,
    );
    return true;
  }
  async allocate(
    id: string,
    fingerprint: string,
  ): Promise<{ error?: string; expires?: number }> {
    const sql = this.ctx.storage.sql;
    const now = Date.now();
    sql.exec("DELETE FROM leases WHERE expires <= ?", now);
    sql.exec("DELETE FROM invite_codes WHERE expires <= ?", now);
    sql.exec(
      "DELETE FROM invite_generations WHERE room_id NOT IN (SELECT id FROM leases)",
    );
    const existing = sql
      .exec<{ fingerprint: string; expires: number }>(
        "SELECT fingerprint, expires FROM leases WHERE id = ?",
        id,
      )
      .toArray()[0];
    if (existing)
      return existing.fingerprint === fingerprint
        ? { expires: existing.expires }
        : { error: "conflicting_create" };
    if (sql.exec<{ n: number }>("SELECT COUNT(*) n FROM leases").one().n >= 10)
      return { error: "capacity_reached" };
    const expires = now + IDLE_MS;
    sql.exec("INSERT INTO leases VALUES (?, ?, ?)", id, fingerprint, expires);
    await this.scheduleCleanup();
    return { expires };
  }
  lookup(id: string): number | null {
    return (
      this.ctx.storage.sql
        .exec<{ expires: number }>(
          "SELECT expires FROM leases WHERE id = ? AND expires > ?",
          id,
          Date.now(),
        )
        .toArray()[0]?.expires ?? null
    );
  }
  protected makeInviteCode(): string {
    return generateInviteCode();
  }
  async createInviteCode(
    roomId: string,
    expires: number,
  ): Promise<{ code: string; digest: string }> {
    const sql = this.ctx.storage.sql;
    const existing = sql
      .exec<{ code: string; digest: string }>(
        "SELECT code, digest FROM invite_codes WHERE room_id = ? AND purpose = 'create'",
        roomId,
      )
      .toArray()[0];
    if (existing) return existing;
    for (let attempt = 0; attempt < 8; attempt++) {
      const code = this.makeInviteCode();
      const digest = await hash(code);
      try {
        sql.exec(
          "INSERT INTO invite_codes (digest, room_id, purpose, code, status, guest_hash, generation, expires) VALUES (?, ?, 'create', ?, 'active', NULL, 0, ?)",
          digest,
          roomId,
          code,
          expires,
        );
        sql.exec(
          "INSERT INTO invite_generations VALUES (?, 0) ON CONFLICT(room_id) DO NOTHING",
          roomId,
        );
        return { code, digest };
      } catch {
        const winner = sql
          .exec<{ code: string; digest: string }>(
            "SELECT code, digest FROM invite_codes WHERE room_id = ? AND purpose = 'create'",
            roomId,
          )
          .toArray()[0];
        if (winner) return winner;
      }
    }
    throw new Fault(503, "invite_code_unavailable");
  }
  async prepareReinvite(
    roomId: string,
    commandKey: string,
    generation: number,
    expires: number,
  ): Promise<{ code: string; digest: string }> {
    const sql = this.ctx.storage.sql;
    const purpose = `reinvite:${commandKey}`;
    const existing = sql
      .exec<{ code: string; digest: string }>(
        "SELECT code, digest FROM invite_codes WHERE room_id = ? AND purpose = ?",
        roomId,
        purpose,
      )
      .toArray()[0];
    if (existing) {
      sql.exec(
        "UPDATE invite_codes SET generation = ? WHERE room_id = ? AND purpose = ? AND status IN ('pending', 'active', 'used')",
        generation,
        roomId,
        purpose,
      );
      return existing;
    }
    for (let attempt = 0; attempt < 8; attempt++) {
      const code = this.makeInviteCode();
      const digest = await hash(code);
      try {
        sql.exec(
          "INSERT INTO invite_codes (digest, room_id, purpose, code, status, guest_hash, generation, expires) VALUES (?, ?, ?, ?, 'pending', NULL, ?, ?)",
          digest,
          roomId,
          purpose,
          code,
          generation,
          expires,
        );
        return { code, digest };
      } catch {
        const winner = sql
          .exec<{ code: string; digest: string }>(
            "SELECT code, digest FROM invite_codes WHERE room_id = ? AND purpose = ?",
            roomId,
            purpose,
          )
          .toArray()[0];
        if (winner) return winner;
      }
    }
    throw new Fault(503, "invite_code_unavailable");
  }
  activateReinvite(
    roomId: string,
    commandKey: string,
    generation: number,
  ): boolean {
    const sql = this.ctx.storage.sql;
    const purpose = `reinvite:${commandKey}`;
    const target = sql
      .exec<{ status: string; generation: number; expires: number }>(
        "SELECT status, generation, expires FROM invite_codes WHERE room_id = ? AND purpose = ?",
        roomId,
        purpose,
      )
      .toArray()[0];
    if (
      !target ||
      target.generation !== generation ||
      target.expires <= Date.now()
    )
      return false;
    const latestGeneration =
      sql
        .exec<{ generation: number }>(
          "SELECT generation FROM invite_generations WHERE room_id = ?",
          roomId,
        )
        .toArray()[0]?.generation ?? 0;
    if (target.status === "active" || target.status === "used") return true;
    if (target.status === "revoked") return true;
    if (generation < latestGeneration) {
      sql.exec(
        "UPDATE invite_codes SET status = 'revoked' WHERE room_id = ? AND purpose = ?",
        roomId,
        purpose,
      );
      return true;
    }
    sql.exec(
      "UPDATE invite_codes SET status = 'revoked' WHERE room_id = ? AND status IN ('active', 'used') AND purpose != ?",
      roomId,
      purpose,
    );
    sql.exec(
      "UPDATE invite_codes SET status = 'active', guest_hash = NULL WHERE room_id = ? AND purpose = ?",
      roomId,
      purpose,
    );
    sql.exec(
      "INSERT INTO invite_generations VALUES (?, ?) ON CONFLICT(room_id) DO UPDATE SET generation = MAX(generation, excluded.generation)",
      roomId,
      generation,
    );
    return true;
  }
  lookupInviteCode(
    digest: string,
    guestHash: string,
  ): { roomId: string } | { error: "invite_expired" | "invalid_invite" } {
    const row = this.ctx.storage.sql
      .exec<{
        room_id: string;
        status: string;
        guest_hash: string | null;
        expires: number;
      }>(
        "SELECT room_id, status, guest_hash, expires FROM invite_codes WHERE digest = ?",
        digest,
      )
      .toArray()[0];
    if (!row) return { error: "invalid_invite" };
    if (row.expires <= Date.now()) {
      this.ctx.storage.sql.exec(
        "DELETE FROM invite_codes WHERE digest = ?",
        digest,
      );
      return row.status === "active" ||
        row.status === "used" ||
        row.status === "expired"
        ? { error: "invite_expired" }
        : { error: "invalid_invite" };
    }
    if (row.status === "expired") return { error: "invite_expired" };
    if (row.status === "active") return { roomId: row.room_id };
    if (row.status === "used" && row.guest_hash === guestHash)
      return { roomId: row.room_id };
    return { error: "invalid_invite" };
  }
  consumeInviteCode(
    digest: string,
    roomId: string,
    guestHash: string,
  ): boolean {
    const sql = this.ctx.storage.sql;
    const row = sql
      .exec<{
        room_id: string;
        status: string;
        guest_hash: string | null;
        expires: number;
      }>(
        "SELECT room_id, status, guest_hash, expires FROM invite_codes WHERE digest = ?",
        digest,
      )
      .toArray()[0];
    if (!row || row.room_id !== roomId || row.expires <= Date.now())
      return false;
    if (row.status === "used") return row.guest_hash === guestHash;
    if (row.status !== "active") return false;
    sql.exec(
      "UPDATE invite_codes SET status = 'used', guest_hash = ? WHERE digest = ? AND status = 'active'",
      guestHash,
      digest,
    );
    const current = sql
      .exec<{ status: string; guest_hash: string | null }>(
        "SELECT status, guest_hash FROM invite_codes WHERE digest = ?",
        digest,
      )
      .toArray()[0];
    return current?.status === "used" && current.guest_hash === guestHash;
  }
  revokeInviteCode(roomId: string, digest: string): void {
    this.ctx.storage.sql.exec(
      "UPDATE invite_codes SET status = 'revoked' WHERE room_id = ? AND digest = ?",
      roomId,
      digest,
    );
  }
  renew(id: string): number | null {
    const expires = Date.now() + IDLE_MS;
    const rows = this.ctx.storage.sql
      .exec<{ expires: number }>(
        "UPDATE leases SET expires = ? WHERE id = ? AND expires > ? RETURNING expires",
        expires,
        id,
        Date.now(),
      )
      .toArray();
    if (rows[0])
      this.ctx.storage.sql.exec(
        "UPDATE invite_codes SET expires = ? WHERE room_id = ? AND status IN ('active', 'used', 'pending')",
        expires,
        id,
      );
    return rows[0]?.expires ?? null;
  }
  release(id: string): void {
    const retainUntil = Date.now() + INVITE_TOMBSTONE_MS;
    this.ctx.storage.sql.exec("DELETE FROM leases WHERE id = ?", id);
    // Only codes a guest could have seen become invite_expired tombstones.
    this.ctx.storage.sql.exec(
      "UPDATE invite_codes SET status = 'expired', expires = ? WHERE room_id = ? AND status IN ('active', 'used')",
      retainUntil,
      id,
    );
    this.ctx.storage.sql.exec(
      "DELETE FROM invite_codes WHERE room_id = ? AND status != 'expired'",
      id,
    );
    this.ctx.storage.sql.exec(
      "DELETE FROM invite_generations WHERE room_id = ?",
      id,
    );
  }
  private nextExpiry(): number | null {
    const lease = this.ctx.storage.sql
      .exec<{ expires: number | null }>(
        "SELECT MIN(expires) AS expires FROM leases",
      )
      .one().expires;
    const code = this.ctx.storage.sql
      .exec<{ expires: number | null }>(
        "SELECT MIN(expires) AS expires FROM invite_codes",
      )
      .one().expires;
    const times = [lease, code].filter(
      (value): value is number => typeof value === "number",
    );
    return times.length ? Math.min(...times) : null;
  }
  private async scheduleCleanup(): Promise<void> {
    const next = this.nextExpiry();
    if (next == null) {
      await this.ctx.storage.deleteAlarm();
      return;
    }
    // One alarm at the soonest lease or tombstone. No per-row and no 60s loop.
    await this.ctx.storage.setAlarm(Math.max(next, Date.now() + 1_000));
  }
  async alarm(): Promise<void> {
    const now = Date.now();
    this.ctx.storage.sql.exec("DELETE FROM leases WHERE expires <= ?", now);
    this.ctx.storage.sql.exec(
      "DELETE FROM invite_codes WHERE expires <= ?",
      now,
    );
    this.ctx.storage.sql.exec(
      "DELETE FROM invite_generations WHERE room_id NOT IN (SELECT id FROM leases)",
    );
    this.ctx.storage.sql.exec(
      "DELETE FROM rates WHERE window < ?",
      Math.floor(now / 60_000),
    );
    await this.scheduleCleanup();
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    let response: Response;
    try {
      if (request.method === "OPTIONS") {
        response = new Response(null, {
          status: 204,
          headers: {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Max-Age": "600",
          },
        });
      } else {
        const url = new URL(request.url);
        if (url.pathname === "/health" && request.method === "GET") {
          response = json({ service: "bvn-matchmaking", protocol: 1 });
        } else {
          const admission = env.ADMISSION.getByName("global-v1");
          const ip = request.headers.get("CF-Connecting-IP") ?? "local";
          requireThat(
            await admission.rate("global", 1200),
            "rate_limited",
            429,
          );
          requireThat(
            await admission.rate(await hash(ip), 240),
            "rate_limited",
            429,
          );
          if (url.pathname === "/v1/rooms" && request.method === "POST") {
            requireThat(
              await admission.rate("create", 30),
              "rate_limited",
              429,
            );
            const input = parse(create, await body(request));
            const id = await hash(input.createToken);
            const fingerprint = await hash(JSON.stringify(input));
            const lease = await admission.allocate(id, fingerprint);
            requireThat(
              !lease.error,
              lease.error ?? "capacity_reached",
              lease.error === "capacity_reached" ? 503 : 409,
            );
            const invite = await admission.createInviteCode(id, lease.expires!);
            response = await env.ROOMS.getByName(id).fetch(
              new Request("https://room/internal/create", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  input,
                  id,
                  fingerprint,
                  leaseUntil: lease.expires,
                  shortInviteHash: invite.digest,
                }),
              }),
            );
            if (response.status === 410) await admission.release(id);
            else response = await attachInviteCode(response, invite.code);
          } else if (
            url.pathname === "/v1/rooms/join-by-code" &&
            request.method === "POST"
          ) {
            requireThat(
              await admission.rate("join-by-code", 120),
              "rate_limited",
              429,
            );
            const input = parse(joinByCode, await body(request));
            requireThat(validInviteCode(input.code), "invalid_invite", 403);
            const normalizedCode = normalizeInviteCode(input.code);
            const [codeDigest, guestHash] = await Promise.all([
              hash(normalizedCode),
              hash(input.sessionToken),
            ]);
            const inviteLookup = await admission.lookupInviteCode(
              codeDigest,
              guestHash,
            );
            if ("error" in inviteLookup)
              throw new Fault(403, inviteLookup.error);
            const roomId = inviteLookup.roomId;
            response = await env.ROOMS.getByName(roomId).fetch(
              new Request("https://room/join-by-code", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(input),
              }),
            );
            if (response.ok)
              requireThat(
                await admission.consumeInviteCode(
                  codeDigest,
                  roomId,
                  guestHash,
                ),
                "invalid_invite",
                403,
              );
          } else {
            const route =
              /^\/v1\/rooms\/([a-f0-9]{64})\/(join|state|commands|ticket|socket|ice)$/.exec(
                url.pathname,
              );
            requireThat(route, "not_found", 404);
            const [, id, action] = route;
            requireThat(await admission.lookup(id), "room_expired", 410);
            const target = new URL(request.url);
            target.pathname = "/" + action;
            target.search = "";
            response = await env.ROOMS.getByName(id).fetch(
              new Request(target, request),
            );
          }
        }
      }
    } catch (error) {
      response = failure(error);
    }
    if (response.status === 101) return response;
    const headers = new Headers(response.headers);
    headers.set("Access-Control-Allow-Origin", "*");
    headers.delete("Vary");
    headers.set("X-Content-Type-Options", "nosniff");
    return new Response(response.body, { status: response.status, headers });
  },
} satisfies ExportedHandler<Env>;
