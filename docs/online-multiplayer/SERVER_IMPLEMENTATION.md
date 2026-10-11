# Durable Object room server implementation

2026-09-22 baseline; reviewed again 2026-09-23. **The standalone TypeScript server is implemented and locally tested**
in [services/matchmaking](../../services/matchmaking/README.md). It is independent
of the ongoing Godot rollback work. No battle runtime, locked input or original
reference fixture was changed for this server implementation.

The user's subsequent request explicitly authorizes this independent backend
slice before full-game snapshot/rollback gates finish. The executable v1 room
contract is scoped to HTTP, room projections and signaling; it does not close
NET-005's gameplay-input, control-ordering or complete-state contracts.

## Delivered

- Worker routing, strict schema/byte validation, wildcard HTTP CORS and
  authenticated room endpoints. WebSocket `Origin` is not restricted; invite
  and seat capabilities are separate. Long invitation/session secrets are
  stored as digests. Short invite codes use a SHA-256 lookup index; their raw
  values are retained only in private Admission/idempotency state so uncertain
  create/reinvite retries return the same code. Room projections omit all invite
  material.
- SQLite `Admission` DO with ten durable leases and bounded minute-rate buckets;
  one SQLite `Room` DO per unguessable, non-recycled identity. Single-state-row
  commits preserve atomic room transitions. Version mismatches fail closed.
- Two-seat admission, owner/guest permissions, invite rotation, guest replacement,
  explicit owner closure, and digest/connection-generation-based revocation.
- Revisioned fighter/helper/map/rule settings, readiness invalidation, build/content
  compatibility comparison, agreed profile, unique epoch/seed/clock baseline,
  initial-state comparison, start acknowledgments and preparation deadline.
- Agreement-only result commitment, mismatch/abort/departure without a winner,
  new-epoch rematches and bounded persisted request idempotency.
- Hibernation-compatible WebSocket acceptance and attachments, one-use 30-second
  tickets, automatic ping/pong, authenticated bounded offer/answer/ICE forwarding,
  negotiation expiry and stale-epoch rejection. Raw SDP/ICE is not persisted.
- 2026-09-23 review fixes: preparation timeout transitions are persisted and
  broadcast before awaiting the admission lease RPC; health responses use the
  common CORS decoration. A later handshake fix keeps the negotiation id across
  socket replacement; projections add a per-seat `signaling` flag, and
  `negotiate` is idempotent until the 45-second TTL. While the room object stays
  in memory, signals already accepted for that id are replayed onto a
  replacement socket; clients ignore an identical description or candidate.
  Regression tests inspect
  raw SQLite after the alarm, verify arbitrary-origin preflight and HTTP
  responses, preserve WebSocket ticket authentication across origins, and
  exercise guest-first, host-first, and replacement with actual WebSockets.
- Alarm-based 30-minute idle expiry, independent service reachability leases,
  and active-match exemption from idle expiry. Disconnect alone never means exit.
  Unreachable abandoned service leases eventually release capacity; an existing
  healthy peer match may finish independently and cannot be redirected into a
  recycled room. See the precise lease/reconnect policy in the service README.
- Cloudflare Realtime TURN credential issuance through its server-side API,
  authenticated room membership checks, rate limits and Worker secret config.
  Cloudflare is now the selected default provider; account key creation,
  deployment and real relay connectivity remain unverified.
- Reproducible npm package, lockfile, Node version, SQLite migration bindings,
  local scripts, protocol/runbook documentation and isolated failure tests.
- 2026-09-23 short invite codes: room creation returns a readable
  `adjective-animal-xxxxxxxx` capability with 50 bits of random entropy; the
  body-only `join-by-code` route consumes it for one guest session while allowing
  exact uncertain retries. The existing sequenced `reinvite` command rotates the
  code; guest departure, owner closure and room expiry revoke it. The long-token
  join route remains compatible. Migration adds the invite-generation SQLite
  column to already-created local tables; Miniflare seeded an older schema to
  cover that path. A real local Wrangler create/owner-leave returned 201/200 after
  the hot reload; the original table itself could not be read directly, so its
  pre-migration column layout is not asserted as observed fact.

## Measured verification

Environment: macOS, Node 24.18.0, npm 11.16.0; exact npm versions are in the
[lockfile](../../services/matchmaking/package-lock.json). Wrangler 4.136.2 pins
Miniflare 5.20260921.0-alpha / workerd 1.20260921.1. Test harnesses use that same
runtime, not a mock implementation of the Durable Object APIs.

The integration suite covers concurrent admission/creation, room isolation,
credential separation, build mismatch, malformed nicknames and payloads, atomic
rejection, revision invalidation, profile disagreement, disabled content, duplicate
and conflicting operations, both start barriers, initial/result mismatch,
rematches, token rotation/revocation, single-use tickets, arbitrary-origin
preflight and ticketed WebSockets, signaling scope/limits, timer-driven idle
expiry, active-match exemption, preparation timeout, expired leases, TURN
HMAC/TTL/rate limits, and a fresh workerd process using the same SQLite
directory. A separate smoke
starts the actual production Wrangler configuration and connects a WebSocket.
Catalog checks detect drift from the current enabled menu IDs. The revised alarm
test checks persisted SQLite state and its scheduled successor alarm without a
`/state` read, preventing the request path from hiding a lost alarm transition.

The dated baseline in the server evidence records 14 passing tests from
2026-09-22. The 2026-09-23 short-code follow-up passes **17 tests**, TypeScript,
formatting and the Worker dry-run build; its exact boundary is recorded in the
[short-code validation note](../../evidence/online/room-server/short-code-validation.md).
The repository-wide integrity
check reported five concurrently modified Godot file hashes; those unrelated
entries were not rewritten by this task.

Commands and retained measured output are indexed in
[server evidence](../../evidence/online/room-server/README.md).
Actual implementation effort was not reliably timed; no person-day estimate is
invented from code size. No cloud deployment or paid resource was created.

## Tracker boundary

| Tasks | Implementation state | Gate still open |
|---|---|---|
| NET-007 / NET-027 | Native Wrangler workflow selected; package, clean install, startup and tests delivered | Full NET-005 contract remains broader than this server-only contract |
| NET-028 / NET-029 | SQLite lifecycle, isolation, atomic admission, capabilities and restart implemented/tested | Full predecessor acceptance; browser must retain the seat token only in page memory |
| NET-030 | Server setup/ready/epoch/result coordination implemented/tested | Frozen full game fingerprints (NET-002), peer simulation-boundary start (NET-038) |
| NET-031 | Hibernation API/attachments and real local WebSocket signaling implemented/tested | Natural deployed hibernation/eviction and network recovery soak |
| NET-032 / NET-033 | Ten-lease allocation, rate limits, expiry/departure/recovery implemented/tested locally | Cloud fault/load/cost measurements and healthy-peer outage integration |
| NET-034 | Cloudflare Realtime TURN issuer and authorization path implemented | Cloud account configuration, actual relay paths and billing; already issued credentials last until TTL |
| NET-035 | Local contract/failure/restart suite plus production Wrangler smoke implemented | Full dependency gates; deployed lifecycle behavior is not inferred from local workerd |

The umbrella TODO checkboxes remain open while their listed upstream/integration
acceptance criteria are unfinished. This does **not** mean the backend is still
only a proposal: the implementation and local evidence above are delivered.
Migration milestones in `plan/tasks.json` remain unchanged.

## Explicit remaining integration

The server accepts matching client-supplied build fingerprints; it does not
certify their completeness or client honesty. The catalog is a menu ID snapshot,
not a full runtime/resource hash manifest. Profile limits are validation bounds,
not measured latency/prediction recommendations. Page reload rejection depends
on the client discarding in-memory capabilities; copied credentials cannot prove
browser page identity.

The service's `active` state follows both loaded hashes and start acknowledgments.
A bounded Godot room client and WebRTC peer transport have since been added in
`godot/online_room_client.gd` and `godot/online_peer_transport.gd`; their native
protocol smoke and HTTP/WebSocket signaling contract run are recorded in
[client-network evidence](../../evidence/online/client-network/README.md). The
HTTP/WebSocket smoke uses placeholder SDP strings and does not validate WebRTC.
Clients still need the reliable peer start barrier before stepping, peer pause/
resume/intro controls, ten-second peer recovery, confirmed-state validation and
all rollback/visual/audio handling. Neither loss of the room socket nor a room
alarm decides combat state. A real paired Chrome WebRTC run, Chrome two-machine
matches, forced TURN, mainland network paths, natural cloud hibernation/failover
and operating-cost acceptance remain pending.

The startup investigation found that the current Miniflare converter requires a
correct temporary module root and an explicit v5 resource persistence path.
The regression runner fixes both. Earlier startup failures were not counted as
successful tests. Production build/tests do not include the test-only alarm API.
