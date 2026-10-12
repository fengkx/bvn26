# Netcode step 1 — 2026-10-12

Base: `d8437fab`; branch: `fix/netcode-step1`. No deployment or merge.

## Part 1: read-only findings

The line references in this section refer to the base commit.

- **Window zero:** accepted without clamping by `godot/online_match.gd:953`, `godot/online_lobby.gd:1271`, `services/matchmaking/src/protocol.ts:63`, `services/matchmaking/src/state.ts:185`, and `godot/rollback_session.gd:48`. The original lobby only exposed prediction 2/4/6 and delay 0/1/2. At `rollback_session.gd:143`, the next frame cannot exceed `confirmed + window`; zero therefore requires both inputs. Snapshot saving at `rollback_session.gd:227` still saved confirmed frames even with sparse saves. Lockstep can omit ordinary snapshots while retaining initial, periodic hash, control and terminal boundaries. The independent guest clock gate at `online_match.gd:468` still applied.
- **Sync waits:** `online_match.gd:464` sets the pacing wait reason; `online_performance.gd:159` accumulates transitions and elapsed time. The old host-only pacing at `online_match.gd:492` skipped at most one in three ticks. That alone cannot explain ~5.6 sim fps: input waits, guest clock dependency, checkpoint work and replay compound it. The supplied automated wait totals describe a different run from the retained human log, where `hostPacing=false`.
- **Snapshot size:** `battle_checkpoint.gd:155` serializes the graph with `var_to_bytes`; the coordinator adds battle/timer envelopes (`online_match.gd:653`). Human logs contain save time/count but no snapshot byte measurements. A native two-fighter fixture measured graph **218,048 B**, battle envelope **218,468 B**, initial online envelope **218,972 B**, and frame-60 online envelope **220,352 B**. Initial-size streaming at 30 Hz costs **6,569,160 B/s = 52.55 Mbit/s**, before framing/compression. This is a fixture measurement, not a match-wide size bound; local references also prevent treating these bytes as a portable network format.

## Changes and root causes

1. `godot/online_match.gd:1237`: inputs use the existing unordered, zero-retransmission channel. Packets repeat up to 64 unacknowledged input frames plus a contiguous cumulative ACK. Immutable frame input, gap tracking, channel-scoped duplicate detection and batched reconciliation handle reordering/duplication. ACK progress has one recovery attempt and a terminal deadline; controls remain reliable.
2. `godot/online_match.gd:719`: online time is derived from simulation frame (`floor(frame*1000/30)`); both peers and replay generate identical timer samples. No host clock packet gate remains. This deliberately changes online wall-clock behavior under lag; it is not a claim of source wall-clock equivalence.
3. `godot/online_match.gd:506`: symmetric smoothed frame advantage, enter/leave hysteresis at 3/1 frames, at most one extra tick per ten advances (10% stretch). No clock-based stall.
4. `godot/battle_checkpoint.gd:448`: initial checkpoint hashes included fixed native nodes' sibling indices, which vary with local UI/deferred scene disposal despite never being consumed on restore. A different-parent-layout fixture reproduced `$[0].order` divergence and now matches. Dynamic child ordering remains captured. This establishes a reproducible cause; retained human logs do not include the failing initial snapshots.
5. `godot/online_peer_transport.gd:311`, `online_match.gd:524`, `online_lobby.gd:3100`, and `services/matchmaking/src/room.ts:678`: retired epoch traffic, unscoped signaling errors and superseded deferred startup could poison a later match. Ignore retired packets before sequence accounting, scope errors to negotiation ID and reject outdated startup snapshots.
6. `godot/online_lobby.gd:1111`: host URL flags `online_window=0` and `online_delay=3|4` update the existing authoritative pre-match profile. Both members must acknowledge it. No mid-match delay mutation. `rollback_session.gd:225` omits unnecessary lockstep saves.
7. `godot/rollback_battle.gd:150`, `diagnostic_runtime.gd:61`, `main.gd:1023`: replay suppresses diagnostic events and avoids constructing input event payloads. The watchdog distinguishes zero simulation progress from an animation stall.

The super-pause warning at frame 2408 coincided with host page suspension (~17.56 seconds) and guest recovery. No source-level super deadlock was established. The clock dependency is removed and recovery is bounded, but no forced unpause was added. A fresh human super/round-2 match remains required. No fighter timelines or locked inputs were changed.

Compatibility is isolated with regenerated build fingerprints. There are no new Durable Object timers, unconditional alarms or background polling loops.

## Validation

- Worker: 31/31 passed, including profile freeze and retired signaling; typecheck and Prettier passed. Native HTTP integration against local Worker passed.
- Python: 270 run (268 passed, 2 skipped), plus 10 top-level tests passed.
- Godot: all 165 discovered smoke entries attempted; after targeted reruns, **139 passed, 25 native failures, 1 Web-only scene harness pending**. Native failures include 11 AI/menu assertions and 14 exit resource-leak checks. Full per-test results and independent base-runtime comparisons are in the adjacent JSON; not every leak reproduced on base, so these remain unresolved.
- Replay display/event suppression, initial layout, independent clocks/replay, redundant inputs/ACK timeout/lockstep saves, profile/epoch handling and symmetric pacing tests passed. The pair and timer-round functional markers passed but exit leak diagnostics remain failures.
- PVP and training-timer each matched 602 original actor states; super/guard matched 1,800 original snapshots.
- Lossy d3-p6 and d4-p0, plus 100 ms RTT d3-p6 virtual simulations: 300 frames per peer, 10 matching hash checkpoints, zero clock waits. Lossy cases dropped 20 input packets. These are model results, not browser frame-rate measurements.
- `verify.py`, `check_handoff.py`, contract validation (6 schemas/6 examples), online fingerprint verification and `git diff --check` passed.
- Fresh paired-browser/human acceptance remains open. No deployment or merge.

## Manual Web acceptance

1. Rebuild both clients from this commit. Host uses `?online_delay=3`; verify both negotiated profiles before ready.
2. Repeat with `?online_window=0&online_delay=4`; verify d4-p0, no prediction/replay and only periodic/control/terminal snapshots.
3. Inject packet loss, duplication and reordering; verify cumulative ACK progress, matching hashes, reliable controls and zero clock waits.
4. Finish/abort and start a second match in the same room; late first-epoch results/ICE must not abort it.
5. Cast supers on both sides, pause/resume and briefly hide/restore a tab. Export both diagnostics; verify animation resumes or bounded recovery ends the match. Do not infer gameplay deadlock solely from the previous heuristic warning.
