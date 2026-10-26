# s04 — Renji matrix execution

Execution base: `7dc2b0a5cb81e79c88bd104acf9139577b67af3f`.
Branch: `feat/roster-sampling-matrix`; PR #49. One additional fighter only,
with unchanged harness, input setup and strict execution-coverage checks.

## Reproduction

Godot `4.7.2.stable.official.ed1daf0bf`, headless; use fresh output directories.

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-sampling-s04-renji --fighters renji
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-sampling-s04-renji \
  --output /tmp/bvn-sampling-s04-renji-run \
  --godot /tmp/bvn-loud-fail/r02/engine/Godot.app/Contents/MacOS/Godot
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-sampling-s04-renji \
  --output /tmp/bvn-sampling-s04-renji-run
python3 -m unittest tools.tests.test_sampling_matrix tools.tests.test_move_cases_paths \
  tools.tests.test_move_cases_targets tools.tests.test_move_acceptance_harness
```

The 324 cases cover six action keys, nine directions, ground/air and three starting
distances. Each case has 61 observations of both actors and root camera position.
See `acceptance.json` for final measured counts and `renji-report.json` for all
case results. Representative ground/air tapes and compressed outputs are retained;
bulky generated campaigns and engine files remain scratch artifacts.

## Results

- Renji **324/324** passed, **39,528** actor observations; full coverage exit 0.
- Missing-case negative exits 1 despite the preserved success summary; restoring
  the original report passes again. Exact diagnostics are retained in text files.
- **35/35** focused tests, integrity and handoff passed.
- Across s01/s03/s04: **3/26 fighters**, **972/8,424 cases**. These are separate
  executions, not a full-roster or native parity run. No Web/runtime changes.

## Negative check

Remove one result from the completed scratch report while preserving its summary
success flag. The unchanged coverage gate must exit 1. Restore the exact report
bytes and verify the complete campaign again. No native references are changed.

## Known follow-ups

Deidara and Chad were proven separately in s01/s03 and are not rerun here. Remaining
fighters are listed explicitly in `acceptance.json`. Execution coverage is not
Flash parity or proof that every requested move actually triggered. Same-input
native capture, global hitboxes, child display lists, full camera, BitmapData
exact comparison and DoAction execution coverage remain follow-ups, not review
blockers for this evidence slice. `production_admitted=false` and
`native_parity_proven=false`; no runtime/importer change, merge or deployment.
