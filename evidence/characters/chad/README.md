# Chad / 茶渡 (chad), 2026-10-13

Imported from `b15aeec43c9cc3ffc897b817261fe72d1ce0202e` using the existing
Renji-compatible pipeline. No production runtime or compiler rules changed.
Sprite 607 has 1,136 frames and 128 indexed scripts: three normal attacks,
directional/air moves, three supers and their continuations, movement,
guard/hurt/recovery, opening and result animations. Source matrices, hitbox
placements/removals, sounds, presentation events and controller lifetimes are
compiled. The original card, five portrait frames, footer name, local roster,
online catalog and compatibility fingerprints include Chad. Orihime (`zhiji`)
is out of scope; the existing four selectable helpers remain available.

## SOURCE_FIRST five questions

1. `data/slices/chad-base.json` indexes all 128 Sprite 607 scripts at their
   original `scripts/fighter/chad.json` paths. Every frame, including empty
   frames, is retained in `data/slices/chad-base.timeline.json`. Sprite 16's
   controller, Sprite 2's receiver and Sprite 607 frame 1 are byte-identical
   to Renji's corresponding scripts. The shared receiver audit covers all
   35 fighters; no character-specific receiver logic was introduced.
2. New PlaceObject, MOVE and removal records retain depth, matrix and placement
   frame. The new combo controller lives at 190–194 / 208–215; the contact
   controller at 245–252; diagonal motion at 394–401; ultimate contact at
   662–671. Callbacks begin after placement. The hitbox instances are source
   `kj10atm` and `zh20atm`, not visible-effect bounds. Compiled controller hooks
   preserve placement identity rather than inheriting another clip's state.
3. Frame 245's controller branches on `kj10atm.hitTest(opponent.bdmn)`:
   contact enters `砍技11`, otherwise `moveX(speed * 3)`. Frame 255 explicitly
   returns to standing on a miss. Frame 662 similarly branches on `zh20atm`:
   contact enters `超必杀1`, otherwise `moveX(speed * 4)`. Frame 672 explicitly
   enters `超必杀0`; `超必杀1` naturally falls through at 698. Frame 721 returns
   to standing. No label end is treated as an invented exit. Other source
   exits include 197/216/240 (normals), 523/612 (supers), 810 (guard recoil),
   823 (hurt), 864 (knockdown), 885 (recovery) and 922 (opening). Hurt stops
   at 819 until `beidax` releases it.
4. Focused checks assert source properties: the exact contact branches and
   clip lifetimes, 394 `moveX(8); moveY(15)`, source `gjl1` packets, 802
   `onDefence`, 814 `onBeHit`, 827 `onBeHit(true)`, and super pause/face events
   at 482/495, 550/566 and 646/662. Frame 131 retreats X only while the
   opponent is alive but always raises Y when unpaused; the full conditional
   controller is compiled. Frame 627's diagonal motion is retained even though
   the ordinary upper-super path exits at 612. No guessed boxes or displacement.
5. Fixed-input fixtures in `cases/` exercise combo/cancel, ordinary interrupt,
   attack-versus-guard, Chad's own guard/hurt, contact dash, diagonal movement,
   all three supers and ultimate miss continuation. `checks.json` records
   actual original/Godot comparisons and coverage observations separately.
   These focused cases are not an exhaustive cancel-boundary or visual matrix.

## Validation and deviations

All ten focused original-player comparisons match 482/482 states each across
14 exact fields, with both source and native target reach verified. See
`checks.json` for results, trace hashes and observed hit/guard branches. `chad_rollback_smoke.gd` uses the
production selected actors, completes the natural intro, saves during ultimate
pause, replays through guard/guard-break settlement, compares complete simulation
state, and checks next-round reset. No gameplay thresholds or oracle outputs
were changed to obtain a match.

**Retained Flash deviation:** `FighterRuntime._clear_interrupted_super_preparation`
clears the orphaned `bs` lock on a real hit before the super pause starts. The
user explicitly requires this existing shared anti-deadlock fix. It is unchanged.
No additional Chad-specific deviation is intended. Full audiovisual, browser,
AI and exhaustive boundary parity remain unverified. Missing source voice
linkages are not invented.

The matchmaking Worker validates its own `services/matchmaking/src/catalog.json`;
it must be redeployed later to accept Chad. This change does not deploy it.

## Reproduce

Use the commands in `docs/OPERATIONS.md` with 茶渡, `chad`, Sprite 607 and
`chad-base`. Compile player and AI controllers/bodies, context, hit state,
hurt voice and sound segments; rebuild the source opening. Build source
portraits/footer into a temporary directory, merging only Chad's assets. Rebuild
`tools/build_online_manifest.py` after catalog changes.

The persistent reference player is
`/Users/fengkx/me/code/flash-player/Flash Player.app`, Adobe 32.0.0.465, executable
SHA-256 `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
The recorded installer hash and official download are in
`evidence/reference-environment.md`. Probes use temporary instrumented copies,
`tools/probes/mm.cfg`, and `capture_native_player.py` with `open -g`; Flash can
still activate its own window. The account-wide capture lock is respected.

Build `build_ai_reference.py --p1-character 茶渡 --p2-character 一护
--p1-helper 我爱罗 --p2-helper 魂 --frames 240 --dynamic-move-case
--move-case evidence/characters/chad/cases/combo.json`, then use
`test_move_cases.py` and `test_move_references.py` with these same fixtures.
Raw exports, traces, logs and caches remain under `/tmp/chad-*`.
