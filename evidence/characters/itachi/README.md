# Itachi / 鼬 (itachi)

Imported on `feat/itachi` from `84d567fe`. The complete locked fighter is
`game/fighter/itachi.swf`; `game/fighter/fz/you.swf` remains a separate assist.
The single-player selection, original portraits/footer, opening, player and AI
controllers, body, receivers, combat fields, assets and sound segments are
connected. Online catalogs/fingerprints include the fighter; no Worker or Web
production deployment is performed.

## Source-first gate

1. **Scripts:** Sprite 294 has 1,248 frames. The slice retains all 134 body
   scripts and original paths/hashes. Player/AI controller Sprite 11 and the
   shared Sprite 2 receiver compile from the locked bundle. The source SWF SHA-256
   is `35f626a8fc95352f61d25c93b4f139745cc9d50c39ba169b74e327ed61f25c3c`;
   script bundle SHA-256 is
   `a7af8284d41693c9506a433edcfd45f4b1e2a47bfda401dd2005952832e6e4fc`.
2. **PlaceObject/MOVE:** The timeline retains new placements, MOVE records,
   removal, matrices and child callbacks. The on-load copies at 305/405 only
   position the effect when the target is in front; 678 copies X without that
   guard. Frame 313 copies `zzzz` plus facing-relative 10 px and Y minus 4;
   415 copies only `zzzz._x`. New placements re-run these writes. Counter
   receiver 448–467 calls `checkHit()` and enters `招21` without applying
   `beida` damage. Frame 494 is an authored container warp using opponent
   `bdmn` width, including source Y. Projectile placements 157/160/163 and
   526/529/532 move by `movspeed` horizontally and respectively +/− half that
   speed vertically, starting after placement. No invented frame, hitbox or
   character-specific runtime movement was added.
3. **Exits:** Compiled `action_exits` retain authored goto/stop/play calls.
   Ground combo exits are 210/241/287; down-J 333; up-J 386 → `落`; air-J
   145 → `落`; air-U 181 → `落2`; U/down-U/counter/up-U exit at
   429/478/510/550. Supers exit at 634/736/901, summon at 953. The label
   end frame is never used as an implicit standing transition. This source
   has no compiled natural label fallthroughs.
4. **Invariants:** Super start/end pairs are 580/599, 655/675 and 758/834.
   Shared `gjl1` packets, heavy-hit/guard-break mapping, combo HUD, source
   face labels and black overlay are compiled through the existing common
   receive chain. `onBeHit` occurs at 1010 (ordinary) and 1023 (flying).
   Nested Sprite 61 frame 10 sound 42 has independent 20369/20665 channel
   envelope levels; the converter bakes them into PCM and the player does not
   attenuate the result twice. Shape 6's actual four-point contour masks the
   source bitmap sheet through PlaceObject `clipDepth` (for example depth
   28 through 30 at frame 313); the renderer intersects bitmap fill geometry
   with that contour rather than replacing assets or guessing a crop.
5. **Original same-input comparison:** `cases/` contains 32 fixed-input,
   explicit-helper cases covering movement, air/ground attacks, three-hit
   combo, both directional J moves, U/down-U/counter/up-U, all three supers,
   summon and receiving guard. Directional projectile and super cases include
   mirrored, guarded and airborne targets. Each capture includes tick 0–300
   for both fighters: 602 states, 14 exact observed fields. `flash-builds/`
   retains per-case configuration, fixture URL/tape and source/tool hashes;
   `traces/` retains the immutable original events. See `checks.json` for
   actual execution, target reach, comparisons and regression totals.

## Shared corrections and regression scope

The importer/runtime additions are generic source operations needed by Itachi:
load-time target coordinates, later clip-relative copies, fractional projectile
motion, a checkHit-only counter callback and checkpoint restoration, nested
sound envelope segments, and bitmap `clipDepth` masking. Existing generated
fighters retain their data. The mask compiler accepts a single closed contour
and rejects unsupported mask geometry; this change does not claim support for
arbitrary Flash masks or exact solid-fill rendering under masks.

Close up-U exposed another existing shared error: `_fsArray` had been scanned
in insertion order. Native AVM1 `for…in` enumerates this dense array backwards.
`diagnostics/enumeration.as` copies the locked array construction;
`enumeration.txt` records all 96 names in actual native order. The instrumented
fight selects zh3 at tick 14, zh31 at 18 and zh32 at 22. Scanning forward
selected an older overlapping projectile instead of the third flying packet,
then dealt an extra hit. Runtime now explicitly reverses the compiled insertion
order. `diagnostics/pre-priority-fix-comparison.json` retains the three failures;
no source tape, oracle, field or tolerance was changed to make them pass.

All 71 saved Flash fixtures covering the 15 previously available fighters are
replayed against final code. The baseline comparison is `84d567fe`; its initial
14 runs with missing imported-asset sidecars were invalid and rerun after
restoring sidecar links. The first current-code pass preceded the priority fix
and is not the final acceptance run. Final regression records are in
`regressions.json`, with native traces in `regression-traces/`.

## Validation and remaining differences

`checks.json` records exact results rather than treating assets/schema validity
as acceptance. The actual graphical snapshots in `diagnostics/` show correct
selection and the mask fix; they are not a Flash pixel comparison. The AI report
replays one AI-level-5 original random/clock tape from a partial standing
checkpoint (including nine original intro polls), not all five difficulty levels
or every AI branch. Dedicated rollback checks cover natural intro, ultimate,
three-frame delayed guard input, counter receiver restoration and round reset.

The following remain **unaccepted**, so `coverage.json` remains `partial` and
M6 remains pending:

- Exhaustive four-edge cancellation boundaries, all opponent/helper combinations,
  KO/match transitions and every spacing edge. The [medium-review follow-up](review-mediums/README.md)
  verifies one native input for each of the 22 windows, focused interrupts/guard,
  a helper/spacing variant and repeated casts with changed position/facing.
- Whole-fight Flash/Godot pixel and audio waveform/timing comparison, and browser
  parity. Source assets, event dispatch, PCM baking and selected rendered frames
  do not establish whole-role audiovisual identity.
- Exhaustive AI difficulty/branch coverage. The saved AI tape is focused evidence.
- The inherited pre-super interruption anti-deadlock behavior intentionally
  differs from Flash and is unchanged here.
- Five pre-existing Godot failures (`ai_colors`, `ai_context`, `ai_host`,
  `title_menu_source`, `ai_hit_gate`) reproduce on `84d567fe`; see
  `baseline-godot-failures.json`. They prevent claiming a wholly green Godot
  suite. Dummy-audio shutdown-only resource diagnostics are reported separately
  from assertion failures, using the existing rollback runner's classification.

This port makes Itachi playable and verifies the recorded cases. It does not
certify the user's broader requirement of complete one-to-one equivalence.

## Reproduction

Use the existing `tools/test_move_references.py` workflow with `cases/`, JPEXS,
Flash Player Debugger and Godot, or replay each saved fixture with
`godot/tests/move_case_reference.gd` and compare against its decompressed original
trace using `tools/probes/compare_mode_reference.py`. Preserve explicit helper
configuration. Native paths passed after Godot `--` must be absolute.

Run `python3 -m unittest discover -s tools/tests`,
`tools/validate_contracts.py` using `requirements-dev.txt`, `tools/verify.py`,
`tools/check_handoff.py`, the new `itachi_*_smoke.gd` scripts and
`tools/test_rollback_foundations.py`. The whole-roster rollback needs a quiet
machine or an increased process timeout; an earlier concurrent run exceeded the
wrapper's 180-second limit and is not counted as a pass. No test assertions or
comparison tolerances were relaxed.


## PR #12 medium-review follow-up

The [follow-up evidence](review-mediums/README.md) records the shared one-shot
placement fix, native Flash proof, rollback red/green test, 22-window matrix,
35 new fixed-input captures and 103 saved comparisons across all 16 implemented
fighters. All recorded actor-state comparisons match without changing an oracle
or tolerance. Calibration diagnostics are labeled separately from required
trigger coverage. The inherited anti-deadlock deviation is preserved.
