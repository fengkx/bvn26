# PR #12 medium-review follow-up

Base: `f8d22f3a` (PR #12), on `fix/itachi-review-mediums`. This follow-up
preserves PR #10/#11/#12 and `_clear_interrupted_super_preparation`. The latter
remains an intentional Flash deviation: interruption of super preparation must
not leave the port in the original permanent pause/deadlock.

## Source-first answers

1. `source-audit.json` retains every Sprite 294 script and every timeline frame's
   changes/events in the affected action ranges, including frames without
   scripts. The 22 compiled input windows come from nine distinct enterFrame
   paths at 24, 114, 139, 202, 228, 270, 986, 1002 and 1034. Their order and
   predicates remain unchanged. The source controller is Sprite 11; the shared
   Sprite 2 receiver supplies `beida`/`fangyu`/`checkHit`.
2. The audit records new PlaceObject versus MOVE/removal. In particular `zzzz`
   loads at 305/405; new `kj1atm` at 313 copies `zzzz._x + 10 * facing` and
   `zzzz._y - 4`; new `zh1atm` at 415 copies `zzzz._x`. Frame 678 loads
   `bs2atm` at the opponent's X. Load and DoAction assignments are single
   executions; enterFrame cancellation callbacks begin after placement.
3. The compiled exits preserve source goto/stop/play, not label end frames.
   Relevant explicit exits include 210/241/287 (combo), 333 (down-J), 429 (U),
   736 (super), 145 (air-J to fall), and the authored guard/landing/recovery
   scripts in the audit. No cancellation or exit rule was invented here.
4. The invariant is **consume an attempted source write even if its receiver
   or reference is undefined**. The native semantic probe in `placement/`
   executes the exact `zh1atm._x = zzzz._x` assignment from frame 415 on a
   stopped timeline. It observes X=17 immediately and X=17 after the reference
   appears at X=123. A missing receiver later created at X=23 also stays at 23,
   rather than receiving the old assignment to 99. This is a synthetic native
   AVM1 probe, separately identified from original-game input fixtures.
5. New fixed-input original-game captures use `capture_native_player.py` and
   the existing dynamic move probe. Per-case fixtures, build metadata,
   instrumentation and original traces are retained alongside the results.
   Comparisons use the existing 14 exact fields, without oracle/field/tolerance
   changes. The saved 16-fighter suite is rerun after the shared change.

## Shared fix and state lifetime

`_apply_clip_placement` records the event in `_clip_placements_applied` before
opponent/name/origin/reference lookup. Both `origin == Vector2.INF` and missing
`reference_instance` therefore consume the invocation. The polling entry point
also routes an absent opponent through this bookkeeping. Successful writes and
front-only rejections keep their existing behavior.

| State | Owner/write | Retained | Reset |
|---|---|---|---|
| `_clip_placements_applied` | Fighter, before source placement lookup | Repeated ticks and rollback snapshots | Existing source action entry / new cast |
| `_placement_owned`, local offsets | Fighter, successful assignment | Existing PlaceObject/MOVE lifetime | Existing placement expiry / explicit clear |

`BattleCheckpoint._build_field_descriptors` captures script variables; the
consumption dictionary is not in `IMMUTABLE` or external exclusions. No separate
unsnapshotted cache was introduced. `clip_placement_once_smoke.gd` saves after
both kinds of failed lookup, makes both names available, and verifies no retry
before and after restoring the checkpoint. It also verifies action re-entry
executes again and a successful-placement snapshot round-trips exactly. The
unchanged test fails on `f8d22f3a` and passes with the fix (`placement/checks.json`).
The controlled missing-instance test is not counted as a full-game Flash case.

## Coverage and limits

The window matrix uses one calibrated point per compiled window, rather than
88 boundary permutations. Additional cases cover incoming attack interruption,
guard and guard break, interruption after a confirmed hit/cancel, an active You
assist, changed spacing, and repeated placement casts with target movement and
changed facing. Target reach, actual cancellation, and observed hit transitions
must be checked separately from a comparator pass.

Full audiovisual/browser/AI/opponent-combination acceptance remains outside this
review and pending. Existing five baseline Godot failures documented in the
parent evidence are not resolved by this change. M6 and whole-role coverage
remain pending/partial. There is no deployment or merge in this task.

## Reproduction

Use Godot `4.7.2-stable`, the existing native Debug Flash `32.0.0.465`, and the
locked JPEXS version. Generated SWFs, imported-resource caches and runtime logs
belong in a temporary directory. `flash-builds/` records the exact external
fixture and source/tool hashes used for each capture; instrumentation belongs
to analysis copies only. Archived `instrumentation.diff.gz` preserves the original
CRLF bytes; decompress it before checking `instrumentation_sha256`.

For an existing saved case, decompress its `.original.jsonl.gz`, then run:

```sh
/path/to/Godot --headless --path godot \
  --log-file /tmp/itachi-reference-engine.log \
  -s res://tests/move_case_reference.gd -- \
  /absolute/path/to/case.json /tmp/itachi-native.json
python3 tools/probes/compare_mode_reference.py \
  /tmp/itachi-original.jsonl /tmp/itachi-native.json \
  --source-build /absolute/path/to/build.json --output /tmp/itachi-comparison.json
/path/to/Godot --headless --path godot \
  --log-file /tmp/clip-placement-test.log \
  -s res://tests/clip_placement_once_smoke.gd
```

Fresh captures use `tools/probes/build_ai_reference.py --dynamic-move-case`
with the fixture's exact fighters and helpers, followed by
`tools/test_move_references.py --capture-only --allow-window-activation` and
`--case-id` for that fixture (batch only identical helper selections), with
`tools/probes/capture_native_player.py` as the capture runner. The AS2 fixture
URL is embedded in the temporary SWF, so copying the movie to a new directory
does not rebind it. Never let concurrent batches mutate the same `case.txt`.
The account-wide Flash log lock must cover launch, capture, snapshot and owned
process cleanup; waits for another capture are not failed gameplay assertions.

`regressions.json` points to the unchanged original fixtures/traces from PR #12
and records the new native outputs. `window-coverage.json` additionally checks
that each new input reached its calibrated source frame and target action;
matching final HP alone is insufficient.

## Observed trigger coverage

Fight ticks below are original root observations, before publishing the next
input. The source/native comparison covers every recorded tick, not just these
landmarks. Fixture names are retained exactly even when an exploratory intention
was not reached.

| Required behavior | Fixture suffix | Native Flash observation |
|---|---|---|
| All 22 windows / all 13 predicates | `window-0` through `window-21` | Every calibrated source frame is observed; each destination first appears on the next tick. See `window-coverage.json`. |
| Hit during an active attack | `attack-interrupt-active` | Tick 13 enters 191; tick 15 changes 192 → 1009; tick 16 settles 40 damage. |
| Blocking incoming attacks | `guard-break` (initial diagnostic) | Actually blocks up-J: enters 997 at tick 24; chip HP is 998/996/990 at ticks 25/29/33, with hits=0. It does **not** prove guard break. |
| Interrupt guard by breaking it | `guard-break-active` | Down-J's source `kj1zl=13` changes 986 → 1022 at tick 39; tick 40 settles 80 damage. |
| Confirmed hit, cancellation, then interruption; alternate active assist | `helper-you` | Opponent loses 30 HP at tick 19; Itachi cancels 202 → 300 at tick 23; the selected You assist interrupts 307 → 1009 at tick 89, then settles 40 damage at 90. |
| Changed spacing / cancel after whiff | `spacing` | Opponent starts at X=500 instead of 350. J does not damage the opponent, but cancellation enters 300 at tick 23; down-J deals 150 at tick 38. |
| Knockdown recovery input | `knockdown-ranged`, `window-21-at_start` | Source knockdown reaches 1034 at tick 50; dash input produces the authored recovery destination at tick 51. |
| Three placements on the same fighter, movement and both facings | `repeated-placement-cross` | Down-J enters 300 at ticks 13/158/243. Facing changes +100 → −100 at tick 132. Opponent X at the three hits is 350/240/80, with HP 850/700/550. |

The 35 new comparisons include six retained exploratory intentions, rather than
silently discarding them: `attack-interrupt` hit before attack startup;
`guard-break` was ordinary blocking; `knockdown` was ordinary hurt; the first
`hit-confirm-interrupt` hit after recovery; `hit-confirm-cancel-interrupted`
interrupted the opposing attacker instead; and `repeated-placement-mirror`
pushed the opponent on the ground without changing sides. These traces match,
but are not counted as proof of their originally intended triggers. The table
uses the actual successful replacements (including one case covering both
confirmed-hit interruption and the alternate assist).

No observed-field Flash/Godot mismatch remains in the new cases. The original
pre-super deadlock is still an intentional behavioral difference, not an oracle
adjustment. `preservation.json` records unchanged anti-deadlock function bytes
and ancestry through PR #10/#11/#12. The online build fingerprint is regenerated;
content fingerprints are unchanged.
