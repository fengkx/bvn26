# Sparse checkpoint and host pacing experiments — 2026-10-03

Status: opt-in local implementations; paired Web/TURN acceptance is open.
Neither experiment establishes that the reported online lag or super freeze is
resolved. No deployment, push, or original-player parity claim is included.
Work took one assisted implementation/test session; elapsed effort was not
tracked precisely. This does not close any migration or NET acceptance gate.

## Implementation and source-first scope

`RollbackSession.sparse_saves` skips a save only below the contiguous confirmed
input frontier. Predicted frames retain stride-one checkpoints. Every 30th
frame, pending pause/resume frame, and terminal KO frame must be saved. Inputs
are still consumed each frame. Replayed snapshots that are no longer saved are
erased, so an old incorrect graph cannot survive a correction.

The input admission floor is independent of retained checkpoints. Restore uses
the nearest saved predecessor and retains its input, immutable clock, and intro
journals. Retention is deliberately conservative and contiguous from the older
restore/recovery anchor. Online sessions using either policy retain periodic
hash frames; generic every-frame fixtures keep their original history limit.
Recovery exchanges `hashFloor`, compares a common periodic checkpoint, and
reports its input admission floor for retransmission. This wire change is
covered by the regenerated compatibility fingerprint. Mixed builds must not pair.

Source-first answers: no per-frame source script, PlaceObject/MOVE, label exit,
or source invariant changes. This changes checkpoint storage and optional host
scheduling only; it does not invent battle rules or edit locked inputs. The
clock remains immutable real elapsed milliseconds and replay uses recorded
samples. Timer phase, random/input tape and callback order remain unchanged.
The original-player comparison limitation in `CLIENT_TIMING.md` still applies;
local full-state comparisons establish engineering determinism only.

`host_pacing` skips at most one in three eligible host ticks when the observed
lead exceeds input delay plus two frames. It excludes the guest and pending
pause/resume/recovery. Input sampling and heartbeat run before the decision.
It stays off: the simulator showed no throughput benefit.

Both flags default off pending browser acceptance. For same-build Web A/B use
`?online_sparse=1` and optionally `&online_pacing=1`. With neither parameter the
baseline save/pacing policy is selected. Native equivalents are
`--online-sparse-saves` and `--online-host-pacing` after Godot's `--` separator.
Exported performance context records `profile.sparseSaves` and
`profile.hostPacing`. These controls have not been tested in an exported browser.

## Validation

The machine-readable companion records measurements, command lines, source
hashes and log hashes. Tests cover:

- Confirmed-input skipping, forced off-interval saves, exact state equality,
  immutable input admission, stale replay snapshot deletion and bounded history.
- Real battle retained full graph bytes with identical inputs, clocks, duplicate
  delivery and temporary outage; no extra live `save_state` calls on skipped
  frames that could mask serializer-cache dependencies.
- Recovery at confirmed frames 60 versus 59 selects common frame 30, including
  mixed local save policies.
- Paired Main scenes: intro, hashes, hits, pause/resume, recovery, timeout,
  terminal KO, room results and new epoch, with both sparse and baseline policies.
- Pacing cooldown and exclusions, rollback failure hooks, diagnostics, timers,
  clock bounds and service/startup cancellation.

The diagnostics counter fixture originally assumed anchors advance on every
input-floor move. The first implementation unnecessarily extended history in
all generic fixtures; this was narrowed to online/sparse sessions, retaining the
original generic memory bound. The extra counter check measures both anchor
copies when the actual retained floor advances. No state expectation, input tape
or performance threshold was relaxed.

## Measurements and limits

The confirmed-input profile runs the same 330-frame battle tape after a no-late
reference warm-up, delivering eight-frame input blocks before advancement.
This isolates confirmed-input storage cost; it is a workload experiment, not a
reproduction of field packet timing. The baseline and candidate are compared
in ABBA order without concurrent test workloads. The final raw graph must match
the no-late reference. The delayed-input profile separately preserves its
existing reverse arrival/duplicate/outage schedule and full-state comparison.
Final confirmed-input means: **13.68 ms → 7.45 ms** per step
(**45.6%** reduction), saves **331 → 51**. Step p95 spans
15.126–15.314 ms baseline versus 14.273–14.320 ms sparse; periodic saves still
produce longer frames. The delayed prediction-heavy workload saves only
371 → 367 checkpoints; mean operation wall time is 5.247 s → 5.139 s (2.1%).
Its worst correction across each pair is recorded in the JSON and remains far
above the 33 ms target. All four runs in each ABBA series match the full-state
reference. See [machine-readable results](lag10-20-local.json).

The six 10-second simulator cases pass their recorded hash/order checks with
sparse saving, both with and without pacing. In LAN/TURN40, the guest saves 9
checkpoints for 299 advanced frames (rather than one per frame), while the host
still saves 298 for 300. These are actual counter counts; their time costs and
logical rates use the simulator's provisional model, not browser timings.
Pacing changes TURN100 from 24.1/23.8 to 23.9/23.6 modeled Hz despite reducing
host replay from 59 to 42 frames. Other cases show no rate gain. Do not enable
pacing by default or claim it fixes lag.

The field bottleneck remains the prediction-heavy host's serialization and
correction stalls. Redundant unordered input/clock delivery, bounded catch-up,
and the reported nine-second super freeze remain unimplemented/unresolved.
The next acceptance run needs two foreground machines on the same exported
build, paired diagnostics and a performance trace spanning that freeze. Native
measurements cannot close that gate.
