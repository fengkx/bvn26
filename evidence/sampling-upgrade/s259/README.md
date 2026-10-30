# s259 — Post-s258 rank 1: opt-in geometry completion window

Baseline master `8734c3d6` / #136; branch `feat/s259-post-s258-rerank`.
The [new ranking](../next-fix-priority-after-s258.md) precedes the experiment.
Only rank 1 is executed: **the exact retained s232 Yijiao geometry case**.
`production_admitted=false`; `native_parity_proven=false`; M0-02 stays pending.
A bounded instrumentation fix is demonstrated in an isolated opt-in wrapper;
there is **no default closure rollout or production runtime change**.

## Result and impact

| Run | Complete events | Receipt | Geometry samples / boxes | Full geometry gate |
| --- | --- | --- | --- | --- |
| Normal exit | 5,503 | exit0 | 61 / 240 | exit0 |
| Declared held quit | 5,416 | exit0 | 61 / 240 | exit0 |
| Historical s232, unchanged | 5,705 | exit1 | zero admitted | blocked at receipt |

The normal run ends at done and does not exercise the guard. The held run retains
**34 key_read callbacks after done**, then emits `capture_window_closed` before
any next root increment. All 35 suffix events retain done's tick/display pair;
there is no tick61 or second done. The complete final geometry sample ends with
`geometry_end|4,4` before done. [diagnosis.json](diagnosis.json) retains the exact
sequences, payloads, clocks, root observer and source/build hashes.

Both runs match s232's **122 actor rows on all 14 fields**, all three sets of 122
helper rows and all 61 input-latch rows at ticks0–60. The held run also matches
all **1,591 key reads** exactly by tick/payload. The normal run has 1,557 key reads:
its 34 terminal callbacks did not occur before ordinary shutdown; ticks0–59 match.
No suffix was removed to obtain a receipt. Historical tick61 remains archived;
comparison selects the requested tick range without feeding a shortened trace to
any validator or collector.

Random events remain recorded in full: both runs have the same two callsite
ordinals/order as s232, but **their random values differ**. This is not a replay
of a locked random tape and is not proof of general behavioral invariance or zero
probe perturbation. Each raw stream retains its own random observations. The
actor/input equality establishes only the measured control for this case.
Pre-fight counts and root offsets are retained, not normalized in the capture.

The recovered prerequisite is one bounded non-display capture window. The existing
full geometry gate also passes this particular case after admission; that gate
checks source-bound boxes and both receivers, not native/Godot geometry parity.
It does not close Deidara's receiver initialization, nested Yulong ownership,
other non-display completion failures, display/source, AS or visual obligations.
No claim of a fixed number of other newly passing cases is made.

## Implementation and source-first boundary

[build_probe.py](build_probe.py) fixes the case, characters, helpers, frame count
and standalone geometry mode. It invokes the unchanged ordinary builder, then
recompiles only temporary main script copies with the existing source-bound
terminal-window instrumenter. It uses the historical `aiYulongDisplayComplete`
private flag for compatibility; this does not enable a Yulong case exemption.
The wrapper and complete two-stage instrumentation diff are hash-bound in each
build. Original `game/` and `scripts/` remain untouched.

At done the probe arms the flag. On the next root invocation it records closure,
disables only root observation and event emission, and returns **before**
`aiDisplay++`, `aiFight++`, input/state observation and `aiGeometrySample()`.
The held control moves only the probe's quit request to after closure. It does
not defer an authored gameplay call, alter a source predicate, initialize a
receiver, or change geometry sampling order. Captured SWFs, generated patches,
complete raw streams and new case-bound receipts are archived for both controls.

The five-question source-first boundary is explicit:

1. s254 binds the archived original root observer order; each new build archives
   its complete generated root script and diff. The measured difference is the
   probe's terminal root re-entry, not an authored fighter instruction.
2. No PlaceObject/MOVE lifetime is changed or newly interpreted. All geometry
   source/lifetime fields are still collected by the unchanged observer.
3. No authored label exit, goto or stop is changed. This is a probe window close,
   not a model of a fighter's return or timeline completion.
4. Tests assert actual retained callbacks, final geometry count and strict
   rejection of missing/extra records. They do not encode guessed gameplay.
5. Two fresh original-player runs use the exact s232 case bytes and match the
   measured actor/input controls above. Loader attestation remains absent
   (`runtime_fighter=null`); artifact hashes are not live allocation identity.

This limited source audit does **not** authorize a Godot gameplay change or mark
M0-02 complete. No shared builder, collector, validator, threshold, baseline,
source tape, aliases or runtime is changed. Ranks **2–5 are not started**.

## Verification, provenance and limits

67 focused tests pass, including old s232 rejection, missing terminal callback,
injected later-root event, missing final geometry end and wrong box count.
Receipt completeness and geometry completeness remain separate gates: deleting
geometry_end is rejected by the dimension collector, not treated as a new receipt
rule. Exact commands/exits and measured validation subprocess durations are in
[gates.json](gates.json) and [project-checks.json](project-checks.json).

Both captures used the existing serialized native player lock and explicitly
allowed window activation. No lock was removed. The held capture was additionally
compared byte-for-byte with all run-prefixed host log lines in original order;
the normal host log had already been replaced by the next player launch, so that
extra audit is unavailable for normal. Its complete adapter output and receipt
remain archived. This limit and an initial packaging audit failure are recorded
in [development-notes.json](development-notes.json). No capture was retried or
historical receipt resealed. Build/capture total wall costs were not separately
measured; no duration or person-days are inferred from event counts or tool waits.

## Reproduce

Portable recomputation and focused checks require no player or XML cache:

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s259/diagnose.py --output /tmp/s259-diagnosis.json
python3 -m unittest tools.tests.test_geometry_completion_window tools.tests.test_non_display_completion_diagnosis tools.tests.test_display_completion_default tools.tests.test_yulong_display_completion tools.tests.test_sampling_geometry tools.tests.test_sampling_native tools.tests.test_import_guards
PYTHONPATH=. python3 evidence/sampling-upgrade/s254/diagnose.py --output /tmp/s259-old-strict.json --strict-native
python3 tools/verify.py
python3 tools/check_handoff.py
```

The historical strict command intentionally exits1. To revalidate the fresh full
receipts/gates, restore each `normal/` or `held/native-build.tar.gz` into
`/private/tmp/bvn-s259-{normal,held}-build`, decompress the corresponding raw log
to `/private/tmp/bvn-s259-{normal,held}-capture/native.log`, and copy its receipt
there as `receipt.json`. Use the unchanged pinned probe sources and native player,
then execute the exact receipt/geometry commands in `gates.json`.

For new captures use fresh output directories and run IDs:

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s259/build_probe.py --ffdec /path/to/ffdec.jar --output /tmp/s259-new-build --run-id s259-new
mkdir -p /tmp/s259-new-capture
python3 -m tools.sampling_native --case evidence/sampling-upgrade/s232/yijiao__attack__neutral__ground__near.json --build /tmp/s259-new-build --trace /tmp/s259-new-capture/native.log --receipt /tmp/s259-new-capture/receipt.json --timeout 180 --allow-window-activation
```

Repeat with another fresh directory/run ID and `--hold-quit` for the explicit
held control; do not remove the capture lock. No merge or deployment.
