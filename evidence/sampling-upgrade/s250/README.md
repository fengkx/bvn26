# s250 — Rank 2: AImain display source/frame ownership diagnosis

Baseline `0c1f4d026f17eebc974e97f32a20bd56e9df4f4f`, branch
`feat/s250-display-source-frame`. Exclusive s250 was absent from STATUS/tasks and
on disk at start. This is an **evidence-only Draft PR**, not a mapping fix.
`production_admitted=false`; `native_parity_proven=false`; M0-02 stays pending.

## Decision

The repeated family is `_level0.game.p{1,2}.mc.AImain` at native depth -16383
(authored depth 1), native frame **0**, undefined geometry source stamp and no
sampled children. All 610 observations across s86/s93/s100/s248/s249 have this
shape. Each actor keeps one display ID within its 61-sample capture.

The historical priority description calls these main-source obligations, but
recomputed joins establish **fighter SWF ownership**, not `game/main.swf`:
parent frames place `AImain` as `DefineSprite_3`. Parent body symbols are Lee 518,
Neji 535, Sakura 630, Yulong 345, Yijiao 455 and the shared P2 Yihu 638. Every
sample's actual parent frame, placement attributes, native ID and source hashes
are retained in `diagnosis.json.gz`. No name-only alias is introduced.

Sprite 3 has two authored frames: frame 1 is empty and executes `stop()`;
frame 2 places the fighter-specific AI sensor clips and has no DoAction.
The body `DefineSprite_N/frame_1/DoAction.as::initCtrl` selects frame 2 for AI,
but for a non-AI actor executes `AImain.gotoAndStop(1)` followed by
`AImain.unloadMovie()`. Exact original function text and script paths are in the
report. These captures use mode 3 / P2 CPU false. The native frame-zero empty
object is **consistent with the unload branch**, not an authored frame zero.

A placement proves the source of the authored slot; it does not alone prove
that the sampled frame-zero object retains that timeline after unload.
`sampling_display.as::aiDlWalk` assigns `__aiDlId` only when it visits the object.
These logs do not bind that ID to the receiver before/after `unloadMovie`, and
`__aiGeoSource` is already undefined. A stable sampled ID cannot establish the
missing earlier lifecycle. Consequently neither 0→1 nor a blanket unloaded-node
exception is justified. The existing source-frame gate is left intact.

## Source-first questions and the remaining proof

1. Sprite 3 frame 1 has only `stop()`; frame 2 has no DoAction. The parent
   `initCtrl` function owns the conditional goto/unload operation. Full locked
   bundles and hash-checked timeline exports were inspected; this is a bounded
   source investigation, not an exhaustive gameplay audit.
2. The matched depth-1 placement is a new PlaceObject2 (`placeFlagMove=false`),
   named AImain, characterId 3, placement frame 1. Per-sample retained placement
   records prove the authored slot; they do not prove the unloaded live content.
3. The authored first frame stops. Non-AI initCtrl explicitly goes to 1 and
   unloads; AI goes to 2. There is no authored frame-zero destination to alias.
4. Tests assert authored placement/frame inventory, retain the observed zero
   and its gap, reject removed nodes, and retain sensor-child obligations for 2.
5. Five existing same-tape native captures supply the observations; no fresh
   player run, runtime identity attestation or native/Godot parity is claimed.
   Their pre-sample unload boundary is not captured with a continuous identity.

Before a mapping change, capture **one** source-bound initCtrl unload lifetime:
observe the receiver and the parent's getInstanceAtDepth result immediately
before/after the authored unload, then at the next root boundary and first
sample. Record identity, parent identity/frame, depth/name, current/total frames,
source stamp and child inventory. Preserve the original statements and tape;
retain any terminal callbacks. A later model must distinguish authored slot
provenance from current loaded timeline, retain the zero-frame object and all
unresolved obligations until that distinction has explicit evidence. This PR
does not implement or pre-authorize a gate exemption.

## Recomputed results

| Prior capture | Raw sequence / structure | Samples | Missing source frames | Unresolved symbols |
| --- | --- | --- | --- | --- |
| s86 Lee | 0 / 0 | 61 | 122 | 0 |
| s93 Neji | 0 / 0 | 61 | 122 | 0 |
| s100 Sakura | 0 / 0 | 61 | 122 | 45 |
| s248 Yulong held exit | 0 / 0 | 61 | 122 | 44 |
| s249 Yijiao held exit | 0 / 0 | 61 | 122 | 47 |

All samples and full gap lists recompute byte-for-data equal to the parsed
retained reports. Raw validation here means `validate_capture`, **not** newly
sealed historical receipts: old probe hashes are not rewritten. The current
s249 receipt and full display CLI are separately revalidated in `gates.json`;
full display remains exit 1 with 169 obligations. Masks/camera ownership, other
ranks, mixed modes and s241–s244 remain untouched. No gameplay or production
runtime files change. No prior traces, tapes, receipts or baselines change.

## Reproduction and verification

Restore the XML exports at each earlier slice's `source-exports.json` paths
from its documented source archive (s30 common files; s86 Lee, s93 Neji,
s100 Sakura, s240 Yulong, s233 Yijiao). Restore s249 held build/trace/receipt
as described in its README for the receipt and CLI checks. Then:

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s250/diagnose.py
python3 -m unittest tools.tests.test_display_source_frame_diagnosis
python3 tools/verify.py
python3 tools/check_handoff.py
```

The diagnosis checks locked SWF/script and XML hashes, raw sequence/structure,
and exact recomputation against the retained samples and gaps. The focused
source test reads the retained Lee XML archive directly, with hash verification;
it needs no external XML cache. `gates.json`, `focused-tests.txt` and
`project-checks.json` record executed checks. `manifest-audit.json` records only
reviewed tracked-document hash changes. `session-timing.json` records elapsed
wall time, not inferred person-days. The deliverable is the diagnosed family and
its concrete missing proof; **zero frame obligations are fixed**.

Final verification: 167 focused tests pass (exit 0); s249 retained receipt
validation exits 0, full display exits 1 (169 unchanged obligations). Integrity,
handoff and contracts each exit 0. Development failures are retained: the first
node-removal test forgot URL decoding, then expected ValueError instead of the
collector's existing KeyError; a receipt command initially invoked the capture
CLI without its required arguments (exit 2, no player launch). Only the tests
and invocation were corrected; collector/validator behavior did not change.
