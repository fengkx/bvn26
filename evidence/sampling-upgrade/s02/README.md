# s02 — required-native evidence reservation

Base: `d513f561b6113722d7ed6af9c6c0d910f3f7e21d`; branch `feat/roster-sampling-matrix`.
This is option B: a small rejecting native-capture hook, not a capture implementation.

`generate --require-native` records a boolean requirement in each generated tape
and its manifest entry. The loader checks both agree. `run` checks selected entries
before launching Godot; `check` checks the entire campaign. Required native evidence
is currently always rejected with the case ID because the adapter is not connected.
No claimed success receipt, Godot trace, or missing output can satisfy it. Unmarked
s01 campaigns retain their existing strict execution-coverage behavior.

## Validation

- 35/35 focused tests passed, including the previous missing/duplicate/wrong-prep/
  mutated-tape checks.
- New negative: required-native case rejects both run and check, with no engine launch.
- New negative: stripping the requirement from a tape still rejects even if its
  digest is updated, because the manifest retains the requirement.
- Actual CLI check on a generated required-native campaign exits 1; exact diagnostic
  in `missing-native.txt`. No new runtime/native captures or full-roster runs.
- Integrity and handoff checks retained alongside this note.

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-required-native --fighters didala --require-native
# Expected exit 1, naming the case and missing native evidence:
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-required-native --output /tmp/bvn-required-native-run
python3 -m unittest tools.tests.test_sampling_matrix tools.tests.test_move_cases_paths tools.tests.test_move_cases_targets tools.tests.test_move_acceptance_harness
```

## Known follow-ups

Implement the native adapter with case-bound capture identity, original source
readbacks and completeness validation before allowing this hook to accept evidence.
Full-roster execution, same-input native capture, global hitboxes, child display
lists, full camera, BitmapData exact comparison and DoAction execution coverage remain
follow-ups. They do not block review of this rejecting hook. `production_admitted=false`
and `native_parity_proven=false`; no runtime/importer changes, allowlists or tolerances.
