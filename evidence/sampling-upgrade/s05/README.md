# s05 — Lee and Neji matrix execution

Execution base: `428d6dcc2cf791003e79bd587ca7d08b4b0406bc`.
Branch: `feat/roster-sampling-matrix`; PR #49. Exactly two additional fighters:
Lee (`lee`) and Neji (`neji`), each in a separate unchanged 324-case campaign.
The existing runner processes each campaign sequentially; the two independent
Godot processes run concurrently. No harness, gameplay or input changes.

## Reproduction

Godot `4.7.2.stable.official.ed1daf0bf`, headless. For each fighter, use fresh paths:

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-sampling-s05-lee --fighters lee
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-sampling-s05-lee \
  --output /tmp/bvn-sampling-s05-lee-run \
  --godot /tmp/bvn-loud-fail/r02/engine/Godot.app/Contents/MacOS/Godot
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-sampling-s05-lee \
  --output /tmp/bvn-sampling-s05-lee-run
# Repeat the same three commands with lee replaced by neji.
python3 -m unittest tools.tests.test_sampling_matrix tools.tests.test_move_cases_paths \
  tools.tests.test_move_cases_targets tools.tests.test_move_acceptance_harness
```

Each campaign covers six action keys × nine directions × ground/air × three
starting distances, with 61 root observations for both actors per case. Final
counts, exact remaining roster and campaign hashes are in `acceptance.json`.
Per-case results and representative ground/air tapes and traces are retained.
Bulk generated inputs and engine output remain scratch artifacts.

## Results

| Fighter | Passed / expected | Actor observations | Coverage exit | Missing-case exit |
| --- | --- | --- | --- | --- |
| Lee | 324 / 324 | 39,528 | 0 | 1 |
| Neji | 324 / 324 | 39,528 | 0 | 1 |

Both restored reports pass again. **35/35** focused tests, integrity and handoff
passed. Across s01/s03/s04/s05: **5/26 fighters, 1,620/8,424 cases**, in separate
campaigns. This is not a full-roster or native parity run. No Web/runtime changes.

## Negative checks

For each completed campaign, remove one case result from the scratch report while
retaining its summary success flag. The coverage gate must exit 1. Restore the
exact original report bytes and recheck the full campaign. These mutations affect
only scratch reports, never native references or expected outputs.

## Known follow-ups

Prior Deidara/Chad/Renji results are separate s01/s03/s04 evidence, not rerun here.
Remaining fighters stay follow-ups. Execution coverage does not establish native
Flash parity or prove that every requested move triggered. Same-input native
capture, global hitboxes, child display lists, full camera, BitmapData exact
comparison and DoAction execution coverage remain open. `production_admitted=false`
and `native_parity_proven=false`; no merge, deployment, Worker change or allowlists.
