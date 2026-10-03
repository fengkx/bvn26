# Online client integration

Status: The experimental lobby, room client and online battle coordinator are
implemented, with native/fake-peer checks through the integrated `Main` path.
The original-style character/helper selector is now connected to the room-level
peer connection: both peers use the existing VS Human selection view, control
only their own seat, and submit confirmed choices through ordered room commands
before ready is enabled. Short-code create, `join-by-code`, signaling, reinvite,
old-code rejection and cleanup pass in a real RoomClient-to-local-Worker smoke.
A complete browser match has not been accepted.

## Player entry and local setup

The title menu entry is **联机对战**. It opens the experimental room lobby, where
players can create a friend room or join with its invitation code. After both
peers establish the room connection, each uses the original VS Human-style
selector for their own fighter and helper. The room owner controls stage, time
and life multiplier; the network profile must currently agree between both
peers. After both fighter/helper choices are committed, the owner drives the
original-style map selector while the guest sees the same map without local map
input. The service applies the owner's map/rules, the guest acknowledges that
setup, and both players then ready. The owner-side start command is submitted
automatically after both ready states are confirmed. The default room service
URL is `https://bvn26-pvp.fengkx.top`; the editable field can be set to
`http://127.0.0.1:8787` when testing against the local Wrangler Worker.

Run the local service with Node 24.18.0:

```sh
cd services/matchmaking
npm ci
npm run dev
```

In a second terminal, run the native game with Godot 4.7.2 or build and serve the
Web export:

```sh
./tools/build_web.sh
python3 -m http.server 8000 --directory dist/web
```

The service sends wildcard CORS headers for HTTP (`Access-Control-Allow-Origin: *`)
and does not restrict WebSocket `Origin`. It does not use cookie credentials;
room operations still require bearer session tokens and WebSocket upgrades need
a valid one-use ticket. The client keeps seat credentials in page memory; a
browser reload cannot resume an active battle. Local room persistence does not
persist a live match.

The room service admits peers and coordinates setup, start and result agreement.
It does not simulate combat or relay gameplay inputs. `OnlineRoomClient` owns
HTTP room commands and WebSocket signaling, `OnlinePeerTransport` owns WebRTC
offer/answer and data channels, and `OnlineMatchCoordinator` owns immutable
input exchange, rollback clock, ordered match controls, recovery and confirmed
results. Timer delivery and pause-clock policy are documented in
[CLIENT_TIMING.md](CLIENT_TIMING.md).

## Browser match controls

The custom Web shell shows online status and actions in a compact toolbar row
outside the canvas. Fullscreen uses the existing top-edge toolbar and its small
edge handle; an incoming pause/resume request adds a persistent edge label but
does not open the toolbar automatically. An already open toolbar remains visible
while a request or the exit-confirmation step is pending, and the player can
collapse it explicitly. If the shell bridge is missing or rejects a snapshot,
the Godot in-canvas HUD remains available as a fallback.

The bridge accepts bounded schema-versioned JSON snapshots under a registration
token. Each action returns only a fixed action name plus the current local
session, revision and (for a reply) request ID; the lobby validates those values
before dispatch. User-facing strings are assigned as text, never HTML. No match
or transport protocol runs in the shell.

`node --test tools/tests/web_diagnostics_shell.test.mjs` passes 11/11 cases for
snapshot validation, owner-token isolation, action arguments, pending requests,
fullscreen expansion/collapse and the existing diagnostic shell. The
2026-09-23 Godot 4.7.2 production Web export passed online manifest and Lobby UI
smokes; its PCK SHA-256 is
`c474d27d74d19ab46a5547af28954cc8bedbd933c95b81144318e09f8c3e330d`. Chrome
153 then exercised the production Lobby's actual JavaScript bridge in an
isolated Web fixture with a fake coordinator: the compact windowed controls
were 30 px tall with zero overlap, clicking pause incremented the coordinator
callback once, and fullscreen collapse left the edge handle visible while the
canvas retained its 1.5 aspect ratio. The screenshots were temporary files
reviewed inline, not archived repository evidence. The white fixture validates
the bridge and layout only; no WebRTC peer or real online battle was exercised.

The selector integration and room-reconnect cleanup were included in a later
2026-09-23 production Web export built with
`GODOT_BIN=/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot bash tools/build_web.sh`.
The package SHA-256 is
`73968fd70347231b4bb2b85b1f5b46916dd1b220326ef3977c873884dde821d9`; the
export pipeline regenerated and checked the online manifest, ran the native
Lobby UI suite, and produced the Web package. This is a build and native
integration result, not browser WebRTC or full-match acceptance.

## Explicit same-machine or LAN candidate mode

The room setup page exposes **同局域网联调：允许本地地址候选（需双方开启）**.
Both players must opt in so their agreed profile ends in `-lan`; this selects
host-candidate-only ICE configuration and skips the service `/ice` request. It
does not bypass room admission, signaling, browser origin rules or the service
URL. Local candidates can reveal private network addresses to the other player.
Use this only on the same machine or a trusted LAN. It is not an internet
fallback. Leave it off for normal use: internet connectivity requires configured
TURN credentials and browser path testing. No public STUN server is silently added.

## Diagnostics and failure behavior

At the match result page, **下载本局诊断** writes a JSON report to the browser;
the game does not upload it. State-mismatch details remain in local diagnostics;
only a bounded reason, frame and hash are sent to the peer. A peer disconnect or
short signaling-service outage does not itself end a healthy WebRTC battle. The
coordinator attempts bounded reconciliation and applies the tested 10-second
no-winner timeout policy. This is covered with a fake clock/peer, not a real
browser disconnect.

If the room service has no TURN configuration, normal setup fails closed instead
of silently using a public relay. An `-lan` profile bypasses that missing TURN
configuration only when both ready profiles agree. A room-service error and an
unavailable/expired room are shown separately from an agreed match result; a
terminal server result is retained as authoritative.

## Verification and acceptance boundary

The following evidence is available:

- `python3 tools/test_rollback_foundations.py` reports 15/15 native rollback
  foundation cases. `python3 tools/test_shared_modes.py` still compares 602 PvP
  and 602 training-timer actor states.
- `online_match_pair_smoke.gd` runs two independent production `main.tscn`
  instances through the real coordinator, checkpoint and `Main` code. A test-only
  in-memory room/transport JSON-round-trips messages. It covers delayed-input
  correction, a real hit, confirmed hashes, ordered intro skip, mutual pause and
  resume, short recovery, the 10-second no-winner timeout, a source KO, both
  result submissions and rejection of an old epoch. It does not instantiate
  WebRTC peers.
- `online_match_json_room_smoke.gd` round-trips a room projection through the
  production `OnlineRoomClient` validation and `OnlineLobby` into a production
  `Main` scene, then crosses the coordinator's load/start barriers with fakes.
  It exercises the JSON integral-float boundary and rejects booleans, fractions
  and out-of-range metadata without mutating the scene.
- `python3 tools/test_online_lobby_ui.py` and
  `online_lobby_terminal_ui_smoke.gd` cover the native menu/lobby entry, UI
  navigation, terminal results and admission-abandon behavior.
- `online_character_selection_smoke.gd` covers the original-style selection
  adapter, including local-slot-only input, the fighter/helper phase barrier,
  delayed peer confirmation, stale-session rejection and source-rule validation.
  `online_lobby_selection_integration_smoke.gd` runs two production Lobby
  instances with fake room connections and room clients through selection,
  ordered owner/guest `select`, a synchronous room-state push before each HTTP
  reply, return to ready controls, same-choice reselection gating, cancellation
  and re-entry. It verifies adapter-to-Lobby wiring and command ordering; it does
  not use real WebRTC peers or establish browser-gameplay parity.
- `online_map_selection_smoke.gd` wraps the existing `MapSelection` view and
  checks host-only navigation, guest mirroring, confirmation delay, cancellation,
  stale-session rejection and re-entry. `online_lobby_map_selection_integration_smoke.gd`
  drives two production Lobby instances through map configure/guest-ack, failed-
  refresh recovery, host rules draft preservation, readiness after the service
  clears both profiles, and one-shot auto-prepare only after both peers are ready.
  Its fake service JSON-round-trips state and exposes integral-float rule values
  at the same boundary as HTTP; integral values are accepted and fractions are
  rejected. Repeated qualifying state pushes do not duplicate a rejected prepare;
  an explicit retry submits once more. These are native fake-service checks, not
  browser map-flow acceptance.
- A dedicated Chrome 153 two-tab fixture then exercised the production Lobby,
  RoomClient, PeerTransport and selector against the local Worker at
  `127.0.0.1:8787`. Both WebRTC data channels opened; CDP input moved through
  fighter and helper selection, choices appeared in authoritative room state,
  both players reached ready, and both left successfully. The fixture used the
  explicit same-machine/LAN profile with `ICE_SERVERS=[]`; it did not use the
  regular `dist/web` package. Its temporary fixture PCK SHA-256 is
  `b810ae7a78fe160ab5cdb86f72dcf97fa2f83fe2f33fc6c7c62500b0913cccd7`.
  The fixture, run results, production source hashes and one sanitized fighter
  selection screenshot are recorded in
  [client-selection evidence](../../evidence/online/client-selection/README.md).
  This verifies same-machine connection and selection only, not
  cross-network/TURN, reconnect, or a full battle.
- The map selector now wraps the existing `MapSelection` scene behavior. In a
  later same-machine Chrome run, the host's map input moved the picker and the
  guest mirrored it while guest-local map input was ignored. That run stopped
  during service configure with `configured_state_mismatch`; the lobby now
  compares only validated integral rule values so JSON floats match integer
  drafts, and a post-fix browser map configure/ack/prepare result is pending.
  Do not treat the earlier picker observation as a completed browser map flow.
- The Web paste bridge was verified through the browser integration path, and
  the user confirmed macOS Cmd+V works in the online text fields. This does not
  test every IME or clipboard format.
- An isolated production `OnlineRoomClient` Godot Web HTTPRequest probe against
  the allowed local service observed `/health` 200, invalid empty-create 400,
  create 201 and leave 200. It did not use the production menu or `Main`.
- A 2026-09-23 smoke against the deployed production endpoint observed health
  200, room create 201, authenticated `/ice` 200 with two configured
  STUN/TURN/TURNS server entries, and leave 200. Credentials were not recorded.
  A separate Chrome 153 transport harness then used those credentials with
  `iceTransportPolicy=relay`: both selected candidate types were `relay`, and
  bidirectional ping/pong succeeded before the test room was released. See
  [forced-relay evidence](../../evidence/online/turn-relay/README.md). This
  verifies the provider relay path in that harness, not the production Godot
  Lobby/coordinator or a complete match.
- The short-code client has native/fake-service coverage for create, normalized
  `join-by-code`, exact retry, invite rotation and rejection of an old code.
  The real local-Worker RoomClient smoke passed create, normalized
  `join-by-code`, authenticated reads and commands, ticket WebSockets, placeholder
  offer/answer forwarding, guest leave, owner reinvite, stale-code rejection,
  rejoin with the new code and final cleanup. The service's Miniflare short-code
  tests also pass. An earlier local attempt reported HTTP 500, but subsequent
  Worker and RoomClient checks passed; its cause has not been established.
- The 2026-09-23 production Web build with the HTTPS default endpoint and ICE URL
  normalization passed manifest generation/check and the Lobby UI runner. Its
  PCK SHA-256 is `601632b676b1a7cad1cf5cbc893aaf7972f1a3ce65a894884e8470fa62a272bf`.
  This is build/native evidence; the separate forced-relay harness is documented
  above and does not establish full-match acceptance.

Commands and source hashes are recorded in
[client-match evidence](../../evidence/online/client-match/README.md) and
[client-network evidence](../../evidence/online/client-network/README.md).
The RoomClient service smoke ran under approved loopback access; an earlier
default-sandbox attempt could not connect to localhost and is not evidence of a
service outage. The forced-relay harness proves relay-selected ICE and bidirectional
data-channel traffic only at its transport test seam; it does not prove that the
production Godot Lobby/coordinator completes an internet match. The user has
reported that two side-by-side browser windows can start a match, but a confirmed
60-state hash divergence remains under investigation and this is not repeatable
release evidence. Background-tab throttling also remains unresolved. The earlier
Chrome lobby-home observation did not include room admission. The later two-tab
fixture verified the production Lobby's connection and selection path but used a
dedicated test export, so it is not evidence for the regular `dist/web` admission
page or a full game. The production service endpoint is deployed and its
forced-relay transport path has a separate Chrome smoke, while cross-city testing,
production Godot full-match acceptance, full content/action coverage, browser
performance and migration gates remain open; the checkboxes in [TODO.md](TODO.md)
are intentionally unchanged.

## Vercel build commit provenance

The Web build requires either a readable Git HEAD or, when `.git` is absent,
`VERCEL_GIT_COMMIT_SHA`. For Git-connected Vercel projects, enable **Settings →
Environment Variables → Automatically expose System Environment Variables**,
then redeploy. For CLI/source uploads, supply the exact source commit as a
build environment variable for that deployment. Do not save a fixed SHA as a
permanent project variable: later artifacts would claim the wrong revision.
See [Vercel system variables](https://vercel.com/docs/environment-variables/system-environment-variables).

`build_web.sh` now checks provenance before downloading the engine/templates.
Missing provenance fails with `WEB_BUILD_PROVENANCE_ERROR`, actionable setup
instructions, and cleanup of stale sidecars. A content fingerprint does not
replace Git provenance. The `embedded` line printed by metadata unit tests is a
temporary test fixture, not evidence that deployment metadata was generated.

Local regression: 8 metadata tests and 4 pipeline tests cover missing/present
Vercel provenance, Git precedence, early failure/cleanup, template binding and
import failure. This does not establish a successful Vercel deployment; the
project setting still needs to supply the commit at build time.
