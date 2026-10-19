# Pain / 佩恩 (pain), 2026-10-19

Base: `aed7c7e4`, branch `feat/pain`. Coverage remains **partial**.
The base form is source-compiled for local and online selection. The locked
`game/fighter/pain.swf` is 1,073,884 bytes; its body is Sprite 573 (1,416 frames,
138 indexed body scripts). There are no ExportAssets aliases in this fighter
SWF; `manifest.json` maps 佩恩 to `pain.swf`. Controllers, body, receiver,
geometry, sounds, five portrait frames, footer and natural opening are imported.
Existing helpers are unchanged; the default assist is outside this fighter port.
No Worker deployment or merge is performed.

## SOURCE_FIRST five questions

1. `data/slices/pain-base.json` indexes every body script at its original
   `scripts/fighter/pain.json` path; the timeline retains all frames, including
   empty ones. Sprite 18 controller equals Renji Sprite 16; Sprite **5** receiver
   equals Renji Sprite 2; body frame 1 equals Renji Sprite 717 frame 1.
   Pain Sprite 2 is an obsolete implementation, not the placed receiver.
   `test_pain_import.py` locks these identities.
2. Source placements, MOVE, matrices, depth and removals are retained.
   Normals place movement callbacks at 205/229/261/300 and cancels at
   211/240/277. The ultimate places a fresh Sprite 18 at depth 38 on frame 943,
   retains it through 1053, then removes it at 1054. Its enterFrame starts on
   the following root tick. No instance variables are carried across placement.
3. Normals explicitly return at 220/249/285/323. `砍技2 → 砍技21 → 砍技22`
   naturally falls through at 427/431; the move returns at 450. Frame 423
   flips facing, sets X to opponent X ±30 and copies opponent Y. Super pause
   pairs are 603/640, 745/769, 844/856 and 908/941; exits are 717/817/891/1083
   (891 goes to 落2). Guard calls `onDefence(2)` at 1170 and returns at 1178.
   Hurt calls `onBeHit` at 1182, stops at 1187 for `beidax`, returns at 1191;
   flying hurt calls `onBeHit(true)` at 1195. Opening writes `kcplayed` at
   1267/1269/1313 and returns at 1313.
4. Tests lock source receiver events, super events, fallthroughs and callback
   membership. No guessed hitbox, movement constant or role-specific runtime
   branch is introduced. Fixtures document controlled initial positions/energy;
   actual trigger coverage is reported separately from exact state equality.
5. Before changing runtime, the original native Flash ultimate/guard capture
   completed with 6,228 events, including `done`. It shows the defender pulled
   above the attacker, taking repeated hits and then flying away. Retained
   source-first provenance and final same-input comparisons are under this
   directory. No source input or comparison tolerance is changed to hide a diff.

## Attraction and state lifetimes

The source callback at
`DefineSprite_573/frame_943/PlaceObject2_18_38/CLIPACTIONRECORD onClipEvent(enterFrame).as`
uses local aliases `pp` (opponent wrapper) and `self` (own wrapper). Under
`gameRunning()`, it computes X distance and distance to `self._y - 250`;
on each axis, only absolute distance greater than 25 moves the opponent by
20 toward the target. These numbers come directly from the source.
The old compiler rejects the local wrapper alias with `Unsupported AI expression`.
The shared offline compiler now resolves bounded wrapper aliases to the existing
scalar field ABI, rejecting alias reassignment and unknown expressions. The
shared predicate context writes opponent X/Y through the existing Flash twip
coordinate storage, just like own X/Y. It does not bypass ground/hurt processing.

| State | Owner / write | Retention and release |
| --- | --- | --- |
| Playback / action | Sprite 573 scripts and controller callbacks | Source goto/stop/fallthrough; MOVE preserves instances |
| Warp / facing | Wrapper X/Y/scale, frame 423 | Re-evaluated each execution using current opponent coordinates |
| Attraction | Depth-38 controller, frames 943–1053 | First callback after placement; gameRunning gate; removal ends it |
| Attraction locals | `pp`, `self`, `xd`, `yd` in enterFrame | Recomputed on each callback, never cached across frames |
| Hurt / hits | Shared receiver and body | onBeHit increments; standing frame 2 resets; beidax controls recovery |
| Super pause | Root bsd/cbsd and bsw/cbsw pairs | Shared source pause and resume, independent of attraction lifetime |

The repeat/changed-target warp fixture initially differs in 453 states,
starting at tick 14: Flash X=380 and xscale=-100; the port remains at X=300
and xscale=100. `diagnostics/warp-before.json` and its native trace preserve
that failure. The facing-warp parser now retains an optional explicit
`scale_X` assignment in each branch as `set_scale_x`; runtime writes it only
when authored. A display `_xscale` write alone still does not change logical
facing. The second cast exercises the opposite branch against a moved target
(Flash X=388 and xscale=100). Both casts copy opponent Y.

## HIT_RECEIVE SOP A–E

A: the Python source inventory tests cover the shared 35-fighter chain and
26 helpers without that chain. B: the existing compiler emits `gjl1`, standing
reset frame 2, receiver frames 1182/1195, guard frame 1170 and the authored
佩恩1/佩恩2 face labels. C: runtime interprets those fields; the new coordinate
write support is generic. D: import/source tests and shared combat/settlement
checks are recorded in `checks.json`. E: same-input original/native comparisons
and their exact scope are recorded in `comparisons.json`.

The comparator checks 14 fighter fields: frame, x, y, xscale, action, hp, ql,
sw, touch, touchFloor, hits, paused, hstm and hurtSkling, plus complete alignment.
State equality does not establish full pixel/audio/browser/AI or exhaustive
move/cancel-boundary acceptance. Milestones remain pending.

**Retained Flash deviation:** `FighterRuntime._clear_interrupted_super_preparation`
clears an orphaned pre-super `bs` lock after an actual interrupt. It is retained
unchanged as explicitly requested. The protected 544-byte SHA-256 remains
`d39b2b50d96d37ac717e1d1e8e9ccd711a67f6bbadcee6afc30593d6e0caa91e`.

## Reproduce

Follow `docs/OPERATIONS.md` with 佩恩, `pain.swf`, Sprite 573 and `pain-base`.
Compile player controller/body into `player_controller`, player body into
`player_body`, and AI controller/body into `ai_controller`; compile context,
hit state, hurt voice and sound segments. Use the unchanged per-fighter opening
block from the Orochimaru README, preserving HUD assets because the full intro
importer has the existing mask-1751 limitation. Generate portraits/footer in a
temporary workspace and merge only 佩恩. Regenerate the online manifest.

Use Godot 4.7.2, JPEXS 26.2.1 and Adobe Flash Player Debugger 32.0.0.465.
Build `tools/probes/build_ai_reference.py` with `--dynamic-move-case`,
`--p1-character 佩恩 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂`.
Run the retained fixtures with `res://tests/move_case_reference.gd`; capture
sequentially with `test_move_references.py` and `capture_native_player.py`,
using the player at `/Users/fengkx/me/code/flash-player/Flash Player.app` and
`--allow-window-activation`. Compare actual native output with
`tools/probes/compare_mode_reference.py`; capture-only placeholder native rows
are never accepted as Godot output. Temporary builds/logs stay in `/tmp/pain-*`.

Shared compiler/runtime changes require the `docs/REGRESSION_INDEX.md` corpus
plus the saved Orochimaru/Jiraiya cases: 121 cases across 17 primary fighters.
Renji appears only in two Sasuke/You assist-overlap cases; there is no
Renji-primary replay. The catalog has 18 prior slots.
The 14-field comparison covers fighter states, not every helper or render field.
Run the shared modes check and `pain_rollback_smoke.gd` for natural opening,
checkpoint replay through ultimate pause, delayed input and next-round reset.
Local matchmaking tests use Node 24.18.0; Worker deployment is deferred.

## Accepted focused comparisons

Ten cases match **4,820 / 4,820 states**, 482 per case, on all 14 fields.

| Case | Observed coverage |
| --- | --- |
| combo | Four-hit chain; defender HP 790 and hits 4 |
| cancel-ranged | Tick 17 source frame 211 → tick 18 frame 469; defender HP 870 |
| interrupt | Normal interrupted; Pain HP 960 |
| guard | Normal blocked; defender HP 997, hits 0 |
| receive-guard | Pain blocks then receives guard break; HP 916 |
| super-guard | Source chip/break chain; defender HP 838 |
| ultimate-guard | Attraction, 23-hit chain and final flight; defender HP 460 |
| upper-super | Source upper-super hit and recovery; defender HP 750 |
| air-super | Jump then air-super; defender HP 750 |
| warp-repeat | Two casts, moved target and opposite facing branches; defender HP 800 |

All accepted native traces are actual Godot output. The source capture batch
used `--capture-only` to decouple recording from native execution; its temporary
source-derived `native.json` placeholders are excluded. `comparisons.json`
contains fresh comparisons against the independent Godot runs, with hashes of
both trace files and each unchanged fixture. The failed warp trace is preserved.

The first native batch overlapped cold resource import and is invalid because
of missing imported textures; it is not counted. The first Flash combo capture
completed but its immediate comparison encountered the native filename mismatch;
final captures use distinct run IDs. Wrangler's first local test attempt hit
its user-registry sandbox restriction; the authorized escalated rerun passed.
None of these harness failures is treated as gameplay parity.

Local Web export and its original selection/lobby integration checks pass.
Interactive browser validation was attempted, but no browser provider was
available (`Browser is not available: iab`; provider inventory empty), and
native Chrome access returned `Computer Use was not approved to use Google Chrome`.
No browser screenshot or keyboard-flow pass is claimed.

## Final validation

- Saved Flash replay: **121/121 cases**, 17 primary fighters plus Renji in two
  assist-overlap cases only (no Renji-primary replay; catalog: 18 prior slots),
  **74,402/74,402 states** on 14 fields. The 43 cases already started before
  the final warp rule were rerun, and their newer results replace the earlier
  ones in `regressions.json`.
- Python: **313 passed, two skipped** (315 run).
- Final related Godot checks: **10 passed**, including Pain natural opening,
  ultimate pause replay, delayed input correction and source next-round reset.
  Broader checks: **33 passed**, five unchanged baseline failures
  (`ai_colors_smoke`, `ai_context_smoke`, `ai_host_smoke`,
  `title_menu_source_smoke`, `ai_hit_gate_smoke`). All 19 selectable fighters
  emit successful roster rollback case markers. The reference driver's old
  expected count of 16 was corrected from the current catalog and raw log;
  the pre-correction report is retained under `diagnostics/`.
- Shared modes: PvP and training timer references each match 602 states.
- Matchmaking: Node 24.18.0, typecheck and **31/31 tests** pass locally.
- Locked hashes, handoff, six schemas/examples and online manifest pass.
  Local Web build and metadata verification pass; no deployment. Browser
  interaction remains blocked as recorded above.

Measured goal-session wall time through evidence packaging: **1,483 seconds**,
including cold imports, failed harness attempts, capture and regression waits.
No person-day estimate is inferred. `checks.json` records hashes and limits;
raw check/capture logs are compressed under `logs/`.
