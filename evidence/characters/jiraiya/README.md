# Jiraiya / 自来也 (jiraiya), 2026-10-19

Base: `e5ef09ab`, branch `feat/jiraiya`. Coverage remains **partial**.
The base form is source-compiled for local and online selection. Sprite 342
contains 1,280 frames and 152 indexed body scripts. The locked SWF is 975,570
bytes. Controllers, body callbacks, receiver, timeline geometry, sound segments,
five original portrait frames, footer name and natural opening are imported.
Existing helpers are unchanged; Jiraiya's default assist is outside this port.
No Worker or Vercel deployment is performed.

## SOURCE_FIRST five questions

1. `data/slices/jiraiya-base.json` indexes all body scripts with their original
   `scripts/fighter/jiraiya.json` paths; the timeline retains every frame,
   including empty frames. Sprite 11 controller equals Renji Sprite 16,
   Sprite 2 receiver equals Renji Sprite 2, and body frame 1 equals Renji
   Sprite 717 frame 1. `test_jiraiya_import.py` verifies these source identities.
   The established 35-fighter shared receive chain and 26-helper exclusion apply.
2. Placements, MOVE, depth, matrices and removals remain source-derived.
   Normal movement callbacks occur at 184/203/225; cancel callbacks at
   187/211/232/272. The next tick starts each newly placed callback.
   `招2` frame 467 checks `zh20atm` before movement and jumps to `招21`
   on contact. Frame 558 warps X/Y relative to the opponent; upper super
   frame 767 flips facing and warps only X, preserving authored ±50 offsets.
3. Normals explicitly return at 196/220/244/288. Natural fallthroughs are
   `跳招→跳招1` at 152, `砍技2→砍技20` at 359 and `招3→招31` at 554.
   Super start/end pairs are 611/637, 733/765 and 820/868; exits are
   716/813/956. Guard uses `onDefence(2)` at 1022 and exits at 1030.
   Ordinary hurt calls `onBeHit` at 1034, stops at 1039 for `beidax`, then
   returns at 1043; flying hurt calls `onBeHit(true)` at 1047.
   Opening sets `kcplayed` at 1119/1121/1202 and returns at 1202.
4. Assertions lock source receive events, fallthroughs and super calls.
   No character-specific runtime branch, guessed hitbox or timing constant is
   introduced. Input fixtures record controlled initial positions and energy;
   target coverage is reported separately from state equality.
5. Native Flash fixed-input comparisons are recorded in `comparisons.json` and
   `checks.json`, with original and Godot traces under `traces/` and instrumented
   build identities/LoadVars payloads under `source-builds/`.

## HIT_RECEIVE SOP A–E

A: the full Python suite runs `HitReceiveChainTests` in
`tools/tests/test_source_inventory.py`, covering the shared 35-fighter receiver
and 26 helpers without that chain. B: the existing compiler emits `gjl1` into
`attacks_by_form[1]`, standing reset frame 2, receiver frames 1034/1047,
`onDefence(2)` frame 1022 and the authored 自来也1/自来也2 super face labels.
C: the unchanged runtime interprets those fields. D: source import assertions,
combat/settlement/hit-test and interruption checks pass. E: accepted same-input
Flash comparisons are listed below; full audiovisual acceptance remains open.

## State lifetimes

| State | Owner / write | Retention and release |
| --- | --- | --- |
| Playback / action | Sprite 342 frame scripts and controller callbacks | MOVE preserves clips; explicit goto/stop or documented fallthrough changes playback |
| Contact branch | `zh20atm`, frame 467 callback | Exists only for its authored placement lifetime; successful hitTest enters 495 |
| Warp / facing | Wrapper `_x`, `_y`, `_xscale`, frames 558/767 | Re-evaluated on every execution; no cached target position |
| Hurt / hits | Shared receiver and body | `onBeHit` increments; standing frame 2 resets; `beidax` controls recovery |
| Super pause | Root `bsd/cbsd`, source frame pairs above | `bsw/cbsw` restores shared stage and opponent playback |

The comparator checks the established 14 fighter fields: frame, x, y, xscale,
action, hp, ql, sw, touch, touchFloor, hits, paused, hstm and hurtSkling,
plus complete alignment. This does not establish full pixel/audio/browser/AI
or exhaustive move/cancel-boundary parity. Milestones remain pending.

**Retained Flash deviation:** the shared
`FighterRuntime._clear_interrupted_super_preparation` anti-deadlock fix clears
an orphaned pre-super `bs` lock after a real interrupt. It is retained unchanged
as explicitly requested. Its 544-byte SHA-256 is
`d39b2b50d96d37ac717e1d1e8e9ccd711a67f6bbadcee6afc30593d6e0caa91e`. This port does not introduce or modify it.

## Reproduce

Follow `docs/OPERATIONS.md` with `自来也`, `jiraiya.swf`, Sprite 342 and
`jiraiya-base` paths. Compile player controller/body into `player_controller`,
player body into `player_body`, and AI controller/body into `ai_controller`;
compile context, hit state, hurt voice and sound segments. Compile only the
per-fighter opening block documented in the Orochimaru README, preserving
existing HUD assets (the full intro importer has the known mask-1751 limitation).
Generate portraits/footer in a temporary workspace and merge only 自来也.
Regenerate the online manifest after local and Worker catalog updates.

Use Godot 4.7.2 from `~/me/agent-code/bvn-godot-toolchain`, JPEXS 26.2.1,
and native Flash Player Debugger 32.0.0.465 at
`/Users/fengkx/me/code/flash-player/Flash Player.app`.
Build `tools/probes/build_ai_reference.py` with `--dynamic-move-case`,
`--p1-character 自来也 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂`
and the retained fixture. Run `tools/test_move_cases.py` and
`tools/test_move_references.py`, passing `tools/probes/capture_native_player.py`,
the player app and `--allow-window-activation`. Temporary SWFs, logs and exports
stay under `/tmp/jiraiya-*`; Flash is never a production dependency.

Run `res://tests/jiraiya_rollback_smoke.gd` for natural opening, checkpoint
replay through ultimate pause, delayed guard input correction and round reset.
Local matchmaking tests require Node 24.18.0. Worker catalog redeployment is
explicitly deferred; only catalog data and client fingerprints are updated.

## Accepted comparisons and validation

Ten cases match **4,820 / 4,820 states**, 482 per case, on all 14 fields.

| Case | Actual observed coverage |
| --- | --- |
| combo | Four-hit chain; defender HP 820 and hits 4 |
| cancel-super | Tick 16 source frame 187 → tick 17 super frame 608; defender HP 610 |
| interrupt | Normal interrupted; Jiraiya HP 960 |
| guard | Normal blocked; defender HP 998, hits 0 |
| receive-guard | Jiraiya blocks then receives guard break; HP 916 |
| super-guard | Normal super chip; defender HP 963, hits 0 |
| ultimate-guard | Chip and source guard break; defender HP 858, hits 1 |
| upper-super | Source frame 767 changes side/facing; eight hits, defender HP 710 |
| warp-repeat | Two casts in one fight; frame 558 re-reads moved target (X 340 then 387), defender HP 600 |
| rush-contact-held | Held down+U reaches 461, motion through 469 then contact branch 495; defender HP 850 |

Short down+U is retained under `diagnostics/`: both engines enter guard and
never reach the rush, so it is excluded from the ten accepted cases. The first
guard capture was invalidated by a supplementary task overwriting the temporary
LoadVars input while waiting for the capture lock. Final guard and held-rush
captures ran sequentially with fresh run IDs; invalid attempts are not counted.

Python: 309 passed, two skipped. Nine existing Godot checks plus the dedicated
Jiraiya rollback smoke pass. Matchmaking: Node 24.18.0, typecheck and 31 tests
pass locally. Handoff, locked-input hashes, six schemas/examples and online
manifest (18 fighters, four helpers, ten stages) pass. The existing headless
audio shutdown warnings are retained; no SCRIPT ERROR is accepted.

No shared compiler or production runtime changed. Earlier fighter artifacts
remain unchanged, so the conditional whole-roster Flash replay was not needed.

Measured session wall time through evidence packaging: 688 seconds, including
capture waits and failed harness attempts; no person-day estimate is inferred.
