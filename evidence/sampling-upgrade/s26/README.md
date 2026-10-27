# s26 — Yulong matrix execution

Execution base: `5dea2d8576db7b725593b08a64a0d28315b75590`.
Branch: `feat/roster-sampling-matrix`; PR #49. One additional fighter, unchanged
harness, inputs and fail-loud coverage gate. No runtime/importer changes.

## Results

- Yulong (`yulong`): **324/324** passed; **39,528** actor observations.
- Full coverage check exits 0. Removing one case result while preserving the
  success summary exits 1; restoring the exact report bytes passes again.
- **35/35** focused tests; integrity and handoff passed.
- Separate campaigns across s01/s03–s26: **26/26 fighters, 8,424/8,424 cases**.
  Previously proven fighters were not rerun. This completes cumulative execution coverage, not a single-tip full-roster rerun.

`acceptance.json` records counts, campaign hash and no remaining fighters.
`yulong-report.json` records every case result. Representative ground/air tapes
and compressed traces are retained; bulk outputs remain scratch artifacts.

## Reproduction

Godot `4.7.2.stable.official.ed1daf0bf`, headless; use fresh directories:

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-sampling-s26-yulong --fighters yulong
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-sampling-s26-yulong \
  --output /tmp/bvn-sampling-s26-yulong-run \
  --godot /tmp/bvn-loud-fail/r02/engine/Godot.app/Contents/MacOS/Godot
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-sampling-s26-yulong \
  --output /tmp/bvn-sampling-s26-yulong-run
python3 -m unittest tools.tests.test_sampling_matrix tools.tests.test_move_cases_paths \
  tools.tests.test_move_cases_targets tools.tests.test_move_acceptance_harness
```

The matrix retains six action keys × nine directions × ground/air × three
starting distances, with 61 root observations of both actors and root position.
The negative proof mutates only the scratch report, not inputs or native references.

## Known follow-ups

Same-input native capture, global hitboxes, child display
lists, full camera, exact BitmapData comparison and DoAction execution coverage
remain follow-ups. Execution coverage is not Flash parity or proof every requested
move triggered. `production_admitted=false`, `native_parity_proven=false`.
No native capture, Web build, merge, deployment, Worker change or allowlists.

These known gaps are follow-ups, not merge blockers for this execution-evidence slice.

Jinye/Yijiao sampler residuals remain documented known gaps in
[IMPORTER_KNOWN_GAPS.md](../../../docs/IMPORTER_KNOWN_GAPS.md); this execution
slice does not claim to resolve them, and they do not block this slice.

## Cumulative report inventory

`roster-report-inventory.json` checks all 26 archived reports against the existing
26-fighter generated case-ID set: 8,424 unique cases, no missing or duplicate
cases, no reported execution errors. This reads historical reports only; previously
proven fighters and their bulk traces were not rerun or revalidated at this tip.
`full_roster_execution_complete=true` is cumulative execution evidence only;
`native_parity_proven=false` and `production_admitted=false` remain unchanged.
