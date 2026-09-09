# Guarded super regression fixes

The two findings in [the original audit](../super-guard-observation/README.md)
are fixed for the current Vs Com source-controlled path. The original fixture,
input trace and comparison values were not changed. No character-name branches,
geometry padding or consumed-hit suppression were added.

## Fixes and source evidence

1. `FighterRuntime._run_frame_actions` no longer re-evaluates a source-controlled
   super transition through the legacy contact cache. The compiled source
   `DefineSprite_764/frame_538/DoAction.as` exclusively decides whether opponent
   HP > 0 and action == -1. Blocking the starter now leaves HP=999 and never
   triggers the follow-up; a blocked contact cannot override the source branch.
2. The controller compiler recognizes placed clips that rename themselves into
   attack instances even when they have no movement/enterFrame callback. The
   existing child-instance runtime owns their independent playheads and source
   frame events. For Sprite 489, source frames 11/24 rename fensheng to
   sbsatm/sbs2atm, frame 30 flashes, and frame 37 stops on an empty display list.
   A stopped parent is not a stopped child. Natural rename scripts execute at
   the child's registered position before older receiver callbacks; goto scripts
   generated inside callbacks keep their existing deferred queue.

`original-geometry.log` is an additional native Flash observation immediately
before original getHitObj tests the sbs2 clip. At root observation tick 119,
attacker source frame 713 and defender frame 730, the attack child is already
at its empty frame 37 and hitTest is false. The native old implementation sampled
its root-derived local frame instead, retaining nonempty bounds and adding two
14-HP contacts. Empty Flash getBounds returns a degenerate sentinel rectangle;
we preserve its no-area/no-hit result, not its meaningless sentinel coordinate.
`geometry-instrumentation.diff` retains the read-only source query instrumentation.

The placement is source frame 683/depth 27 through 724; MOVE retains its child
playhead, removal/replacement does not. Source rename/stop/flash paths and hashes
are retained in generated player_controller/controller.json. Unknown child frame
behavior is rejected. These are generic compiler/runtime rules, not Naruto rules.

## Validation

- `godot/tests/super_guard_reference_smoke.gd` executes the actual Vs Com main
  loop and compares all 1800 source observations directly against the unchanged
  original.log. Final HP: Ichigo normal/up/ultimate 940/975/730; Naruto
  normal/up/ultimate 999/970/523. Frames, defender HP/hits/action, positions and
  pause agree in every retained snapshot, with no tolerance relaxation.
- Eight native checks passed with exit 0, success markers and no SCRIPT ERROR;
  see checks.json. They cover the new integration trace, projectile rename/removal,
  repeat contact, source settlement, player control, super frames and effect order.
- 29 Python checks passed, including new source clip lifetime, replacement and
  unsupported-script compiler checks. The focused compiler suite was rerun after
  adding the explicit source frame count.
- r13/r14/r15 keep matching their observed fields and boundary/random/clock tapes;
  compact results are in match-regressions.json. Large temporary reports/logs are
  under /tmp/bvn-super-guard-fix and are not added as redundant source artifacts.

Reproduce the primary regression with Godot 4.7.2:

```sh
godot --headless --path godot --script res://tests/super_guard_reference_smoke.gd
python3 -m unittest tools.tests.test_renamed_attack_clips tools.tests.test_source_inventory
```

This closes the two controlled guard findings, not full game parity. The original
AS2 coordinate trace has finite decimal precision. Binary geometry, complete
visual/audio equivalence, and the browser matrix are not established here.
