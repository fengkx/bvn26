# Deidara / 迪达拉 base-form port

Base: `b45e00b8c847582e30914bffe56f6e9dbc7e52d3`, branch `feat/didala`.
Coverage remains **partial**. Assist, deployment and merge are out of scope.
Final execution results, counts, hashes and elapsed time are in `checks.json`;
individual exact comparisons are in `comparisons.json`.

## L movement follow-up

The original port's 12 cases did not cover ordinary L. The generic frame
movement compiler now retains expression operands, restoring source-frame-34
`speed * 18` displacement and frame-970 `(-speed) * 6` recovery movement.
Fresh original captures, failing before traces, the ten L variants, recovery,
compiler impact and current-roster regression are retained in
[l-movement/README.md](l-movement/README.md). Historical port results below remain
unchanged; the follow-up has its own hashes and checks.

## Source-first answers

1. The locked `game/fighter/didala.swf` is 1,390,254 bytes, SHA-256
   `0f9a58902d84759892692fe71b1b9f54d076edfbd3480a51a1449d66e4e5b621`.
   Sprite 542 has 1,148 frames and 132 retained body scripts.
   `source-first.json` indexes every frame, including empty frames, its original
   script paths and display-list changes. Complete geometry is retained in
   `data/slices/didala-base.timeline.json`. Controller 16, receiver 2 and body
   frame 1 match Renji's shared source exactly.
2. Projectile placements at 151, 356 and 434 create new Sprite 84/210/281
   instances named `abcd`. Their frame-1 scripts stop playback and initialize
   `played=0`, with speeds 15/25/20 respectively. The next-tick callbacks query
   their own `hitmc` against the source's ordered opponent targets. On contact
   they set `played=1`, stop motion and goto frame 5, renaming to `tzatm`,
   `zh1atm` or `zh3atm`; frame 9 renames to `bbb`. At frame 5 the flight child
   is replaced with Sprite 82, whose frame 12 is empty and calls `stop()`.
   MOVE preserves a child; a new placement starts at age zero.
3. Normals return at 188/211/232/262. The frame-220 controller offers the
   source super/skill/normal/ranged/rush cancel branches. Super pause/release
   pairs are 477/496, 581/617 and 707/769; the first two return at 566/676.
   Ultimate frame 826 sets jump and moves Y by −250, then 832 enters 落2.
   Guard calls `onDefence(2)` at 892; hurt calls `onBeHit` at 904 or 917,
   and ordinary hurt returns at 913. Opening states are 989/991/1070.
   Label end frames are not invented standing transitions.
4. Tests lock these source paths, exact super/receiver frames, new explosion
   placement, retained child age, source stop and checkpoint restoration.
   Damage, matrices, hitbox dimensions and comparison thresholds are unchanged.
   The 35-fighter common receiver chain and assist-without-receiver audit remain
   part of the Python suite. HIT_RECEIVE A–E uses the existing compiled shared
   chain, Deidara's gjl1 and face labels, generic consumers and native captures.
5. Fixtures were executed in Adobe Flash Player Debugger 32.0.0.465 from its
   persistent installation, through `tools/probes/capture_native_player.py`.
   Instrumented SWFs remained in scratch directories. Separate Godot runs
   replay the same fixtures, with AI off, current world and explicit Gaara/Kon
   helper selections; no helper input is sent. Source capture placeholders are
   not counted as Godot results.

## Targeted cases

The 12 cases cover four-hit normals, source-frame-220 cancellation to super,
normal interruption, outgoing guard chip, incoming guard followed by guard
break, super guard chip, ultimate, upper super, two consecutive ranged casts,
upper ranged, airborne ranged and upper attack. Actual target reach, minimum
HP and hit counts are recorded per case in `comparisons.json`. Whiffs remain
whiffs; observing the animation alone is not claimed as hit coverage.

The comparator checks the established 14 fields (`frame`, `x`, `y`, `xscale`,
`action`, `hp`, `ql`, `sw`, `touch`, `touchFloor`, `hits`, `paused`, `hstm`,
`hurtSkling`) and complete tick/slot alignment. It does not prove sample-exact
audio, pixel equality, exhaustive cancel boundaries or full AI/browser parity.
The source references absent `空中必杀` and `absmian`; the original no-op is
preserved instead of inventing a move or sensor.

## Shared nested-child clock correction

The initial repeat-ranged comparison first differed at tick 100: Godot hit
three ticks late on the second cast. Both projectile placement and motion were
correct. The explosion's bounds incorrectly used the projectile's total flight
age, skipping newly placed explosion frames and briefly selecting empty frames.
The retained diagnostic native Flash `source_hit_test` observes the renamed
attack at local frame 6, bounds X=503.5..633, Y=−121.45..−1.8, with a true hit.
The source has just created Sprite 82 at parent frame 5.

`TimelinePreview` now records immediate child placement identity and age inside
the existing checkpointed instance records. A changed placement starts at zero;
retained placements advance independently even while the parent is stopped.
The compiler emits `child_stop_frames` only for direct child scripts consisting
solely of `stop()`. The runtime preserves this compiled table and clamps the
child clock at that stop. There is no character-specific runtime branch.
Only child IDs in the compiled table opt into these clocks. An initial
unconditional version changed Itachi's retained air-ranged replay; the final
version preserves legacy compiled playback. The failed full replay and its
Itachi trace are retained in `diagnostics/legacy-child-clock/`.
Combat and player/AI controller compilation call the same child-stop parser.
The intermediate combat-only export and its repeat-cast failure are retained
in `diagnostics/controller-child-stop-before/`; generated-controller assertions
also check the source stop table. `controller-compiler-impact.json` confirms
unchanged player/AI compilation for all prior 21 fighters.

`diagnostics/` retains the original failed comparison, both traces, the added
Flash hitbox instrumentation and initial smoke failures. The compiler audit
compares old/new compilation of all prior 21 fighters; no prior generated
combat output needs changing. The complete saved-roster replay is recorded in
`regressions.json`, with individual execution and comparison results.

**Intentional Flash deviation retained:** PR #37 direct and queued interrupted
super-preparation recovery is unchanged, including both call sites.
`_clear_interrupted_super_preparation` remains 1,086 bytes, SHA-256
`9da62022432d7093b22b265b9e411db392ede4cbb1656fec21fe244f93f274ed`.
The protected-function gate is run before shared edits and at final verification.
No new intentional gameplay deviation is introduced.

## Selection and visual evidence

Local selection and `services/matchmaking/src/catalog.json` include `didala`.
Five original portrait frames, footer, natural opening and 45 StartSound frame
groups are imported. `screenshots/selection.png` and `screenshots/opening.png`
are actual native Godot renders; the opening captures source frame 1010.
These are visual inspection evidence, not Flash pixel comparisons.
The Web build copies retained character screenshot PNGs to
`dist/web/evidence/characters/`, making them available on the eventual Vercel
deployment. This work does not deploy Vercel or the Worker.

## Reproduction

Use pinned JPEXS 26.2.1 and Godot 4.7.2 with `docs/OPERATIONS.md`. Extract
迪达拉, export didala.swf to scratch, extract Sprite 542, build combat and
materialize `didala-base`. Compile player/AI controller and body, context,
receiver, hurt voice and sound segments. Use the bounded per-fighter intro
block documented in Orochimaru's README. Merge only Deidara's original five
portrait frames/footer, then regenerate the online manifest after importing.

Build `tools/probes/build_ai_reference.py` with `--dynamic-move-case`,
`--p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂`,
240 frames and a retained fixture. Capture with `test_move_references.py` and
the native capture runner. Replay independently with
`res://tests/move_case_reference.gd`, then use `compare_mode_reference.py`.
`source-builds/` retains instrumentation, capture identity, LoadVars payload,
random/clock tapes and logs. `replay_saved_roster.py` uses `BVN_GODOT` and
`BVN_CHECK_DIR` from the repository root.

`didala_rollback_smoke.gd` exercises natural opening, ultimate pause, restored
checkpoint, delayed guard delivery and source next-round reset, using the same
starting separation as the focused Flash fixture. Full acceptance and M3/M6
remain pending.

## Final validation

- Native Flash: **12/12 cases, 5,784 states**, all 14 compared fields match.
- Entire saved roster: **155/155 cases, 90,790 states** match; 20 prior primary
  fighters. Renji occurs as opponent only in the saved corpus.
- Godot gate: **35 passed**, with five inherited failures matching their exact
  recorded signatures. All **22** individual rollback-roster records pass;
  the test's old printed summary still says 11. The evidence runner derives
  the expected count from the current selection catalog instead of using 16.
- Python: 323 passed, two existing skips. Matchmaking: 31 passed plus typecheck.
  Shared PvP/training: 602 + 602 states match. Contracts, locked-input verify,
  handoff and online manifest checks pass.
- Local Web export and Chromium boot are recorded in `web-build.json` and
  `browser-check.json`; `web-source-snapshot.json` checks the final production
  runtime and controller inputs. Native screenshots are copied byte-for-byte
  into the Web output. No deployment or merge was performed.

`checks.json` records measured elapsed time through evidence packaging. It does
not infer person-days or upgrade the partial coverage to full acceptance.
