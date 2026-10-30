# s274 — Encoded digit lifetime before scene join

Base: master `ed5f1e13ecb0b95cea3e4df656ccda885f03418e` / #151.
Branch: `feat/s274-encoded-digit-lifetime`. Exclusive authority:
[AFTER-s272 rank 2](../next-fix-priority-after-s272.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 stays pending.

**Evidence-only: a bounded encoded placement interval is now observed, but the
thin lifetime/state-admission contract is still unproved. Required admission exits 1.**
No production mechanism is implemented. Other ranks and s254–s273 are untouched.

## What changed and what was observed

The locked s265 run observes loads without encoding; s262 encodes without a load
observer. Neither can supply the missing same-run observation. s272 independently
retains the scene-state rejection. One bounded new native run is therefore needed.
[build_probe.py](build_probe.py) extends the archived s262 build using s265's exact
Sprite1813 frame1 depth3 ones placement and load/unload-hook design. Authored
callback code, input tape, timer registration and gameplay scripts are unchanged.
It adds only the local [observer](observer.as), leaving source files locked.

[diagnosis.json](diagnosis.json) replays all **26,828 events**, **512 placement
samples** (61 fight samples), **63 callback pairs** and **57 in-memory encoding
windows** (ticks 4–60). All **122 actor rows equal s265**. This is not equality of
wall-clock timing, intro, random consumption or callback schedules: fight tick0
is display452 here, versus display478 in s265 and display450 in s262. This run has
63 callbacks, versus 17 and 68 respectively. No tape is transplanted.

| Observation | Same-run evidence |
| --- | --- |
| Authored ones load | sequence8, display0, depth -16381, load generation1 |
| Last sampled ones | sequence26778, display512, tick60, generation1/frame2 |
| No-encoding retained control | generation2; forced frame1 entry sequence21691 at tick1, after the observer returns |
| First replacement control | unload2/load3 at sequences21783/21784, tick2; generation3 sampled tick3 |
| Encoded retained control | generation3; forced frame1 entry sequence22066 at tick5, after encoding |
| Encoded replacement control | unload3/load4 at sequences22168/22169, tick6; generation4 sampled tick7; cleanup tick8 |

Controls are hidden duplicates at the same dynamic depth100001 in the same
parent, made from the same source ones digit. Only controls receive forced gotos
and replacement; the actual ones digit is never reset, replaced or forced.
Unload depth -132770 is retained as delivered, not rewritten to placement depth.
Load generations label observed ClipAction delivery, not native allocation
pointers. The actual placement interval is right-censored; its unload is not forced.

The natural ones target-frame entries have a distinct source callback selecting
frame1, completed encoding, then actual frame-script entry, next callback and
next root in the **same run**. Sequence numbers below are raw event indices:

| Fight tick | Encoding end | Actual frame1 entry | Next callback | Next root |
| --- | ---: | ---: | ---: | ---: |
| 17 | 23118 | 23122 | 23124 (ordinal25) | 23129 |
| 27 | 23764 | 23768 | 23770 (ordinal35) | 23774 |
| 37 | 24623 | 24627 | 24629 (ordinal45) | 24665 |
| 48 | 25680 | 25684 | 25686 (ordinal55) | 25722 |

All four entries retain generation1 without a new load. The next callback occurs
before the next root observer in these windows; it is not inferred from elapsed
seconds. The report includes each preceding callback's actual `fire_after` state.
This distinguishes observed frame1 re-entry from placement birth across encoding.
It does not prove that encoding causes the deferred entry or identify an engine
allocation/dispatch implementation. The synthetic retained control is not used
as a substitute for these four natural authored entries.

## State-only guard and remaining admission gap

Before any draw, the local experiment guard requires the retained frame1 entry,
unload2/replacement load3 calibration, the actual generation1/depth -16381,
10-frame digit and timer frame1. It emits `s274_admission=true` before each memory
window. Offline validation additionally requires the complete controls, source
callback outputs and generation/frame snapshots on both sides of every window.
This is **local experiment admission**, not complete visual/scene admission.

The probe draws `_root` into an opaque 600×400 BitmapData and performs the existing
row-RLE arithmetic in memory. It discards row strings and disposes the bitmap;
only total encoded character count is logged. There are **zero pixel payloads,
bitmap rows, image files, new Godot executions or paired images**. Workload differs
from s262 because row traces are removed and lifecycle/control observers added;
no scheduling/non-perturbation equivalence is claimed.

`bounded_encoded_lifetime_observed=true` records the limited result above.
`thin_state_admission_proved=false`, `scene_state_admitted=false` and
`common_visual_phase_proved=false` remain explicit: frame1 entry plus observed
load delivery does not establish an independent child clock across every target
frame, timer allocation identity or registration-to-intro/scene correspondence.
The selected ones interval cannot discharge the whole visual phase contract.
s272's wrong-glyph and camera evidence remains historical and unresolved; it is
neither copied into this run nor repaired. No scene join is attempted here.

**Next discriminator:** for this captured ones placement, first obtain a
source-bound independent child-clock observation across all callback-selected
frames (distinguish synchronous `_currentframe` from actual target entry), with
retained/replaced calibration. Then bind this run's timer registration, intro,
root and callback order to a state-only scene observation. If new hooks require
another capture, use its own run ID, receipt and callbacks; never transplant this
tape into a different run. Require complete same-capture scene admission before
paired images. No HUD reset, camera assignment/rounding, threshold relaxation,
renderer change or gameplay rewrite is authorized by this result.

## Source-first and build audit

1. The locked [source contract](../s262/source-contract.json) enumerates every
   Sprite1810/1813 frame script and timeline change. Digit frame1 has `stop()`;
   frames2–10 have no DoAction. The timer registers its guarded callback at frame1.
2. The ones placement is new (not MOVE), Sprite1810 at Sprite1813 frame1 depth3;
   frame10 removes it. The observed timer remains frame1. Load hooks and the two
   retained/replaced controls independently calibrate the observed interval.
3. The authored callback uses `gotoAndStop`; actual frame1 entry is separately
   logged. No label-end return or inferred playback advance is introduced.
4. Tests reject missing load, wrong generation, missing control, missing admission,
   broken encoding boundaries, pixel payloads, callback loss and mixed runs. They
   do not turn observed generation counters into universal allocation identity.
5. This is one fresh original-player run of the unchanged case. Actor states
   match the locked control; missing scene/child-clock evidence prohibits a
   production mechanism change or parity claim.

[build-audit.json](build-audit.json) enumerates all 164 XML deltas against s262:
two observer script edits, the ones ClipAction flag and records, and 160 serialized
bit-width changes (1→0). The unchanged s265 audit tool rejects unclassified deltas;
no decoded coordinate/shape value changes. This is not a raster-equivalence proof.
The archived build, instrumentation diff, source hashes and raw trace are bound
by a fresh [native receipt](native-receipt.json), not a resealed historical receipt.

## Gates, cost and reproduction

[gates.json](gates.json) records diagnosis, receipt, focused tests, the required
state-admission exit1 and historical strict RGBA exit1 (0/61 exact).
[project-checks.json](project-checks.json) records verify/handoff/contracts.
Existing strict validators and thresholds are unchanged. Contracts are consistency
checks, not behavioral admission.

One successful build took **5.565 seconds** and one successful native capture
**91.580 seconds**, including launch/wait/cleanup with window activation and the
existing serialized capture lock. No capture retry was needed. New capture cost
is necessary because neither locked run contains both lifecycle and encoding.
[Session timing](session-timing.json) records elapsed work; person-days are unknown.
Temporary XML, cache and player logs stay under `/tmp`; only evidence is archived.

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s274/diagnose.py --output /tmp/s274.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s274/diagnose.py --output /tmp/s274-required.json --require-state-admission # expected exit 1
python3 -m unittest tools.tests.test_encoded_digit_lifetime tools.tests.test_callback_scene_lifetime tools.tests.test_strict_raster_admission tools.tests.test_callback_visual_state tools.tests.test_countdown_phase_tape tools.tests.test_sampling_native tools.tests.test_sampling_bitmap
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

Portable replay needs no player or images. To revalidate the original receipt,
extract `native-build.tar.gz` to `/private/tmp/bvn-s274-r01-build` and decompress
`native-capture.log.gz` to `/private/tmp/bvn-s274-r01-capture/native.log`; run the
receipt command in `gates.json` with the pinned player and source versions.
Build reproduction: `PYTHONPATH=. python3 evidence/sampling-upgrade/s274/build_probe.py
--ffdec /path/to/ffdec.jar --output /tmp/fresh-s274-build` (Python 3.12+).
The builder retains the recorded run ID; do not recapture it into a player log
already containing that ID. A future capture needs a separately recorded fresh
ID/build and its own receipt. The executed command is in [capture-command.json](capture-command.json).
For the XML audit, export the archived s262/s274 main SWFs with JPEXS26.2.1
`-swf2xml`, then run `s265/audit_build.py --before ... --after ... --output ...`.

Only s274 evidence, focused tests and requested tracking files change.
No image export, tape transplant, production adapter, merge or deployment.
