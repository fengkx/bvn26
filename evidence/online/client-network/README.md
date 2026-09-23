# Client and transport local evidence

2026-09-23. This record separates protocol/service checks from a real browser
peer connection. It contains no room credentials, tickets, TURN credentials, SDP
or ICE candidate strings.

## Passed checks

The native transport test passed with marker
`ONLINE_PEER_TRANSPORT_SMOKE_OK reordered_input=true reliable_order=true envelope_validation=true early_ice_queue=true`.
It directly exercises the transport's bounded envelope validation, unordered
input reordering/deduplication, reliable sequence gap handling and candidate
queue before SDP. It does **not** initialize two WebRTC peers.

The native room-client unit test passed with marker
`ONLINE_ROOM_CLIENT_SMOKE_OK state_validation=true monotonic_revision=true leave_projection=true exact_retry=true`.
It covers room state validation, revisions, departure projections and byte-identical
retry of uncertain HTTP commands.

The room-client contract test passed against the running local Wrangler service
with marker
`ONLINE_ROOM_CLIENT_SERVICE_SMOKE_OK create=true join=true read=true commands=true ticket_ws=true signal_forward=true leave=true`.
It exercised room creation/join, authenticated reads and commands, one-use ticket
WebSockets, initial room state, and offer/answer forwarding between the two
clients. The signaling payloads were placeholder strings, not real SDP; this is
not evidence of ICE gathering, data-channel establishment, gameplay traffic or
internet connectivity.

An isolated, real two-page Chrome transport probe also passed on 2026-09-23:

```text
ONLINE_WEBRTC_CHROME_PAIR_RESULT chrome=153.0.8010.53 mode=headless_dedicated_profile elapsedMs=2974 success=true cleanupComplete=true iceServers=0
owner offer=1 answer=0 candidate=1 reliable_open=true input_open=true received_reliable=1 received_input=1 leave_http=200
guest offer=0 answer=1 candidate=1 reliable_open=true input_open=true received_reliable=1 received_input=1 leave_http=200
```

The exported probe used the production `OnlineRoomClient` and
`OnlinePeerTransport`: two same-machine Chrome pages created/joined a local
room, opened authenticated signaling sockets, exchanged real SDP/ICE through
the service, opened both WebRTC data channels, exchanged one test packet in
each channel in both directions, and left the room. The service observed
preflight 204, admission 201, ticket 200 and command/leave 200 responses. The
pages were closed after both leave commands succeeded. A noncritical static
resource returned 404; it did not interrupt signaling, channels or cleanup.
No credentials, SDP or ICE candidates were retained.

This is transport-only evidence: it used two browser pages on one machine and
an empty ICE server list for a local/LAN-style path. It does not test two
physical devices, NAT traversal, TURN, cross-city networks, production menu
admission, `OnlineMatchCoordinator` in a browser, or a complete browser battle.
The exported probe inputs were temporary copies with hashes recorded in
`results.json`; this check is not a release acceptance gate.

The paired match-coordinator smoke passed with these markers:

```text
ONLINE_MATCH_PAIR_INITIAL_OK hash=9078270f91f8206c1e144366abd34be703cad3a20061035f69e9b70acb3d16c0 local_preferences_diverge=true
ONLINE_MATCH_PAIR_STARTED_OK
ONLINE_MATCH_PAIR_BOOTSTRAP_CORRECTION_OK frame=15 p1_rollback_count=2 json_roundtrip=true
ONLINE_MATCH_PAIR_INTRO_SKIP_ORDERED_OK target=17
ONLINE_MATCH_PAIR_FIGHT_HASH_OK frame=327 hashes=30,60,90 real_hit=true helper_activity=false
ONLINE_MATCH_PAIR_PAUSE_BARRIER_OK frame=329 equal_hash=true
ONLINE_MATCH_PAIR_RESUME_BARRIER_OK frame=330 equal_hash=true
ONLINE_MATCH_PAIR_SHORT_RECOVERY_OK both_reconciled=true equal_hash=true
ONLINE_MATCH_PAIR_TIMEOUT_ABORT_OK fake_elapsed_ms=10000 winner=null
ONLINE_MATCH_PAIR_SMOKE_OK initial_hash=9078270f91f8206c1e144366abd34be703cad3a20061035f69e9b70acb3d16c0 frame=331 p1_rollback_count=6 json_roundtrip=true
ONLINE_MATCH_PAIR_SOURCE_KO_FIXTURE_OK fighter_check_dead=true
ONLINE_MATCH_PAIR_RESULT_COMMIT_OK source_ko=true p1_waited_for_peer=true room_waited_for_both=true winner=1
ONLINE_MATCH_PAIR_NEW_EPOCH_OK previous_result_rejected=true epoch_changed=true
```

This test runs two separately instantiated production `main.tscn` trees and
real `OnlineMatchCoordinator`, rollback, checkpoint and `Main` logic. It gives
each peer different local input/render preferences, exchanges envelopes through
a fake room and in-memory transport, and JSON-round-trips each peer packet (so
JSON numeric values arrive as floats). It verifies initial full-state equality,
late-input rollback, confirmed hashes, real health loss, ordered intro skip,
pause/resume, short recovery, the 10-second no-winner timeout, source fighter
KO, result confirmation/room agreement, and rejection of an old-epoch result.
The result test holds P2's result message until P1 has not yet confirmed; the
fake room changes to lobby only after both equal results are submitted.

The focused `online_match_json_room_smoke.gd` also passed with marker
`ONLINE_MATCH_JSON_ROOM_OK room_projection=true lobby_main=true setup_normalized=true start_barriers=true strict_rejection=true`.
It round-trips a room-state projection through production room-client validation,
passes the state through `OnlineLobby` into a production `Main`, then uses fake
room/transport barriers to reach coordinator startup. Integral float metadata is
normalized only at the coordinator boundary; boolean, fractional and out-of-range
setup values are rejected without mutating the configured battle. This fixture
does not create or join a real service room.

This is **not** a two-browser or WebRTC test: the peers communicate through a
test-only in-memory fake, so it does not establish ICE or channel behavior. The
smoke fixture uses `minren` + `woailuo` against `yihu` + `kon`; helper activation
was not observed (`helper_activity=false`) and the test does not certify every
selectable fighter/helper. It is narrow rollback/coordinator evidence only.

The focused lobby terminal/admission UI smoke also passed with marker
`ONLINE_LOBBY_TERMINAL_UI_OK room_unavailable_clears_credentials=true authoritative_result_preserved=true ordinary_abort_returns=true admission_abandon_warns_and_clears=true`.
It checks that an unavailable room clears page credentials and cannot be
reopened; an already-finished server result remains visible and can return to
the room; a normal confirmed no-winner abort can return; and abandoning an
uncertain create/join clears local credentials while warning that a remote room
may remain until idle expiry.

The service suite passed **15/15**, including TypeScript checking, SQLite and
workerd contracts, real local WebSockets, signaling replacement/negotiation
behavior, the raw-SQLite preparation-timeout regression, health CORS checks and
the production Wrangler startup smoke. Formatting and the Wrangler dry-run build
also passed. Full commands and current source hashes are in [results.json](results.json).

## Short-code follow-up — 2026-09-23

The client now calls `join-by-code`, shows the short `inviteCode`, and rotates
codes with the existing ordered `reinvite` command. Native client/fake-service
tests cover code normalization, exact uncertain retry, old-code rejection and
code rotation. The matchmaking service Miniflare short-code create/join/reinvite
tests and typecheck passed. The real RoomClient smoke against the local Worker
also passed:

```text
ONLINE_ROOM_CLIENT_SERVICE_SMOKE_OK diagnostics=true create_code=true join_by_code=true read=true commands=true ticket_ws=true signal_forward=true reinvite=true old_code_revoked=true leave=true
```

It created a room, joined through a normalized code, read state, selected both
seats, exchanged placeholder offer/answer messages over the authenticated
signaling socket, left, rotated the code, confirmed the old code was rejected,
rejoined with the replacement and cleaned up. It used the real `OnlineRoomClient`
and local service, but did not instantiate WebRTC or the production lobby/Main.
An earlier local attempt returned HTTP 500; later Worker and RoomClient checks
passed, and the cause has not been established. A default-sandbox loopback
connection failure was followed by a successful run with approved localhost
access, so that failure is not evidence of service downtime. No live short code
or credential was retained. This does not replace the earlier legacy-token
HTTP/WebSocket smoke above.

## Commands

Run the native checks from the repository root:

```sh
/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path godot --script res://tests/online_room_client_smoke.gd
/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path godot --script res://tests/online_peer_transport_smoke.gd
/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path godot --script res://tests/online_match_pair_smoke.gd
/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path godot --script res://tests/online_match_json_room_smoke.gd
/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path godot --script res://tests/online_lobby_terminal_ui_smoke.gd
/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path godot --script res://tests/online_lobby_ui_smoke.gd
```

With the local service running at `http://127.0.0.1:8787`, run its real HTTP and
WebSocket contract check:

```sh
BVN_MATCHMAKING_URL=http://127.0.0.1:8787 /private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path godot --script res://tests/online_room_client_service_smoke.gd
```

Run the backend checks from `services/matchmaking/`:

```sh
npm test
npm run format:check
WRANGLER_SEND_METRICS=false WRANGLER_LOG_PATH=/private/tmp/bvn-matchmaking-build.log npm run build
```

Miniflare and the standalone Godot-to-Worker test need permission to bind/connect
to loopback; a default sandbox run may fail with `EPERM` before tests execute.

## Not measured here

The production menu and `OnlineMatchCoordinator` have not completed an
integrated browser match. The prior UI attempt stayed at the title screen, so
it provides no evidence of production-menu room admission. Local room testing
is now authorized; that authorization does not turn this transport-only probe
into gameplay acceptance. A separate isolated Godot HTTPRequest probe did
create and leave temporary local rooms, as recorded in
`../client-match/http-probe.json`, but it did not use the production menu or
`Main`. No two-device, cross-city, NAT/TURN path or complete match was tested.
No public STUN service was added. See
[client integration](../../../docs/online-multiplayer/CLIENT_IMPLEMENTATION.md)
and the release gates before treating online PvP as playable.
