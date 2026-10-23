# Parent field ownership and conditional runtime, r08 (2026-10-23)

**Partial implementation: the parent-field/conditional consumer is complete for
these reviewed blocks; the four full body-replacement consumers are not.** Cache
acceptance remains **22/26** and build/fingerprint remains **FAIL**. No new port,
allowlist, pixel tolerance, merge or deployment.

## Implemented runtime and compiler behavior

`FighterRuntime.source_parent_values` owns wrapper fields separately from
`AiSourceState.values`. The compiler reads their boolean initial values from the
source root declarations; runtime reads/writes require an existing compiled field.
Resetting body state does not reset the wrapper dictionary. The existing rollback
graph captures it, verified for both false and true in parent_state_checkpoint.gd.
This establishes state ownership, not full body replacement, callback retirement
or AVM1 MovieClip-reference equivalence.

The exact whole block `if(_parent.万解 == true) { _root.cbsw(pn); bs = 0; }` now
compiles to a parent conditional containing ordered super-end and body-write events.
The callback receives bs before the assignment. Body fields with the same spelling
do not satisfy the parent condition. Top-level `_parent.万解 = true/false` writes
also have an explicit consumer. Built-in display fields keep their existing owners;
this rule does not claim arbitrary parent-property support.

Cached frame-call validation now checks parent initial values with type-preserving
hashes: missing values, false→true, false→0 and false→null all fail. The refresh tool
updates only frame_calls and their required parent initial values, preserving other
cached context fields. Byakuya's exact same 631/985 block is now compiled and its
cache gains the source false initializer. The existing narrowly hashed allowlist
entry is unchanged and no longer needed to skip this compiled block; it was not
expanded. Only this fighter cache changed. Re-running the refresh is idempotent.

## Source-first / native observations

1. Native inputs are the actual minren 1293/frame 996 and Sasuke 1019/frame 1024
   DoAction blocks, retained verbatim in conditional-fixtures.json. Their entire
   bodies are the condition, cbsw call and bs assignment; there is no goto/stop.
   The root declaration is `var 万解 = false;`.
2. The packaged original-SWF probe preserves all non-DoAction root tags, placement
   and clip actions and original nested definitions. It enters parent frame 2,
   waits for the replacement body, then tests false and true separately. Movement
   callbacks are paused. No original game/ or scripts/ file is edited.
3. The tested blocks fall through normally. The probe's explicit setup gotos are
   diagnostic inputs, not inferred gameplay exits or a full transformation replay.
4. Native false result is bs=91 with no cbsw call. Native true result calls cbsw
   while bs=91, then observes bs=0. Godot's real `_frame_service` matches all **6/6
   observations across 2/2 source cases**, exactly. Both harnesses intercept the
   existing super-end service to measure the call and its ordering; this is not a
   new certification of the global cbsw implementation's side effects.
5. Flash Debugger 32 raw captures, actual programs, hashes and environments are in
   native/. Godot's fixture consumes the compiled blocks and captured values in
   conditional-fixtures.json. parent-reference.log records success. Parent state
   survives a body-state reset and false/true rollback restore; neither test claims
   a complete replacement display/controller lifecycle.

The numeric-goto regression remains **31/31**. No form-change native/Godot parity
claim is made for the broader r07 observations.

## Additional real missing behavior, kept as hard errors

Resolving the condition lets the Sasuke target context compile; target-context
acceptance improves **2/4 → 3/4**. Daitu 1138 (1,407 frames), Sasuke 1019 (1,165),
and Yihu 1180 (1,042) contexts compile. They still lack complete published target
assets/controller/combat and a replacement-runtime transaction.

Minren target 1293 exposes another parent transition at **frame 1157 → parent
frame 3 / body 1821**, with a PlaceObject3 load. next-parent-requirement.json
preserves that dependency. It is not safe to declare the source supported after
handling only frame 2.

The immediately preceding source frames also schedule a repeating callback:

- minren base **764/1381**, target **1293/1156**: setInterval(feixue,1000).
- Sasuke base **603/1230**: setInterval(feixue,1000).

These frame timers have no consumer and previously could disappear behind the
later parent-goto error. Non-initial-frame setInterval now hard-fails with SWF,
path, line and statement. The minren/Sasuke base errors consequently report these
earlier sites instead of waiting until their parent jump. The full target audit
now rejects minren at 1156; the next 1157 dependency remains explicitly recorded.
No stripping, unconditional execution or allowlist is used to turn them green.
frame-timer-sites.json also inventories three clearInterval(tdint) sites whose
existing ownership remains to be reviewed; they are not automatically classified
as missing or harmless by this new scheduling guard.

The four replacement runtime/asset consumers, live path-reference resolution,
load/frame-script/enterFrame ordering, callback retire/re-register and broader
wrapper transfer state remain unfinished. This is why **26/26 is not reached**.

## Acceptance

- Python: **392 run, 390 passed, 2 skipped** (parent-scope, strict initializer,
  unsupported-write and timer guards); python-final.log.
- Roster: **227/227**, **130,334 states** against unchanged native baselines.
- Godot usual smoke **4/4**, existing GPU assertions **7/7**; Blur **242/242 /
  37,280 alpha samples**, blend **38/38** under its unchanged existing contract.
- New conditional native reference **2/2 cases / 6/6 observations**; new parent
  rollback test passes; existing controller checkpoint test passes.
- Extra battle_checkpoint_smoke prints its success marker and exits 0, but reports
  a resource still in use / three ObjectDB instances at shutdown. Its strict log
  check is recorded as failed (the documented headless/audio cleanup class of
  diagnostic); it is not counted as an unqualified pass or hidden from the logs.
- Strict colors still **3/5** exact and order **2/4** exact, remaining maximum 1;
  full comparisons fail. No new pixel tolerance. Real component/XG_rush pixel
  captures were not rerun and their earlier failures remain open.
- Placement/control closure checks **89/89** against the pinned r06 62-SWF
  inventory; all **34** source placement errors remain. No raw rescan this turn.
- PROTECTED_FUNCTION_OK; integrity after reviewed manifest hashes, handoff and
  contracts **pass**.
- Cache **22/26**, target contexts **3/4**, build/fingerprint **FAIL**.

## Reproduce

With local FFDEC/GODOT/FLASH_APP paths and a fresh OUT directory:

```sh
python3 tools/probes/build_parent_goto_probe.py --fighter minren --conditional-frame 996 \
  --ffdec "$FFDEC" --output "$OUT/minren"
# Use --fighter sasuke --conditional-frame 1024 for the other source block.
python3 tools/probes/capture_native_player.py "$OUT/minren" "$OUT/minren/native.log" \
  --player-app "$FLASH_APP" --allow-window-activation --timeout 40
"$GODOT" --headless --path godot --script res://tests/parent_frame_state_reference.gd
"$GODOT" --headless --path godot --script res://tests/parent_state_checkpoint.gd
python3 tools/importer/audit_parent_forms.py \
  --requirements evidence/importer-loud-fail/r07/parent-form-requirements.json \
  --ffdec "$FFDEC" --output "$OUT/targets.json"
python3 tools/importer/audit_frame_calls.py --output "$OUT/frame-calls.json"
python3 tools/importer/audit_shipped_placements.py --output "$OUT/placements.json"
python3 tools/test_importer_roster.py --godot "$GODOT" --output "$OUT/roster"
python3 tools/build_online_manifest.py --check
```
