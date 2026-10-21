# Gaara / 我爱罗 base-form port

Base: `aaec012d5be3f7d3adeebc3bb54721c033719609`, branch `feat/gaara`.
Coverage remains **partial**. No merge or deployment.

## Source-first answers

1. Locked `game/fighter/gaara.swf`: 1,119,487 bytes, SHA-256
   `441340a3e05589646d82ed570c79e32f3d97d639bc153c7da385d06a522d3bd3`.
   Sprite 673 has 1,343 frames and 136 body scripts. `source-first.json` indexes
   every frame, including empty scripts and display-list changes;
   `data/slices/gaara-base.timeline.json` retains matrices and geometry.
   Receiver Sprite 2, controller Sprite 20 and body frame 1 match Renji's shared
   source exactly. Player and AI controllers are compiled from Gaara's bundle.
2. PlaceObject/MOVE/removal and instance generations remain source-derived.
   Sand `zzz1` (Sprite 197) is placed at 304; `followMc` runs at 304–307.
   `bs1atm` (Sprite 349) is placed at 501 and follows the opponent on that frame.
   These calls copy X only, using display facing and a strict front-side guard;
   they do not move the fighter container or copy opponent height. Sprite 349
   renames itself `zzz1` at child frame 17, stops at 34, has label `boom` at 35,
   renames itself `bsatm` at 37 and stops at 52. Root 535 explicitly jumps the
   current `zzz1` instance to `boom`. New placements retain the existing next-tick
   callback semantics and do not inherit prior instance state.
3. Normal returns are 188/212/244. Root 200 permits ultimate/normal/directional
   attack cancels, and 230 permits supers/ranged/rush. Ranged `招1` falls through
   into `招11`. Super start/end pairs are 486/498, 611/626 and 730/795, with
   source face labels 我爱罗1/我爱罗2. At 519, a living hurt opponent is hidden;
   otherwise Gaara jumps to 必杀1. Frame 539 reveals the opponent. Upper super
   hides a living hurt opponent at 654, skips to standing if still visible at
   673, and reveals at 679. Ultimate hides at 857, branches to 超必杀1 if visible
   at 865, otherwise falls through at 942. It copies only the opponent's X
   at 867, reveals at 948 and returns at
   994. Guard/hurt callbacks are 1081/1093/1106; ordinary hurt stops at 1098
   and returns at 1102. Opening state writes are 1177/1179/1265.
4. Tests lock exact shared source, receiver and super frames, complete conditional
   branches, source child label resolution, X-only opponent warp, and follow
   flags. Runtime checks cover the visibility else branch, live/hurt conditions,
   strict front guard, display-facing versus logical-facing, and independent Y.
   HIT_RECEIVE A–D reuses the existing shared chain and source `gjl1` fields;
   no damage, collision geometry or comparison tolerance is guessed or enlarged.
5. Twelve fixed-input fixtures are captured with Adobe Flash Player Debugger
   32.0.0.465 using `capture_native_player.py --allow-window-activation`, without
   manual clicks. Instrumented SWFs remain in scratch. Source traces, tapes,
   hashes and instrumentation diffs are committed alongside independent Godot
   comparisons. Build-time `built_not_run` metadata stays immutable; adjacent
   capture records and `comparisons.json` establish actual execution.

## Shared compilation and runtime

`compile_ai_context.py` admits complete living/hurt visibility blocks (including
else), visible-target jumps and single-axis opponent-container assignments.
It validates the shared `followMc` function body before emitting explicit flags.
Child goto destinations are resolved from locked SWF labels and the current
placement's source names, including nested rename scripts. The runtime resolves
that live instance before applying the child goto and queues its frame script.
No Gaara-specific condition is added to runtime code. Recompilation on identical
inputs preserves all 24 prior fighter contexts; see `compiler-impact.json`.

The source compiler initially rejected frame 519 instead of silently dropping
its branch. The first Godot trial overlapped initial resource import and is not
counted as passed. Final evidence uses completed imports and independent replay.

## Assist and selection

The separate `game/fighter/fz/woailuo.swf` helper was already compiled and listed
in both local and online catalogs. Its assets, behavior and registry entry are
unchanged. The new fighter is `gaara`, with its own source portrait and opening.
Both `available.json` and `services/matchmaking/src/catalog.json` expose it.
The existing Gaara footer is shared with the helper and retains its source name.

`screenshots/selection.png` and `screenshots/in-fight.png` are real native Godot
Compatibility renders. The fight capture follows natural opening and special
input to source frame 537. The existing Web build copies character evidence
PNGs for future publication; this task does not deploy. Screenshots establish
rendered content, not Flash pixel equality.

## Intentional difference from Flash

PR #37 direct and queued interrupted-super preparation recovery is retained
unchanged. Flash may deadlock in those sequences; Godot intentionally recovers.
`_clear_interrupted_super_preparation` remains 1,086 bytes, SHA-256
`9da62022432d7093b22b265b9e411db392ede4cbb1656fec21fe244f93f274ed`.
The gate prints `PROTECTED_FUNCTION_OK`. No new intentional gameplay deviation.

## Validation scope and reproduction

The fixtures cover combo, normal-to-super cancel, interruption, outgoing normal
and super guard, incoming guard/break, airborne ranged, ranged, repeated sand,
upper attack, upper super and ultimate. Each records ticks 0–360 for both actors.
The comparator checks 14 exact fields: frame, x, y, xscale, action, hp, ql, sw,
touch, touchFloor, hits, paused, hstm and hurtSkling, with complete slot/tick
alignment. Reach, actual damage and hit counts are reported separately.
Full audiovisual/browser/AI and exhaustive boundary acceptance remain pending.

The rollback smoke uses production rollback locally, with natural opening,
ultimate pause checkpoint/replay, late remote guard inputs and source next-round
reset. It is not a live Internet matchmaking test. Shared-mode replay covers
PvP and training timer behavior. Whole-roster results are in `regressions.json`.

Use pinned JPEXS 26.2.1 and Godot 4.7.2 with `docs/OPERATIONS.md`: extract 我爱罗,
export to scratch, extract Sprite 673, build combat and materialize gaara-base;
compile controller/body/context/hit-state/hurt-voice and sound segments. The
bounded intro generation follows the preceding ports. Build a dynamic move
probe for 360 frames, Gaara/Ichigo and existing Gaara/Kon helpers; capture with
`test_move_references.py --capture-only --allow-window-activation`. Replay each
fixture independently through `move_case_reference.gd`, then compare with
`compare_mode_reference.py`. Capture-only placeholder native files are excluded.
Run `check_protected.py` and `replay_saved_roster.py` with `BVN_GODOT` and
`BVN_CHECK_DIR`; the saved corpus includes Kenpachi and all preceding ports.

## Executed focused results

**12/12 cases, 8,664/8,664 actor states, 14 exact fields**, zero differences.
All targets are reached and both actors recover before the 360-tick horizon.
Normal/super guard chips **3/4 HP with zero hits**. Incoming guard followed by
Ichigo's low attack reaches **916 HP / one hit**, and interruption reaches
**960 HP / one hit**. Ultimate deals **540 damage / 23 hits** and upper super
**350 damage / 7 hits**. Normal-to-super cancel reaches the super and deals
530 total damage across 9 hits. Repeated sand deals 90 damage on each cast;
its maximum simultaneous combo count is one because the opponent recovers
between casts. These are source observations, not inferred attack-table totals.

Five final Godot checks pass (conditional/follow semantics, rollback, protected
recovery, input controller and visual controller). Python: 339 tests run,
337 pass and two skips; the 14 focused import/selection tests also pass after
final review. Matchmaking typecheck and 31 tests pass (the sandbox-restricted
Wrangler local-server test passes separately). Seven online-manifest tests,
six contract schemas/examples, locked-input integrity and handoff checks pass.

Final saved-roster replay: **192/192 cases, 110,344/110,344 actor states**
match all 14 fields (602.505 seconds). The copied runner
initially retained the predecessor aggregate count; the complete 192-case report
is independently verified against the exact new total, and the reproduction
script asserts 110,344. No fixture, baseline or comparison tolerance changed.
