# Cross-machine online lag: diagnosis and optimization plan

Status: In progress, updated 2026-09-29. LAG-01–03 have implementation and
local-test evidence; LAG-01's final export and local IAB identity log match.
LAG-04 has a simulator implementation, but its slow-host result does not
reproduce the field pattern and its cost model remains uncalibrated. No
two-machine field or deployed-page browser-log gate has passed. LAG-11 transport-drain batching has local correctness and native A/B evidence
as of 2026-10-03; see [the record](../../evidence/online/network-lag/lag11-local.md).
LAG-10 sparse saves and LAG-20 host pacing have opt-in local implementations;
[local evidence](../../evidence/online/network-lag/lag10-20-local.md) records their
limits. LAG-30/22/40 and paired acceptance remain open. Current
package states and evidence are tracked in
[NETWORK_LAG_IMPLEMENTATION.md](NETWORK_LAG_IMPLEMENTATION.md), which supersedes
the step order below where they differ. This diagnosis is based on
one pair of user-exported browser logs; no DevTools network capture or
Performance trace could be saved because the pages were too slow. The
[30 Hz performance gate](../../evidence/online/performance-30hz/README.md)
remains **not passed**.

## Input logs

The logs are retained byte-for-byte in
[evidence/online/network-lag](../../evidence/online/network-lag/README.md),
renamed from the exported `P1 net.json` and `P2 net.json`.

| Peer | File | SHA-256 | Browser | Local match id |
|---|---|---|---|---|
| P1 (clock authority) | [`p1-net-2026-09-29.json`](../../evidence/online/network-lag/p1-net-2026-09-29.json) | `bf45ff68ca8c3555111461c8be600fd4cca97b370af7ad82c6cf91e35498d18d` | Chrome 153, DPR 2 | `122058300-46640661829` |
| P2 (guest) | [`p2-net-2026-09-29.json`](../../evidence/online/network-lag/p2-net-2026-09-29.json) | `4417e022c24926d80ab163e90539b6f03551fca5c80080bcffd6daebfa091ade` | Chrome 152, DPR 2 | `118872500-46657439045` |

Both logs report `build.status = "unknown"` with empty build, commit and PCK
fields. The running source therefore cannot be tied to a commit, and it is not
known whether the R4 scalar-dispatch checkpoint change was included. The match
was 白哉 + 松本 against 小李 + 我爱罗 on 温泉, profile `chrome-exp-d2-p6`
(input delay 2, prediction window 6). The figures below come from the
`online_performance` one-second windows and their cumulative `matchTotals`.

## Findings

### Whole-match totals (about 129 s per peer)

| Measure | P1 | P2 |
|---|---:|---:|
| Frames advanced / logical rate | 1,822 / 14.11 Hz | 1,812 / 14.04 Hz |
| Mean `simulation_step` | 30.5 ms | 14.7 ms |
| Per-window step p95, median / p95 of windows | 38.5 / 53.0 ms | 19.3 / 24.9 ms |
| Checkpoint encode / pack per save | 16.6 / 4.0 ms | 7.7 / 1.8 ms |
| Corrections, replayed frames | 375, 1,478 (3.9 per correction) | 0, 0 |
| Correction receive, mean / max | 142 ms / 273 ms | — |
| Simulation + correction receive time | 55.6 s + 53.4 s | 26.7 s + 0 s |
| Waiting | `input` 58.3 s (222 waits) | `clock` 58.7 s (375 waits) |
| Longest caller-tick interval | 0.83 s | 8.57 s |

`correction` time is a subset of `input_receive` time and is not added to it.
`simulation_step` (measured in `process_tick`) and correction receive (measured
in the transport signal path) do not overlap, so they are summed.

### Network path

ICE selected relay/relay (TURN) candidates. Consent RTT samples on the match
connection were mostly 19–50 ms, with isolated 105 ms and 148 ms samples. Traffic
was about 14 KB/s per direction at roughly 276 bytes per packet. The ICE RTT is a
connectivity measure, not input end-to-end latency, but nothing in the logs
suggests that the network is the main limit.

### Root causes

1. **P1 is CPU-saturated.** One logical frame has a 33.3 ms budget at 30 Hz.
   P1's ordinary step already takes 30.5 ms on average, about two-thirds of it
   in checkpoint encode and pack. In the one-second windows, simulation plus
   correction receive used 84–100% of wall time. P2 is about twice as fast on
   the same work.

2. **The clock gate turns rollback into lockstep at P1's speed.** The guest
   cannot step frame N until the host's `clock_sample` for N arrives
   (`godot/online_match.gd::_process_tick`, `local_slot != clock_authority_slot`
   branch). P2 therefore always runs behind P1, holds P1's input before it steps
   (P2 `confirmed` was 2–3 frames ahead of its `frontier` in every window), and
   never predicts wrongly. P1 always runs ahead, predicts every P2 input change,
   and so pays for every rollback on the slower machine. When P1 is 6 frames past
   `confirmed` it stops with `waiting_for_input`. Each peer's speed is bounded by
   the other's, and P2's spare CPU cannot help.

3. **One rollback per mismatched input frame.** `RollbackSession.receive()` calls
   `_correct(frame)` immediately for each late frame that differs from the
   prediction. Several frames arriving in the same transport poll can each
   restore and replay to the frontier. This runs from
   `OnlinePeerTransport._process`, so it also blocks rendering.

4. **Redundant work on the step hot path.** For every advanced frame,
   `RollbackSession._advance_one` saves a complete snapshot, validates it twice
   (`State.validate_snapshot` and the adapter's nested `validate_state`, which
   reaches `BattleCheckpoint.validate_state`), and stores a deep copy
   (`duplicate(true)`). `_correct` copies and validates again, then
   `load_state` validates a third time. In steady play the oldest retained frame
   moves every step, so `_prune` passes the whole retained list to
   `retain_states` every step. A state is saved even for frames stepped with
   both inputs already confirmed, which is every frame on P2.

5. **Lost time is never recovered.** At most one logical step runs per physics
   tick (the delivery contract in [CLIENT_TIMING.md](CLIENT_TIMING.md)). Every
   wait or slow tick becomes permanent slow motion rather than a short catch-up.

6. **All peer messages share the reliable ordered channel.** `_send_peer` always
   uses `"reliable"`. Each input frame is a separate JSON envelope with no
   redundancy. The unordered `input` channel with `maxRetransmits: 0` is created
   but unused. At the observed RTT this is secondary, but over TURN one lost
   packet delays every later input and clock sample (head-of-line blocking).

### Other observations

- **P2 stopped for about 9.2 s.** P2's last input was consumed at monotonic
  250,964 ms and the next at 260,198 ms, and the longest caller-tick interval
  was 8.57 s. The one-second performance summaries, which are emitted from the
  same tick, also stopped. Whether rendering stopped too is not recorded. The
  page was still visible and turned hidden only at 257,450 ms. Both peers then
  raised `suspected_super_pause_stall` with `globalSuperPaused = true` and
  `rootZhanting` set for both fighters. The logs do not identify the blocking
  work. P1 waited at frontier 1,780 for P2's input during this time and entered
  recovery.
- **Replayed combat events on P1.** P1's console shows the same `COMBAT_EVENT`
  two or three times, for example `summon_天天` at 03:11:08.921, 09.143 and
  09.260, while P2 shows it once. Console output is emitted during rollback
  replay; its CPU cost and whether other presentation side effects repeat have
  not been measured.

## Plan

Order is by expected effect and dependency. Each runtime change must answer the
five questions in [SOURCE_FIRST.md](../SOURCE_FIRST.md) where it touches
simulation-visible state, keep the complete-graph parity evidence used by the
existing checkpoint rounds, and must not change retained input/random tapes or
expected outputs. Earlier encoder micro-optimizations
([round 3](../../evidence/online/performance-30hz/round3-checkpoint-profiling.md),
[R4](../../evidence/online/performance-30hz/acceptance-r4-2026-09-28.md)) gave no
stable gain, so this plan targets how often work is done, not the encoder.

### Step 0: Make the next field log attributable

- Fill `build` identity (commit, PCK hash) in the exported Web log so a log can be
  tied to source. Without this, no before/after claim is valid.
- Split the step timer into save, validate, deep copy, load and advance, and
  record them per window.
- Record, per window, how many input frames each `receive` batch contained,
  corrections per batch, and the local-minus-remote frame advantage taken from
  heartbeat `frontier`.
- Suppress console `COMBAT_EVENT` output during replay, or tag it with
  `replaying`, so logs show the confirmed timeline only.

Done when a two-machine log reports non-empty build identity and all of the above
counters on both peers.

### Step 1: Remove redundant per-frame work (both peers)

Code review after this diagnosis found that validation of a locally produced
snapshot is cheap (the binary graph envelope short-circuits `validate_value`);
the measured cost is the checkpoint encode itself. Treat this step as
measurement-gated (LAG-12 in the implementation plan).

- Validate snapshots when they come from outside the process (recovery, peer
  comparison) and in debug/test builds. Do not re-validate a snapshot that the
  local adapter produced one call earlier, and do not deep-copy a snapshot that
  the session owns and never mutates. Keep the existing tamper and rejection
  tests; they must still fail closed on the external path.
- Load a retained snapshot without a second `duplicate(true)` and a second
  validation pass.
- Measure `retain_states`; if it is significant, release only the frame that
  left the window instead of re-deriving retention from the full list.

Done when the delayed-input profile (`rollback_delayed_input_profile.gd`) and the
331-frame graph comparison are unchanged, and paired native runs show a lower
per-step mean than the frozen source on the same fixture.

### Step 2: Save checkpoints only where they can be used

Rollback can only restore the state before an unconfirmed frame. A frame stepped
with both inputs already confirmed never needs its own snapshot unless it is the
last confirmed frame before prediction starts, a `HASH_INTERVAL` frame, or the
recovery comparison frame.

- Save the snapshot at the confirmed boundary before the first predicted frame,
  at hash frames, and at every predicted frame (or only at the confirmed
  boundary and replay from there; measure both).
- `state_at`, recovery sync and hash comparison must keep working from the saved
  frames.

This mostly removes checkpoint cost on the guest and on the host whenever inputs
are confirmed. Done when full-graph parity at hash frames and after every
correction matches the current every-frame save on the existing rollback
fixtures, and the frozen-source A/B shows fewer saves per advanced frame.

### Step 3: One correction per tick

- `receive()` records the remote input and the earliest mismatched frame without
  restoring.
- `process_tick` performs at most one restore and replay from the earliest
  mismatch before sampling and stepping.
- Receiving input no longer runs simulation inside the transport `_process`
  path.

Done when the corrected state after a batch equals the current per-frame
correction result on the rollback fixtures, and the field log shows corrections
per window no higher than batches per window.

### Step 4: Decide the guest clock policy (design decision)

The implementation plan recommends the host throttle (LAG-20) and schedules it
before sparse saves, because the host advances almost every frame as a predicted
frame and sparse saves cannot help it until pacing keeps it near the guest.

The current contract in [CLIENT_TIMING.md](CLIENT_TIMING.md) says the guest waits
for the host's elapsed-millisecond sample and no timer is inferred from a frame
count. That contract is what forces lockstep behavior. The options below keep the
host's samples authoritative but change when the guest may step. A choice needs an
update to CLIENT_TIMING.md and [ADR 0002](adr/0002-rollback-battle-synchronization.md)
before any runtime change:

- **Host throttle by frame advantage.** Keep the guest gate. The host slows down,
  by skipping a tick, when its frame advantage over the guest's reported frontier
  exceeds a threshold. This reduces host prediction depth and rollbacks, but does
  not let the guest use its spare CPU.
- **Speculative guest clock.** The guest steps with a predicted sample and treats
  the host sample as a rollback input. A mismatch only needs a correction when it
  changes which countdown, intro or BODY callbacks are due. This needs a proof
  that the predicted sample never becomes simulation-visible after confirmation.
- **Host sample lead.** The host publishes samples for frames ahead of its own
  frontier. This changes what an elapsed sample means relative to the frame
  that consumes it, and needs its own review.

Done when one option is recorded in the ADR with its invariants, and the paired
same-machine test shows the guest's `clock` wait no longer tracks the host's
`input` wait.

### Step 5: Bounded catch-up (decision, after Steps 1–3)

Allow a small, capped number of logical steps per physics tick when the local
frontier is behind the agreed schedule, while keeping the existing rule that a
backgrounded tab must not trigger an unbounded burst. This changes the delivery
contract in CLIENT_TIMING.md and is only useful once a step costs well under
33 ms on the slower peer.

### Step 6: Input transport

- Send input frames on the existing unordered, no-retransmit `input` channel.
  Each packet carries the last 8 local input frames plus the highest remote frame
  received, so one lost packet is covered by the next. Keep clock samples,
  hashes, control and recovery on the reliable channel.
- Use a compact encoding for input packets (frame number plus a button bitmask)
  instead of a full JSON envelope per frame.
- Rerun the [TURN buffer model](../../evidence/online/performance-30hz/turn-buffer-model.md),
  which currently assumes reliable ordering.

### Step 7: The P2 main-loop freeze

Reproduce the super-pause sequence from this match (白哉 against 小李 on 温泉)
with a Chrome Performance trace on the guest. Check whether the 9 s gap is
synchronous resource or shader loading, garbage collection, or a script loop.
Fix only with evidence from that trace.

### Profile experiment (can run at any time)

Compare `d2-p6` with `d3-p4` on the same two machines. A larger input delay
should mean fewer mispredictions and shorter replays at the cost of about 33 ms
more input latency. This only tunes around the problem; it does not replace
Steps 1–4.

## Acceptance

Use the existing gate in the
[30 Hz performance README](../../evidence/online/performance-30hz/README.md):
a visible 60-second paired match, 30 logical ticks per second without a growing
backlog, and a normal step p95 of 25 ms. In addition, this plan is only complete
with a **two-machine TURN run** like the one above, with build identity recorded
on both peers, showing:

- both peers sustaining 30 Hz, including the slower machine;
- guest `clock` wait and host `input` wait each under 5% of match time;
- no single correction receive over 33 ms at the chosen profile;
- the super-pause sequence completing without a stall on either peer.

A same-machine run or native burst benchmark does not satisfy this acceptance.
