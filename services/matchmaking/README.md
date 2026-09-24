# BVN room service

A standalone TypeScript Cloudflare Worker with SQLite-backed Durable Objects.
The Worker routes HTTP; one `Admission` object owns ten room leases; each `Room`
object owns two seats, setup, start coordination and WebRTC signaling. It never
simulates combat or relays gameplay inputs. No deployment is required to run it.

## Local development

Use Node **24.18.0** (`.node-version`) and the committed npm lockfile:

```sh
cd services/matchmaking
npm ci
npm run dev
```

Wrangler serves HTTP/WebSocket on localhost:8787 and persists local SQLite state
under the ignored `.wrangler/` directory. HTTP responses allow browser requests
from any origin (`Access-Control-Allow-Origin: *`), and WebSocket upgrades do
not restrict the `Origin` header. The service does not use cookie credentials:
room access still requires bearer session tokens, and each WebSocket upgrade
requires a valid one-use ticket. Use HTTPS/WSS together for a hosted game;
configure LAN addresses explicitly for two-computer tests.

```sh
npm test                 # Typecheck, workerd contracts and production Wrangler smoke
npm run test:restart     # Fresh workerd process, same SQLite path, new WebSockets
npm run build            # Wrangler dry run only; writes ignored dist/
```

Tests use fresh temporary persistence directories and remove only their own
files. A test-only DO subclass exposes alarm controls; it is never imported by
`src/index.ts` or included in the production build. `test/server.test.mjs` uses
the exact Miniflare version pinned by Wrangler, currently `5.20260921.0-alpha`,
through its exported v4-options converter. Its persistence path is explicitly
set using the v5 API; the older per-plugin option is not honored by that converter.
This pre-release dependency is part of the pinned Wrangler toolchain, not a
claim of deployed lifecycle stability. Package versions and test boundaries are
recorded in [backend status](../../docs/online-multiplayer/SERVER_IMPLEMENTATION.md).

For restricted environments, `WRANGLER_LOG_PATH=/tmp/bvn-wrangler.log` keeps CLI
logs outside the user configuration directory. Tests need permission to bind
loopback ports. Set `WRANGLER_SEND_METRICS=false` to disable Wrangler telemetry.

## Protocol v1

The executable validation contract is [src/protocol.ts](src/protocol.ts).
All HTTP JSON bodies are limited to **16 KiB**, streamed with a byte limit. Unknown
keys/types, invalid protocol versions and unsupported content are rejected.
Errors are `{ "error": "stable_code" }` with an HTTP status. Responses use
`Cache-Control: no-store`; secrets must not be logged by callers or gateways.
Nicknames are plain text, at most 32 characters, without markup/control characters.

Generate each token independently using 32 cryptographically random bytes,
base64url without padding (43 characters). Keep seat credentials **only in the
current page's memory**. A browser reload loses them and cannot restore the old
battle. This is a client lifecycle rule; a server cannot prove a browser was not
reloaded when a caller has copied the credentials. Invitations are separate
capabilities, preferably shared in a URL fragment to avoid request/referrer logs.

| Method / path                 | Request / purpose                                                                                     |
| ----------------------------- | ----------------------------------------------------------------------------------------------------- |
| `GET /health`                 | Service/protocol liveness, no credentials                                                             |
| `POST /v1/rooms`              | `{createToken, sessionToken, inviteToken, nickname, compatibility}`; response adds short `inviteCode` |
| `POST /v1/rooms/:id/join`     | `{sessionToken, inviteToken, nickname, compatibility}`                                                |
| `POST /v1/rooms/join-by-code` | `{code, sessionToken, nickname, compatibility}`; code is in the JSON body, never the URL              |
| `GET /v1/rooms/:id/state`     | Authenticated current projection and caller slot                                                      |
| `POST /v1/rooms/:id/commands` | Authenticated `{version:1, seq, operation}`                                                           |
| `POST /v1/rooms/:id/ticket`   | Authenticated, one-use WebSocket ticket, 30-second TTL                                                |
| `GET /v1/rooms/:id/socket`    | WebSocket upgrade, protocols `['bvn.v1', ticket]`                                                     |
| `POST /v1/rooms/:id/ice`      | Authenticated short-lived TURN REST credentials                                                       |

Authenticated HTTP routes use `Authorization: Bearer <sessionToken>`. Browser
WebSockets use the one-use ticket as the second subprotocol, never a URL query
parameter. The server selects `bvn.v1`. Do not log the subprotocol request header.
A new ticket invalidates any unused ticket for that seat. The first socket for a
seat preserves a negotiation already created for the room; replacing an existing
seat connection closes the old socket and invalidates the previous negotiation.
Clients should connect both signaling sockets before negotiating where possible.

`compatibility` is `{protocol:1, build:<sha256>, content:<sha256>}`. Both peers must
supply identical fingerprints. These are caller-supplied identifiers, not server
attestation. The client-side manifest generator exists at
[`tools/build_online_manifest.py`](../../tools/build_online_manifest.py); full
release acceptance and server-side attestation remain outside this service.
`src/catalog.json` freezes the currently exposed 11 fighter resource IDs, four
helper resource IDs and ten map card IDs. Forms are not selectable. The catalog
is checked against current menu data in tests; it does not hash the whole game.

Creation returns `{roomId, slot:0, state, inviteCode}`; joining by either route
returns slot 1. A short code has the form `adjective-animal-xxxxxxxx`; it uses two
32-word indexes and eight random base32 characters for 50 bits of entropy. Codes
are case-insensitive and surrounding whitespace is ignored. Retrying the same
create body returns the same code. The Admission DO keeps a private code result
for that idempotent reply and indexes it by a SHA-256 digest; neither the code nor
its digest appears in room projections. The raw code is returned only to the
owner's create/reinvite response and is not logged.

Join-by-code also includes the guest's client-generated `sessionToken`. An
uncertain retry with the same code and session token returns the same seat; only
one different session token can claim the code. The owner rotates both the legacy
invite capability and the short code using the existing sequenced `reinvite`
command; its response contains the new `inviteCode`. Rotation invalidates the old
code. Guest departure invalidates the code used for that admission; the owner
must re-invite to admit a replacement. Owner departure or room expiry invalidates
all short codes. The legacy token-based join route remains available for existing
clients.

A changed create body with the same create token fails. The room ID derives from
the secret create token, cannot be chosen sequentially, and is never reassigned.
A closed room cannot be recreated with its old token.
The room ID derives from the secret create token, cannot be chosen sequentially,
and is never reassigned. A closed room cannot be recreated with its old token.

Each seat sends commands sequentially with `seq=1,2,...`. Retry the **last**
accepted command unchanged to recover its original reply. Same sequence with a
different command is rejected; older/future sequence numbers are rejected. Read
`members[slot].seq` after reconnecting. Failed commands do not consume a sequence.
Successful leave revokes the credential, so its retry returns unauthorized/closed;
that also confirms it cannot mutate the room again. Idempotency data is bounded
to one reply per seat and persists with the state, not raw signaling payloads.

| Operation           | Fields and authorization                                                                               |
| ------------------- | ------------------------------------------------------------------------------------------------------ |
| `select`            | `revision, choice:{fighter,helper}`; changes only caller's selection                                   |
| `configure`         | `revision, stage, rules:{time,life}`; owner only                                                       |
| `configure_network` | `revision, profile:{id,inputDelay,predictionWindow}`; owner only                                       |
| `ready`             | `revision, ready, profile:{id,inputDelay,predictionWindow}`; ready profile must equal the room profile |
| `prepare`           | `revision`; owner, both ready with the authoritative room profile                                      |
| `loaded`            | `epoch, initialHash`; each peer reports its initialized state                                          |
| `start_ack`         | `epoch`; allowed after both initial hashes match                                                       |
| `result`            | `epoch, frame, hash, winner` (`0`, `1` or `null`)                                                      |
| `abort`             | `epoch`; ends without a winner                                                                         |
| `negotiate`         | `epoch` (null in lobby); owner with an admitted peer                                                   |
| `reinvite`          | `inviteToken`; owner in lobby, replaces the invitation                                                 |
| `leave`             | Guest frees seat; owner closes room; active match has no winner                                        |
| `keepalive`         | Explicit authenticated room activity                                                                   |

Use `state.setupRevision` for the `revision` field. Every projection includes
`state.networkProfile:{id,inputDelay,predictionWindow}`. New rooms default to
`{id:"chrome-exp-d2-p6",inputDelay:2,predictionWindow:6}`. Older SQLite rows
without this field project the same default; an already preparing or active
match continues to use its stored `match.profile` until it ends.

Only slot 0 may change the shared network profile while in the lobby, by sending
`configure_network` with the current setup revision. IDs must be canonical
`chrome-exp-dN-pN` or `chrome-exp-dN-pN-lan`, and N must agree with the bounded
input-delay/prediction-window fields. The `-lan` suffix records the client's
explicit LAN candidate policy; the room server does not choose ICE servers.
Changing the profile invalidates both ready flags and the current negotiation;
resubmitting the same profile preserves readiness. Character, map, rule and
membership changes still invalidate readiness and negotiation but preserve the
independent room network profile. `ready:true` must include the exact current
room profile or is rejected as `network_profile_mismatch` without consuming the
command sequence. `ready:false` clears only the caller's readiness. `prepare`
rechecks that both stored ready profiles match the current room profile and
copies that authority into `match.profile`.

`state.revision` orders room projections, including connection replacement and
lifecycle changes. Ignore older projections on clients, including replies to
retried old commands.

Rule IDs preserve existing configuration: `time` is 30/60/90/**100** (100 is the
source infinity sentinel); `life` is 1–5 (100%–500%, mapping to `maxhp=life*1000`).
The server does not introduce a different combat rule. Profile input delay is
bounded to 0–8 and prediction window to 0–15, but those are protocol limits,
**not measured playable settings**. Both clients must validate their supported
profile and perform NET-039 path/performance checks before becoming ready.

`prepare` generates a unique epoch, uint32 RNG seed, explicit clock baseline 0
and a 30-second setup deadline. Setup is frozen until completion/abort. Both
clients preload, initialize from this common setup, compare via `loaded`, then
acknowledge through `start_ack`. Only the `active` projection permits proceeding
to the reliable **peer** start barrier. Receiving a service reply alone cannot
prove the other client received it: NET-038 must still coordinate the effective
simulation boundary and bounded peer wait. This service does not authorize
independent unbounded simulation or predict client controls.

Results commit only when both peers report the same epoch/frame/hash/winner.
Disagreement, initialization mismatch, explicit abort or departure yields no
winner. Agreement is coordination, not anti-cheat validation. Rematch requires
fresh readiness and a fresh epoch. Old epoch operations are rejected.

## Signaling and room connection loss

Connect with a ticket, receive `{type:'state',state}`, and send textual `ping` to
receive `pong` without waking a hibernating object. During active gameplay send
one ping every minute when possible. The room connection does not carry inputs,
pause/resume, simulation controls, diagnostics or snapshots.

Connect both signaling sockets and wait for each socket's initial room state. The
owner then sends `negotiate`; both peers read its new UUID and expiry before
creating or sending an offer. A first socket attach preserves the negotiation,
but replacing a seat connection revokes it. Then send:

```json
{
  "version": 1,
  "type": "signal",
  "seq": 0,
  "epoch": null,
  "negotiationId": "00000000-0000-4000-8000-000000000000",
  "kind": "offer",
  "payload": "SDP text"
}
```

`kind` is `offer` (owner), `answer` (guest), or `candidate` (either). Payloads are
at most 12,000 characters within the outer byte limit. The peer receives the
message plus `from`; the sender receives `{type:'signal_ack',seq,delivered}`.
Sequence numbers increase per socket; duplicate or decreasing values fail.
`delivered` means a send was accepted by the peer's live server-side socket, **not**
that the peer processed it. There is no durable SDP/ICE queue. When `delivered` is
false, the client may retry that signal with a higher per-socket sequence number;
the receiving client must tolerate repeated descriptions/candidates if an
acknowledgment is lost. If signaling is lost, obtain new tickets as needed, start
a new negotiation and retry the WebRTC exchange. Negotiations expire after 60
seconds; old IDs/epochs never spill into a new exchange.

Socket close/error is not voluntary leave and does not end an active battle.
An active match is exempt from idle expiry. Its service lease is renewed while
there is recent room activity or heartbeat (10-minute reachability window).
If neither page can reach the room service, the 30-minute lease eventually
expires to avoid permanently leaked capacity. The old **peer** battle may still
finish; another match then needs a new room. This is separate from the **10-second
peer interruption** policy, which belongs in the client. A room-service outage
must not trigger that battle timeout. Idle lobby expiry is 30 minutes; pings and
mere state reads do not keep an unused lobby alive.

## Persistence, limits and TURN

All authoritative room transitions are synchronous and committed in a single
SQLite state-row write. Validation failures leave that row unchanged. Async
hashing/issuer/RPC work happens before re-reading state and validating membership;
no in-memory state object is a source of truth across events. WebSocket attachments
retain seat, credential digest, connection generation and rate/sequence counters.
Schema version 1 is mandatory; incompatible versions fail closed. Future schema
migrations must preserve old epochs and credential revocation. Initial migration
`v1` creates SQLite namespaces; no existing production schema is migrated here.

Admission leases, minute-rate counters and alarms are durable. Limits: 10 live
leases, 30 create attempts/minute globally, 1,200 HTTP requests/minute globally,
240/IP/minute, 120 commands/seat/minute, 10 tickets/seat/minute, 4 TURN issues/seat/
minute, 20 join attempts/room/minute, 120 socket messages/connection/minute and
240 signaling messages/room/minute. Rate keys are capped at 1,024 and expired
buckets are removed. IP rate keys contain a SHA-256 digest, not the raw address.
These guardrails are not a billing cap or a replacement for edge abuse protection.
Closed rooms retain a tombstone/state so old IDs cannot be reopened; no gameplay
histories or raw SDP/candidates are persisted. Snapshot projections omit all
credential/invitation digests. Observability is off by default.

Cloudflare Realtime TURN is the default relay provider. Create a TURN key in the
Cloudflare dashboard, then configure its key ID as `TURN_KEY_ID` and its bearer
token as the server-only `TURN_API_TOKEN`. Locally, put these in ignored
`.dev.vars`; in production, add them as Worker secrets with Wrangler. Never put
the token in the repository or send it to clients. The `/ice` route asks
Cloudflare's credential API for four-hour credentials and returns its ICE server
configuration. `stun.cloudflare.com` is free; TURN relay traffic currently has a
1,000 GB monthly free allowance, then costs $0.05/GB egress. Check Cloudflare's
current [TURN pricing](https://developers.cloudflare.com/realtime/sfu/platform/pricing/)
before launch. If the Cloudflare API is unconfigured or unavailable, `/ice`
returns 503. Leaving a room prevents new credential issuance; already issued
credentials expire naturally after four hours. Cloudflare key creation,
production deployment and real relay connectivity have not yet been verified.

Implementation references: Cloudflare's
[hibernation WebSockets](https://developers.cloudflare.com/durable-objects/best-practices/websockets/),
[SQLite storage](https://developers.cloudflare.com/durable-objects/api/sqlite-storage-api/),
and [alarms](https://developers.cloudflare.com/durable-objects/api/alarms/).
