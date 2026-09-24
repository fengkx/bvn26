import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { randomBytes } from "node:crypto";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { once } from "node:events";
import { build } from "esbuild";
import { Miniflare, Log, LogLevel, convertV4MiniflareOptions } from "miniflare";
import WebSocket from "ws";

let directory;
let script;
before(async () => {
  directory = await mkdtemp(join(tmpdir(), "bvn-room-tests-"));
  script = join(directory, "worker.mjs");
  await build({
    entryPoints: ["test/fixture.ts"],
    bundle: true,
    format: "esm",
    platform: "neutral",
    external: ["cloudflare:workers"],
    outfile: script,
  });
});
after(async () => {
  await rm(directory, { recursive: true, force: true });
});
const token = () => randomBytes(32).toString("base64url");
const compatibility = {
  protocol: 1,
  build: "a".repeat(64),
  content: "b".repeat(64),
};
const profile = { id: "chrome-exp-d2-p6", inputDelay: 2, predictionWindow: 6 };
async function runtime(persistence, bindings = {}) {
  const options = convertV4MiniflareOptions({
    name: "matchmaking-tests",
    rootPath: directory,
    scriptPath: script,
    modules: true,
    compatibilityDate: "2026-09-22",
    log: new Log(LogLevel.ERROR),
    durableObjects: {
      ROOMS: { className: "TestRoom", useSQLite: true },
      ADMISSION: { className: "TestAdmission", useSQLite: true },
    },
    durableObjectsPersist: persistence,
    bindings,
  });
  options.resourcePersistencePath = persistence;
  options.workers[0].dev.unsafeRegisterWorker = false;
  const mf = new Miniflare(options);
  let url;
  try {
    url = (await mf.ready).toString().replace(/\/$/, "");
  } catch (error) {
    await mf.dispose();
    throw error;
  }
  return { mf, url };
}
async function request(server, path, input, credential, method) {
  const response = await fetch(server.url + path, {
    method: method ?? (input === undefined ? "GET" : "POST"),
    headers: {
      ...(input === undefined ? {} : { "Content-Type": "application/json" }),
      ...(credential ? { Authorization: `Bearer ${credential}` } : {}),
    },
    body: input === undefined ? undefined : JSON.stringify(input),
  });
  return { status: response.status, ...(await response.json()) };
}
async function createRoom(server, override = {}) {
  const input = {
    createToken: token(),
    sessionToken: token(),
    inviteToken: token(),
    nickname: "owner",
    compatibility,
    ...override,
  };
  const response = await request(server, "/v1/rooms", input);
  assert.equal(response.status, 201, JSON.stringify(response));
  return {
    ...response,
    input,
    owner: input.sessionToken,
    guest: token(),
    ownerSeq: 0,
    guestSeq: 0,
  };
}
const endpoint = (room, action) => `/v1/rooms/${room.roomId}/${action}`;
async function joinRoom(
  server,
  room,
  sessionToken = room.guest,
  overrides = {},
) {
  return request(server, endpoint(room, "join"), {
    sessionToken,
    inviteToken: room.input.inviteToken,
    nickname: "guest",
    compatibility,
    ...overrides,
  });
}
async function op(server, room, slot, operation, seq) {
  const key = slot === 0 ? "ownerSeq" : "guestSeq";
  const next = seq ?? room[key] + 1;
  const response = await request(
    server,
    endpoint(room, "commands"),
    { version: 1, seq: next, operation },
    slot === 0 ? room.owner : room.guest,
  );
  if (response.status === 200) {
    room[key] = Math.max(room[key], next);
    room.state = response.state;
  }
  return response;
}
async function setup(server, room) {
  assert.equal((await joinRoom(server, room)).status, 201);
  let response = await op(server, room, 0, {
    type: "select",
    revision: 2,
    choice: { fighter: "minren", helper: "you" },
  });
  assert.equal(response.status, 200);
  response = await op(server, room, 1, {
    type: "select",
    revision: response.state.setupRevision,
    choice: { fighter: "yihu", helper: "kon" },
  });
  assert.equal(response.status, 200);
  const revision = response.state.setupRevision;
  for (const slot of [0, 1])
    assert.equal(
      (
        await op(server, room, slot, {
          type: "ready",
          revision,
          ready: true,
          profile,
        })
      ).status,
      200,
    );
  return revision;
}
async function start(server, room) {
  const revision = await setup(server, room);
  const prepared = await op(server, room, 0, { type: "prepare", revision });
  assert.equal(prepared.status, 200);
  const epoch = prepared.state.match.epoch;
  for (const slot of [0, 1])
    assert.equal(
      (
        await op(server, room, slot, {
          type: "loaded",
          epoch,
          initialHash: "c".repeat(64),
        })
      ).status,
      200,
    );
  for (const slot of [0, 1])
    assert.equal(
      (await op(server, room, slot, { type: "start_ack", epoch })).status,
      200,
    );
  assert.equal(room.state.phase, "active");
  return epoch;
}
async function socket(server, room, credential, origin) {
  const response = await request(
    server,
    endpoint(room, "ticket"),
    {},
    credential,
  );
  assert.equal(response.status, 200);
  const ws = new WebSocket(
    server.url.replace("http:", "ws:") + endpoint(room, "socket"),
    ["bvn.v1", response.ticket],
    origin ? { headers: { Origin: origin } } : undefined,
  );
  const queue = [];
  ws.on("message", (data) => {
    queue.push(data.toString() === "pong" ? "pong" : JSON.parse(data));
  });
  await once(ws, "open");
  async function receive(type) {
    const timeout = Date.now() + 4000;
    while (Date.now() < timeout) {
      const index = queue.findIndex(
        (value) => value === type || value.type === type,
      );
      if (index >= 0) return queue.splice(index, 1)[0];
      await new Promise((resolve) => setTimeout(resolve, 10));
    }
    throw new Error(`Missing ${type}: ${JSON.stringify(queue)}`);
  }
  await receive("state");
  return { ws, receive, ticket: response.ticket };
}
async function withServer(t, bindings) {
  const persistence = await mkdtemp(join(directory, "sqlite-"));
  const server = await runtime(persistence, bindings);
  t.after(() => server.mf.dispose());
  return server;
}

test("atomic admission, private capabilities, isolation and compatibility", async (t) => {
  const server = await withServer(t);
  const room = await createRoom(server);
  const retry = await request(server, "/v1/rooms", room.input);
  assert.equal(retry.roomId, room.roomId);
  assert.equal(retry.status, 200);
  assert.equal(retry.inviteCode, room.inviteCode);
  assert.match(room.inviteCode, /^[a-z]+-[a-z]+-[a-z2-7]{8}$/);
  const badInvite = await joinRoom(server, room, token(), {
    inviteToken: token(),
  });
  assert.equal(badInvite.error, "invalid_invite");
  assert.equal(
    (
      await joinRoom(server, room, token(), {
        compatibility: { ...compatibility, build: "d".repeat(64) },
      })
    ).error,
    "incompatible_build",
  );
  assert.equal(
    (await joinRoom(server, room, token(), { nickname: "<script>" })).status,
    400,
  );
  const racers = await Promise.all([
    joinRoom(server, room),
    joinRoom(server, room, token()),
    joinRoom(server, room, token()),
  ]);
  assert.deepEqual(racers.map((x) => x.status).sort(), [201, 409, 409]);
  assert.equal(
    (await request(server, endpoint(room, "state"), undefined, token())).status,
    401,
  );
  const other = await createRoom(server);
  assert.equal(
    (await request(server, endpoint(other, "state"), undefined, room.owner))
      .status,
    401,
  );
  const publicState = JSON.stringify(retry.state);
  for (const forbidden of [
    "credential",
    "inviteHash",
    "creationHash",
    "shortInviteHash",
    room.inviteCode,
    room.owner,
    room.input.inviteToken,
  ])
    assert.ok(!publicState.includes(forbidden));
});

test("room network profile is owner controlled, authoritative, and independent of map setup", async (t) => {
  const server = await withServer(t);
  const room = await createRoom(server);
  const defaultProfile = {
    id: "chrome-exp-d2-p6",
    inputDelay: 2,
    predictionWindow: 6,
  };
  const lanProfile = {
    id: "chrome-exp-d1-p3-lan",
    inputDelay: 1,
    predictionWindow: 3,
  };
  assert.deepEqual(room.state.networkProfile, defaultProfile);

  const setupRevision = await setup(server, room);
  await op(server, room, 0, { type: "negotiate", epoch: null });
  assert.ok(room.state.negotiation);

  const noOp = await op(server, room, 0, {
    type: "configure_network",
    revision: room.state.setupRevision,
    profile: defaultProfile,
  });
  assert.equal(noOp.state.setupRevision, setupRevision);
  assert.ok(noOp.state.members.every((seat) => seat.ready));
  assert.ok(noOp.state.negotiation);

  const guestSequence = room.guestSeq;
  const guestEdit = await op(server, room, 1, {
    type: "configure_network",
    revision: room.state.setupRevision,
    profile: lanProfile,
  });
  assert.equal(guestEdit.error, "owner_required");
  assert.equal(room.guestSeq, guestSequence);
  assert.equal(room.state.networkProfile.id, defaultProfile.id);
  assert.ok(room.state.negotiation);

  const ownerSequence = room.ownerSeq;
  const invalidProfile = await op(server, room, 0, {
    type: "configure_network",
    revision: room.state.setupRevision,
    profile: { ...lanProfile, id: "chrome-exp-d2-p3-lan" },
  });
  assert.equal(invalidProfile.error, "invalid_message");
  assert.equal(room.ownerSeq, ownerSequence);

  const ownerEdit = await op(server, room, 0, {
    type: "configure_network",
    revision: room.state.setupRevision,
    profile: lanProfile,
  });
  assert.equal(ownerEdit.status, 200);
  assert.deepEqual(ownerEdit.state.networkProfile, lanProfile);
  assert.equal(ownerEdit.state.setupRevision, setupRevision + 1);
  assert.ok(
    ownerEdit.state.members.every((seat) => !seat.ready && !seat.profile),
  );
  assert.equal(ownerEdit.state.negotiation, null);

  const mapEdit = await op(server, room, 0, {
    type: "configure",
    revision: ownerEdit.state.setupRevision,
    stage: "流魂街",
    rules: { time: 60, life: 2 },
  });
  assert.deepEqual(mapEdit.state.networkProfile, lanProfile);

  const staleReady = await op(server, room, 1, {
    type: "ready",
    revision: mapEdit.state.setupRevision,
    ready: true,
    profile: defaultProfile,
  });
  assert.equal(staleReady.error, "network_profile_mismatch");
  assert.equal(room.guestSeq, guestSequence);

  const readyRevision = mapEdit.state.setupRevision;
  for (const slot of [0, 1])
    assert.equal(
      (
        await op(server, room, slot, {
          type: "ready",
          revision: readyRevision,
          ready: true,
          profile: lanProfile,
        })
      ).status,
      200,
    );
  const prepared = await op(server, room, 0, {
    type: "prepare",
    revision: readyRevision,
  });
  assert.equal(prepared.status, 200);
  assert.deepEqual(prepared.state.match.profile, lanProfile);
});

test("legacy state projects a default network profile without changing the current match profile", async (t) => {
  const server = await withServer(t);
  const room = await createRoom(server);
  const epoch = await start(server, room);
  await request(server, "/_test/alarm", {
    id: room.roomId,
    kind: "legacy-network-profile",
  });

  const legacyProfile = {
    id: "legacy-profile",
    inputDelay: 0,
    predictionWindow: 6,
  };
  const current = await request(
    server,
    endpoint(room, "state"),
    undefined,
    room.owner,
  );
  assert.deepEqual(current.state.networkProfile, profile);
  assert.equal(current.state.match.epoch, epoch);
  assert.deepEqual(current.state.match.profile, legacyProfile);

  const raw = await request(server, "/_test/alarm", {
    id: room.roomId,
    kind: "inspect",
  });
  const persisted = JSON.parse(raw.rows[0].value);
  assert.equal(Object.hasOwn(persisted, "networkProfile"), false);
  assert.deepEqual(persisted.match.profile, legacyProfile);
});

test("setting the legacy default lazily does not invalidate matching readiness", async (t) => {
  const server = await withServer(t);
  const room = await createRoom(server);
  const revision = await setup(server, room);
  await op(server, room, 0, { type: "negotiate", epoch: null });
  const negotiationId = room.state.negotiation.id;
  await request(server, "/_test/alarm", {
    id: room.roomId,
    kind: "legacy-network-profile",
  });

  const projected = await request(
    server,
    endpoint(room, "state"),
    undefined,
    room.owner,
  );
  assert.deepEqual(projected.state.networkProfile, profile);
  const migrated = await op(server, room, 0, {
    type: "configure_network",
    revision,
    profile,
  });
  assert.equal(migrated.status, 200);
  assert.equal(migrated.state.setupRevision, revision);
  assert.ok(migrated.state.members.every((seat) => seat.ready));
  assert.equal(migrated.state.negotiation.id, negotiationId);

  const raw = await request(server, "/_test/alarm", {
    id: room.roomId,
    kind: "inspect",
  });
  const persisted = JSON.parse(raw.rows[0].value);
  assert.deepEqual(persisted.networkProfile, profile);
});

test("short invitation codes are private, single-use, retryable and rotatable", async (t) => {
  const server = await withServer(t);
  assert.equal(
    (
      await request(server, "/_test/invite-candidates", {
        codes: [
          "amber-otter-aaaaaaaa",
          "amber-otter-aaaaaaaa",
          "brisk-cat-bbbbbbbb",
        ],
      })
    ).ok,
    true,
  );
  const room = await createRoom(server);
  const publicState = JSON.stringify(room.state);
  assert.ok(!publicState.includes(room.inviteCode));
  assert.ok(!publicState.includes("shortInviteHash"));

  const guestInput = {
    code: ` ${room.inviteCode.toUpperCase()} `,
    sessionToken: room.guest,
    nickname: "guest",
    compatibility,
  };
  const firstJoin = await request(server, "/v1/rooms/join-by-code", guestInput);
  assert.equal(firstJoin.status, 201, JSON.stringify(firstJoin));
  assert.equal(firstJoin.slot, 1);
  assert.ok(!JSON.stringify(firstJoin.state).includes(room.inviteCode));

  const retryJoin = await request(server, "/v1/rooms/join-by-code", guestInput);
  assert.equal(retryJoin.status, 200);
  assert.equal(retryJoin.slot, 1);

  const reinviteToken = token();
  const reinviteCommand = {
    version: 1,
    seq: 1,
    operation: { type: "reinvite", inviteToken: reinviteToken },
  };
  const reinvited = await request(
    server,
    endpoint(room, "commands"),
    reinviteCommand,
    room.owner,
  );
  assert.equal(reinvited.status, 200, JSON.stringify(reinvited));
  assert.match(reinvited.inviteCode, /^[a-z]+-[a-z]+-[a-z2-7]{8}$/);
  assert.notEqual(reinvited.inviteCode, room.inviteCode);
  assert.equal(reinvited.inviteCode, "brisk-cat-bbbbbbbb");

  const retriedReinvite = await request(
    server,
    endpoint(room, "commands"),
    reinviteCommand,
    room.owner,
  );
  assert.equal(retriedReinvite.status, 200);
  assert.equal(retriedReinvite.inviteCode, reinvited.inviteCode);
  assert.equal(
    (
      await request(server, "/v1/rooms/join-by-code", {
        ...guestInput,
        sessionToken: token(),
      })
    ).error,
    "invalid_invite",
  );

  const left = await request(
    server,
    endpoint(room, "commands"),
    { version: 1, seq: 1, operation: { type: "leave" } },
    room.guest,
  );
  assert.equal(left.status, 200);
  const retriedAfterLeave = await request(
    server,
    endpoint(room, "commands"),
    reinviteCommand,
    room.owner,
  );
  assert.equal(retriedAfterLeave.status, 200);
  assert.equal(retriedAfterLeave.inviteCode, reinvited.inviteCode);
  assert.equal(
    (
      await request(server, "/v1/rooms/join-by-code", {
        ...guestInput,
        code: reinvited.inviteCode,
        sessionToken: token(),
      })
    ).error,
    "invalid_invite",
  );

  const nextReinviteCommand = {
    version: 1,
    seq: 2,
    operation: { type: "reinvite", inviteToken: token() },
  };
  const nextReinvite = await request(
    server,
    endpoint(room, "commands"),
    nextReinviteCommand,
    room.owner,
  );
  assert.equal(nextReinvite.status, 200);
  assert.notEqual(nextReinvite.inviteCode, reinvited.inviteCode);
  const nextGuestInput = {
    code: nextReinvite.inviteCode,
    sessionToken: token(),
    nickname: "new guest",
    compatibility,
  };
  const nextJoin = await request(
    server,
    "/v1/rooms/join-by-code",
    nextGuestInput,
  );
  assert.equal(nextJoin.status, 201, JSON.stringify(nextJoin));
  assert.equal(nextJoin.slot, 1);
  const retriedNextReinvite = await request(
    server,
    endpoint(room, "commands"),
    nextReinviteCommand,
    room.owner,
  );
  assert.equal(retriedNextReinvite.status, 200);
  assert.equal(retriedNextReinvite.inviteCode, nextReinvite.inviteCode);
  assert.equal(
    (
      await request(server, "/v1/rooms/join-by-code", {
        ...nextGuestInput,
        sessionToken: token(),
      })
    ).error,
    "invalid_invite",
  );
  const leaveNext = await request(
    server,
    endpoint(room, "commands"),
    { version: 1, seq: 1, operation: { type: "leave" } },
    nextGuestInput.sessionToken,
  );
  assert.equal(leaveNext.status, 200);
  assert.equal(
    (await request(server, "/v1/rooms/join-by-code", nextGuestInput)).error,
    "invalid_invite",
  );

  const closingRoom = await createRoom(server);
  const closed = await request(
    server,
    endpoint(closingRoom, "commands"),
    { version: 1, seq: 1, operation: { type: "leave" } },
    closingRoom.owner,
  );
  assert.equal(closed.status, 200);
  assert.equal(
    (
      await request(server, "/v1/rooms/join-by-code", {
        code: closingRoom.inviteCode,
        sessionToken: token(),
        nickname: "guest",
        compatibility,
      })
    ).error,
    "invalid_invite",
  );

  const racingRoom = await createRoom(server);
  const race = await Promise.all(
    [token(), token()].map((sessionToken) =>
      request(server, "/v1/rooms/join-by-code", {
        code: racingRoom.inviteCode,
        sessionToken,
        nickname: "racer",
        compatibility,
      }),
    ),
  );
  assert.equal(race.filter((reply) => reply.status === 201).length, 1);
  assert.equal(
    race.filter((reply) => [403, 409].includes(reply.status)).length,
    1,
  );
});

test("setup revisions, transactional rejection, retries, barriers and rematch epochs", async (t) => {
  const server = await withServer(t);
  const room = await createRoom(server);
  const revision = await setup(server, room);
  const beforeState = await request(
    server,
    endpoint(room, "state"),
    undefined,
    room.owner,
  );
  assert.equal(
    (
      await op(server, room, 1, {
        type: "configure",
        revision,
        stage: "现世",
        rules: { time: 90, life: 1 },
      })
    ).status,
    403,
  );
  assert.deepEqual(
    (await request(server, endpoint(room, "state"), undefined, room.owner))
      .state,
    beforeState.state,
  );
  const edit = await op(server, room, 0, {
    type: "configure",
    revision,
    stage: "流魂街",
    rules: { time: 60, life: 2 },
  });
  assert.ok(edit.state.members.every((x) => !x.ready));
  assert.equal(
    (await op(server, room, 0, { type: "prepare", revision })).error,
    "stale_revision",
  );
  const nextRevision = edit.state.setupRevision;
  for (const slot of [0, 1])
    await op(server, room, slot, {
      type: "ready",
      revision: nextRevision,
      ready: true,
      profile,
    });
  const prepare = { type: "prepare", revision: nextRevision };
  const prepared = await op(server, room, 0, prepare);
  const retried = await op(server, room, 0, prepare, room.ownerSeq);
  assert.deepEqual(retried, prepared);
  assert.equal(
    (await op(server, room, 0, { type: "leave" }, room.ownerSeq)).error,
    "conflicting_retry",
  );
  const epoch = prepared.state.match.epoch;
  assert.equal(
    (await op(server, room, 0, { type: "start_ack", epoch })).error,
    "load_barrier_pending",
  );
  for (const slot of [0, 1])
    await op(server, room, slot, {
      type: "loaded",
      epoch,
      initialHash: "c".repeat(64),
    });
  await op(server, room, 0, { type: "start_ack", epoch });
  assert.equal(room.state.phase, "preparing");
  await op(server, room, 1, { type: "start_ack", epoch });
  assert.equal(room.state.phase, "active");
  const result = {
    type: "result",
    epoch,
    frame: 900,
    hash: "e".repeat(64),
    winner: 0,
  };
  await op(server, room, 0, result);
  assert.equal(room.state.phase, "active");
  await op(server, room, 1, result);
  assert.deepEqual(room.state.lastResult, {
    epoch,
    winner: 0,
    reason: "agreed",
  });
  assert.equal(room.state.phase, "lobby");
  for (const slot of [0, 1])
    await op(server, room, slot, {
      type: "ready",
      revision: room.state.setupRevision,
      ready: true,
      profile,
    });
  await op(server, room, 0, {
    type: "prepare",
    revision: room.state.setupRevision,
  });
  assert.notEqual(room.state.match.epoch, epoch);
  assert.equal((await op(server, room, 0, result)).error, "stale_epoch");
});

test("CORS preflight and room responses allow every origin", async (t) => {
  const server = await withServer(t);
  const origin = "https://untrusted.example";
  const preflight = await fetch(server.url + "/v1/rooms", {
    method: "OPTIONS",
    headers: {
      Origin: origin,
      "Access-Control-Request-Method": "POST",
      "Access-Control-Request-Headers": "authorization,content-type",
    },
  });
  assert.equal(preflight.status, 204);
  assert.equal(preflight.headers.get("Access-Control-Allow-Origin"), "*");
  assert.equal(
    preflight.headers.get("Access-Control-Allow-Methods"),
    "GET, POST, OPTIONS",
  );
  assert.equal(
    preflight.headers.get("Access-Control-Allow-Headers"),
    "Authorization, Content-Type",
  );
  assert.equal(preflight.headers.get("Access-Control-Allow-Credentials"), null);
  assert.equal(preflight.headers.get("Vary"), null);

  const invalid = await fetch(server.url + "/v1/rooms", {
    method: "POST",
    headers: { Origin: origin, "Content-Type": "application/json" },
    body: "{}",
  });
  assert.equal(invalid.status, 400);
  assert.equal(invalid.headers.get("Access-Control-Allow-Origin"), "*");
  assert.equal((await invalid.json()).error, "invalid_message");

  const created = await fetch(server.url + "/v1/rooms", {
    method: "POST",
    headers: { Origin: origin, "Content-Type": "application/json" },
    body: JSON.stringify({
      createToken: token(),
      sessionToken: token(),
      inviteToken: token(),
      nickname: "cors-test",
      compatibility,
    }),
  });
  assert.equal(created.status, 201);
  assert.equal(created.headers.get("Access-Control-Allow-Origin"), "*");
  assert.ok((await created.json()).roomId);
});

test("WebSockets accept every Origin but still require a valid one-use ticket", async (t) => {
  const server = await withServer(t);
  const room = await createRoom(server);
  const origin = "https://untrusted.example";
  const client = await socket(server, room, room.owner, origin);
  t.after(() => client.ws.terminate());

  const forged = new WebSocket(
    server.url.replace("http:", "ws:") + endpoint(room, "socket"),
    ["bvn.v1", token()],
    { headers: { Origin: origin } },
  );
  const [, response] = await once(forged, "unexpected-response");
  assert.equal(response.statusCode, 401);
  response.resume();
});

test("real WebSockets authenticate, scope signaling, revoke seats and tolerate disconnect", async (t) => {
  const server = await withServer(t);
  const room = await createRoom(server);
  await joinRoom(server, room);
  await op(server, room, 0, { type: "negotiate", epoch: null });
  const negotiationId = room.state.negotiation.id;
  const a = await socket(server, room, room.owner);
  const afterOwnerAttach = await request(
    server,
    endpoint(room, "state"),
    undefined,
    room.owner,
  );
  assert.equal(afterOwnerAttach.state.negotiation.id, negotiationId);
  const b = await socket(server, room, room.guest);
  t.after(() => {
    a.ws.terminate();
    b.ws.terminate();
  });
  const afterGuestAttach = await request(
    server,
    endpoint(room, "state"),
    undefined,
    room.owner,
  );
  assert.equal(afterGuestAttach.state.negotiation.id, negotiationId);
  a.ws.send("ping");
  assert.equal(await a.receive("pong"), "pong");
  const message = {
    version: 1,
    type: "signal",
    seq: 0,
    epoch: null,
    negotiationId: room.state.negotiation.id,
    kind: "offer",
    payload: "local-test-sdp",
  };
  a.ws.send(JSON.stringify(message));
  assert.equal((await b.receive("signal")).payload, message.payload);
  assert.equal((await a.receive("signal_ack")).delivered, true);
  a.ws.send(JSON.stringify(message));
  assert.equal((await a.receive("error")).error, "invalid_sequence");
  a.ws.send(
    JSON.stringify({ ...message, seq: 1, negotiationId: crypto.randomUUID() }),
  );
  assert.equal((await a.receive("error")).error, "stale_negotiation");
  const replacement = await socket(server, room, room.owner);
  t.after(() => replacement.ws.terminate());
  await new Promise((resolve) => setTimeout(resolve, 30));
  assert.notEqual(a.ws.readyState, WebSocket.OPEN);
  const afterReplacement = await request(
    server,
    endpoint(room, "state"),
    undefined,
    room.owner,
  );
  assert.equal(afterReplacement.state.negotiation, null);
  b.ws.send(JSON.stringify({ ...message, seq: 1 }));
  assert.equal((await b.receive("error")).error, "stale_negotiation");
  b.ws.terminate();
  assert.equal(
    (await request(server, endpoint(room, "state"), undefined, room.owner))
      .state.phase,
    "lobby",
  );
  assert.equal((await op(server, room, 1, { type: "leave" })).status, 200);
  assert.equal(
    (await request(server, endpoint(room, "ticket"), {}, room.guest)).status,
    401,
  );
  assert.equal((await joinRoom(server, room, token())).status, 201);
  await op(server, room, 0, { type: "leave" });
  assert.ok(
    [410].includes(
      (await request(server, endpoint(room, "state"), undefined, room.owner))
        .status,
    ),
  );
});

test("ten concurrent leases cannot overbook and owner departure releases capacity", async (t) => {
  const server = await withServer(t);
  const inputs = Array.from({ length: 11 }, () => ({
    createToken: token(),
    sessionToken: token(),
    inviteToken: token(),
    nickname: "owner",
    compatibility,
  }));
  const results = await Promise.all(
    inputs.map((input) => request(server, "/v1/rooms", input)),
  );
  assert.equal(results.filter((x) => x.status === 201).length, 10);
  assert.equal(results.filter((x) => x.error === "capacity_reached").length, 1);
  const index = results.findIndex((x) => x.status === 201);
  const room = {
    ...results[index],
    owner: inputs[index].sessionToken,
    ownerSeq: 0,
  };
  await op(server, room, 0, { type: "leave" });
  await new Promise((resolve) => setTimeout(resolve, 100));
  await createRoom(server);
});

test("alarm expiry runs without a client request; active play and prepare timeout differ", async (t) => {
  const server = await withServer(t);
  const room = await createRoom(server);
  await request(server, "/_test/alarm", { id: room.roomId, kind: "scheduled" });
  await new Promise((resolve) => setTimeout(resolve, 200));
  assert.equal(
    (await request(server, endpoint(room, "state"), undefined, room.owner))
      .status,
    410,
  );
  const active = await createRoom(server);
  await start(server, active);
  await request(server, "/_test/alarm", { id: active.roomId, kind: "idle" });
  assert.equal(
    (await request(server, endpoint(active, "state"), undefined, active.owner))
      .state.phase,
    "active",
  );
  const preparing = await createRoom(server);
  const revision = await setup(server, preparing);
  await op(server, preparing, 0, { type: "prepare", revision });
  await request(server, "/_test/alarm", {
    id: preparing.roomId,
    kind: "preparing",
  });
  const raw = await request(server, "/_test/alarm", {
    id: preparing.roomId,
    kind: "inspect",
  });
  const persisted = JSON.parse(raw.rows[0].value);
  assert.equal(persisted.phase, "lobby");
  assert.equal(persisted.lastResult.reason, "start_timeout");
  assert.equal(persisted.match, null);
  assert.ok(raw.nextAlarm > Date.now());
});

test("SQLite restart restores epoch, seats and idempotency with new real WebSockets", async (t) => {
  const persistence = await mkdtemp(join(directory, "restart-"));
  let server = await runtime(persistence);
  t.after(() => server.mf.dispose());
  const room = await createRoom(server);
  const epoch = await start(server, room);
  const oldSocket = await socket(server, room, room.owner);
  oldSocket.ws.terminate();
  const beforeState = (
    await request(server, endpoint(room, "state"), undefined, room.owner)
  ).state;
  await server.mf.dispose();
  server = await runtime(persistence);
  const afterState = (
    await request(server, endpoint(room, "state"), undefined, room.owner)
  ).state;
  assert.deepEqual(afterState, beforeState);
  assert.equal(afterState.match.epoch, epoch);
  const replay = await op(
    server,
    room,
    1,
    { type: "start_ack", epoch },
    room.guestSeq,
  );
  assert.equal(replay.status, 200);
  const a = await socket(server, room, room.owner);
  const b = await socket(server, room, room.guest);
  t.after(() => {
    a.ws.terminate();
    b.ws.terminate();
  });
  await op(server, room, 0, { type: "negotiate", epoch });
  a.ws.send(
    JSON.stringify({
      version: 1,
      type: "signal",
      seq: 0,
      epoch,
      negotiationId: room.state.negotiation.id,
      kind: "candidate",
      payload: "restart-candidate",
    }),
  );
  assert.equal((await b.receive("signal")).payload, "restart-candidate");
});

test("TURN REST issuance is authenticated, short-lived and rate limited", async (t) => {
  const server = await withServer(t, {
    TURN_KEY_ID: "0123456789abcdef0123456789abcdef",
    TURN_API_TOKEN: "test-only-api-token",
  });
  const room = await createRoom(server);
  assert.equal(
    (await request(server, endpoint(room, "ice"), {}, token())).status,
    401,
  );
  const response = await request(server, endpoint(room, "ice"), {}, room.owner);
  assert.equal(response.expiresIn, 14_400);
  const ice = response.iceServers[0];
  assert.deepEqual(ice.urls, [
    "turn:turn.example:3478?transport=udp",
    "turns:turn.example:5349",
  ]);
  assert.equal(ice.username, "fixture-user");
  assert.equal(ice.credential, "fixture-credential");
  assert.ok(!JSON.stringify(response).includes("test-only-api-token"));
  for (let i = 0; i < 3; i++)
    await request(server, endpoint(room, "ice"), {}, room.owner);
  assert.equal(
    (await request(server, endpoint(room, "ice"), {}, room.owner)).status,
    429,
  );
});

test("malformed and oversized requests remain rejected with wildcard CORS", async (t) => {
  const server = await withServer(t);
  const room = await createRoom(server);
  assert.equal(
    (
      await request(
        server,
        endpoint(room, "commands"),
        { version: 1, seq: 1, operation: { type: "inputs", buttons: 1 } },
        room.owner,
      )
    ).status,
    400,
  );
  assert.equal(
    (
      await request(server, endpoint(room, "join"), {
        text: "x".repeat(17_000),
      })
    ).status,
    413,
  );
  const response = await fetch(server.url + endpoint(room, "state"), {
    headers: {
      Origin: "https://evil.example",
      Authorization: `Bearer ${room.owner}`,
    },
  });
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("Access-Control-Allow-Origin"), "*");
});

test("initial-state and confirmed-result mismatches end without a winner", async (t) => {
  const server = await withServer(t);
  const room = await createRoom(server);
  const revision = await setup(server, room);
  await op(server, room, 0, { type: "prepare", revision });
  const epoch = room.state.match.epoch;
  await op(server, room, 0, {
    type: "loaded",
    epoch,
    initialHash: "c".repeat(64),
  });
  await op(server, room, 1, {
    type: "loaded",
    epoch,
    initialHash: "d".repeat(64),
  });
  assert.deepEqual(room.state.lastResult, {
    epoch,
    winner: null,
    reason: "initial_state_mismatch",
  });
  const active = await createRoom(server);
  const activeEpoch = await start(server, active);
  await op(server, active, 0, {
    type: "result",
    epoch: activeEpoch,
    frame: 20,
    hash: "c".repeat(64),
    winner: 0,
  });
  await op(server, active, 1, {
    type: "result",
    epoch: activeEpoch,
    frame: 20,
    hash: "d".repeat(64),
    winner: 1,
  });
  assert.deepEqual(active.state.lastResult, {
    epoch: activeEpoch,
    winner: null,
    reason: "result_mismatch",
  });
});

test("disabled content is rejected without consuming sequence", async (t) => {
  const server = await withServer(t);
  const room = await createRoom(server);
  const revision = await setup(server, room);
  const seq = room.ownerSeq;
  assert.equal(
    (
      await op(server, room, 0, {
        type: "select",
        revision,
        choice: { fighter: "minren-bankai", helper: "you" },
      })
    ).error,
    "unsupported_content",
  );
  assert.equal(room.ownerSeq, seq);
});

test("revoked invitations, single-use socket tickets and expired leases cannot be replayed", async (t) => {
  const server = await withServer(t);
  const room = await createRoom(server);
  const newInvite = token();
  const reinvited = await op(server, room, 0, {
    type: "reinvite",
    inviteToken: newInvite,
  });
  assert.equal((await joinRoom(server, room)).error, "invalid_invite");
  assert.equal(
    (await joinRoom(server, room, room.guest, { inviteToken: newInvite }))
      .status,
    201,
  );
  const connected = await socket(server, room, room.owner);
  t.after(() => connected.ws.terminate());
  const reused = new WebSocket(
    server.url.replace("http:", "ws:") + endpoint(room, "socket"),
    ["bvn.v1", connected.ticket],
  );
  const error = await new Promise((resolve) => {
    reused.on("error", resolve);
  });
  assert.match(error.message, /401/);
  await request(server, "/_test/alarm", { id: room.roomId, kind: "lease" });
  assert.equal(
    (await request(server, endpoint(room, "state"), undefined, room.owner))
      .status,
    410,
  );
  assert.equal((await request(server, "/v1/rooms", room.input)).status, 410);
  assert.equal(
    (
      await request(server, "/v1/rooms/join-by-code", {
        code: reinvited.inviteCode,
        sessionToken: token(),
        nickname: "guest",
        compatibility,
      })
    ).error,
    "invalid_invite",
  );
});

test("signaling sockets reject binary, oversized and flooded messages", async (t) => {
  const server = await withServer(t);
  const room = await createRoom(server);
  await joinRoom(server, room);
  const a = await socket(server, room, room.owner);
  t.after(() => a.ws.terminate());
  a.ws.send(Buffer.from([1, 2]));
  assert.equal((await a.receive("error")).error, "message_too_large");
  const replacement = await socket(server, room, room.owner);
  t.after(() => replacement.ws.terminate());
  replacement.ws.send("x".repeat(17000));
  assert.equal((await replacement.receive("error")).error, "message_too_large");
  const limited = await socket(server, room, room.owner);
  t.after(() => limited.ws.terminate());
  for (let i = 0; i < 121; i++) limited.ws.send("{}");
  let reachedLimit = false;
  for (let i = 0; i < 121; i++)
    if ((await limited.receive("error")).error === "rate_limited") {
      reachedLimit = true;
      break;
    }
  assert.ok(reachedLimit);
});
