# Ikkaku / 斑目·一角 (yijiao)

Ported from `fecb763064404c25fadd54f37a63369756188a6b` (includes Chad #6)
in the isolated `feat/ikkaku` worktree. The source asset slug remains `yijiao`.
Ikkaku was selected because he has one body timeline, no transformation or
independent summoned/projectile actors, and byte-identical Renji input/body/
receiver implementations. Ulquiorra retains multiple forms; Kenpachi has an
additional contact-receiver branch. Default assists are outside this port.

## SOURCE_FIRST

1. `data/slices/yijiao-base.json` indexes all 159 Sprite 455 scripts from
   `scripts/fighter/yijiao.json`; the timeline retains all 1,041 frames,
   including empty frames, matrices, nested display lists and StartSound events.
   Controller Sprite 18 equals Renji 16; body frame 1 equals Renji 717;
   receiver Sprites 2 and 439 are identical to Renji 2. The existing shared
   receiver audit covers all 35 fighter bundles. Source `gjl1` packets, source
   hit priority, hit/guard callbacks, presentation and opening are compiled.
2. Placement identity and MOVE/removal records are preserved. Sprite 267's
   movement-only callbacks are placed at 483–485, 486–490 and 491–495. Their
   own `moveX(spd)` writes `body._parent._x += spd * scale_X`; `moveY(spd)`
   subtracts from container Y. Callbacks begin after placement; each new
   placement has independent lifetime. These are body motion, not projectiles.
   The importer now recognizes pure `moveX`/`moveY` child controllers and
   reuses byte-identical placed receiver implementations, rejecting distinct
   sources. A generic `wrapper_move` frame event executes literal wrapper calls
   in the source FIFO, validating the wrapper function body before compilation.
   No character-specific runtime branch or combat threshold changed.
3. Normal exits are explicit at 200/222/250; down+J exits at 363; up+U at 499
   goes to `落`. Air U naturally falls through `跳招` → `跳招0` at 151;
   frame 158 loops, and its controller enters `跳招1` on floor contact.
   Missing `招21`, referenced at frame 465, remains a source missing-label
   no-op; no move is invented. Supers end at 567/641/766, guard recoil at 829,
   hurt stops at 838 until recovery and exits at 842, knockdown at 880,
   recovery at 905. Label end frames are never invented standing transitions.
4. Focused source tests lock controller identity, child placement lifetimes,
   rejection of nonidentical receiver aliases, `onDefence(2)` at 821,
   `onBeHit()` at 833 and flying receive at 846. Super pause/face calls are
   520/543, 579/604 and 675/717, using `一角1`/`一角2`. Frame 545 calls wrapper `moveX(150)`;
   frame 131 calls wrapper `moveX(5)` then `moveY(5)` (positive Y is down).
   This differs from the child controller upward `moveY` and is compiled separately. The ultimate packet
   `cbs.zl=17` breaks guard; ordinary `k1.zl=1` does not. No guessed geometry.
5. Fixed-input fixtures in `cases/` cover combo, down+J cancel, ordinary
   interrupt, outgoing/incoming guard, up+U child movement, all three supers,
   ultimate guard break, mirrored positions, mirrored normal super, and air attack. `checks.json` distinguishes
   execution, actual target reach and exact original-player comparison.

## Validation and limits

All 12 focused Flash comparisons match 482/482 actor states each across 14
exact fields; all source/native targets are reached. `checks.json` records
results, observed source frames and trace hashes. Compressed original/native
traces and instrumentation are retained in `traces/` (decompress before using
`compare_mode_reference.py`). The initial normal-super mismatch is retained:
202 differing states began at tick 39/source frame 545, where the missing
wrapper `moveX(150)` left native X at 300 instead of Flash X=450. The corrected
normal and mirrored super traces match without tolerance/oracle changes.

Rebased onto Neji master `46567086` for PR #8. Chad, Neji and Ikkaku
remain in the 15-fighter selection, portraits, footer, opening and online catalog.
The shared pure-motion `collision_queries=[]` change is retained; rebuilding
Ikkaku combat data with the merged compiler produces identical bytes.
The fresh 12-case native Flash rerun again matches all 482 actor states per case
across 14 exact fields. Frame 545 still moves X=300 to 450; the mirrored case
moves X=350 to 200. Existing fixtures and earlier traces are preserved.
See [rebase review](rebase-review.json) and `rebase-traces/` for fresh evidence.

Python: 283 run, 281 passed, two skipped, zero failures/errors; master has
279 run, 277 passed, two skipped. All four focused compiler tests pass.
All 15 roster rollback cases pass. Fourteen selected Godot checks pass their
assertions, including the Ikkaku,
Neji, Chad and Gin rollback/reset checks. Combat and stage_sound strict scans
flag dummy-audio shutdown resources (only AudioStreamMP3/AudioStreamPlaybackMP3
in verbose reruns); master combat reproduces this, while master stage_sound
exited cleanly, so identical shutdown frequency is not claimed.
The five known failures (`ai_colors`, `ai_context`, `ai_host`,
`title_menu_source`, `ai_hit_gate`) reproduce identical errors and locations
on master and the PR. Both shared-mode references match 602/602.
Online manifest: 7 passed. Matchmaking: typecheck passed, 30/31 on the initial
sandboxed run, then the local Wrangler registry test passed 1/1 with access;
31 unique tests passed across those runs, without login or deployment.
Contracts: 6 schemas / 6 examples. Package integrity and handoff are rechecked
after evidence updates. These counts distinguish run, pass and skip totals.
The rollback smoke uses production selected actors and natural intro, restores
inside the ultimate pause, compares complete state after replay, delivers guard
inputs three frames late through the production rollback session, then verifies
next-round reset. Full audiovisual/pixel, browser, AI and exhaustive cancel-window
boundary parity are not claimed by this focused port.

**Existing Flash deviation:** the shared
`FighterRuntime._clear_interrupted_super_preparation` clears an orphaned `bs`
lock when a real hit interrupts a super before its pause begins. This inherited
anti-deadlock behavior is unchanged by this PR. No new character-specific
runtime deviation is intended.

The local selector includes the original card, five alpha-preserved portrait
frames and source-built name. The online manifest and Worker catalog include
`yijiao`. **The matchmaking Worker must be redeployed later; this PR does not
perform deployment.** The default assist remains out of scope.

## Reproduce

Use `docs/OPERATIONS.md` with 一角, `yijiao`, Sprite 455 and `yijiao-base`.
Compile both player/AI controllers and bodies, context, hit state, hurt voice,
sound segments and opening. Bake source portraits/footer into a temporary
folder and merge only 一角. Rebuild `tools/build_online_manifest.py` last.

Reference player: `/Users/fengkx/me/code/flash-player/Flash Player.app`, Adobe
Flash Player Debugger 32.0.0.465. Executable SHA-256:
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
The persistent install provenance is in `evidence/reference-environment.md`.
Captures use `capture_native_player.py`, temporary instrumented SWFs and
`open -g`, serialized on the account-wide capture lock. Flash can still raise
its own window. No Chrome interaction or CLI login is used.

Build `build_ai_reference.py --p1-character 一角 --p2-character 一护
--p1-helper 我爱罗 --p2-helper 魂 --frames 240 --dynamic-move-case
--move-case evidence/characters/ikkaku/cases/combo.json`; run `test_move_cases.py`
and `test_move_references.py` against the same fixtures. Temporary exports and
logs are under `/tmp/ikkaku-*`. Failed/contended initial capture attempts are
excluded; the accepted capture batches are explicitly identified in checks.
