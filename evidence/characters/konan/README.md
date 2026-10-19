# Konan / 小南 (konan), 2026-10-19

Base: `79ef536759cbd94db336f98b0fa87500d9d07a7b`, branch `feat/konan`.
Coverage remains **partial**. The base form is source-compiled for local and
online selection, with original portraits/footer, natural opening and sound
segments. `game/fighter/konan.swf` has no ExportAssets; the locked main catalog
maps 小南 to `konan.swf`, so the existing filename convention gives `konan`.
The SWF is 427,218 bytes; Sprite 563 has 1,359 frames and 134 indexed body
scripts. `assist_source` is null. No helper was added and no Worker or Vercel
deployment is performed.

## SOURCE_FIRST five questions

1. `data/slices/konan-base.json` retains all 134 body scripts at their original
   `scripts/fighter/konan.json` paths. Its `.timeline.json` retains all frames,
   including frames without scripts. Sprite 16 controller, Sprite 2 receiver
   and Sprite 563 frame 1 equal Renji's 16/2/717 sources byte for byte.
2. Placements, MOVE, removal, matrices and child lifetimes remain source-derived.
   Cancel callbacks are placed at 215/245/285/323/401/503, starting on the next
   root tick. Frame 380 assigns `kj2atm` relative to the opponent. Placement
   load callbacks at 496/547/707 divide opponent-relative coordinates by the
   inner `mc` scale, with a front-only guard. Sprite 284 starts as `zh2atm`,
   renames to `abcd` at local frame 6, and stops at 26. Sprite 344 changes names
   at 13/16/20/23 and stops at 46; Sprite 399 changes at 12/22/25 and stops at 41.
   The root mounts `mc` at scale 0.718353271484375 (SWF fixed-point value).
3. Normals explicitly return at 224/256/302. Super start/end pairs are
   624/638, 691/704, 775/790 and 812/846. Air super explicitly enters
   `超必杀2` at 793. Ultimate naturally falls through at 912, loops there via
   frame 918 until the placed callback detects floor contact and enters
   `超必杀3`, then returns at 937. Guard calls `onDefence(2)` at 1065 and
   returns at 1073. Ordinary hurt calls `onBeHit` at 1077, stops at 1082 for
   `beidax`, and returns at 1086; flying hurt calls `onBeHit(true)` at 1090.
   Opening writes `kcplayed` at 1162/1164/1206 and returns at 1206.
4. Tests lock these source identities, receiver/super events, fallthrough,
   placement divisors and name release. No guessed damage, hitbox, movement,
   gravity or character-specific runtime branch is introduced. Fixture setup
   explicitly controls positions/energy and disables AI. Existing Gaara/Kon
   helper slots are explicit harness configuration; no helper input is used.
5. Original-player traces, independent Godot output and fixture hashes are in
   `comparisons.json`, `traces/` and `source-builds/`. Failed pre-fix output is
   retained under `diagnostics/`. No source tape or comparison tolerance changes.

## Shared corrections and HIT_RECEIVE A–E

A: `HitReceiveChainTests` retains the shared 35-fighter receive chain and
26-helper exclusion. B: the existing compiler emits `gjl1`, standing reset,
receiver/guard events, and source face labels 小南1/小南2. C: the runtime consumes
those fields. D: source tests and Godot receive/settlement/interruption checks
run with this port. E: fixed-input native Flash comparisons are recorded below;
full audiovisual acceptance remains open.

The first down+U comparison diverged at tick 38: Godot still offered `zh2atm`
after its source `_name = "abcd"` event, so the opponent was hit repeatedly.
The shared controller compiler now preserves a timeline that starts with an
attack name and later releases it, as well as timelines that acquire attack
names. Existing motion-owned clips remain excluded from duplicate hooks.
The combat compiler also recognizes the source load-coordinate divisors; the
runtime interprets optional `divide_parent_scale_x/y` using the imported `mc`
transform. The source front-only return remains intact. The retained failure
and post-fix exact comparison establish the correction; no hitbox was enlarged.

`compiler-impact.json` compares old/new compiler output for all 20 selectable
base forms. Only Konan changes; the prior 19 artifacts remain unchanged.
The conditional whole-roster saved Flash replay is recorded in `regressions.json`.

| State | Owner / source writes | Retention / release |
| --- | --- | --- |
| Body playback / action | Sprite 563 frame scripts and placed controllers | MOVE retains instances; explicit goto/stop or source fallthrough changes playback |
| Child attack name | Sprites 284/344/399 local DoAction | Source rename replaces the lookup name; new PlaceObject starts a new lifetime |
| Opponent-relative child position | Load at 496/547/707; DoAction 380/450 | Recomputed on new placement/execution; front-only load returns for a target behind |
| Hits / hurt motion | Shared receiver and body | `onBeHit` increments; standing frame 2 resets; `beidax` controls recovery |
| Super pause | Root bsd/cbsd and bsw/cbsw pairs | Restores shared stage and opponent playback at the authored end frame |

## Retained intentional Flash deviation

`FighterRuntime._clear_interrupted_super_preparation` is unchanged from PR #37,
including marking interrupted queued preparation entries and clearing their
orphaned `bs` after the retained DoAction executes. Other queued writes,
including energy cost, remain intact. The 1,087-byte function section (through
the blank lines before `_apply_hit_settlement_frame`) has SHA-256
`4eb7a77f734c95b7427cfa67b244a73972c3f2c71b06754cdd74203ff8293c44`.
This is the explicitly retained anti-deadlock deviation from Flash, not a new
Konan exception. `interrupted_super_lock_smoke.gd` exercises its queued recovery.

## Acceptance scope and reproduction

The established comparator checks 14 fields: frame, x, y, xscale, action, hp,
ql, sw, touch, touchFloor, hits, paused, hstm and hurtSkling, plus completeness
and alignment. State equality does not establish exhaustive move/cancel edges,
AI, audio, pixel or cross-browser fidelity. Milestones stay pending.

Use `docs/OPERATIONS.md`: extract 小南; export `konan.swf` with JPEXS 26.2.1;
extract Sprite 563; build/materialize `konan-base`; compile player controller
and body into `player_controller`, player body into `player_body`, AI controller
and body into `ai_controller`, then context, hit state, hurt voice and sound
segments. The per-fighter intro block documented in Orochimaru's README avoids
the existing full HUD mask-1751 importer limitation. Merge only 小南's original
five portrait frames and footer, then regenerate the online manifest.

Build `tools/probes/build_ai_reference.py` with `--dynamic-move-case`,
`--p1-character 小南 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂`,
240 frames and a retained case. Capture sequentially with
`tools/test_move_references.py`, `tools/probes/capture_native_player.py`,
`--player-app '/Users/fengkx/me/code/flash-player/Flash Player.app'` and
`--allow-window-activation`. Adobe Debugger 32.0.0.465 is used solely as the
analysis oracle. Run Godot 4.7.2's `res://tests/move_case_reference.gd` for each
fixture and compare the independently generated trace. The capture-only
harness's source-derived `native.json` placeholders are never counted.

`res://tests/konan_rollback_smoke.gd` exercises natural opening, controlled
X=300/350 and energy=300, ultimate pause checkpoint replay, delayed guard input
and source next-round reset. An initial inherited Pain assertion expected
Konan's ultimate to hit at natural distant spawn positions; that unsupported
assumption was rejected and the setup now matches the original-player fixture.
The failure is retained. The initial native batch overlapped cold resource
import; a later batch exceeded the runner's 180-second limit. Neither batch
is counted. Accepted traces come from successful independent per-case runs.

## Focused comparisons

Twelve accepted cases match **5,784 / 5,784 states**, 482 per case, on all
14 fields with zero differences. The four supplemental/diagnostic runs are
kept separately and do not inflate this count.

| Case | Actual observed coverage |
| --- | --- |
| combo | Three-hit normal chain; defender HP 880 |
| cancel-super-held | Tick 34 frame 323 → tick 35 frame 810; defender HP 380, 17 hits |
| interrupt | Konan's normal interrupted; HP 960 |
| guard | Normal blocked; defender HP 998, hits 0 |
| receive-guard | Konan blocks, then receives source guard break; HP 916 |
| super-guard | Normal super chip; defender HP 850, hits 0 |
| ultimate-guard | Ultimate chip and recovery; defender HP 920, hits 0 |
| upper-super | Scaled load targeting plus source attack-name changes; defender HP 820, four hits |
| air-super | Air super enters ultimate landing continuation; defender HP 750 |
| down-ranged | Scaled load and Sprite 284 name release; defender HP 930, one hit |
| target-repeat | Two up+J placements after target movement; defender HP 800 |
| upper-ranged-mirror | Two up+U casts in the same instance; target X 350 then 234, attacker facing +100 then −100; defender HP 800 |

The initial cancel input occurred during hitstop and did not enter a super.
The first two repeated upper-ranged movement fixtures moved the target but did
not cross the attacker (ground contact or landing blocked passage). Their
matched traces remain diagnostics; the accepted mirror fixture approaches,
then jumps across, and actually executes both facing branches. No controlled
teleport or mid-fight refill is used in that fixture.

## Final validation

The shared-change replay passes **131/131 cases and 79,222/79,222 states** on
14 fields. It replays the 103-case Itachi review corpus plus eight Orochimaru,
ten Jiraiya and ten Pain cases. There are 18 primary fighters; Renji appears
only as opponent in two overlap cases, so this is not a Renji-primary claim.
The old/new compiler audit leaves all prior 19 character outputs unchanged.

Python: 319 run, 317 pass, two skipped. Relevant Godot checks: 11/11, including
Konan rollback/late input/reset and shared queued-preparation recovery. PvP and
training timer each match 602 states. Matchmaking has 31 passing tests and a
passing typecheck. Contracts, handoff, locked-input integrity and online
manifest checks pass. See `checks.json` for runtime hashes and measured wall
time; no person-day estimate is inferred.

The first final-build attempt in the restricted sandbox failed the local HTTP
cancellation check with `Cancellation reported a stale transport error:
["http_transport_failed"]`. Its log is retained as
`logs/web-sandbox-failed.log.gz`; the test and its assertions were not changed.

The unchanged full build succeeds with local HTTP/user-directory permissions:
`WEB_BUILD_METADATA_OK`, matching PCK/sidecar hash, and
`ONLINE_LOBBY_UI_RUNNER_OK`. `web-build.json` identifies the tested working-tree
snapshot based on the recorded base commit; it is not a post-commit rebuild.
A final-export Chrome smoke passes title → Konan portrait/name → fighter/helper
confirmation → map → natural opening → live fight, including movement and
normal attack input. `browser-check.json` records this limited observation;
full audiovisual/cross-browser acceptance remains pending. An earlier computer
control service startup error recovered on retry. No deployment or merge.
