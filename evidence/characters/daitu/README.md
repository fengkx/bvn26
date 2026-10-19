# Daitu / 带土 base-form port

Worktree: `/Users/fengkx/me/agent-code/bvn2_6-daitu`, branch `feat/daitu`.
Base: `8fc5c5e458938f39cc1f5f20162eab17bdcde23f` (Konan PR #38).
Coverage: **partial**. Targeted gameplay parity is accepted below; full role
audiovisual/browser/AI acceptance remains pending.
Assist is out of scope. No deployment or merge.

## Source-first scope

1. `source-first.json` indexes every frame of Sprite 458, its complete retained
   DoAction/clip scripts and timeline changes, including empty frames.
   `data/slices/daitu-base.timeline.json` preserves all 1,327 frames and their
   display lists; the slice contains 149 original script paths.
2. The controller callbacks at 332 and 710 are newly placed instances, and run
   starting on the next tick. They hide the opponent and subtract 3 from the
   opponent wrapper Y while root pause is false. Frame 651 uses source-local
   aliases `pp` and `self`, moves each opponent axis by 10 while the gap exceeds
   15, and enters 上必杀2 only when both axes are within range. MOVE retains
   instances; no guessed gravity or capture binding is added.
3. Normal exits: 183/206/227/246/263. Frame 149 copies opponent Y and flips
   display X scale with opponent-relative X ±50. Frame 310 initializes
   `kj2hit=false`; 311 saves `zh30atm.hitTest(opponent.mc.bdmn)`; 318 tests that
   saved value, opponent HP >0 and action ==−1 before entering 招32. Frames
   412/773 reveal the opponent; 423/789 return to standing. Super pairs are
   530/547, 630/647 and 802/916; ultimate returns at 1001. Guard 1052 calls
   onDefence(2); hurt 1064 and flying hurt 1077 call the shared receiver chain.
4. Tests must lock those source assignments and their lifetime, not infer
   damage or hitboxes from animation. The source misspelled `kj2aDtm` and
   `zh1aDtm` Y writes are not corrected into attacks. Receiver Sprite 19 is
   invoked by the base timeline; Sprite 5 is also placed but is not selected
   merely because it contains similar packet code.
5. Fixtures use the original Adobe Flash Player Debugger 32.0.0.465 through
   `capture_native_player.py`, with separate instrumented copies in /tmp.
   Original captures, independent native replays, actual target reach and
   comparison results are recorded separately. No tolerance or baseline edits.

## State ownership

| State | Source owner/write | Lifetime |
| --- | --- | --- |
| kj2hit | Body frame 310 reset; 311 collision snapshot; 318 read | Retained until another source write; reset on another cast |
| Opponent visibility | Controller 332/710 hides; body 412/773 reveals | Opponent wrapper property; checkpoint must preserve it |
| Opponent displacement | Controller 332/710 and attraction 651 | Executed in source callback order, subject to authored pause gate |
| Super preparation | Body bs writes; shared root bsd/cbsd and bsw/cbsw | Preserve PR #37 interrupted queued-preparation recovery |
| Hit state | Shared receiver and body onBeHit/onDefence | Standing resets hits; source beidax owns recovery |

HIT_RECEIVE A–E: use the retained shared 35-fighter/26-assist source-chain
checks, compiled gjl1/receiver/face events, generic runtime consumers, source
regressions and targeted native comparisons. Full audiovisual/browser/AI and
exhaustive boundary acceptance remains pending; coverage will stay partial.

## Preparation interruption boundary

The source display lists at 529/530, 629/630 and 800/801/802 have no `bdmn`.
A same-input Ichigo strike during normal-super preparation therefore cannot
interrupt Daitu. The first diagnostic only entered guard; the revised fixture
actually enters 529 at tick 15 and 530 at tick 16, spends 100 energy and remains
unhit. Its hurt target is deliberately not seen. This is a source-protected
negative, not evidence of a successful interruption. The shared PR #37 smoke
retains positive direct and queued preparation recovery for vulnerable fighters.
No receiver is added to force a Gin-class interruption where Flash disallows it.

## Targeted original-player comparisons

All **12/12 cases, 5,784/5,784 states** match exactly on the established 14
fields: frame, x, y, xscale, action, hp, ql, sw, touch, touchFloor, hits, paused,
hstm and hurtSkling, plus complete tick/slot alignment. Original and independent
native trace hashes are in `comparisons.json`. No source tape or threshold was
changed. Capture-only harness placeholders are not counted as native replays.

| Case | Actual observed coverage |
| --- | --- |
| combo | Five-hit chain; defender HP 810 |
| cancel-super | Normal 砍4 cancels to 必杀 at tick 73; defender HP 560, 19 hits |
| down-ranged | Source opponent-relative placement; defender HP 870 |
| guard | Normal chip; defender HP 998, no hits |
| prep-interrupt | Strike attempt during receiver-free preparation; caster unhit, super completes |
| receive-guard | Daitu blocks normal then receives guard break; HP 916 |
| super-guard | Normal super chip; defender HP 978, no hits |
| ultimate | Full preparation/release/recovery; defender HP 450, five hits |
| upper-attack | Contact branch into 砍技21; defender HP 910, three hits |
| upper-ranged | Saved contact enters 招32; hide/movement/reveal; defender HP 787, 17 hits |
| upper-super | Two-axis attraction and hide/movement/reveal; defender HP 740, 15 hits |
| warp-repeat | Two placements with target movement between; caster X 400/357, X scale −100/+100 |

The first upper-ranged fixture at target X=350 missed its narrow original
contact box. The accepted close-range fixture uses X=325, explicitly recorded
as initial setup. The earlier miss and two initial preparation/warp fixtures
remain under `diagnostics/`. They do not inflate the accepted count.

## Shared changes and evidence limits

The controller compiler exposes opponent visibility through a scalar adapter.
The frame compiler retains a contact snapshot and a later conditional branch,
and emits explicit opponent reveal events. The runtime only interprets these
generic fields. The receiver compiler verifies equivalent placed sources before
selecting symbols actually invoked as receivers; the existing divergent-alias
rejection remains tested. An initial overly narrow selection failed that
regression and was corrected before acceptance.

Sound 282 has two authored envelope points at sample 23,100. Baking preserves
the incoming ramp and outgoing zero-level step instead of rejecting the asset.
All 32 source StartSound segments were produced. Audio waveform parity,
including this endpoint, remains unmeasured; state comparison does not establish
sample-exact audio or pixel parity.

The old/new compiler audit leaves all prior 20 fighters' context and receiver
outputs unchanged. `_clear_interrupted_super_preparation` and both PR #37 call
sites remain unchanged: the REGRESSION_INDEX 1,086-byte gate reports
`PROTECTED_FUNCTION_OK`, SHA-256
`9da62022432d7093b22b265b9e411db392ede4cbb1656fec21fe244f93f274ed`.
Its anti-deadlock recovery is the retained intentional Flash deviation.

`daitu_rollback_smoke.gd` verifies natural opening, upper-super pause replay,
checkpoint restoration while the opponent is hidden, late guard delivery,
final reveal and source next-round reset. Shared mode replays each match
602 states for PvP and training timer. Final checks and the whole
saved-roster replay are recorded in `checks.json`.

## Reproduction

Use `docs/OPERATIONS.md` with pinned JPEXS 26.2.1 and Godot 4.7.2. Extract
带土, export daitu.swf outside the repo, extract Sprite 458, build combat and
materialize `daitu-base`. Compile player controller/body, AI controller/body,
context, receiver state, hurt voice and sound segments. The per-fighter intro
block documented in Orochimaru's README avoids rebuilding the unrelated main
HUD. Merge only the original five 带土 portrait frames and footer; append daitu
to local/online catalogs and regenerate the online manifest.

Build `tools/probes/build_ai_reference.py` with `--dynamic-move-case`,
`--p1-character 带土 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂`,
240 frames and a retained case. Run `tools/test_move_references.py` with
`tools/probes/capture_native_player.py` and the reference Debugger 32 app.
No helper input is used. Replay each fixture independently with
`res://tests/move_case_reference.gd`; compare using `compare_mode_reference.py`.
Retained `source-builds` include capture metadata, instrumentation, fixture URL
payload, random/clock tapes and capture logs. Native logs include metadata and
intervention records. Transient SWF copies and tool caches remain in /tmp.

## Final validation

The whole saved-roster replay passes **143/143 cases, 85,006 states** on the
changed shared runtime: the prior 131-case / 79,222-state baseline plus Konan's
12 cases / 5,784 states. There are 19 primary fighters; Renji occurs only as an
opponent in the saved corpus. See `regressions.json`. To repeat, run
`replay_saved_roster.py` from the repository root with `BVN_GODOT` set to the
Godot executable and `BVN_CHECK_DIR` set to a fresh scratch directory.

Python ran 322 tests (320 passed, two existing skips). Matchmaking passed all
31 tests and type checking on Node 24.18.0. Eleven focused Godot smokes pass;
the stage-sound exit warning from the initial run is retained and its verbose
rerun is clean. Input integrity, handoff, six schemas/six examples, online
manifest and diff checks pass. The final Web export passes local lobby and
build-metadata checks. `browser-check.json` records the limited Chrome
portrait/selection/natural-opening observation and its exact earlier build.

No new intentional gameplay deviation. The retained PR #37 recovery is noted
above. Full acceptance remains pending; `plan/coverage.json` stays partial.
Measured pipeline wall time is recorded in `checks.json`.
