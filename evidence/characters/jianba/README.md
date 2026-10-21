# Kenpachi / 更木剑八 base-form port

Base: `078ebdd0d2c8555a87a577ca11920ec8a75c85e7`, branch `feat/jianba`.
Coverage remains **partial**. No merge or deployment.

## Source-first answers

1. Locked `game/fighter/jianba.swf`: 569,987 bytes, SHA-256
   `d1e4851ce8274fffe8dfdc6e8bc8b9407a7ffff690512693fc5866bfe49cc609`.
   Sprite 514 contains 1,249 frames and 157 body scripts. `source-first.json`
   indexes every frame, including empty frames, original script paths and
   display-list changes. `data/slices/jianba-base.timeline.json` retains geometry.
   Receiver Sprite 2, controller Sprite 13 and body frame 1 match the existing
   shared Renji source exactly. Both player and AI code are compiled from
   Kenpachi's own locked bundle.
2. New PlaceObject, MOVE, removal, depth and matrices remain source-derived.
   Controller placements at 207/233 permit normal continuation and cancellation;
   316/348 permit upper-attack follow-ups. Frame 304 copies opponent Y and
   positions X at +/-100 based on display facing; upper-super frame 615 uses
   +/-50 X and opponent Y+50. These are container warps, not walking.
   Ultimate motion callbacks are placed at 754/759/780/785. New callbacks start
   on the following timeline tick and do not inherit old instance state.
3. Normals return explicitly at 196/217/248. Jump ranged falls through at 152;
   upper attack falls through at 306. Super start/end pairs are 535/554,
   595/611 and 708/752; ordinary/upper supers return at 587/700 (700 goes to 落).
   Ultimate frame 767 first returns if opponent HP <= 0, then enters 超必杀1
   if opponent action is -1, otherwise tests cbs0atm against the actual bdmn.
   A miss continues to the standing return at 776; continuation returns at 966.
   Guard callback is 1036; hurt calls are 1048/1061, hurt stops at 1053 and
   returns at 1057. Opening flags are 1133/1135/1177. No label end becomes an
   invented standing transition.
4. Tests assert shared-source equality, exact receiver/super frames, authored
   fallthroughs, complete conditional admission and helper packets. HIT_RECEIVE
   A–D reuses the shared chain, Kenpachi gjl1, source face labels 剑八1/剑八2,
   actual matrices and generic consumers. No threshold, damage or hitbox is
   enlarged. Step E is recorded separately in the executed comparisons.
5. Fresh fixed-input original captures use Adobe Flash Player Debugger
   32.0.0.465 via `capture_native_player.py --allow-window-activation`.
   Capture is non-interactive, with no manual clicks. Flash may briefly raise
   its window. Instrumented copies stay in scratch; input tapes, build hashes,
   instrumentation diffs and original/native traces accompany each comparison.

## Assist

The catalog's `fzurl: jianba.swf` is Kenpachi's separate assist; `fz: 夜一`
identifies the recommended companion and does not rename that assist. This port
imports `game/fighter/fz/jianba.swf`, its root timeline, original packet and
sound assets. The root has 104 frames, starts at frame 2, starts/ends helper
super pause at 16/61 and emits exit presentation at 104 before wrapping to the
stopped frame 1. Its atm1 packet is damage 200, strength 15, X impulse 15,
Y impulse 0, hitstun 0 and 击飞. Sprite 62 is placed as atm1 at frames 71–77. Its older receiver function
definitions are never called by this helper: no receiver enterFrame callback
is present. Yoruichi is not imported by this port.

## Intentional difference from Flash

PR #37 direct and queued interrupted-super preparation recovery is retained
unchanged. Flash may deadlock in those preparation-interruption sequences;
Godot intentionally recovers. `_clear_interrupted_super_preparation` remains
1,086 bytes, SHA-256
`9da62022432d7093b22b265b9e411db392ede4cbb1656fec21fe244f93f274ed`.
The protected-function gate must print `PROTECTED_FUNCTION_OK`.

## Selection and screenshots

Local selection and the matchmaking catalog include fighter and assist `jianba`.
Original five-frame portraits, footer and natural opening are imported.
`screenshots/selection.png` and `screenshots/in-fight.png` are real native Godot
Compatibility renders. The fight capture follows natural opening and special
input to source frame 560. The Web build already copies these evidence PNGs
for future publication; no deployment is performed. These images establish
rendered content, not Flash pixel equality.

Full audiovisual/browser/AI and exhaustive cancel/spacing boundary acceptance
remain pending. Saved original comparisons use the established 14 exact fields:
frame, x, y, xscale, action, hp, ql, sw, touch, touchFloor, hits, paused, hstm and
hurtSkling, with complete tick/slot alignment. Target reach and actual damage
are reported independently from execution success. The rollback smoke exercises
production rollback and delayed input locally, not a live Internet match.

## Executed comparisons

Twelve targeted fighter fixtures match all **7,224 actor states**; the separate
assist fixture matches another **602 actor states**. Total: **13/13 cases,
7,826/7,826 states on 14 exact fields**. Each fixture records ticks 0–300 for
both actors. This is twelve fighter tests plus one required assist check.
All actor targets are reached. Native helper lifecycle snapshots are retained
separately and are not claimed as original-helper internal-state parity.

Normal guard chips 4 HP with zero hits. The `super-guard` fixture **breaks guard**:
120 HP and one hit, not 12 HP chip. Incoming normal guard followed by Ichigo
low attack reaches 916 HP and one hit. The normal interruption reaches 960 HP.
Normal-to-super cancel goes from source frame 233 to 532 at tick 52. Air ranged
has two hits / 150 HP; upper super has thirteen hits / 280 HP. The ultimate
enters continuation at tick 87 and reaches 28 hits / 490 HP by tick 300; its
attacker is still at source frame 952 then. These counts describe the recorded
horizon, not a completed ultimate recovery. The separate rollback smoke runs
380 ticks after input and checks standing recovery, checkpoint replay, late
remote guard inputs and source next-round reset.

`compile_ai_context.py` recognizes the entire live-target/state/contact source
block, requiring identical destinations on both branches. `ai_cpu_driver.gd`
interprets the compiled alternatives in order and short-circuits before the
collision query. No character-specific runtime condition is added. The focused
conditional smoke checks dead target, already-hurt target, actual contact,
miss and absent geometry. Context recompilation on identical inputs is unchanged
for all **23 prior fighters**; see `compiler-impact.json`. Full saved-roster
execution is reported in `regressions.json` and `checks.json`.

## Reproduction

Use JPEXS 26.2.1 and Godot 4.7.2 with `docs/OPERATIONS.md`. Extract 剑八,
export its SWF to scratch, extract Sprite 514, build combat and materialize
`jianba-base`. Compile player/AI controller and body, context, hit state, hurt
voice and sound segments. Use the bounded per-fighter intro block documented
in Orochimaru's README and merge only 剑八 portraits/footer. Extract the assist
as a root timeline and build with `--helper-id 剑八`. Regenerate the online
manifest after resource import.

Build `build_ai_reference.py --dynamic-move-case` with 300 frames and explicit
characters 剑八/一护 and helpers 我爱罗/魂. For the separate assist fixture use
剑八/魂 helpers. Capture with `test_move_references.py --capture-only` and
`capture_native_player.py --allow-window-activation`; then execute
`res://tests/move_case_reference.gd` independently and compare with
`compare_mode_reference.py`. Capture-only placeholder traces are never used as
Godot evidence. Build-time `built_not_run` records remain immutable; adjacent
capture metadata and `comparisons.json` establish subsequent actual execution.

Run `python3 evidence/characters/jianba/check_protected.py` for the protected
function gate. Run `replay_saved_roster.py` with `BVN_GODOT` and `BVN_CHECK_DIR`
from the repository root. The corpus includes all prior saved role fixtures,
including Aizen; Renji appears as an opponent rather than a primary fighter.

Final saved-roster replay: **179/179 cases, 102,518/102,518 states**, all matched
on 14 fields (568.712 seconds). Five focused Godot checks, 333 Python
passes plus two skips, 31 matchmaking tests, seven online-manifest tests,
contracts, locked-input verification and handoff checks pass.
