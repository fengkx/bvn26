# Retained run animation regression (2026-09-09)

The source player controller repeatedly returns to the run label while a direction
is held. The renderer previously derived the unnamed run child's local frame from
the parent frame minus placed_frame. With the source controller, the observed
parent is always frame 10, so the child was always frame 1. The older locomotion
smoke only advanced the parent sequentially; the newer controller smoke checked
position, facing and parent frames but never the rendered child frame.

## Source-first answers

1. `scripts/fighter/minren.json`, `DefineSprite_16/frame_1/DoAction.as`,
   `doAllAction`: cache left/right, write `_xscale` and `scale_X`, move X and
   `gotoAndPlay("走")`. The root `DefineSprite_764` has no DoAction at 10-12;
   frame 13 calls `gotoAndStop("站立"); play();`. The run child `DefineSprite_31`
   has 14 display frames and no retained DoAction. All seven bitmap poses are
   present in `godot/generated/fighters/minren/timeline.json` definitions.
2. Root frame 10 removes depth 27 and places Sprite 31. Frames 11-12 retain
   it without MOVE or replacement. Moving the parent playhead inside this
   placement span does not replace the child. Leaving the span and reentering
   creates a new child. The placement itself starts on child frame 1.
3. Held input repeats the run goto; released input reaches root frame 13 and
   its explicit stand goto. Neither a label boundary nor a parent goto is an
   instruction to reset a retained child's playhead.
4. Tests assert the 14-frame run cycle, restart after replacement, independent
   advancement under repeated parent goto, rendered X/Y orientation, and source
   input priority. Direction checks are made without incoming hits: onBeHit
   intentionally changes facing and is tested separately.
5. The original verified-input captures in `evidence/ai/input-binary-r13/` and
   `player-controller-and-binary-trace.md` cover the held-input controller path.
   They do not sample Sprite 31's visual playhead. This repair uses the retained
   SWF display lists and placement semantics; a new original/Web per-pose paired
   capture is still outstanding. Do not claim complete visual parity.

## Change

Source-driven fighters advance unnamed root children once per display tick using
retained placement identity (depth, character and authored placement frame).
Repeated gotos preserve age; removal/replacement clears it. Named projectiles keep
their existing source-controlled playheads. Driver shutdown clears the visual
clock so reentering a different mode cannot inherit it. Legacy sequential preview
continues to use its existing frame-derived clock.

## Verification and limits

`red.log` records the new assertion failing on the pre-fix code.
`checks.json` and the adjacent logs record seven passing native checks: player
controller, real-menu/keyboard player visuals, Vs Com, standing, player lifecycle,
pause and KO. The controller test includes 32 additional held/reversed ticks,
loop wrap and leaving/reentering the run placement. The real-menu check finishes
the queued Ready transition and places fighters apart to isolate locomotion.

The broad legacy `combat_smoke.gd` fails at line 177 (projectile hit lifetime).
`combat-existing-failure.log` reproduces the same failure in a temporary copy
with only this repair removed. Its expectation was not changed. This is an
existing failure, not a passing full combat suite.

Godot 4.7.2 exported `dist/web/index.html` and its PCK; the local browser booted
the new package. Full browser hold/release automation and original pixel parity
are not certified by these native tests. Native logs retain the existing macOS
certificate and headless audio exit warnings.

## Prevention

- Any controller, goto scheduling or renderer change must run both
  `player_controller_smoke.gd` and `player_visual_smoke.gd`, plus the affected
  lifecycle tests. A passing legacy sequential playback test is insufficient.
- Check input, logical facing, rendered transform, parent frame and visible child
  frame together. Position/HP/parent trace parity alone cannot catch frozen art.
- Keep source placement identity separate from parent frame and render-node
  rebuilding. A new placement resets state; a repeated goto need not.
- Rebuild the Web package after runtime changes. State the exact checked artifact
  and retain any preexisting failures instead of silently changing expectations.

## Shared-worktree verification

During this repair, other work continued changing projectile compilation and
runtime files. `verify.log` preserves their remaining manifest mismatches; this
repair updates only the hashes of its own modified files. `handoff.log` passes.
The two `*-current.log` checks rerun player/controller visuals after those writes
and pass. The Web PCK was exported earlier, before the later projectile edits.
The in-app browser showed the title; menu interaction then produced a black
canvas without console errors, so browser gameplay acceptance remains open.

The temporary Web `--script` harness did not emit a test completion marker in
release or debug exports. Those attempts are not counted as passed Web tests;
temporary harness files were removed. Native controller and main-scene keyboard
results above remain the verified behavioral evidence.
