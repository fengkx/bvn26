# Online client and timer evidence

Engine: Godot 4.7.2.stable.official.ed1daf0bf. `results.json` records the
15-case rollback foundation report, unchanged PvP/training source comparisons,
controller and visual smokes, both online timer regressions, clock sample
window checks, result normalization checks, terminal-service settlement checks,
the paired coordinator run, a JSON room-projection → Lobby → `Main` startup
regression, and a separate Godot Web HTTPRequest probe of the production
`OnlineRoomClient`. The source hashes describe the exact
client/runtime files reviewed for these results.

The source-triggered round check uses the production `Main` scene and the same
non-terminal KO trigger used by `rollback_round_smoke.gd`. It drives the
compiled `nextfight` interval through round 2, verifies the existing countdown
registration remains active, and compares the full battle-plus-timer checkpoint
after restoring and replaying across the boundary. The separate timer-authority
smoke covers irregular samples, generic cancel/re-register behavior, late
delivery bounds, BODY cancellation and deadline restoration.

These are native adapter and simulation checks. They do not establish original
Flash wall-clock phase equivalence, browser readiness, or an external-network
match. The macOS Godot executable emits a certificate-store warning; the smoke
markers and test exit status are the acceptance evidence.

`http-probe.json` records a separate isolated Godot Web test of the existing
room client against the allowed local matchmaking endpoint. It successfully
read `/health`, received the expected validation error for an empty create,
created and left a temporary room twice, and recorded numeric Godot HTTP
transport/status fields. It does not execute the production menu, Main scene,
WebRTC setup, or an online fight.

`chrome-checkpoint-samples-2026-09-23.md` records one same-machine paired Chrome
Main run with matching frame 0/30/60 checkpoint graphs, plus one hidden-guest
startup timeout probe. The prior false frame-60 mismatch artifact remains
unexplained, and the browser run used an older temporary UI/coordinator/client
copy; see that note for exact hashes and acceptance limits.

The startup-cancellation smokes exercise a configured production `Main` with a
fake room client. They cover cancellation during refresh and ICE lookup, draining
an older uncertain command before aborting, skipping abort after the epoch has
already ended, and retrying an uncertain abort with its retained sequence and
body. The cancellation retry loop has a 20-second budget, but an HTTP request
already in flight may also consume the room client's request timeout; 20 seconds
is not a hard end-to-end wall-clock bound. A timed-out cancel remains
unconfirmed and can be called again to settle the same pending request. These
smokes do not establish remote-tab visibility detection or browser background
fight behavior.
