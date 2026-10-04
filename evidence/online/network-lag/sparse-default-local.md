# Online sparse checkpoints by default — 2026-10-04

Online matches now default to sparse saving with prediction stride two. Battle
logic, inputs, authored timers and diagnostics still execute every frame. The
existing rollback algorithm and checkpoint encoding are unchanged. Mandatory
control/KO snapshots and periodic hash/recovery checkpoints remain exact.
Offline rollback sessions retain their original defaults. Host pacing stays off.

The user's P1/P2 browser reports both identify commit `6a64b043` and the same
PCK. Their last cumulative samples cover about 95 seconds: 27.90/27.82 Hz,
10.57/12.73 ms per save, and P1 83 corrections / 438 replayed frames. Both had
`sparseSaves=false`, `checkpointStride=1`. The reports are bounded captures, not
complete replay tapes. The attached [JSON](sparse-default-local.json) records
source file hashes and the selected performance samples without copying raw logs.

## Baseline and measured change

Sequential ABBA native Godot 4.7.2 runs use the unchanged 330-frame delayed-input
workload with batching and deferred presentation enabled on both sides. Only
`--sparse --stride-two` changes. All eight runs compare the final full state to
their no-late-input reference; no baseline, tape or tolerance changes.

| Fixture | Full-save wall time (ms) | Sparse stride-two wall time (ms) | Mean reduction |
|---|---|---|---|
| Naruto/Ichigo | 5245.377, 5258.830 | 3965.829, 4040.498 | 23.8% |
| Byakuya/Lee | 7809.326, 7213.367 | 4814.870, 4934.000 | 35.1% |

Each workload reduces saves from 371 to 184, with six corrections unchanged and
replayed frames increasing from 40 to 44. The second fixture has substantial
wall-time and correction-tail variability; 35.1% is this run's observation,
not a browser estimate. Even optimized corrections can exceed 33 ms. Production
browser performance and the user's eventual subjective comparison remain pending.

## Storage-only scope and fallback

This promotes the existing storage policy; it does not alter frame scripts,
PlaceObject/MOVE lifetimes, label exits, damage, combo accounting or any other
source mechanic. Source execution continues on each frame. Source-first evidence
and unchanged reference tapes remain those documented in
[the stride experiment](lag12-stride-local.md) and
[replay presentation](replay-display-local.md). No new Flash parity claim is made.

`?online_sparse=0` disables sparse saving for comparison. `?online_stride=1`
selects the conservative sparse stride; `?online_sparse=1&online_stride=2`
explicitly selects the new default. Missing/invalid parameters preserve the
configured policy. Native fallbacks are `--online-full-saves` and
`--online-checkpoint-stride-one`. These local options do not modify the agreed
input delay or prediction window, and are reported in performance telemetry.

Validation includes default, mixed sparse/full and full/full paired battles;
exact state hashes, pause/resume, recovery, timeout, KO/result and new epochs;
sparse correction graph comparisons on both rosters; timer rounds, startup
cancellation, terminal room handling and performance diagnostics. See the JSON
for executed checks and command lines. Large raw logs and temporary exports
remain under `/private/tmp/bvn-sparse-default-20261004`.

The complete clean-copy Web build also passed import, lobby tests, export,
post-export compatibility checks and final PCK verification. PCK SHA-256:
`e7d7d5e5d594ead90b3cc7be0828b26068594d55480558c205d88e1755e351bb`.
This temporary artifact includes this working-tree change over the recorded base
commit; it is not the deployed artifact. Repository verification, handoff, six
schema/example validations, manifest checking and seven manifest tests passed.
Locked `game/` and `scripts/` inputs are unchanged.
