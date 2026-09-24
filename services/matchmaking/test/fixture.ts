// Test-only control surface. This entry point is never bundled by Wrangler.
import worker, { Admission } from "../src/index";
import { Room } from "../src/room";
export { Admission };

const nativeFetch = globalThis.fetch.bind(globalThis);
globalThis.fetch = async (input, init) => {
  const request = new Request(input, init);
  const url = new URL(request.url);
  if (
    url.hostname === "rtc.live.cloudflare.com" &&
    url.pathname.endsWith("/credentials/generate-ice-servers")
  ) {
    const input = (await request.clone().json()) as { ttl?: number };
    if (
      request.headers.get("Authorization") !== "Bearer test-only-api-token" ||
      input.ttl !== 14_400
    )
      return Response.json(
        { error: "invalid_test_issuer_request" },
        { status: 403 },
      );
    return Response.json({
      iceServers: [
        {
          urls: [
            "turn:turn.example:3478?transport=udp",
            "turns:turn.example:5349",
          ],
          username: "fixture-user",
          credential: "fixture-credential",
        },
      ],
    });
  }
  return nativeFetch(request);
};

export class TestAdmission extends Admission {
  constructor(ctx: DurableObjectState, env: any) {
    ctx.storage.sql.exec(
      "CREATE TABLE IF NOT EXISTS invite_codes (digest TEXT PRIMARY KEY, room_id TEXT NOT NULL, purpose TEXT NOT NULL, code TEXT NOT NULL, status TEXT NOT NULL, guest_hash TEXT, expires INTEGER NOT NULL, UNIQUE(room_id, purpose))",
    );
    super(ctx, env);
    ctx.storage.sql.exec(
      "CREATE TABLE IF NOT EXISTS test_invite_candidates (position INTEGER PRIMARY KEY, code TEXT NOT NULL)",
    );
  }
  queueInviteCandidates(codes: string[]): void {
    this.ctx.storage.sql.exec("DELETE FROM test_invite_candidates");
    codes.forEach((code, position) =>
      this.ctx.storage.sql.exec(
        "INSERT INTO test_invite_candidates VALUES (?, ?)",
        position,
        code,
      ),
    );
  }
  protected override makeInviteCode(): string {
    const row = this.ctx.storage.sql
      .exec<{ code: string }>(
        "DELETE FROM test_invite_candidates WHERE position = (SELECT MIN(position) FROM test_invite_candidates) RETURNING code",
      )
      .toArray()[0];
    return row?.code ?? super.makeInviteCode();
  }
}

export class TestRoom extends Room {
  expire(kind: string): void {
    const row = this.ctx.storage.sql
      .exec<{ value: string }>("SELECT value FROM state WHERE id=1")
      .one();
    const state = JSON.parse(row.value);
    if (kind === "idle") state.lastActivity = Date.now() - 31 * 60_000;
    if (kind === "lease") state.leaseUntil = Date.now() - 1;
    if (kind === "preparing") state.match.deadline = Date.now() - 1;
    this.ctx.storage.sql.exec(
      "UPDATE state SET value=? WHERE id=1",
      JSON.stringify(state),
    );
  }
  async fireAlarm(kind: string): Promise<void> {
    this.expire(kind);
    await this.alarm();
  }
  async scheduleExpiry(): Promise<void> {
    this.expire("idle");
    await this.ctx.storage.setAlarm(Date.now() + 50);
  }
  inspect(): unknown {
    return this.ctx.storage.sql.exec("SELECT value FROM state").toArray();
  }
  useLegacyNetworkProfileState(): void {
    const row = this.ctx.storage.sql
      .exec<{ value: string }>("SELECT value FROM state WHERE id=1")
      .one();
    const state = JSON.parse(row.value);
    delete state.networkProfile;
    if (state.match)
      state.match.profile = {
        id: "legacy-profile",
        inputDelay: 0,
        predictionWindow: 6,
      };
    this.ctx.storage.sql.exec(
      "UPDATE state SET value=? WHERE id=1",
      JSON.stringify(state),
    );
  }
  nextAlarm(): Promise<number | null> {
    return this.ctx.storage.getAlarm();
  }
}
export default {
  async fetch(request: Request, env: any): Promise<Response> {
    const path = new URL(request.url).pathname;
    if (path.startsWith("/_test/")) {
      if (path === "/_test/invite-candidates") {
        const { codes } = (await request.json()) as { codes: string[] };
        await env.ADMISSION.getByName("global-v1").queueInviteCandidates(codes);
        return Response.json({ ok: true });
      }
      const { id, kind } = (await request.json()) as {
        id: string;
        kind: string;
      };
      const room = env.ROOMS.getByName(id);
      if (kind === "inspect")
        return Response.json({
          rows: await room.inspect(),
          nextAlarm: await room.nextAlarm(),
        });
      if (kind === "legacy-network-profile") {
        await room.useLegacyNetworkProfileState();
        return Response.json({ ok: true });
      }
      if (kind === "scheduled") await room.scheduleExpiry();
      else await room.fireAlarm(kind);
      return Response.json({ ok: true });
    }
    return worker.fetch(request, env);
  },
};
