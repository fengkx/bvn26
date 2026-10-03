# Checkpoint field path and prediction stride — 2026-10-03

Local implementation and native measurements only. No deployment, browser
performance claim, original-player parity claim, or closed NET acceptance gate.
This is one additional assisted implementation/test session; effort was not
tracked as a precise duration. The previous sparse-save and pacing results
remain historical evidence in `lag10-20-local.md`.

## Source-first scope and changes

The source scripts, PlaceObject/MOVE operations, label exits, battle invariants,
input/random tapes and timer delivery order are unchanged. These changes affect
checkpoint encoding and storage frequency only. The same logical frames still
execute and corrections use retained input and immutable host clock samples.
Full graph comparisons are engineering determinism evidence, not an original
Flash timing comparison; the five-question review in `CLIENT_TIMING.md` retains
its original-player limitation.

A temporary encoder probe counted 442,170 field visits and 157,788 container
hashes in the 330-frame delayed-input workload. Container hashing took 21,928 us
out of 2,146,425 us of encoding (~1%); it was not changed. Probe instrumentation
is outside the final implementation.

A candidate marked ordinary fields in cached descriptors to bypass special-case
checks. It preserved all 331 raw graph bytes and reduced encoding time slightly,
but a repeat ABBA screen had mean total time 5.270 s baseline versus 5.349 s
candidate. The initial apparent gain was not stable. **The candidate was reverted**;
`battle_checkpoint.gd` is byte-identical to the previous working-tree baseline.
The adopted experiment changes only save frequency, not the encoder or format.

Sparse saves now optionally use `checkpoint_stride=2` for predicted frames.
A correction may start one frame earlier; all inputs and clocks needed from
that saved predecessor are retained. Every 30th frame, pause/resume barrier and
terminal KO still forces an exact save, including odd-numbered frames. Unsaved
frames return an empty state rather than exposing an old snapshot. Only strides
one and two are accepted. The default remains one and sparse saving remains
opt-in pending browser acceptance.

To select the experiment in an exported build, use
`?online_sparse=1&online_stride=2`; omit `online_pacing` (its earlier experiment
showed no throughput benefit). Native flags after `--` are
`--online-sparse-saves --online-checkpoint-stride-two`. Performance diagnostics
record `profile.checkpointStride`. No exported browser was run in this round.

## Verification

- Frozen pre-change and candidate graph captures contain 331 exactly matching
  raw graphs. The complete 155,530,838-byte tapes have SHA-256
  `d4d481fb02ba34f943b18a994131d87e159fa10eb2491b20ccac525ade1c54e9`.
- Every-frame and stride-two real battle sessions compare all candidate retained
  graphs through a 330-frame delayed/duplicate/reversed-input and outage tape.
  There are 1,524 exact comparisons; both correct six times, replaying 40 and 44
  frames respectively. The same retained-state comparison also passes for the field-roster variant.
  No extra live checkpoint saves mask skipped-save effects.
- Synthetic sequential/reversed/shuffled arrivals compare state after every
  arrival, including an unsaved odd frontier and correction across a missing
  predecessor. Unsupported stride three is rejected.
- The paired Main test with stride two covers intro, hit/hash exchange, an odd
  pause barrier at frame 329, resume, recovery, timeout, source KO, result
  agreement and a new epoch.
- Checkpoint scalar, typed-container, immutable-cache, controller and timer
  tests pass. The roster test covers 11 fighters, 4 helpers and 10 maps; the
  round test covers non-terminal transition and terminal KO. These are the
  existing representative checks, not exhaustive move/roster parity acceptance.

## Measurements

Native macOS ARM64, Godot 4.7.2, separate ABBA processes with reference warm-up;
no concurrent test workload during each timing series. The field-path microbenchmark's frozen baseline is an APFS copy of this task's
prior working tree, not a different upstream build. After rejecting that change,
both stride timing series were rerun with the original encoder on both sides to
isolate save frequency. All runs compare their complete final state to the no-late reference.
Commands, source/log hashes, all timing samples and final metrics are in
[lag12-stride-local.json](lag12-stride-local.json).

In the default prediction-heavy workload, stride two reduces saves **371 → 184**,
with replay **40 → 44**. Mean operation wall time falls **5.366 s → 3.931 s**
(**26.7%**); the worst correction across each pair falls **121.591 → 107.460 ms**.
The original input schedule, six corrections, 15 waits and final state remain
unchanged. This does not meet the 33 ms correction target.

The field-roster variant uses 白哉/小李, 松本/我爱罗 and 温泉 with the same
synthetic tape; it is not a reconstruction of the old network log's inputs.
Its mean wall time falls **5.771 s → 4.319 s (25.2%)**, with the same
371 → 184 saves and 40 → 44 replayed frames. The worst correction in the final
ABBA pair is 126.043 → 93.693 ms. Earlier screening runs had more variable worst
corrections; these are local samples, not a tail-latency guarantee.

The old nine-second super freeze is still unlocated. Unordered redundant
input/clock delivery and bounded catch-up remain separate future work. Native
savings establish a useful candidate without substituting for eventual
foreground two-machine Web/TURN acceptance.

The six final simulator scenarios pass their state-hash and reliable-order checks
with sparse stride two. Modeled TURN100 is 25.2/25.0 Hz; the cost model remains
provisional and does not establish browser performance or reproduce the original
slow-host field pattern. Repository verification, handoff, six schema/example
checks, manifest validation, seven manifest unit tests and nine analyzer tests
pass (two analyzer tests skipped). Locked `game/` and `scripts/` inputs are unchanged.
