# Neji / 宁次 (neji), 2026-10-13

Imported from `b15aeec4` in the isolated `feat/neji` worktree. Source Sprite 535
has 1,358 frames and 153 scripts. The existing compiler imports movement, four
normals, directional/air attacks, the three-part down-J chain, three supers and
the conditional ultimate continuation, guard/hurt/recovery, summon, opening and
results. Original portraits/footer and local/online selection are wired. Default
Hinata (`zhitian`) remains out of scope; existing selectable assists are retained.

## SOURCE_FIRST five questions

1. Every Sprite 535 script is indexed by original path in
   `data/slices/neji-base.json`; all frames, including empty frames, are in
   `data/slices/neji-base.timeline.json`. Original text remains in
   `scripts/fighter/neji.json`. Controller Sprite 20, receiver Sprite 2 and the
   frame-1 body are byte-identical to Renji's audited corresponding scripts.
2. New placements, MOVE, depth and removal remain in the extracted timeline.
   `frame_391/PlaceObject2_250_28` places `zh1atm`; its callback starts the next
   tick and adds 20 **local** X pixels while `_root.zhanting == false`, through
   frame 404. It is not fighter movement. Mirroring follows its parent transform.
   Frame 478 copies the opponent's Y and X minus 30 when facing right, plus 30
   otherwise; it preserves facing. These compile as `projectiles` and
   `body_warps`, without character-specific runtime code.
3. Source exits include normals 188/212/236/261, down-J stages 285/324/346,
   projectile 412, teleport 495, supers 553/635, hurt 1117 and recovery 1182.
   Frame 786 enters `超必杀1` only when the opponent is alive and action == -1;
   otherwise frame 797 returns to standing. The continuation returns at 1005.
   Frame 1113 stops until the shared hurt callback resumes playback. Source
   super pause pairs are 508/521, 588/601 and 652/689. Ultimate approach at 691
   stops advancing past the opponent-relative 10-pixel threshold; subsequent
   displacement clips preserve their source speed factors and placement clocks.
4. Three focused source checks lock the shared receiver/controller/body,
   projectile placement lifetime, facing-dependent warp, super events and cancel
   placement. Existing source predicates and `gjl1` implement interrupt/cancel,
   chip damage, guard break and reaction labels. No boxes or thresholds are tuned.
5. Fixed-input fixtures in `cases/` cover combo, interruption, giving/receiving
   guard, projectile in both facings, teleport and three supers including the
   long hit/guard ultimate, plus projectile pause/resume. Original-player and Godot results are recorded in
   `checks.json`; source extraction alone is not parity evidence.

## Validation and limits

All 12 focused original-player comparisons match all 1,202 fighter states each
(14,424 total), across the 14 compared fields, on the final runtime/data. The
moving-hitbox pause case exposed and fixed a missing source distinction:
`collision_queries=[]` must bypass the legacy contact cache so an unconditional
movement clip keeps moving through contact. See `projectile-pause-fix.json` for
the red trace, original callback geometry and successful corrected comparison.
No hitbox, damage or timing threshold was tuned.

Post-rebase review against master `fecb7630`: Python ran **279 tests, zero
failures/errors, two skipped** on this macOS worktree (master: 276, zero
failures/errors, two skipped). The reviewer's earlier environment reported
274 run, one pre-existing `test_sasuke_compilers` setup error and three skipped:
the test requests lowercase `sasuke-base.timeline.json`, while Git tracks
`Sasuke-base.timeline.json`; this case-insensitive filesystem resolves it.
The original unqualified test-count/pass claim is superseded by these results.

All 14 selected Godot smokes pass, including the three character rollback/reset
checks and the complete 14-fighter roster rollback (eight checkpoints each).
Five additional known smokes fail identically on master and this branch:
`ai_colors`, `ai_context`, `ai_host`, `title_menu_source`, `ai_hit_gate`.
`ai_host` prints an OK marker but also SCRIPT ERROR and is counted as failed.
Shared PvP/training-timer references match 602 actor states each. Online-manifest
checks (7), matchmaking tests/typecheck (31), contracts, integrity and handoff pass.

The shared-change regression rerun covers 53 saved Flash cases / 37,066 fighter
states: 51 cases match exactly. Sakura's neutral ground ranged case (492 different
states, first tick 54) and Kakashi's ground ranged case (262, first tick 33) retain
historical Flash differences; both rerun to **identical native states on master**.
No new regression was found in the tested scope. The compiler-rule delta was
also applied to Kakashi's pure-motion air callback in an isolated in-memory test:
its 602 states still match Flash; shipped Kakashi data was not changed.
Full per-character counts, source/fixture/native hashes, first differences,
master comparisons and limitations are in [pre-merge review](premerge-review.json).

Full audiovisual/browser/AI acceptance is not claimed.
The role remains partial in the global coverage table. The online Worker must be
redeployed: `services/matchmaking/src/catalog.json` validates selected fighters.

**Accepted Flash deviation:** retain the shared
`FighterRuntime._clear_interrupted_super_preparation` unchanged. A real hit before
`bsd` clears the orphaned `bs` lock, avoiding the original deadlock. All other
interrupt/cancel and guard rules are source-derived. No new deviation is intended.

## Reproduce

Follow `docs/OPERATIONS.md` using `neji`, `neji-base`, Sprite 535 and source 宁次.
Compile both player and AI controllers/body, AI context/hit state, hurt voice,
sound segments and opening. Bake source portraits with temporary output and
append only 宁次 to the shared portrait/footer and selection maps; regenerate the
online manifest after Godot import has completed.

Reference player: `/Users/fengkx/me/code/flash-player/Flash Player.app` (Adobe
32.0.0.465). Use `build_ai_reference.py --p1-character 宁次 --p2-character 一护
--p1-helper 我爱罗 --p2-helper 魂 --frames 600 --dynamic-move-case` and the retained
fixtures, then `capture_native_player.py` (windowed `open -g`, `tools/probes/mm.cfg`).
The account-wide native capture lock must serialize concurrent ports. Temporary
builds and raw captures belong under `/tmp/neji-*`, not the locked source tree.

## Moving hitbox source gate

`DefineSprite_535/frame_391/PlaceObject2_250_28` contains only the global pause
guard and `_X = _X + 20`; there is no `hitTest`, hit-state branch or stop-on-contact
assignment. The new Sprite 250 placement lasts through frame 404 (removed at
405), with no intervening MOVE; its one-frame child contains two Sprite 249
placements. Leaving this interval removes the moving hitbox. This answers the
frame/placement/exit questions without guessing new behavior.

The retained `projectile-pause` input produces the same first hit in Flash and
Godot at tick 34, but the old model/runtime incorrectly stops the hitbox after
contact and hits again at tick 38. Flash continues its +20 local-X callbacks and
ends at 960 HP; the old port ends at 920 HP. The fix compiles an explicit
empty collision-query list and interprets it before the legacy settled-hit cache.
Only source-authored collision branches may stop projectile movement. Original
trace: `/tmp/neji-original-pause-final/neji-projectile-pause/events.jsonl`; the
red native trace is retained at `/tmp/neji-native-pause/neji-projectile-pause.json`.
The invariant is continued movement through contact, subject only to the source
pause guard, not a hardcoded Neji exception or a change in damage/hitbox size.

Final native traces: `/tmp/neji-native-final`. Accepted originals are under
`/tmp/neji-original-focused-r3`, `/tmp/neji-original-final` and
`/tmp/neji-original-pause-final`; `checks.json` binds each exact path and hash.
Capture lock/queue failures remain recorded and are excluded from parity.
