# Sasuke base-boundary original-player evidence

This record covers the 66-case base-form boundary manifest in
`/tmp/sasuke-base-boundary-batch-r01.json`. The source-player captures were
run serially with fresh AIREF run IDs and are retained under the capture roots
listed in `sasuke-base-boundary-final-r01.metadata.json`. Every source capture
has a raw log and a collector output; the per-case capture records retain its
exact start/end timestamps and completion state.

The native side uses the explicit-helper fixture manifest
`sasuke-base-boundary-native-case-paths-r01.json`. It is a copy of the source
fixtures with `p1_helper: "鼬"` and `p2_helper: "魂"`, derived from the source
build metadata. The original fixtures were not modified. This explicit helper
mapping is required because `move_case_reference.gd` otherwise defaults p1 to
我爱罗. The full source/copy/hash audit is in
`sasuke-base-boundary-native-fixture-r01.json`.

The final native run used the frozen Sasuke generated data and the explicit
helper manifest for every case. Before and after SHA-256 values for both
`godot/generated/fighters/sasuke/combat.json` and
`data/actions/sasuke-base.json`, along with the exact per-case Godot command,
source events hash, native fixture hash, native output hash, state counts, and
comparison result, are retained in
`sasuke-base-boundary-final-r01.metadata.json` and
`sasuke-base-boundary-final-r01.json`.

## Result

| Scope | Cases | Source states | Native states | Matched | Different | Tool errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sasuke base boundary | 66 | 602 each | 602 each | 66 | 0 | 0 |

All 66 comparisons have status `matched` and zero field differences. Earlier
comparisons against the pre-freeze native output, including the 775 summon
diagnostics, remain in `/private/tmp` as diagnostic records only; they are not
used for this final result.

The r01 runner did not collect before/after hashes for the fighter, main, or
helper runtime files. Its metadata records only the generated action data
hashes. A subsequent native-only r02 run records those runtime hashes without
re-capturing Flash; r01 remains the immutable first native pass. The final
runtime-hash-backed record is
`sasuke-base-boundary-final-r02.metadata.json`, with the standalone hash audit
in `sasuke-base-boundary-runtime-hashes-r02.json`. It reran all 66 native cases
against the same explicit-helper fixture manifest and remained 66 matched, 0
different, and 0 tool errors. The r02 metadata records unchanged before/after
hashes for fighter, main, helper, game-world, combat-resolver, Sasuke action and
generated data, and You helper data.

The native runner was
`/private/tmp/run_sasuke_native_unified.py`, using Godot
`/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot` and
`res://tests/move_case_reference.gd`. The source runner was
`/private/tmp/capture_sasuke_base_boundary_r04.py`; its raw source logs remain
outside the repository so the locked evidence directory does not contain a
large temporary capture bundle.
