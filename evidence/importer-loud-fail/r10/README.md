# Retained form callback runtime checkpoint, r10 (2026-10-23)

**Partial runtime implementation, not full parent/body replacement.** The shared
initial-frame feixue callback now has a compiled native consumer with live state
and method resolution, and the timer queue supports repeating registrations and
captured-function ownership. Full transformation entry is still rejected: caches
**19/26**, target contexts remain blocked, build/fingerprint **FAIL**. No allowlist,
pixel tolerance, new port, merge or deployment.

## Implemented and verified

`compile_ai_body.py --form-callbacks` compiles the actual initial BODY feixue and
loseHp functions for each source. Its existing expression/statement compiler
rejects unsupported operations; receiver initialization must be exactly one
`_this = this` binding. Default compilation and production generated fighter data
are unchanged. `build_form_callback_fixture.py` reproducibly generates the four
source-bound test programs; unit tests check each program and source metadata.
This option does not admit wankai, later callback reassignment or form entry.

`AiBodyContext` resolves callback reads through the current wrapper/body state.
Crucially, a saved feixue function must resolve its unqualified `loseHp` call against
the **current** body, rather than calling a permanently bound old method. Native
Flash confirms this: replacing loseHp with a diagnostic double-damage function
makes the saved old feixue subtract20, not10. The compiled callback now uses
`call_live_body_function` through fighter.source_body, with a hard assertion if
there is no compiled current method. This does not equate Flash MovieClip equality
with Godot node identity.

`AiSourceTimeouts.schedule(..., repeating=true)` retains the registration ID until
explicit cancellation and keeps the captured RefCounted function object alive.
Clearing one registration does not clear another. Removing a one-shot registration
before delivery also keeps its captured function alive for the duration of that
call. Cancellation releases ownership. Delivery remains independent of Godot
pause/time scale; source pause checks are inside the compiled callback.

Recorded queue snapshots are version2 and require an exact boolean repetition map.
Missing, wrongly typed or mismatched repetition records fail before mutating the
live queue; version1 remains readable as one-shot-only state. Tests cover repeated
ID delivery, independent IDs, self-cancellation, cancellation during notification,
function retention/release, restore atomicity and live paused delivery. Existing
one-shot and timeout-checkpoint tests pass.

**No match-level feiint/feiint2 owner is wired yet.** The queue capability is a
building block; calling the existing driver.stop() would still clear that driver's
queue. The future replacement transaction must place these registrations under
the correct root owner and must not use match teardown as replacement.

## Source-first and native evidence

Source callbacks are in the frame1 DoAction for daitu458, minren764, Sasuke603 and
yihu638. Each initial feixue checks root pause, then `_this.hp > _root.maxhp / 5`,
and calls loseHp(10); loseHp checks wudi before decrementing HP. There is no clamp
at the threshold:201 becomes191. Source metadata and hashes are recorded beside
the generated fixtures in godot/tests/fixtures/form_callbacks/sources.json.

1. Native probes preserve original nested definitions, placements/load actions
   and child frame scripts, with source/output/non-action hashes in native/*/build.json.
   Root-only instrumentation saves the actual source function and controls HP,
   wudi and pause only around synchronous callback delivery.
2. The root observer forces the same source parent goto as r07. The original
   replacement/load sequence runs; it is not replaced by a synthetic Flash body.
3. The probe's source goto exits to parent frame2. This still bypasses earlier
   transformation preparation, as explicitly established in r09. It is not a full
   transformation replay or a claim about all load/frame-script/enterFrame phases.
4. The regression checks native values, including the threshold crossing and
   dynamic method rebinding, not assumptions based on Godot object identities.
5. Four Flash Debugger32/Rosetta captures contain **56 total observations**. The
   Godot test compares the **48 callback-result observations, 48/48 across 4/4
   cases**, exactly. It excludes the native MovieClip equality and done markers;
   it does not fake equivalent identity checks in Godot.

The native root observer registers a diagnostic 1000ms interval before replacement.
Its wrapper delivers the saved original feixue with pause temporarily disabled,
then restores pause. After replacement it observes600→590→580 on two deliveries.
This proves the captured callable remains usable; it does not certify the complete
original feiint registration branches, timer drift/catch-up or main-game timing.
The method-rebinding diagnostic temporarily overrides loseHp at runtime and restores
it before interval delivery. The original definition tags remain unchanged.

The Godot fixture executes generated BODY code with the real AiBodyContext, replaces
the state and current compiled-body objects, then invokes the retained old callback.
It does not load/render the target form or perform a full profile replacement.
The scheduler keeps the old function alive after other references are dropped and
releases it when cancelled. See godot/form_callback_reference.log and
callback-observations.json.

## Still blocking full form replacement

All r09 guards remain unchanged, including the narrow Byakuya631/985 exception.
No cache has been refreshed to pretend that these components complete a form:

| Source | First unresolved entry | Required continuation |
| --- | --- | --- |
| daitu458 | 1307 wankai | wrapper HP/energy transfer, feiint, parent2/body1138 |
| minren764 | 1379:5 wrapper transfer | slot-specific feixue reassignment,1381 interval,1382 parent2/body1293 |
| Sasuke603 | 1228:5 wrapper transfer | slot-specific feixue reassignment,1230 interval,1232 parent2/body1019 |
| yihu638 | 1052 wankai | wrapper transfer,feiint,parent2/body1180 |
| Byakuya631 | 1110 wankai | full form transaction |
| rifagu638 | 1233 wankai | full form transaction |
| rukia533 | 1164 wankai | full form transaction |

The initial callback compiled here is **not** the later minren/Sasuke slot-specific
callback assignment. Those branches directly modify root.game.p1/p2.mc.hp and have
different ownership/conditions; they remain blocked. Also unresolved: atomic
visual/combat/controller asset replacement, doWanKai/initCtrl/key binding,
wrapper HP/energy restore, old pending frame action retirement, child callback
retire/re-register timing, shared root interval handles, and minren1293/1157 →
parent3/body1821. Target yihu1180/1036 wankai remains rejected.

The existing34 source placement errors, complete AS/clip-action audit and exact
pixel mismatches remain open.

## Acceptance

The final roster rerun after the live-method fix passed **227/227**, **130,334
states** against unchanged baselines. Final logs and acceptance-summary.json record
all checks:

- Python **398 run,396 passed,2 skipped**.
- GPU **7/7**, Blur **242/242 /37,280 alphas**, blend **38/38** under its existing contract.
- Standard Godot smoke **4/4**, additional references/rollback **8/9 strict passes**.
  battle_checkpoint prints success/exit0 but reports3 leaked instances/1 resource
  at shutdown; its strict result is failed and the raw log is retained.
- Callback native comparison **4/4,48/48**.
- PROTECTED_FUNCTION_OK; reviewed-hash integrity, handoff and contracts **pass**.
- Cache **19/26**, target contexts **2/4**, build/fingerprint **FAIL**.
- Placement closures **89/89**, source placement errors **34**.

Full merge acceptance is **FAIL**. Color comparisons remain3/5 exact and order2/4
exact, maximum difference1; no tolerance was added. Real shipped component/XG_rush
pixel captures were not rerun. Placement closures use the pinned r06 62-SWF
inventory; no fresh raw SWF scan is claimed.

## Reproduce

```sh
python3 tools/probes/build_parent_goto_probe.py --fighter daitu --body-callback \
  --ffdec "$FFDEC" --output "$OUT/daitu"
python3 tools/probes/capture_native_player.py "$OUT/daitu" "$OUT/daitu/native.log" \
  --player-app "$FLASH_APP" --allow-window-activation --timeout 40
# Repeat sequentially for minren, sasuke and yihu.
python3 tools/probes/build_form_callback_fixture.py \
  --output godot/tests/fixtures/form_callbacks
"$GODOT" --headless --path godot --script res://tests/form_callback_reference.gd
"$GODOT" --headless --path godot --script res://tests/repeating_timeouts_smoke.gd
"$GODOT" --headless --path godot --script res://tests/ai_timeouts_smoke.gd
"$GODOT" --headless --path godot --script res://tests/timeout_checkpoint_smoke.gd
python3 -m unittest discover -s tools/tests
python3 tools/test_importer_roster.py --godot "$GODOT" --output "$OUT/roster"
python3 tools/importer/audit_frame_calls.py --output "$OUT/frame-calls.json"
python3 tools/importer/audit_shipped_placements.py --output "$OUT/placements.json"
python3 tools/build_online_manifest.py --check
python3 tools/verify.py
python3 tools/check_handoff.py
python3 tools/validate_contracts.py
```
