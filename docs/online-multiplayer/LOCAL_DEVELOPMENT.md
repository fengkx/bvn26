# Local room development with SQLite

Status: Research and proposed workflow, 2026-09-22. No package installed, backend
scaffolded, SQLite database created or server started during this design task.

## Recommendation

Yes: SolidObjects + SQLite can implement a local room/signaling backend. Prefer
**Wrangler local development with SQLite-backed Durable Objects** as this project's
default, because production is already planned around Cloudflare DO. Evaluate
SolidObjects as an optional alternative if running the same room business logic
in a standalone Node process is valuable. Do not maintain two independent room
implementations merely to obtain local SQLite persistence.

This is a recommendation, not a new accepted architecture decision. The selection
and evidence belong to [NET-007](TODO.md). It does not move Godot battle simulation
to the server and does not replace WebRTC or TURN.

## What was verified

The user supplied [Introducing Solid Objects](https://solidobjects.dev/blog/introducing-solidobjects).
The article was retrieved through a public HTTP read after the web reader could
not open it. Capability claims were checked against current maintainer sources;
the original introduction alone is not evidence of current runtime compatibility.

| Option | Local state/runtime | Production relationship | Assessment |
|---|---|---|---|
| Wrangler + local DO | workerd/Miniflare, local SQLite-backed DO | Native Worker/DO code and bindings | Recommended primary path |
| SolidObjects + SQLite | Node and `node:sqlite`, Solid actor runtime | Shared actor definitions plus a separate Cloudflare runtime | Viable optional path, additional adapter/verification work |

Cloudflare documents local `wrangler dev` for SQLite-backed DO. Local state is
persisted separately from production, normally under `.wrangler/state`; custom
`--persist-to` directories are supported and should be ignored by version control.
Populate DO data through its application methods. DO SQLite is not a separate D1
database and does not require PostgreSQL for this plan.
Sources: [DO local setup](https://developers.cloudflare.com/durable-objects/get-started/),
[local runtime](https://developers.cloudflare.com/workers/local-development/),
[local data](https://developers.cloudflare.com/workers/local-development/local-data/).

SolidObjects' support matrix specifies Node 24.4+, recommends 24.15+, and lists
TypeScript 5.9+. SQLite uses Node's built-in driver. Bun compatibility has not been
established by this review. The project is MIT/pre-1.0; its Cloudflare runtime is
marked experimental. Pin and re-check exact released versions before a spike.
Sources: [support matrix](https://github.com/cardmagic/solid-objects-js/blob/main/docs/support.md),
[README and license](https://github.com/cardmagic/solid-objects-js),
[Cloudflare release](https://github.com/cardmagic/solid-objects-js/releases/tag/v0.14.7).

The Cloudflare runtime shares definitions imported from `solid-objects/core`;
runtime setup uses `solid-objects/cloudflare`. Actor-host and session-host DOs
provide durable work and hibernating WebSockets. Delivery may repeat; subscription
reconnection yields current committed projections, not every missed event.
Shared application-SQL `commitAction` and SQL-to-DO database migration are not
provided. Maintainers require deployed lifecycle/hibernation soak tests before
claiming this backend stable.
Source: [SolidObjects Cloudflare backend](https://github.com/cardmagic/solid-objects-js/blob/main/docs/cloudflare.md).

## Meaning of SQLite in this project

Persist room ID/lifecycle, setup revision, participant slots, authorization/session
references, match epoch, readiness, expiry and bounded idempotency/lease metadata.
Where secrets require persistence, store only the necessary protected reference
or digest rather than leaking invitations and credentials through SQL debug output.

Do not store 30 Hz gameplay inputs, rollback snapshots, random tapes or live damage
calculations in the room database. Those remain in the two browser simulations and
their bounded local diagnostics. Database recovery does not restore a disconnected
player's battle; page-reload match recovery remains out of the first version.

SQLite supplies storage, not the entire service. Both runners still need routing,
authentication, atomic room transitions, WebSocket handling, expiry and limits.
A database file is not a TURN server or a WebRTC signaling protocol.

## Proposed default project layout and commands

Create one backend package at `services/matchmaking/` in NET-027. No existing JS
backend package-manager convention was found in the inspected root/service paths;
use npm as the initial proposal unless a current repository convention supersedes it.
Pin toolchain/dependencies with the package manager and commit its lockfile.

Proposed scripts, to implement and verify rather than run before scaffolding:

| Script | Purpose |
|---|---|
| `npm ci` | Reproduce the pinned backend dependencies |
| `npm run dev` | Run pinned Wrangler locally with SQLite DO state |
| `npm test` | Room contract, SQL lifecycle and real local WebSocket tests |
| `npm run test:restart` | Restart with the same test persistence directory and reconnect clients |
| `npm run dev:solid` | Optional only after NET-007 selects a supported Solid runner |
| `npm run test:parity` | Optional shared room-contract suite across selected runners |

The local environment uses local bindings and development-only secrets; no remote
binding or production credential should be required for ordinary room tests. Stub
TURN credential issuance locally when testing authorization; actual relay behavior
is tested separately with a real provider in NET-040.

Use per-test temporary persistence directories for clean isolation and a separate
ignored development directory for deliberate restart persistence. Reset only the
explicit test directory; do not erase a developer's persistent state by default.
Keep SQLite/WAL/SHM files, `.wrangler/` runtime state and private secrets untracked.

Serve the Godot Web build over local HTTP(S), connect its configured room endpoint
to the local service, and use two Chrome contexts for the first integration smoke.
For two-computer/LAN tests, explicitly configure reachable addresses and the correct
HTTP/WS or HTTPS/WSS pair; localhost success does not validate mixed-content rules,
TLS deployment, NAT traversal or internet connectivity.

## Optional SolidObjects path

This is an alternative framework/runtime design, not an arbitrary native DO-code
emulator. Keep room transitions in portable Actor definitions, with thin adapters
for Node + SQLite and Workers + Solid's DO backend. Avoid Node-only calls and shared
SQL transactions in portable room logic if production needs the Cloudflare backend.
Use versioned application schema/state migrations in both environments, without
assuming a local SQLite file can be uploaded as production DO storage.

Preserve the project's externally observable room protocol. Node still needs an
HTTP/WebSocket gateway. Either supply protocol adapters or validate that Godot can
consume the framework's documented realtime envelopes; the presence of a JavaScript
browser client does not automatically supply a GDScript client.

Do not treat state subscriptions as reliable replay of WebRTC negotiation. Room
state may use a revisioned current-state projection, but offer/answer/ICE messages
need their own `negotiation_id`, match epoch, expiry and retry/restart rules.
An old candidate must not leak into a new connection after reconnect. This is a
project design requirement derived from the documented subscription semantics.

Solid's actor/session DO layout adds objects, envelopes and storage work relative
to the current direct room-DO proposal. If selected, update the backend diagram,
request/storage counts, lifecycle handling and `COSTS.md`; keep the production
budget target and two-browser battle architecture unchanged.

## Required NET-007 comparison probes

| Probe | Required observation |
|---|---|
| Create two rooms and race three joins into one | Isolation and exactly two seats, with explicit third-player rejection |
| Duplicate ready/start or edit after ready | One epoch and correct readiness invalidation |
| Persist, stop the local process, restart | State survives; clients explicitly reconnect because process death closes sockets |
| Evict/hibernate an instance without killing the process | State and subscriptions reconstruct according to that runtime's supported semantics |
| Idle expiry with no subsequent client request | Expiry work fires; missing scheduler liveness is detected |
| Fail after accepting an operation, retry it | No duplicate seat/start/result despite at-least-once delivery |
| Reconnect during offer/answer/ICE exchange | Explicit retry/new negotiation; no assumed replay of every missed event |
| Revoke member/session while connected | No unauthorized future messages, subscriptions or credential issuance |
| Restart/roll forward state schema | Migrations retain invariants; unsafe rollback is reported explicitly |
| Stop room service during healthy peer gameplay | Current game continues; next match remains blocked until revalidation |

Run the same observable room-contract cases against every supported runner. Native
Wrangler remains the deployment-compatibility gate for the selected Cloudflare
backend. After local tests pass, real deployed isolated-environment tests are still
required for lifecycle, quotas and mainland paths under authorized implementation.
Do not equate Node persistence, local hibernation and cloud failover.

Record runtime/library versions, code/adapters needed, cold-start/recovery times,
storage/DO request counts and unsupported cases. Prefer the smallest validated
solution for this room service; add SolidObjects only if its portability or actor
facilities justify the extra surface. No choice here removes NET-019 full-content
restoration or NET-040 real-network acceptance.
