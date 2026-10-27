# s10 — Konan matrix execution

Execution base: `f78d173f9a51822eff32fd35e406a0195d086379`.
Branch: `feat/roster-sampling-matrix`; PR #49. One additional fighter, unchanged
harness, inputs and fail-loud coverage gate. No runtime/importer changes.

## Results

- Konan (`konan`): **324/324** passed; **39,528** actor observations.
- Full coverage check exits 0. Removing one case result while preserving the
  success summary exits 1; restoring the exact report bytes passes again.
- **35/35** focused tests; integrity and handoff passed.
- Separate campaigns across s01/s03–s10: **10/26 fighters, 3,240/8,424 cases**.
  Previously proven fighters were not rerun. This is not a full-roster run.

`acceptance.json` records counts, campaign hash and the 16 remaining fighters.
`konan-report.json` records every case result. Representative ground/air tapes
and compressed traces are retained; bulk outputs remain scratch artifacts.

## Reproduction

Godot `4.7.2.stable.official.ed1daf0bf`, headless; use fresh directories:

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-sampling-s10-konan --fighters konan
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-sampling-s10-konan \
  --output /tmp/bvn-sampling-s10-konan-run \
  --godot /tmp/bvn-loud-fail/r02/engine/Godot.app/Contents/MacOS/Godot
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-sampling-s10-konan \
  --output /tmp/bvn-sampling-s10-konan-run
python3 -m unittest tools.tests.test_sampling_matrix tools.tests.test_move_cases_paths \
  tools.tests.test_move_cases_targets tools.tests.test_move_acceptance_harness
```

The matrix retains six action keys × nine directions × ground/air × three
starting distances, with 61 root observations of both actors and root position.
The negative proof mutates only the scratch report, not inputs or native references.

## Known follow-ups

Remaining fighters, same-input native capture, global hitboxes, child display
lists, full camera, exact BitmapData comparison and DoAction execution coverage
remain follow-ups. Execution coverage is not Flash parity or proof every requested
move triggered. `production_admitted=false`, `native_parity_proven=false`.
No native capture, Web build, merge, deployment, Worker change or allowlists.
