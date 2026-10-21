# Aizen / 蓝染 base-form port

Base: `04244fae5bef827b8c67d8eb1efe0ae333a5eca7`, branch `feat/lanran`.
Coverage remains **partial**. Native Flash comparison is pending; Godot-only
execution must not be described as Flash parity. No merge or deployment.

## Source-first answers

1. Locked `game/fighter/lanran.swf`: 1,189,406 bytes, SHA-256
   `ae96976f5d912319862cfd5260bac2f06466368d32643aa373af7caa38cc89c7`.
   Sprite 640 contains 1,991 frames and 215 body scripts. `source-first.json`
   indexes all frames, including empty frames, original script paths and ordered
   display-list changes; `data/slices/lanran-base.timeline.json` retains geometry.
   Body frame 1 and receiver Sprite 2 match Renji's shared source exactly.
   Aizen uses controller Sprite 15 and receiver placements of Sprite 4; these
   are compiled from Aizen's own bundle, not copied from another character.
2. New PlaceObject, MOVE, removal, depth and matrices remain source-derived.
   Counter receiver 472 calls `checkHit` and enters 砍技12; frame 513 changes
   logical facing, display scale and X relative to the opponent. Its airborne
   counterpart is 1812/1853. These are container warps, not walking. Frame 165
   copies opponent X/Y for airborne ranged. Upper-super warps at 957, 967, 979,
   992, 1008, 1021, 1038, 1057 and 1075 change display scale, intentionally
   without writing logical `scale_X`. All placements use existing lifecycle rules.
3. Normals explicitly return at 233/252/280/314/358. Frame 291 moves X by 200;
   砍4 falls through to 砍41 at 293. The source controller at 265 permits super,
   ranged, normal and rush cancels. Super start/end pairs are 806/842, 918/955,
   1148/1166 and 1219/1259; their returns are 913/1131/1194/1436 (1194 goes to
   落). Guard callbacks are 1521 and 1801. Hurt calls are 1533/1546; ordinary
   hurt stops at 1538 and returns at 1542. Opening flags are 1618/1620/1675.
   No label end is invented as a standing transition.
4. Tests assert source receiver/super frames, exact counter facing writes,
   scope of controller container assignments and mask fill edges. HIT_RECEIVE
   A–D reuses the 35-fighter shared chain, assist-without-receiver audit, Aizen
   `gjl1`, source face labels and generic consumers. No damage, hitbox or
   comparison threshold is adjusted. Step E awaits fresh original captures.
5. Twelve fixtures are prepared for Adobe Flash Player Debugger 32.0.0.465
   through `tools/probes/capture_native_player.py`. They use AI off, current
   world, Aizen versus Ichigo and explicit Gaara/Kon helpers, with no helper
   input. The capture tool requires `--allow-window-activation` because Flash
   can raise its window despite `open -g`; the user's background-only constraint
   is awaiting clarification. Instrumented SWFs remain in scratch directories.

## Focused cases and scope

The 12 fixtures cover normals, normal-to-super cancellation, normal interruption,
outgoing normal chip, incoming guard/guard break, super chip, ultimate,
upper-super repeated warps, air ranged, air super, counter and upper attack.
Ten run for 240 ticks; upper-super and ultimate run for 280 so recovery fits.
Godot execution produces 5,944 fighter states in total, but no Flash match count
is claimed until the original captures have been compared.

The established comparator checks 14 fields: frame, x, y, xscale, action, hp,
ql, sw, touch, touchFloor, hits, paused, hstm and hurtSkling, plus complete
slot/tick alignment. Actual targets, hits and chip must be reported separately
from mere fixture execution. This does not establish pixel/audio equality,
exhaustive cancel boundaries or full AI/browser acceptance. The source references
missing `absmian`; it remains an original no-op. The catalog has no Aizen assist.

## Shared compiler corrections

- `combat_projectile_parser.py` now anchors `_parent` to its actual scope.
  `_parent._parent.scale_X` in Aizen controller callbacks is not a write to the
  projectile's immediate parent. Immediate-parent unguarded writes still fail.
- `build_combat_model.py` accepts literal logical-facing writes before the
  display-scale/position assignments, as in source frames 513/1853, as well as
  the already supported trailing writes. The runtime consumes existing fields.
- `extract_timeline_geometry.py` ignores line-style selection while compiling
  mask fills. Shape 33's authored rectangle is X=239..1039, Y=-215..1210 twips;
  its stroked bounds must not expand the mask. Flash ignores line styles in mask
  layers: [Adobe Flash CS3 User Guide](https://www.adobe.com/support/documentation/archived_content/en/flash/cs3/flash_cs3_help.pdf).

`compiler-impact.json` compares serialized base/current compiler outputs on
identical inputs for all 22 prior fighters; all are unchanged. No production
GDScript runtime file is changed. The full saved-roster replay matches **167/167 cases, 96,574 states** on all
14 compared fields (21 prior primary fighters; Renji appears only as opponent).
`checks.json` and `regressions.json` retain the actual execution results.

**Intentional Flash deviation retained:** PR #37 direct and queued interrupted
super-preparation recovery remains unchanged, including both call sites.
`_clear_interrupted_super_preparation`: 1,086 bytes, SHA-256
`9da62022432d7093b22b265b9e411db392ede4cbb1656fec21fe244f93f274ed`.
The gate prints `PROTECTED_FUNCTION_OK`. No new intentional gameplay deviation.

## Selection and screenshots

Local selection and `services/matchmaking/src/catalog.json` include `lanran`.
Original five-frame portraits, footer, natural opening and 53 StartSound frame
groups are imported. `screenshots/selection.png` and `screenshots/in-fight.png`
are real native Godot Compatibility renders. The latter follows natural opening
and a special input to source frame 865. They are visual inspection evidence,
not Flash pixel comparisons. The existing Web build copies character screenshot
PNGs into `dist/web/evidence/characters/` for future publication; no deployment
is performed here.

`lanran_rollback_smoke.gd` uses production rollback to exercise natural opening,
ultimate pause/checkpoint replay, delayed guard input and source next-round reset.
Full content acceptance and M3/M6 remain pending.

## Reproduction

Use pinned JPEXS 26.2.1 and Godot 4.7.2 with `docs/OPERATIONS.md`. Extract 蓝染,
export its SWF to scratch, extract Sprite 640, build combat and materialize
`lanran-base`. Compile player/AI controller and body, context, hit state, hurt
voice and sound segments. Reuse the bounded per-fighter intro block in
Orochimaru's README, then merge only Aizen's portraits/footer. Import resources
before running Godot checks and regenerate the online manifest afterward.

Build `tools/probes/build_ai_reference.py` with `--dynamic-move-case`, explicit
characters/helpers above, and 240 or 280 frames matching each fixture. Capture
with `tools/test_move_references.py --capture-only` and the native capture runner;
replay independently with `res://tests/move_case_reference.gd`, then compare using
`tools/probes/compare_mode_reference.py`. Capture-only placeholder traces must
never be counted as Godot results. `replay_saved_roster.py` uses `BVN_GODOT` and
`BVN_CHECK_DIR` from the repository root.
