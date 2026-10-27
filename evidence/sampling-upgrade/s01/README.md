# s01 — deterministic roster input matrix and execution coverage

Base: `6e2cc2a6777aee032023ee562160a42ac0e7c444` (PR #48 ready for review).
Follow-up branch: `feat/roster-sampling-matrix`. No production/runtime/importer change.
`production_admitted=false`; native parity is not claimed.

## Design and actual scope

See [sampling design](../../../docs/SAMPLING_UPGRADE.md). The new CLI generates
26 shipped fighters × six action keys × nine absolute directions × ground/air ×
three explicit starting separations = **8,424 cases**. Fighter subsets retain the
same 324-cell Cartesian product. Every generated case is executable by the existing
fresh-fight `move_case_reference.gd`, not an invented move-name expectation.
The generator pins the selection catalog and tapes. `check` recomputes the matrix,
checks tapes and reads every expected trace; it does not trust a summary pass flag.

A case has 61 root observations of both actors and root camera position. Before
applying the tested input, tick 10 must show the requested ground/air condition.
Air preparation is an actual jump input, never a forced height. Near/mid/far mean
explicit 50/150/300 starting separation, not a claim about native reach.

## Reproduction

Run from the repository root with Python 3.10+ and fresh output directories:

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-sampling-s01
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-sampling-s01 \
  --output /tmp/bvn-sampling-s01-run --godot /path/to/godot \
  --cases didala__dash__neutral__ground__near didala__dash__neutral__air__near
# Expected exit 1: a two-case smoke run cannot satisfy an 8424-cell campaign.
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-sampling-s01 \
  --output /tmp/bvn-sampling-s01-run

python3 -m tools.sampling_matrix generate --output /tmp/bvn-sampling-s01-didala --fighters didala
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-sampling-s01-didala \
  --output /tmp/bvn-sampling-s01-didala-run --godot /path/to/godot
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-sampling-s01-didala \
  --output /tmp/bvn-sampling-s01-didala-run
python3 -m unittest tools.tests.test_sampling_matrix tools.tests.test_move_cases_paths \
  tools.tests.test_move_cases_targets tools.tests.test_move_acceptance_harness
```

Engine used: Godot 4.7.2 at
`/tmp/bvn-loud-fail/r02/engine/Godot.app/Contents/MacOS/Godot` (headless).
No native Flash capture was performed or reference environment changed.
Generated campaigns and bulky engine output remain scratch artifacts; committed
summaries and representative compressed traces record this run. See `acceptance.json`
for final counts and negative-gate outcomes, `focused-tests.txt` for unit regressions.

## Results

- Generated full roster: 8,424 cases; only the named two-case smoke executed in that campaign.
- Complete Didala subset: **324/324**, **39,528** actor observations; camera and
  input-time posture validation passed. `check` exit 0, see `full-subset-coverage.txt`.
- **33/33** focused tests; includes all 324 tapes accepted by the existing native
  fixture encoder (encoding only, not native execution).
- Real-output negative: delete tick-10 P1 observation from a completed trace;
  `check` exit 1 with exact case ID. Original bytes restored and check passed again.
- Integrity, handoff and six schema/example contracts passed. No full Web build or
  227-case roster replay rerun: this slice changes tools/docs only, not production data/runtime.

## Failures must remain visible

The full-roster check on only two executed cases rejects with
`incomplete matrix execution coverage` (see `missing-coverage.log`). Unit negatives
also delete a frame, duplicate another while retaining the total length, remove a
camera observation, remove a matrix cell, edit a tape, emit NaN, and fail air setup.
These are intentionally rejected; they are not production Flash mismatches or
new allowlist entries.

## Remaining work / next slice

This is **execution coverage**, not behavioral or pixel acceptance. It does not
observe whether a requested special move really entered its source label. Full
roster execution, native replay of the same generated tapes, source/engine artifact
provenance, timer/random tapes, richer initial states, direction-only inputs,
per-frame global hitboxes and full child display lists are still open. Existing
camera output is root x/y only. Exact native BitmapData comparison and actual
DoAction/clip-action execution coverage are not implemented by this slice.

Next: connect one generated ground/air pair to the existing native move capture
route with identical initialization and input timing. Require complete native state
and camera records, compare those exactly, and expose missing native observations
as a separate failing gate before widening captures. Add source-addressed geometry
and execution events at that same observation phase; static source inventory is not
execution coverage. Do not resume unbounded Jinye pixel experiments or reopen PR #48.
