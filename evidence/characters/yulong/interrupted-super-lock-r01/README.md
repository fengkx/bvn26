# Interrupted super lock

This case confirms and repairs the same class of interrupted-super lock as the reported stuck fight. It does not claim the full user session was replayed: the controlled Main case reproduces the lock with a fixed tape. The original Flash build with that tape also remains stuck, so this is an intentional correction of source behavior rather than a one-to-one parity claim.

## Controlled case

The fixture runs the production `Main` scene in mode 3 on 现世 with Yulong at x=450 and Sasuke at x=500, both with 300 energy. P1 holds down+I over fight ticks `[10,13)` to start Yulong's super. P2 holds down+N5 over `[82,85)` to attempt Sasuke's super. The selected support assets are Gaar for P1 and You for P2. The fixture explicitly binds `fighters.p1=yulong` and `fighters.p2=sasuke`; its legacy `fighter`/`slot` metadata describes the target character and is not the slot/resource binding.

The original Flash capture is run `yulong-sasuke-bs-window-r02`. `native/original.log` is the run-scoped raw capture; `native/events.jsonl`, `native/summary.json`, and `native/build.json` are the collected trace and provenance. The runner reached its unique `done` marker after 300 fight ticks with 4,638 events and no events after `done`. The runtime Yulong SWF hash was `52ffd529c2ef8028d1367ff31ccbece36f44624653fb5134f95b7395cec6561f`, matching the build output manifest. Input readback observed P1 down+I and P2 down+N5; see `native/summary.json`.

The original and pre-fix Main trace both stall at Yulong frame 887 while Sasuke is held at hurt frame 867 with `bs=1` and `hstm=59`. Fight tick 224 is the normal start of Yulong's black-stage pause; at tick 287, when the expected end frame 887 runs, the source `bsw()` early return fails to restore the stage, and it remains stuck through tick 300. The fixture is a mechanism reproduction, not the exact input tape from the user's browser log.

After the fix, the same Main fixtures 82 and 83 both leave the pause and continue beyond frame 887 by tick 300; Sasuke's source-state `bs` is zero. The nearby timing control, case 84, still completes its independent super and reaches Yulong frame 930 with the pause cleared. Full 602 actor-state rows per case are in `godot/fixed-82.json`, `godot/fixed-83.json`, and `godot/control-84.json`; pre-fix case inputs are retained alongside them.

## Source path and five checks

1. **Frame scripts:** Sasuke's `scripts/fighter/Sasuke.json`, `DefineSprite_603/frame_641/DoAction.as`, writes `bs=1` before the super's `cbsd` at frame 643. The shared hit path can replace this startup action with hurt before the `bsd` pause begins. Sasuke's source frame 1 declares `bs=0`, but that initializer may not run before another super pauses the hurt timeline. Yulong's super enters `bsd` at frame 824 and reaches `cbsw` at frame 887.
2. **Placement and movement:** No hitbox or placement change is involved. The Main scene's two fighter instances and their source timelines stay in their selected slots; the issue is the lifetime of the source `bs` state across a hit-driven action change.
3. **How the action exits:** A successful non-guard hit changes the defender to its sourced hurt action. It does not call the interrupted super's source frame-1 initializer. Later, `scripts/main.json`, `frame_8/DoAction.as`, `bsw()` clears the ending caster's `bs`, then returns early when the opponent still has `bs==1`; the normal stage-resume and root `zhanting=false` statements are below that return.
4. **Source invariant:** While an actual super pause or user pause is active, the shared pause must remain owned by that pause path. A merely prepared super must keep `bs=1` until it is actually interrupted; a guard or no-hit path is not cancellation. The original `bsw()` guard preserves a real opponent super. The fix clears only a prepared `bs=1` on a real, non-guard hit when shared super pause and user pause are inactive and `gameRunning()` is true.
5. **Same-input original comparison:** The run-scoped Flash trace with the exact controlled tape reaches the same held frames and `bs` state as the pre-fix Main run. This documents an original source deadlock and the deliberate portability fix; it is not a claim that the repaired runtime matches the original deadlock.

## Change and checks

`godot/fighter_runtime.gd` clears both the runtime `bs` property and compiled source-state `bs` at the confirmed interruption point. It does not force a resume or alter the shared pause flags. When the shared black-stage or user pause is active, it leaves `bs` untouched so those flows keep their normal ownership.

`godot/tests/interrupted_super_lock_smoke.gd` checks interrupted preparation for Sasuke and Naruto, retained preparation without a hit, guard behavior, a real `bsd` pause blocking another super's `cbsw`, and a user pause. It prints `INTERRUPTED_SUPER_LOCK_SMOKE_OK`. Also passed `ai_super_frames_smoke.gd`, `sasuke_you_native.gd`, helper pause/super overlap (including a 602-state Main trace), and `tools/check_handoff.py`.

Godot 4.7.2 headless emits the environment's CoreFoundation certificate warning and may report missing `user://logs`; these did not affect exit status or the explicit pass markers. `tools/verify.py` reports the updated `fighter_runtime.gd` hash plus a separate concurrent `timeline_preview.gd` hash change; that unrelated file is not part of this task's diff and must be reviewed by its owner before the manifest is updated.
