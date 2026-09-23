# Checkpoint graph-preserving optimization

This note records two focused changes to the battle-local checkpoint encoder.
It is correctness evidence for the serialized graph, not a 30 Hz acceptance
result. Native and Web burst-screening results are recorded below; neither is
a real-time paired-match cadence pass.

## Changes

Round one cached immutable script signal names by Script while still querying
each instance's live signal connections on every save. The first-round
candidate also skipped empty-container identity scans; final-source review
restored the generic scan so a previously registered container keeps its key
if it is later cleared. The round-two prototype cache now limits that scan to
the first prototype of each exact type signature.

Round two caches the empty prototype key by exact Array or Dictionary type
metadata. It avoids repeating duplicate/clear and metadata serialization for
containers of an already-seen type. Typed and untyped dictionaries, key/value
direction, built-in/class/script constraints, and typed Array metadata remain
part of the cache signature. The cache is cleared by `BattleCheckpoint.close()`.
The snapshot graph format and field/record ordering are unchanged.

The next checkpoint pass caches each Script's ordered field descriptors
(property name plus field-name processing flags), replacing repeated property
list reflection and immutable-name classification. Main/match-input identity
checks and the FighterRuntime/HealthHud/KoTimeline/AiSenses type checks remain
per-instance. The immutable-field memo now uses nested instance-id → field
entries and drops invalid instance ids in `retain_states`, avoiding a formatted
string key for each eligible field. These are internal lookup changes only.

The same candidate also includes three non-causal UI/diagnostics fast paths in
`main.gd`: hidden debug labels skip text formatting and writes while health and
energy refreshes continue, and the input-consumed payload is only built when
diagnostics are enabled. The graph-equivalence capture below covers this
combined source.

## Verification

Godot 4.7.2 on macOS passed the focused type-preservation smoke:

```text
BATTLE_CHECKPOINT_PROTOTYPE_SMOKE_OK typed_dictionary_and_array_signatures=true
```

Run it with:

```bash
GODOT=/private/tmp/bvn-toolchain-2026-09-12/Godot.app/Contents/MacOS/Godot
"$GODOT" --headless --log-file /private/tmp/bvn26-checkpoint-graph-a17e361b-round2/typed-final.log \
  --path /Users/fengkx/me/code/bvn2_6/godot \
  --script res://tests/battle_checkpoint_prototype_smoke.gd
```

The capture harness ran the same 331 ticks, fixture, player inputs, intro
events, and engine against the frozen pre-optimization source and the combined
field-descriptor/main hot-path candidate. Each output contains a length-framed
copy of every raw checkpoint graph. `cmp` returned 0, and both final files were 158,996,470 bytes with
SHA-256
`b0227f7af37d10b220bcddcbdc0a73429f31b76c0d1d125c5b81f154897db17b`.

Reproduce the capture and comparison with the checked-in harness:

```bash
GODOT=/private/tmp/bvn-toolchain-2026-09-12/Godot.app/Contents/MacOS/Godot
HARNESS=/Users/fengkx/me/code/bvn2_6/godot/tests/battle_checkpoint_graph_capture.gd
BASELINE=/private/tmp/bvn26-performance-baseline-a17e361b/godot
CURRENT=/Users/fengkx/me/code/bvn2_6/godot
OUT=/private/tmp/bvn26-checkpoint-graph-a17e361b-round2

"$GODOT" --headless --log-file "$OUT/frozen-fields.log" --path "$BASELINE" \
  --script "$HARNESS" -- "$OUT/frozen-fields.trace"
"$GODOT" --headless --log-file "$OUT/current-fields-main.log" --path "$CURRENT" \
  --script "$HARNESS" -- "$OUT/current-fields-main.trace"
cmp "$OUT/frozen-fields.trace" "$OUT/current-fields-main.trace"
shasum -a 256 "$OUT/frozen-fields.trace" "$OUT/current-fields-main.trace"
```

Both capture processes printed `CHECKPOINT_GRAPH_CAPTURE_OK frames=331` and
exited 0. The combined current candidate also passed all 15 cases in
`tools/test_rollback_foundations.py`; `tools/verify.py` and
`tools/check_handoff.py` passed. Godot emitted the known macOS certificate
lookup warning; it did not affect the capture. These checks do not establish
real-time cadence, browser frame rate, or performance improvement.

## Native screening

The native user-log comparison is recorded in
`native-user-log-r01-candidate-r01.json`. It used Godot 4.7.2 and ran in
baseline, candidate, candidate order. Each invocation warmed 90 frames before
the 330 measured frames. The user log supplies inputs on ticks 28–249; the
remaining ticks are neutral padding, and the harness added no attacks,
assists, or supers. This is a partial-tape screening run, not a rollback or
browser acceptance test.

Across the two candidate runs, mean session-step time fell from 21.705 ms to
19.327 ms (about 11%). Mean checkpoint encode time per save fell from 10.557 ms
to 7.768 ms (about 26%). Pack and retain time stayed near 2.0 ms and 0.2 ms per
save. The baseline p95 was 25.983 ms; candidate p95 values were 26.506 ms and
25.350 ms, so the tail did not improve consistently. Candidate p99 values
(38.180 ms and 28.507 ms) and maxima (51.112 ms and 45.702 ms) were also
variable. Host load averages ranged roughly from 6.5 to 9.2, and two candidate
runs are not enough to characterize the tail. Treat the mean and encode
reductions as diagnostic evidence only; the Web results below are a
browser-specific burst measurement, not the paired-match cadence gate.

## Web burst screening

The final browser comparison used the same 330-tick `user-log-r01` fixture and
the visible Web `#report` DOM, loading baseline and candidate sequentially in
one tab. The values below were transcribed from the root's captured DOM
summary (`capture_basis=root-reported visible IAB DOM`); the profiler procedure and build identities are in
`web-build-user-log-r01-final.json`. This is a burst profile of the
single-process rollback workload, not a live two-peer session or a
wall-clock 30 Hz cadence measurement.

For the user no-late-input `receive+step` mode, mean time fell from
23.025 ms to 20.385 ms. p95 moved from 28.000 ms to 26.800 ms, p99 from
29.500 ms to 28.301 ms, and maximum from 31.800 ms to 29.101 ms. Checkpoint
encoding across 331 saves fell from 3,894,400 μs to 2,856,812 μs (about
26.64%). Packing rose slightly from 695,100 μs to 727,489 μs; retain time fell
from 85,900 μs to 78,097 μs. The retained history stayed at 32 states and the
constant table at 1,440 entries. These figures show lower burst workload and
encoding cost for this fixture, but do not measure paired peers waiting on one
another's inputs, real browser frame pacing, or representative rollback under
network jitter; they do not establish a 30 Hz pass.

## Paired-endpoint validation target

The next measurement should exercise two actual Web peers. The current browser
burst profiles do not include the peer clock gate, message delivery timing, or
input correction under delay. In the runtime, the non-authority peer waits for
the next frame's clock sample before calling `rollback.step()` in
`OnlineMatchCoordinator._process_tick`; the authority creates and sends that
sample from its per-frame `advance()`. `_send_peer()` routes input and clock
messages through the ordered reliable data channel. This makes each guest
frame depend on a per-frame peer message, so network wait is the strongest
read-only candidate for the first dual-endpoint cadence bottleneck.

A second candidate is burst correction work: a late input that differs from a
prediction makes `RollbackSession.receive()` restore the preceding snapshot
and replay through the current frontier. Every replayed frame runs the normal
adapter advance and checkpoint validation/save path. The online telemetry
already records `frontierHz`, wait time by reason, coordinator/simulation
percentiles, correction count, replayed frames, correction receive cost, and
checkpoint counters. A minimal check is a visible 60-second paired browser
match with telemetry collected independently from both peers, first on the
normal path and then with controlled network delay. Compare guest `clock`
waits and frontier Hz against coordinator/simulation p95/p99; use correction
counts and replay cost to distinguish late-input CPU spikes. The current
telemetry does not expose peer RTT, so it can localize the stall to clock wait
or correction work but cannot by itself provide one-way delivery latency.
This is a validation proposal only; it does not change the runtime.

## Future candidates

The current graph is serialized to bytes and hex every save because the
snapshot contract stores `owners.graph` as a string. A GDScript hex loop is
unlikely to improve on the engine's native encoder; incremental or compressed
representations would change the graph wire format and decoder contract.

`State.pack_state` and `State.validate_snapshot` traverse only small snapshot
wrappers around that graph string; `validate_value` treats the graph as a
scalar and does not scan its contents. Internal typed pack/validation fast
paths could remove a few repeated wrapper passes while leaving external
validation strict, but their added API complexity is not justified without a
profile showing wrapper traversal is material. If a substantial gap remains,
evaluate an explicit versioned graph representation rather than weakening input
validation or omitting causal fields.
