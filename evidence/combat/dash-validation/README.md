# Dash contact boundary regression (2026-09-09)

The late Naruto Up+I scenario reproduced a real shared collision defect. At
fight tick 103 the original entered a second hit reaction; at 104 it settled
another 40 HP (920 remaining). The port stayed at 960. The unchanged original
trace now matches after correcting the common MovieClip hit-test boundary rule.
No hitbox enlargement, target tracking, character branch, or invulnerability
timer was added.

## Source-first evidence

- `scripts/fighter/yihu.json::DefineSprite_2/frame_1/DoAction.as` calls
  `this.hitTest(_loc4_)` for the current attack object. The common chain has
  gameRunning/canhit gates and no consumed-attack cache. The same source BODY
  pattern selects fighter, helper and stage candidates in order.
- Both base bodies enter ordinary `瞬步` at root 20, remove `bdmn`, create
  the movement controller at 21, move on its next-frame callbacks 22–31,
  remove it at 32, and explicitly goto/play standing at 35. Naruto restores
  `bdmn` at 30; Ichigo at 32. No generic full-dash immunity is authored.
  The other frames in 20–35 have no root action except frame 21's rush effect
  (and Ichigo frame 20's jump write). Source clips are new placements, not
  retained receiver instances; the receiver callback begins next tick.
- Gaara's root-frame audit is in [helper timing](../helper-timing.md).
  `scripts/fighter/fz/woailuo.json::frame_44/PlaceObject2_48_2/CLIPACTIONRECORD onClipEvent(load).as`
  samples opponent X once. Sprite 48 is retained, stops at child 33 and does
  not continually retarget a later second dash. Root wraps after 85.
- Naruto's retained Sprite 489 and rename/stop scripts are documented in
  [super guard evidence](../super-guard-fix/README.md). The parent's labels
  do not reset the child. This change leaves all those source frames intact.
- [Actual collision call](super-geometry/events.jsonl): the original receiver
  right edge and `sbsatm` left edge both equal **462.75**, yet hitTest is true
  (callback observed with fight counter 102, next root snapshot 103).
- [Independent Flash rectangles](edges/events.jsonl): edge and corner contact
  return true, including negative offsets; a 0.05-pixel gap (one twip) returns
  false. These are native Flash observations, not guessed tolerances.

Godot Rect2.intersects defaults to excluding borders. `SourceHitTest` explicitly
includes them and rejects empty clips. All current fighter, helper, stage and
AI MovieClip hit-test sites use this shared rule. Geometry itself is unchanged.

## Reproduction and verification

The isolated original copies retain source hashes, instrumentation diffs,
validated key reads, event sequences, RNG and clock tapes in each directory.
Original `game/` and `scripts/` are unchanged. Adobe Flash Player Debugger is
used only as an analysis oracle, never in production.

| Capture | Scenario | Compared result after fix |
| --- | --- | --- |
| `super-r03` | Rush enters immediately before Up+I pause | 241 snapshots, zero combat-field differences |
| `super-double` | Rush starts after Up+I pause; CPU continues trying | 241 snapshots, zero differences; second 40 HP restored |
| `helper-double` | Rush starts at helper 38; repeated ordinary rushes | 241 snapshots, zero combat-field differences; three rush entries and no damage, also in original |

`super-double/native-before.json` and `before.json` preserve the red regression
(292 differing field observations). `native.json` and `comparison.json` retain
post-fix observations. The comparator checks both fighter frames, HP/hits,
canhit, dashing/dashF, MP, X, pause, helper child and receiver presence exactly.

Helper activation still differs at one root-observer snapshot (original frame
2 vs port 1 at tick 16); subsequent helper frames and contacts agree. This is
reported separately, not silently counted as full timeline parity. Sand AABB
float low bits and renamed child alias lookup are excluded and explicitly
listed in comparison output. Full geometry/presentation parity is not claimed.

Earlier `helper-dashx-r01`, `helper-rush-r02`, `super-rush-r02` are retained
exploration, not calibrated full-state acceptance. The first explores two
100-MP dashX activations; the latter two did not normalize initial idle frames.
`helper-rush-r02` confirms sand generated at the completed rush landing X=450
and eight 30-HP settlements. The ordinary continuous-rush fixture does not
pretend to be two physical key presses. Player-controller regression separately
checks early repeated dash presses do not restart the controller, two completed
rushes move 400 pixels, and both restore Naruto's receiver at frame 30.

Run:

```sh
python3 tools/test_dash_reference.py --godot /path/to/godot
/path/to/godot --headless --path godot -s res://tests/source_hit_test_smoke.gd
/path/to/godot --headless --path godot -s res://tests/player_controller_smoke.gd
```

Rebuild an original case with `tools/probes/build_ai_reference.py --dash-probe
super-rush --dash-trigger-frame 681 --dash-duration 36 --frames 240` plus its
required ffdec/output/run-id arguments, run that isolated SWF in native Flash,
and retain the trace using `collect_ai_reference.py`. `dash_reference.gd`
accepts scenario, output JSON, trigger frame and duration after `--`.

## Preventing recurrence

The reported dash made an existing boundary error visible; checking only attack
centers or final HP misses it. Retain source collision-call geometry and a red
main-loop trace, then test edge/corner/one-twip separation through the shared
operation. Keep run direction/retained-animation checks alongside controller
changes. Normalize initial source frames in comparisons: boot timing otherwise
changes whether CPU predicates run just before a freeze. Record native checks,
original observed-field parity and Web export as distinct evidence.

Seven focused native checks pass, including run visuals, controller, helper
repeat contact, AI helper/super and the six-case original super-guard replay.
The three new main-loop replays pass (723 snapshots); all 67 Python tests pass.
Native main-loop test shutdown still reports existing ObjectDB/resource leaks;
these are not represented as clean lifecycle acceptance. Full browser gameplay
and all-character/all-timing parity remain pending.

Final checks: r13/r14/r15 retained full-match observed-field replays still match.
Web export completed successfully; browser gameplay was not revalidated.
[Check record](checks.json) retains markers, hashes and limitations. The focused
validation/fix work from 14:26 to 14:51 took approximately 25 minutes; earlier
exploratory work is not included in this measured interval.
