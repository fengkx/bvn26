# Parent replacement checkpoint, r09 (2026-10-23)

**The four full replacement consumers remain unimplemented. This is not a
replacement-runtime completion or native/Godot parity claim.** Cache acceptance
is now **19/26**, down from 22/26 because the stricter audit exposes three more
previously skipped transformation helpers. Build/fingerprint remains **FAIL**.
No runtime or production fighter data changed; no new allowlist, pixel tolerance,
port, merge or deployment.

## New source findings and guards

The r07 forced-goto probe bypassed earlier transformation work. It is useful for
replacement observations but cannot certify the complete transformation entry:

| Source | Earlier rejected entry | Previously reported later dependency |
| --- | --- | --- |
| daitu | body458/frame1307: `wankai()` | 1309 → parent2/body1138 |
| minren | body764/frame1379:5: `_parent.中转.ql = ql` | 1381 timer; 1382 → parent2/body1293 |
| Sasuke | body603/frame1228:5: `_parent.中转.ql = ql` | 1230 timer; 1232 → parent2/body1019 |
| yihu | body638/frame1052: `wankai()` | 1055 → parent2/body1180 |

`wankai()` sets the wrapper flag, copies HP/energy into the wrapper transfer
object, conditionally clears/registers a repeating feixue callback, calls
`_parent.nextFrame()` and resets root Y. Therefore the interval dependency also
applies to daitu/yihu, not just minren/Sasuke. The function is not in the compiled
BODY function set. The old selected-call guard did not include this helper.

The same source helper is also retained at **Byakuya631/1110, rifagu638/1233,
rukia533/1164**. These are the three newly rejected shipped contexts. They must not
be called harmless merely because the existing replay cases do not reach them.
The narrowly hashed Byakuya631/985 exception is unchanged and does not cover1110.

Compilation now rejects these helper calls with SWF, frame, line, definition path
and definition hash, and rejects unresolved wrapper transfer access at its source
line. The requirements catalog is regenerated: seven error records change, all
other records remain unchanged (requirement-review.json). Cached build validation
therefore cannot keep treating the three newly exposed caches as accepted.
replacement-entry-sites.json preserves actual source blocks. No source statement
was removed. Unit fixtures for unrelated shake/numeric-goto/initializer checks
are explicitly scoped so their own guard can still be tested; production source
and timeline data are not narrowed.

## Native live-reference / callback evidence

Four original fighter SWFs were instrumented only at root DoAction. The packaged
`--live-references` probe pins the unchanged definition/non-action tags and records
the imported output, program and tool hashes. At tick1 it installs a field, method
and callback on the old body; tick2 forces the same source goto used by r07; tick3
observes the replacement and tests bidirectional field access through the old
reference. Raw programs, logs and environments are under native/.

All four captures have the same **11 events (44 observations total)**:

- The installed old callback runs once before the replacement, with sentinel73.
- Old reference comparison remains true, but sentinel and old method are undefined.
- Calling the saved function with the old reference as `this` reads undefined.
- Writing `old.khit=37` reaches `mc.khit`; writing `mc.khit=41` is read through old.
- The old callback no longer runs; the newly installed callback runs twice with41.

This supports live path-based resolution and retiring old instance state, rather
than equating source reference equality with Godot node identity. It does **not**
measure saved lexical closures, repeating interval ownership, full main-game
transformations or the exact load/frame-script/enterFrame subphase order. The
probe changes a diagnostic body callback and keeps movement paused. These limits
are why no guessed body-replacement runtime is enabled.

Source-first: original source frame scripts and placements are preserved; only
the root observer forces the source transition. r07 retains load declarations and
new-body frame bounds. Here the invariant is old-reference access after replacement
and retirement of the installed diagnostic callback. Neither capture set proves
full production-main ordering or the earlier wankai transfer/timer behavior.

## Remaining implementation dependencies

- Full atomic body/profile replacement and required target visual/combat/controller
  assets; old pending actions and callback retirement/re-registration.
- Wrapper transfer object, HP/energy restore, doWanKai/initCtrl and key binding;
  source-reference resolution beyond the observations above.
- Repeating feixue callbacks and ownership across replacement. Existing driver
  stop() clears its timeouts and controller tree; that is match teardown and is
  not evidence of correct Flash replacement behavior.
- minren1293/1157 → parent3/body1821, plus preceding transfer/timer dependencies.
- 34 source placement errors, complete AS/clip-action audit and strict pixel diffs.

## Acceptance

- Roster replay: **227/227**, **130,334 states**, unchanged native baselines.
- GPU checks **7/7**; Blur **242/242**, **37,280 alphas**. Blend **38/38** uses
  its existing contract, not a new claim of exact native RGBA parity.
- Standard Godot smoke **3/4 strict passes**: player_visual prints its success
  marker and exits0 but reports nine leaked instances/four resources on shutdown.
  The error is preserved in godot/player_visual.log and is counted as failed.
- Parent conditional, parent rollback and numeric-goto references **3/3 pass**.
- Strict color **3/5** and filter-order **2/4** exact: comparisons **FAIL**, max1.
  No tolerance added. Real-component/XG_rush pixel comparisons were not rerun.
- Placement closures **89/89**; **34** source errors persist, using the pinned
  r06 62-SWF inventory (no new raw scan).
- Target contexts **2/4**: minren1293/1154 wrapper transfer and
  yihu1180/1036 wankai now fail before later dependencies. Compiled context
  results are not complete runtime or asset acceptance.
- Cache **19/26**; build/fingerprint **FAIL**, now naming yihu638/1052 wankai.
- Python: **395 run, 393 passed, 2 skipped**; new hard-error and cached-bypass
  regression tests pass.
- PROTECTED_FUNCTION_OK; integrity (reviewed manifest hashes), handoff and
  contracts **pass**. Python results are recorded in python-final.log.
  Full merge acceptance is **FAIL**.

## Reproduce

```sh
python3 tools/probes/build_parent_goto_probe.py --fighter daitu --live-references \
  --ffdec "$FFDEC" --output "$OUT/daitu"
python3 tools/probes/capture_native_player.py "$OUT/daitu" "$OUT/daitu/native.log" \
  --player-app "$FLASH_APP" --allow-window-activation --timeout 40
# Repeat sequentially for minren, sasuke, yihu.
python3 -m unittest discover -s tools/tests
python3 tools/importer/audit_frame_calls.py --output "$OUT/frame-calls.json"
python3 tools/importer/audit_shipped_placements.py --output "$OUT/placements.json"
python3 tools/test_importer_roster.py --godot "$GODOT" --output "$OUT/roster"
python3 tools/build_online_manifest.py --check
python3 tools/verify.py
python3 tools/check_handoff.py
python3 tools/validate_contracts.py
```
