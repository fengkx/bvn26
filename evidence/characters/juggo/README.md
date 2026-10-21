# Juugo / 重吾 base-form port

Base: `782c2cfb9247e262d177bd952eaa1a99389ff06f`, branch `feat/juggo`.
Coverage remains **partial**. Targeted parity and rollback passed; full-roster validation is recorded below. No merge or deployment.

## Source-first answers

1. Locked `game/fighter/juggo.swf` and `scripts/fighter/juggo.json` drive Sprite
   517 (1,373 frames). `source-first.json` indexes every frame's scripts and
   display changes, including empty frames; the unmodified extracted timeline
   retains original matrices, depths, placement frames and absent names.
2. Root frame 315 places unnamed Sprite 146 at depth 28; its next-tick callback
   tests its own full bounds against the opponent's `bdmn`, then jumps to
   砍技21. Root 890 places unnamed Sprite 380 at depth 33. While unpaused and
   the opponent is alive, that callback copies the player's X plus child X
   multiplied by display scale, and player Y plus child Y, to the opponent.
   New placements have separate lifetimes; MOVE retains them. Root 248/877
   tests `kj10atm` against `jiao` as well as the authored body query. The source
   typo `kj10atm` in the ultimate is retained, not replaced with `cbs0atm`.
3. Normal returns: 187/214/239. Frame 200 allows normal/super/low/ranged/rush
   cancels; 227 allows upper super/upper ranged/rush. Normal super starts at
   573, resumes at 611 and returns at 694; upper super 719/755, facing-dependent
   warp at 762 and return at 798. Ultimate 830/876; contact enters 超必杀2,
   otherwise returns at 885. The continuation falls through 1035, loops at
   1041 until touch, enters 超必杀4, then returns at 1070. It does not gain
   an invented gravity or end-of-label recovery. Child Sprite 220 frame 16
   renames itself, conditionally jumps its parent to 招22 when the opponent's
   action is -1, then stops itself. Parent replacement may remove that child.
4. Tests lock source receiver equality, actual super/hurt frames, named foot
   queries and independent unnamed placements. Receiver Sprite 2 is shared.
   The body differs from Renji only in explicit zero offsets for addChildXG
   in doHurtSkill; its existing compiler handles that source call. Guard uses
   onDefence(2) at 1130; hurt callbacks are 1142/1155 and standing recovery is
   1151. HIT_RECEIVE A–D reuses the common chain and compiled gjl1 values.
5. Native Flash Debugger 32.0.0.465 captures run through
   `capture_native_player.py --allow-window-activation`, without manual clicks.
   Adjacent capture records establish execution; immutable build metadata
   retains `built_not_run`. Initial cancel timing copied from Gaara did not
   reach a super; it is retained as diagnostic evidence and recalibrated from
   Juugo's actual frame-200 window, rather than reported as cancel coverage.

## Native representation

Unnamed moving projectiles receive internal `@placement:depth:symbol:frame`
handles only in materialized runtime data, marked `runtime_only_name`. The
extracted Flash display list remains unnamed. Authored rename events control
attack lookup; those handles are not invented attack names. Each placement
keeps its independent movement, playhead and callback lifetime. Random rename
suffixes consume their original random site. Shared source child operations
and explicit foot queries are compiled, with no character-specific runtime
branch or guessed collision geometry.

## Selection and assist

The manifest has no Juugo `fzurl`, and no Juugo assist SWF exists. Its default
helper is the already imported Itachi/鼬. Local availability, online catalog,
source portraits/footer and natural opening include Juugo. Parity fixtures
explicitly use existing Gaara/Kon helpers on both sides.

## Intentional difference from Flash

PR #37 direct and queued interrupted-super preparation recovery is retained
unchanged. Flash can freeze in those sequences; Godot intentionally recovers.
`_clear_interrupted_super_preparation`: 1,086 bytes, SHA-256
`9da62022432d7093b22b265b9e411db392ede4cbb1656fec21fe244f93f274ed`.
The gate prints `PROTECTED_FUNCTION_OK`. No new intentional gameplay deviation.

Full audiovisual/browser/AI and exhaustive boundaries remain unaccepted.
Screenshots demonstrate rendered content, not pixel parity. Rollback smoke
uses the production local rollback session, not a live Internet match.

## Executed focused results

**12/12 cases, 8,664/8,664 actor states, 14 exact fields**, zero differences.
The compared fields are frame, x, y, xscale, action, hp, ql, sw, touch,
touchFloor, hits, paused, hstm and hurtSkling, with complete slot/tick alignment.
Normal/super guard chips **4/30 HP with zero hits**. Incoming guard then
Ichigo's low attack leaves Juugo at **916 HP / one hit**; interruption leaves
**960 HP / one hit**. Ultimate deals **450 damage / seven hits** and recovers.
Upper super deals **300 damage / two hits**. Repeated upper super enters at
ticks 11 and 181; the second cast whiffs identically, so total damage is 300.
Air ranged reaches its action but whiffs at the selected separation.

The calibrated cancel runs source frame 200 at tick 27 and enters super frame
570 at tick 28, dealing 380 total damage with a maximum four hits. The ranged
sequence reaches low-ranged 420 at tick 143, its conditional continuation 480
at tick 181 and low attack 248 at tick 263. Those observations are separate
from simple target-frame reach; the initial incorrectly timed cancel is kept
in `diagnostics/` and excluded from the 12 passing fixtures.

Four Godot checks pass: Juugo production rollback (natural opening, ultimate
pause checkpoint/replay, late guard inputs and round reset), protected super
recovery, player input and visual controllers. Python: **343 run, 341 passed,
two skipped**; final focused source/selection/projectile checks: **21 passed**.
Matchmaking typecheck and **31 tests** pass; its sandbox-restricted local
Wrangler test passed separately outside the sandbox without deployment.
Seven online-manifest tests and six contract schemas/examples pass. Shared
mode replay matches **602 PvP + 602 training-timer states**. Old combat models
recompiled with base/current compilers are identical for **25 prior fighters**;
see `compiler-impact.json`. No prior generated fighter data was rewritten.

Real Godot screenshots are `screenshots/selection.png` and
`screenshots/in-fight.png`, with capture metadata alongside. The selection
capture waits for the source footer timer; fight capture follows natural
opening and special input to source frame 616. The existing Web build copies
character evidence PNGs for a future publication; this work does not deploy.

## Reproduction

Use pinned JPEXS 26.2.1 / Godot 4.7.2 and `docs/OPERATIONS.md`: extract 重吾,
export its SWF to scratch, extract Sprite 517, build combat, materialize assets,
compile player/AI controller and body, context, hit state, hurt voice and sound
segments. Unnamed internal handles are added only during materialization.

Build a 360-frame dynamic move probe with 重吾/一护 and 我爱罗/魂 helpers.
Run `test_move_references.py --capture-only --allow-window-activation`, then
run each committed fixture through `move_case_reference.gd` and compare with
`compare_mode_reference.py`. `source-builds/` retains hashes, exact encoded
fixtures, tapes, capture environment and instrumentation diffs. The final
cancel and extended ranged captures supersede the retained initial diagnostics.
Run `check_protected.py` and `replay_saved_roster.py` using `BVN_GODOT` and
`BVN_CHECK_DIR`; the saved corpus includes Gaara and all preceding ports.

Final saved-roster replay: **204/204 cases, 119,008/119,008 actor states**, all 14 fields match (631.393 seconds). No fixture, baseline or tolerance changed.
