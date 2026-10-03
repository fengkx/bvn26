# LAG-11 transport-drain correction batching — 2026-10-03

Status: locally implemented and tested; **Web/TURN and sustained 30 Hz acceptance
remain pending**. Base: `56218a30` (fast-forward from `406ac790`). The working tree
was clean before the pull. No deployment or change to the input/random tapes.
Actual person-days were not tracked; raw operation timings are retained below.

## Change and safety boundary

`RollbackSession.receive` optionally stores late inputs without replaying. The
session remembers the earliest contradicted prediction and reconciles once after
an input burst. Standalone callers retain synchronous correction. Production
`OnlineMatch` opts in between the existing transport drain signals, including the
startup message queue; a caller tick also provides a safety barrier.

Exact state reads, steps, control barriers, recovery comparisons, hashes and
results reconcile first. `confirmed` still describes received inputs; it does
not authorize publishing or pruning a dirty state. `input_floor` is explicit
and currently equals the oldest retained checkpoint. Every simulation frame is
still saved. Invalid messages abort without simulating pending inputs and report
the dirty range and accepted inputs. Failed corrections preserve their original
replay target, and replay hooks unwind on validation, load, advance or save errors.

An input-only drain needs at most one correction. An interleaved control/recovery
message can require an earlier correction before subsequent inputs are accepted;
correctness takes priority over an unconditional one-correction-per-drain cap.
The drain implementation is enabled for the existing experimental online mode;
there is no separate `BATCH_CORRECTIONS` flag. This is narrower than the original
plan's globally deferred receive API. Sparse saves and pacing remain unimplemented.
The uncalibrated simulator remains a limitation, not a passed dependency gate.

## Source-first scope

1. The modified code schedules rollback work around network delivery; it does not
   change `Main._advance_fight` or any compiled DoAction/enterFrame behavior. Source
   callback paths and phases remain those in [CLIENT_TIMING.md](../../../docs/online-multiplayer/CLIENT_TIMING.md).
2. No PlaceObject/MOVE or instance-lifetime rule changes. The existing complete
   graph checkpoints restore the same nodes, callbacks and placements.
3. No goto, stop, fallthrough, timer deadline or host-clock policy changes.
4. Assertions compare identical input delivery and complete retained states,
   immutable-input rejection, final-state reads and replay cleanup. No guessed
   character movement, hitbox or damage expectations were introduced.
5. The local PvP/training original-player evidence described in CLIENT_TIMING
   remains unchanged. This round compares the existing port against the batching
   candidate; it is not a new original Flash or public-internet parity result.

## Serial native performance screen

Godot `4.7.2.stable.official.ed1daf0bf`, macOS, headless. Each invocation first
runs the full 330-frame reference before timing the delayed-input pass. The
baseline is an APFS copy with the original `rollback_session.gd` from `56218a30`;
the profiling script is identical on both sides. Run order is baseline,
candidate, candidate, baseline; no other test ran during these measurements.
Full commands, source hashes, load samples and logs are in
[lag11-local.json](lag11-local.json).

The existing profiler reset had omitted the newly introduced `rebuild_count`
and `rebuild_us`, causing script errors during restore. It now resets all existing
counter keys to zero. The failed initial run is excluded; no battle expectation
was changed. `--batch` selects batched delivery while leaving the tape, reverse
arrival order, duplicate inputs and temporary outage unchanged.

| Measure | Baseline | Batch candidate |
| --- | ---: | ---: |
| Final/confirmed frame | 330 / 330 | 330 / 330 |
| Corrections | 10 | 6 |
| Replayed frames | 65 | 40 |
| Checkpoint saves | 396 | 371 |
| Input-window waits | 15 | 15 |
| Mean operation wall time across the two runs | 5.538 s | 5.140 s |
| Mean total correction time | 0.972 s | 0.600 s |
| Worst individual correction across the two runs | 119.530 ms | 120.278 ms |

Total operation time fell 7.2%; correction work fell 38.3%. Individual correction
stalls did **not** improve. Both candidate runs match the frozen baseline's full
logical final state and their own no-late-input reference, exactly. This is a
native burst screen, not measured browser FPS. An earlier development screen
showed 5.3% total improvement; it is preserved in `/private/tmp/bvn-online-20261003/abba-first-pass.json`
and is not the final-source measurement.

## Correctness checks

- Synthetic batch test: sequential, reverse and shuffled arrivals; all seven
  retained states equal; duplicate input, conflict, pruning and exact-read barriers.
- Coordinator ordering: late input followed by state hash, result, pause request,
  resume commit, recovery sync or invalid input; final history is corrected before
  use, and abort diagnostics preserve the accepted dirty input range.
- Actual battle comparison: the same 330-frame delayed-input fixture compares all
  1,314 retained checkpoints after every input batch, using exact graph bytes. Each Main
  is the first child of an independent container to reproduce separate process
  roots; an initial fixture attempt caught differing root sibling order at frame 0.
  No graph field is filtered or normalized to hide that fixture error.
- Replay hooks: synchronous and deferred failure paths for validation, load,
  advance and save all unwind cleanly and preserve failure diagnostics.
- Existing checks: paired battle/intro/hash/pause/resume/recovery/timeout/KO/new
  epoch, rollback services/battle, online timer round, performance diagnostics,
  clock bounds, startup cancellation and service terminal handling.

Headless service tests run with `--max-fps 60`: the paired result test waits 90
process frames for a real one-second service poll. An initial unbounded-headless
run exhausted those frames before that timer fired; its failure was retained.
The final run passes without changing the poll or its assertions. Known macOS
CA lookup and existing headless audio shutdown resource warnings are listed in
the structured record; script errors are not allowed in passing runs.

Six 10-second deterministic network cases passed equal common hashes and reliable
ordering/conservation: LAN, 40 ms TURN model, slow host, fixed-skip control,
100 ms TURN model and the existing loss configuration. The 100 ms model remains
24.1/23.8 Hz with 21/0 corrections; other rates also match the retained baseline.
No simulated frame-rate gain is claimed. The slow-host model still fails to
reproduce the field CPU saturation, and the product still sends on reliable
channels, so the configured unordered packet loss is not product loss coverage.

Raw logs, the frozen baseline and full simulator output are outside the repo at
`/private/tmp/bvn-online-20261003/`. Repository input integrity, handoff links,
online compatibility manifest and JSON contracts pass. The manifest suite passes
7 tests; the analyzer suite passes 9 tests with 2 existing skips. The regenerated compatibility manifest prevents mixing this runtime
with a different build; enabled content remains 11 fighters / 4 helpers / 10 maps.
The existing generator also hashes ignored `.import` sidecars: regeneration here
removes 28 stale sidecar entries and updates 349 sidecar hashes. All other content
records are unchanged. This cache-dependent fingerprint behavior predates this
patch; the generator and the assets were not modified to hide it.

The remaining dominant cost is full checkpoint encoding/packing on ordinary
frames. Sparse checkpoints require exact hash/control/result saves and compatible
recovery retention; they were not replaced with an unsafe snapshot-skipping rule.
NET-026, M4 and full LAG-11/M1 field gates remain open.
