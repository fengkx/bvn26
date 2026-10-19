# Coordinator handoff — fresh three-fighter sample audit

Runtime tip SHA: `2d3336bf039e7ad0ac92c22423273f664b432225`.
Branch/worktree: `audit/sample-new-chars` at
`/Users/fengkx/me/agent-code/bvn2_6-sample-new`.
PR: pending creation after evidence validation.

| Fighter | Existing + adversarial cases | States | 14-field parity | First divergence |
| --- | ---: | ---: | --- | --- |
| Orochimaru | 8 + 4 = 12 | 5,784 | 12/12 matched | None |
| Jiraiya | 10 + 3 = 13 | 6,266 | 13/13 matched | None |
| Pain | 10 + 5 = 15 | 7,230 | 15/15 matched | None |
| Total | 28 + 12 = 40 | 19,280 | 40/40 matched | None |

All 28 existing fixtures were freshly captured, not replayed only against old
Flash artifacts. Each new source state sequence also equals its old PR sequence.
`comparisons.json` contains new UTC timestamps, run IDs, raw and canonical hashes,
actual trigger observations and null first divergences.

## Gin-class findings

- Real preparation hits are exercised for Orochimaru and Pain (super tick 15,
  hurt tick 16, HP 960 at tick 17). Mirrored cancels and guard/break receive are
  exercised for all three. Pain's actual ordinary-super cancel is frame 357→600;
  its unsupported first-normal cancel is explicitly retained as a negative.
- Jiraiya's preparation attack is a protected negative: the source removes
  `bdmn` at each super entry. Both engines keep HP 1000 and finish the super;
  this is not falsely reported as a successful interruption.
- **A real freeze is reproduced in both Flash and Godot:** interrupt preparation,
  then let Ichigo cancel immediately into super. Both Orochimaru and Pain remain
  paused through tick 240; each actor has 216 paused observations. The final
  fighter frames are Orochimaru 1108 / Pain 1187, versus Ichigo 463. These are
  exact parity cases but do not establish that gameplay is free of Gin-class
  deadlocks. No divergence was hidden or relabeled as a pass of recovery.
- The explicitly retained `_clear_interrupted_super_preparation` deviation is
  unchanged (544-byte SHA-256 `d39b2b50d96d37ac717e1d1e8e9ccd711a67f6bbadcee6afc30593d6e0caa91e`).
  Its direct-call smoke passes; it does not recover the two end-to-end sequences
  above. Extending that behavior would be an additional intentional Flash
  deviation, not a fix to a state-parity mismatch found by this audit.
- Fresh existing cases cover Jiraiya warp/rush/upper-super and Pain repeated
  facing warp/attraction. Coordinates, facing, source frames and pause agree.
  All three source wrapper matrices and every timeline placement/change match
  packaged data. Masked source frames were exercised; pixels, audio, full AI
  and browser rendering remain unaccepted.

## Changes, package identity and checks

No production runtime, compiler or character data fix was necessary or made:
there were no Flash/Godot differences in this sample. The PR contains fresh
fixtures, compressed traces/provenance, source review, reports and status links.
Milestones remain pending. No stale-checkout edits, manual Flash/Chrome UI,
Worker/Vercel deployment or merge occurred.

The live `https://bvn26.vercel.app/` PCK matches its published SHA-256 and reports
master `2d3336bf`. In an empty temporary Godot project, all 42 fighter JSON
resources match this worktree byte-for-byte. The post-import master content
fingerprint also equals the live fingerprint. The checked-in manifest differs
because import adds one Orochimaru script UID; the build fingerprint includes
the staged template path and was not independently reproduced. Full evidence
is in `live-package.json`.

Fresh shared `interrupted_super_lock_smoke`, `player_visual_smoke` and
`player_controller_smoke` pass. Locked-input and handoff checks and the retained
trace verifier are recorded in final validation logs. The initial native batch
timeout and sandbox preflight rejection were excluded, preserved and resolved;
no fight duration or comparator tolerance changed.

Evidence root: `evidence/characters/_audit-sample-2026-10-19/`.
Key files: `README.md`, `checks.json`, `comparisons.json`, `execution.json`,
`source-review.json`, `geometry-source-check.json`, `live-package.json`,
`cases/`, `traces/`, `source-builds/`, `instrumentation/`, `logs/`, `recheck.py`.

Measured session wall time through packaging: 1644 seconds. No person-day estimate is inferred.
