# Hitsugaya Up+I / Gaara overlap freeze

2026-09-11. User report: P1 Hitsugaya, P2 CPU Renji with Gaara, black stage
stays frozen when Up+I overlaps the summon. The screenshot is a symptom;
the exact user's input timing and deployed build are unknown.

## Cause and source gate

`scripts/main.json`, `frame_8/DoAction.as`, `stopMc` and `playMc` require
`mc.sw === false`. All 26 helper roots leave their own `sw` undefined (You's
frame 189 writes the fighters' `mc.sw`, not its own). HelperRuntime invented
`sw=false`, and SuperRuntime coerced missing values to false. This stopped
Gaara before it could release the fighter summon lock.

1. Retained `source-scripts.json` contains all Gaara scripts and Hitsugaya
   base Sprite 638 scripts in frames 561–570, including clip callbacks.
   Hitsugaya 562 sets `bs=1`, 563 calls `bsd`, and 570 calls `bsw`.
   Gaara 16 calls `bsd(pn,"XG_fzbs",true)`, 38 calls `bsw(pn)` **without**
   the helper argument. This source call was deliberately preserved.
2. Helper roots are retained `p1fz`/`p2fz` instances from main Sprite 1738;
   `yfgj` goes to frame 2, without defining `sw`. Nested placement/MOVE data
   remains in `godot/generated/helpers/woailuo/timeline.json`; this fix does
   not replace clips or change their clocks.
3. Gaara root advances through 38 to 85, then falls through to frame 1's
   explicit `stop()`. Hitsugaya 570's `bsw` can temporarily stop the fighter
   while the opponent summon has `bs=1`; Gaara 38 must remain reachable.
4. The invariant is the exact source strict comparison, including the
   distinction between an undefined field and a boolean false field.
5. `original.log.gz` and `events.jsonl.gz` retain a fresh native Flash run
   with the same `case.json` input. Build hashes and instrumentation are
   retained separately. Capture had 13,412 contiguous events and a done marker.

## Results and limits

- Before: P1 stays at frame 570 and Gaara at frame 5 through tick 300.
  A 31-offset native scan executed completely; offsets -5 through -2 froze.
  The original run releases pause at tick 57 and advances P1 to 571 at 58.
- After: `comparison.json` matches all 602 fighter observations, all 14
  compared fields, without tolerances. Both red and green rows are retained.
- `helper_pause_semantics.gd` fails before the fix and passes after it.
  It also verifies that an explicitly false `sw` still stops/resumes.
- `vs_com_helper_overlap.gd` passes three continuous attempts with the same
  fighters/helper, alternating positions, actual P1 key events and P2 CPU
  mode retained. P2's source summon label is forced to establish the overlap;
  this is a controlled integration test, not a replay of the user's AI tape.
- `kon_helper_smoke`, `helper_repeat_contact_smoke`, `vs_com_smoke` pass.
  PvP/training each match 602 original fighter states; the retained r13
  Vs Com replay reports `boundary_segment_observed_fields_match`.
- Separate helper difference: after Gaara returns to frame 1 at tick 105,
  the port clears its action to 0 while the original retains 1 (196 rows).
  No helper-wide parity claim is made. This is outside the freeze repair.
- The broad `combat_smoke.gd` fails at its pre-existing projectile-offset
  assertion on line 177; both HEAD and this repair reproduce that failure.
- Web build/browser keyboard validation and deployment were not performed.

Focused rerun:

```sh
python3 tools/test_helper_super_overlap.py --godot /path/to/godot
```

This entry point runs both native regressions and replays the retained input
against all original fighter observations. It rejects script errors and missing
success markers even when Godot exits zero. It does not launch Flash.

Individual checks:

```sh
godot --headless --path godot -s res://tests/helper_pause_semantics.gd
godot --headless --path godot -s res://tests/vs_com_helper_overlap.gd
mkdir -p /tmp/overlap-cases
cp evidence/combat/helper-super-overlap/case.json /tmp/overlap-cases/
python3 tools/test_move_cases.py --godot /path/to/godot \
  --cases /tmp/overlap-cases --output /tmp/fresh-overlap
python3 tools/probes/compare_mode_reference.py \
  evidence/combat/helper-super-overlap/events.jsonl.gz \
  /tmp/fresh-overlap/overlap-00.json --output /tmp/overlap-comparison.json
```
