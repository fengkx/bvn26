# s265 — AFTER-s263 rank 2: callback-to-scene visual join

Base: master `929161938e30a96179ec18c0206f5787bf2978c9` / #142.
Branch: `feat/s265-callback-scene-visual-join`.
Authority: [AFTER-s263 priority, rank 2 only](../next-fix-priority-after-s263.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 stays pending.
**Evidence-only: one no-encoding placement interval is bounded independently of
frame1, but the encoded lifetime/scene contract is unproved. Admission exits 1.**
Ranks 1 and 3–9, s254–s264, production and strict validators are untouched.

## Result and limits

The locked s262 trace has no placement load/unload observer. Its frame1 entries
cannot retrospectively supply one. A bounded extension of its archived build
therefore adds load/unload ClipActions only to Sprite1813 frame1 depth3, the
Sprite1810 ones digit (`个`). The authored callback, input tape, timer registration,
placements and game scripts are preserved. The root bitmap sampler is replaced
by a **no-draw/no-encoding state observer**, including pre-fight samples. No bitmap
is constructed or exported; there are no new native or Godot images.

One successful native capture records **27,643 events**, **538 ones observations**
(including all **61 fight samples**) and **17 callback firings**. All **122 actor
rows equal s262**. This does not establish equal intro timing, random consumption,
wall-clock callbacks or observer non-perturbation: s262 has 68 callbacks and
fight tick0 at display450, whereas this run reaches tick0 at display478.
No historical callback tape is transplanted or receipt resealed.

[diagnosis.json](diagnosis.json) contains the exact sequences and source placement.
The load counter is an observation of ClipAction delivery, **not an engine pointer
or a universal allocation identifier**. The interval is right-censored at the
last sample; the actual digit is not forced to unload.

| Observation | Native evidence |
| --- | --- |
| Actual ones load | sequence8, display0, runtime depth -16381, load generation1 |
| Actual ones samples | generation1 through sequence27600, display538, tick60, frame9 |
| Retained control | source digit duplicated at dynamic depth100001; load generation2 |
| Retained `gotoAndStop(2)` then `gotoAndStop(1)` | before/after generation2; frame1 entry sequence23024, with no intervening load |
| Same-name/same-depth replacement | old unload generation2 sequence23116, new load generation3 sequence23117 |
| Replacement observation and cleanup | tick3 generation3; later unload generation3 sequence23210 |

The controls are temporary, hidden duplicates of the same digit in its parent,
created at tick0 and removed by tick3. They are probe interventions, not authored
gameplay. The original digit is never reset, replaced or forced to a frame.
Unload callbacks report depth -132770; that value is retained as observed and
is not substituted for the placement depth. No AS2 reference-equality test is
used as lifetime proof.

## Target entry versus draw/encoding

In the retained control, target-frame entry occurs **after** the no-encoding
observer returns (sequence23023 → 23024), despite the synchronous call already
reporting frame1. This independently shows that deferred frame-script entry is
observable without bitmap encoding. It does not isolate the native dispatch
mechanism or prove that encoding has no scheduling effect.

The locked s262 trace separately retains five ones frame1 reentries at ticks
12/25/36/46/56 immediately after `bitmap_end`, plus the tens entry at tick57.
This diagnosis carries the five ones sequence pairs directly from the original
raw trace. Its draw brackets and encoding completion remain unchanged. There
is **no load observer in that run**, and there is **no natural ones frame1 reentry
after initial load in the new short, no-encoding run**. The forced retained
control is not substituted for that missing authored observation.

Therefore `bounded_no_encoding_lifetime_observed=true`, but
`encoded_lifetime_join_proved=false`, `thin_state_admission_proved=false` and
`common_visual_phase_proved=false`. The scene-boundary join is **not attempted**:
its prerequisite is still missing. The prior s262 camera-X and intro/root
mismatches remain evidence, not targets for this PR to fix. There is no production
adapter, HUD reset, offset, renderer change, threshold change or baseline change.

**Next discriminator:** observe the same source-bound load/unload and
retained/replaced controls across an in-memory draw/encoding boundary, after
explicit state-only admission for the bounded placement and without exporting
images. Record actual digit target-frame entry, next root and next callback in
that same run. Do not reuse s262 callback ordinals as the new run's schedule.
Only after that contract passes should a matching intro/root/callback scene
join be attempted; require state admission before paired images.

## Source-first and build provenance

1. The locked [source contract](../s262/source-contract.json) lists all
   Sprite1810/1813 scripts and changes: digit frame1 only `stop()`, other digit
   frames have no DoAction; timer frame1 stops, initializes, registers and defines
   the guarded callback. No authored timer statement is changed here.
2. Ones is a new Sprite1810 PlaceObject at Sprite1813 frame1 authored depth3;
   frame10 removes it. The captured timer remains frame1. The independent load
   hook and retained/replaced control, rather than frame1 serials, bound this cut.
3. The callback selects digit frames with `gotoAndStop`; frame1 script entry is
   recorded separately. No label-end return or inferred child advance is added.
4. Tests enforce missing-load/control/entry/sample rejection and reject any
   bitmap events before admission. They do not assert full engine allocation
   identity or encoded-scene equivalence from the no-encoding observations.
5. This is a fresh original-player run of the unchanged case; its actor control
   matches s262. No native/Godot mechanism is implemented because the full
   source/runtime/scene contract is incomplete.

[build_probe.py](build_probe.py) verifies the archived s262 outputs and source
hashes, adds empty lifecycle records through JPEXS XML, then compiles the observer
scripts. Only the temporary build is modified. [build-audit.json](build-audit.json)
enumerates all 164 XML deltas against the locked build: two script changes, one
ClipAction flag, one added ClipActions child, and 160 serialized bit-width fields
changing 1→0 during XML round-trip. All decoded coordinate/shape values remain
unchanged in that audit; this is not a raster parity claim. No delta is omitted.
The archived SWF and instrumentation diff are bound by the fresh receipt.

## Gates, cost and reproduction

[gates.json](gates.json) records measured commands/exits; [project-checks.json](project-checks.json)
records integrity/handoff/contracts. Diagnosis and native receipt pass. The
required scene-admission gate honestly exits1. Focused tests pass; historical
strict RGBA still exits1. Existing strict validators are unchanged.

The successful bounded build took **6.715 seconds**; one native capture took
**34.512 seconds**, including launch/wait/cleanup, with explicit window activation
and the existing serialized capture lock. An initial build failed before any
capture because a function anchor omitted its parameters; it is retained in
[build-initial-failure.txt](build-initial-failure.txt). Its elapsed time was not
measured. JPEXS reported sandbox settings-log warnings but produced the audited
SWF. No capture retry was needed. Person-days are unknown, not inferred.

Portable diagnosis and negative admission require no player, XML cache or images:

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s265/diagnose.py --output /tmp/s265.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s265/diagnose.py --output /tmp/s265-required.json --require-scene-join  # expected exit 1
python3 -m unittest tools.tests.test_callback_scene_lifetime tools.tests.test_callback_visual_state tools.tests.test_countdown_phase_tape tools.tests.test_sampling_native tools.tests.test_sampling_bitmap
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

For the original receipt check, restore `native-build.tar.gz` to
`/private/tmp/bvn-s265-r02-build` and decompress `native-capture.log.gz` to
`/private/tmp/bvn-s265-r02-capture/native.log`. Use the pinned player and source
versions and the receipt command in `gates.json`; never reseal a historical
receipt. Build reproduction uses `build_probe.py --ffdec /path/to/ffdec.jar
--output /tmp/fresh-s265-build` (Python 3.12+). This builder retains the recorded
run ID: do not recapture that ID into a log that already contains it. Any future
capture needs a separately recorded fresh run ID/build and its own receipt.
The successful capture command is retained in [capture-command.json](capture-command.json).
To reproduce the XML audit, export the archived s262 and s265 main SWFs with
JPEXS26.2.1 `-swf2xml`, then invoke `audit_build.py --before ... --after ... --output ...`.
Temporary XML, caches and player logs remain outside formal source directories.

No merge or deployment. This delivery does not mark the mechanism complete.
