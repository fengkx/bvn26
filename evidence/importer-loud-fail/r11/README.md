# Form helpers, target assets and clip-action cache guards, r11

**Still Draft; full parent/body replacement and merge acceptance FAIL.** No new
port, merge, deployment, allowlist or pixel tolerance. Production fighter data,
locked SWFs/scripts and replay baselines are unchanged.

Three parallel workers were used: `form_runtime` (A, source helper consumers and
native captures), `placements` (B, fresh SWF/clip metadata audit), and `pixels`
(C, exact arithmetic diagnostic). The lead integrated changes, added target
profile staging/anonymous-load handling, ran acceptance and performed all commits.

## Executable progress and native boundary

A compiles the actual BODY-owned wankai/doWanKai/initCtrl/randAI functions for the
seven blocked base bodies, with explicit wrapper HP/energy/key transfer and a
root-owned interval handle service. Reassigning a handle does not cancel its old
registration; clearInterval cancels only its referenced ID. Independent IDs,
captured functions and strict snapshots are tested. These remain opt-in consumers:
the production root match owner and replacement dispatcher are not connected.
Missing consumers assert, and all existing form entry guards remain hard errors.

Seven original Flash movies establish a new ordering constraint: wankai's
`_parent.nextFrame()` destroys its receiver immediately and aborts its remaining
statements. The following `_root._y=0` does not execute. The compiled helper checks
the replacement consumer's receiver-liveness result and retires accordingly.
Godot matches **7/7 helper sets,28/28 helper observation groups**; all35 raw native
records are retained. This is not full asset/body/phase parity: the test records
boundary effects and invokes initialization separately. Native minren/yihu also
move root_y17→12 in the next target observation; that continuation remains open.
See [form helper evidence](form-helpers/README.md) for source-first answers,
programs, hashes, exact comparison exclusions and commands.

## Target products now staged reproducibly

`tools/importer/stage_parent_forms.py` verifies the locked SWF and every recorded
replacement/load requirement before exporting. An explicit parent-frame slice
supports transformations that are not separate catalog entries, including daitu
parent2. It independently compiles the real visual, combat, body, controller and
context products, records source-located failures, and refuses stale output.
It never publishes generated products or labels a compiled profile as integrated.
Temporary JPEXS exports are deleted automatically; output asset hashes are retained
in [target-profiles.json](target-profiles.json), with [stage log](target-profiles.log).

All four target visual/combat sets now stage: **374/290/254/272 assets** for
daitu/minren/Sasuke/yihu,1190 total. BODY and hit-state compilation also succeed.
Only daitu currently passes every staged compiler, **1/4 profiles**; even that
profile lacks the runtime replacement transaction. Context compilation is **2/4**.

| Target | Exact remaining compile blocker |
| --- | --- |
| minren1293 | frame1154/DoAction.as:5 `_parent.中转.ql = ql`; further timer/frame3→1821 chain still required |
| Sasuke1019 | frame135/PlaceObject2_16_36/enterFrame `_parent.khitn` |
| yihu1180 | frame1036/DoAction.as wankai; frame143/PlaceObject2_651_32/enterFrame `_parent.nn` |

Controller field normalization now preserves identifier boundaries and quoted
strings; it no longer turns khitn into the invalid `value("khit")n`. Unknown fields
still fail, with the SWF and exact controller callback path. No missing field is
defaulted to zero. Target nn/khitn ownership is not silently accepted.

Daitu1138 frame418/PlaceObject2_654_34 has an anonymous load callback positioning
it at the opponent. Combat compilation formerly raised a bare KeyError('name').
It now uses the existing internal placement handle `@placement:34:654:418`, and
materialization exposes that handle to the existing placement consumer without
inventing an ActionScript name. Its source guard/divisor, X-only write and source
hash remain in the compiled operation. Compiler/materializer regressions cover
the missing-name case and unrelated anonymous instances. Runtime code is unchanged;
this is not a new native target-rendering parity claim.

## Placement and pixels

B re-exported all **62 locked SWFs**. The same **34 real unsupported placements**
remain: blend7 ×1, blend13 ×32, DropShadow ×1, with exact frame/depth/XML in the
[fresh inventory](placements/locked-swf-inventory.json). None is harmless or
allowlisted. All are outside current shipped closures, which pass **89/89**.

New **2,407 clip-action lifetime ranges /59,257 frame-depth observations** pin
serialized event names and action-byte hashes through MOVE inheritance and nested
frames. Unknown/malformed metadata and unrepresented KeyPress/keyCode now fail.
Boolean/numeric cache substitution also fails. This closes cache holes, not the
complete runtime ownership audit of each AS event body. Package import and Web
upload dependency regressions were fixed during integration; final tests are
recorded separately from the initial failed run. See [placement evidence](placements/README.md).

C added a packaged ColorMatrix arithmetic probe: **20/24 cases,92/96 channels**
exact, four channels still differ by1. The strict comparator exits1. Opposite error
directions rule out a blanket rounding offset. No production shader changed.
Canonical color/order reruns remain **3/5** and **2/4** exact. Full shipped component
9/54 image and XG_rush mismatches are prior measurements, not new captures here.
See [pixel evidence](pixels/README.md), [color](color-comparison.json) and
[order](order-comparison.json) failures. No tolerance was added.

## Acceptance and remaining gate

Final replay passes **227/227,130334 states** against unchanged baselines
(842.15s). Python **419 run,417 passed,2 skipped**; GPU **7/7** (Blur242/242,
37280 alphas; blend38/38 under its existing contract), standard Godot **4/4** and
additional references/rollback **9/9** pass. No checkpoint shutdown leak occurred
in this run. PROTECTED_FUNCTION_OK, reviewed-hash integrity, handoff and contracts
pass. The new helper check additionally passes7/7,28/28 observation groups.
GPU measurement success does not override the strict pixel failures above.
Counts/logs: [acceptance-summary.json](acceptance-summary.json),
[roster-report.json](roster-report.json), [Python](python.log),
[Godot commands](godot/commands.json) and [Godot results](godot/results.json).
The cache audit remains **19/26** and build/fingerprint FAIL at
`game/fighter/yihu.swf:DefineSprite_638/frame_1052/DoAction.as:1 wankai()`.

Remaining base entry sites are daitu458/1307, minren764/1379:5,
Sasuke603/1228:5, yihu638/1052, Byakuya631/1110, rifagu638/1233 and rukia533/1164.
The narrow hashed Byakuya631/985 rule is unchanged and cannot cover these sites.
Still required: atomic profile/asset swap; actual parent/updateGJL/controller effects;
load/initialization/frame queue and callback retire/re-register ordering; live-path
reference integration; main root timer wiring and later slot-specific feixue
assignments; follow-on forms; full AS/clip-action ownership audit;34 placements;
exact color/order/component/XG_rush pixels. The helper tests do not certify these.

Reproduce the new staging check (use a fresh output directory):

```sh
python3 tools/importer/stage_parent_forms.py \
  --requirements evidence/importer-loud-fail/r07/parent-form-requirements.json \
  --ffdec "$FFDEC" --output "$OUT/forms"
python3 -m unittest discover -s tools/tests
python3 tools/test_importer_roster.py --godot "$GODOT" --output "$OUT/roster"
python3 tools/importer/audit_frame_calls.py --output "$OUT/frame-calls.json"
python3 tools/importer/audit_shipped_placements.py --output "$OUT/placements.json"
python3 tools/build_online_manifest.py --check
python3 tools/verify.py
python3 tools/check_handoff.py
python3 tools/validate_contracts.py
```
