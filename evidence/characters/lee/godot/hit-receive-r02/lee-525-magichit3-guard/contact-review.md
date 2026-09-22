# Lee 525 guard hit-contact review

This is one source/native contact-path comparison for Lee base-form `招3`. It is not a claim that every hitbox or move is pixel-identical.

## Same fixture and accepted state result

- Canonical fixture: `evidence/characters/lee/move-cases/lee-525-magichit3-guard.json`; the probe copy only adds read-only `geometry_probe` selectors. P1 Lee uses `up+ranged` (W+U, codes 87+85) on ticks 10–13; P2 uses down (arrow-down, code 40) on ticks 1–300; initial x=300/350 and energy=300/300.
- Source observer capture: `evidence/characters/lee/validation/hit-receive-r02-source/events.jsonl`, run `hit-receive-lee-525-guard-r02`; raw SHA-256 `ea25be8974bb070e7a3745071d9d65150d11fa78c56e213270bb3a9373fc850c`; build SHA-256 `20b346a4b5c932625762fc6f0f9fdc787ee06fed73a242004008ede80b796242`.
- Native invocation: `/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot --script tests/move_case_reference.gd -- /private/tmp/lee-525-magichit3-guard-geometry-r01.json /private/tmp/lee-525-magichit3-guard-native-r01/out.json`.
- The native state file SHA-256 is `71ca79ca4046033fa4238c6b0de7381b9dfc868e406b96dda8eaf578af18cd18`, byte-identical to the native artifact in `evidence/characters/lee/godot/helper4a0f-full-r01/strict-compare-current-r01/lee-525-magichit3-guard.compare.json`. That accepted comparison is 602/602 states, all 14 fields, zero differences.
- Current implementation hashes for this run: `main.gd` `8ef3f927c78426fbd50b2ed700544aff1b31d2727f59adf018a357a900ca8c7d`; `fighter_runtime.gd` `feb1a03f8a79ef9b9a0e1521d59b4ee57adb7501414c5856cb2c6ded4aefe5ac`; `helper_runtime.gd` `4a0f08ff087a498e9b15ed37bc166e2af9580ed4aa6b8e7853eaf742ce4f94f7`; `move_case_reference.gd` `61f8ef60c65541cb3f863a7c3e64a195cff6a5bd7fe09daa9a847f6b40ac1fec`.

## Contact evidence

At source `display_tick=473`, `fight_tick=18`, seq 3551 records a true `source_hit_test` from P2 `bdmn` against P1 `zh3atm` at source frame 533. P2's arrow-down key read is true in the same input window. The source world AABBs (game coordinates) are:

- P2 `bdmn`: `[341.70, -78.35, 372.25, -26.05]`
- P1 `zh3atm`: `[329.50, -119.40, 406.60, -24.45]`

Seq 3552 records the source receiver packet: `pw=60`, `zl=15`, `htype=被打`, branch `break`. This matches the source `zl > 10` rule; it is a guard break, not a blocked hit.

The native `hit_contact` row seq 660 reports P1 Lee, `zh3atm`, source frame 533, fight tick 325. At contact P2 is guarding (`防御2`, HP 1000, QL 300), and native later settles the hit as `被打`, HP 940, one hit. The native source-coordinate AABBs are:

- P2 `bdmn`: `[341.65, -78.30, 372.25, -26.00]`
- P1 `zh3atm`: `[329.50, -119.35, 406.55, -24.40]`

The boxes overlap and both sides record a hit. Per-edge differences are at most 0.05 px. The user accepts this micro-difference as negligible for this review; the exact values remain documented below, with no production defect inferred. Source and native fight ticks are independent clocks; the comparable anchors are Lee source frame 533, the named instances, and the contact/receiver branch.

The exact edge deltas (native minus source, in `(xMin, yMin, xMax, yMax)` order) are P2 `bdmn=(-0.05,+0.05,0,+0.05)` px and P1 `zh3atm=(0,+0.05,-0.05,+0.05)` px. The source instrumentation calls `this.getBounds(_root.game)` and `_loc4_.getBounds(_root.game)`. Its local transform values match the native placed MATRIX: attack `(a,b,c,d,tx,ty)=(1.3216553,0,0,2.7097778,-1.6,-85.9)` and defender bdmn `(.46374512,0,0,1.2910156,-3.25,-29.35)`. The corresponding native SWF translations are `(-32,-1718)` and `(-65,-587)` twips, which convert to the same pixel translations. Thus the leaf MATRIX values are not where the observed edge difference first appears.

The native `move_case_reference.gd:_source_game_rect` converts local `Rect2` values to integer twips with `roundi`, then `SourceMatrixBounds.bounds_for_chain` transforms the corners and rounds the results to twips with float32/ties-to-even operations. The source observer did not record receiver/attack self-local `getBounds(instance)` or all Flash ancestor matrices. These measurements are retained as provenance only; no further root-cause work or runtime correction is requested for the accepted micro-difference.

## Reproduction artifacts

- `fixture.json`, `native.json`, `native.contacts.json`, `native.geometry.json`, and `native.metadata.json` in this directory preserve the exact probe input and native output.
- Source hit-event field order is defined in the archived source build's `hit_receive_event_schema`.
- The capture instrumentation evaluates the original `hitTest` once, records its Boolean, and uses that same Boolean for the original branch. No production runtime was changed for this review.
