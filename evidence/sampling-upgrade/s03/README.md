# s03 — Chad matrix execution

Execution base: `452297306844fd96e63e164a39886f19fa14af32`.
Branch: `feat/roster-sampling-matrix`; PR #49. This slice adds one fighter's
execution evidence only; no harness or gameplay changes.

## Scope and reproduction

Chad (`chad`): six action keys × nine directions × ground/air × three starting
distances = 324 cases, each with 61 root observations for both fighters. The
unchanged s01 tape setup and strict posture/trace/coverage checks apply.
Godot: `4.7.2.stable.official.ed1daf0bf`, headless.

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-sampling-s03-chad --fighters chad
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-sampling-s03-chad \
  --output /tmp/bvn-sampling-s03-chad-run \
  --godot /tmp/bvn-loud-fail/r02/engine/Godot.app/Contents/MacOS/Godot
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-sampling-s03-chad \
  --output /tmp/bvn-sampling-s03-chad-run
python3 -m unittest tools.tests.test_sampling_matrix tools.tests.test_move_cases_paths \
  tools.tests.test_move_cases_targets tools.tests.test_move_acceptance_harness
```

Use fresh output directories. `acceptance.json` records final measured counts;
`chad-report.json` retains each case result. Representative ground/air traces and
input tapes are compressed/preserved here; bulk engine outputs stay in scratch.

## Results

- Chad **324/324** passed; **39,528** actor observations; coverage check exit 0.
- Missing-case negative exits 1 even with the original summary success flag;
  restored report passes again (see the three coverage text files).
- **35/35** focused tests; integrity and handoff passed.
- Total evidence across s01 and s03: **2/26 fighters**, **648/8,424 cases**.
  This is not a single full-roster run or native Flash validation.
- No harness/runtime changes; no Web build or native capture rerun.

## Negative coverage proof

After the completed run, remove one case result from the scratch report, leaving
the summary success flag unchanged. `check` must exit 1 with incomplete matrix
coverage. Restore original report bytes and rerun the full check. This does not
modify a native reference or relax any threshold.

## Remaining follow-ups

Execution is not native Flash parity or proof that every requested move triggered.
Deidara was proven separately in s01; this slice does not rerun it. The other 24
shipped fighters remain follow-up work, not a prerequisite to reviewing this slice.
Same-input native capture, global hitboxes, child display lists, full camera,
BitmapData exact comparison, and DoAction execution coverage remain open.
`production_admitted=false`; no merge, deployment, Worker change, or native capture.
