# LAG-04 local evidence

Status: deterministic simulator correctness checks passed for the six recorded scenarios. **Field calibration did not pass**: the slow-host comparison did not reproduce the measured ~14 Hz field behavior or its correction/wait pattern. Costs remain provisional; no constants were tuned to force that result.

Environment: Godot `4.7.2.stable.official.ed1daf0bf`, headless macOS. Godot printed a macOS system CA `noErr` warning in these runs. The self-test and pair smoke exited 0; the six-scenario invocation itself exited 1 at output-file creation, as described below.

## Simulator and evidence

The virtual network uses separate seeded delay/loss streams for each sender direction. Reliable packets are never dropped and are clamped to preserve order; the `input` channel can lose or reorder independently. The self-test exercises reliable delivery under sampled inverted jitter, unordered reordering, and loss of one unordered packet without blocking its successor. Per-channel sequence metadata is used for these checks while the extracted fixture retains the original globally increasing envelope `seq`.

Cost units are microseconds per **delta count** from the cumulative `RollbackSession.profile_counters()` API. Normal `advance` and `replay_advance` are exclusive. Every `save_count` is charged once, including replay saves; `replay_save_count` is a subset and is not charged again. Load and presentation rebuild have separate units. The provisional slow-host inputs are 9,979 µs/advance, 20,543 µs/save, and 22,071 µs/load. The fast-host inputs are 5,260 µs/advance and 9,458 µs/save. These are estimates derived from the old aggregate step/checkpoint logs: those logs do not separate load from presentation rebuild, so the slow-host load estimate is a blended correction residual and the rebuild weight is zero. Validation/copy counts are exposed but have zero separate weight because the old aggregate step already includes them. This model is unsuitable as a calibrated performance baseline.

The scheduler models 30 Hz caller ticks. Every send during one drain and its following `process_tick` receives that tick's fire time; work is charged after the call, so CPU time inside the callback does not delay individual sends. Caller ticks during `busy_until` merge. Per-operation costs are fixed means and omit measured variance. These are explicit approximations, not a browser event-loop reproduction.

The run uses input delay 2, so the sampled local input is scheduled two frames (about 66.7 ms) ahead. At 40 ms RTT the slow-host run had no late input, no rollback, and no input/clock-wait pattern matching the field trace. Its nominal slow-host advance plus save cost is 30.522 ms per tick, below the 33.333 ms caller interval; the observed logical rates consequently remained 30.0/29.9 Hz. The old logs also lack the load/rebuild split and a field-comparable arrival-lead distribution. These observations explain why this model fails calibration; they are not grounds to adjust the costs to target 14 Hz.

`lossy` configures 3% loss only for `input` packets, but current product `OnlineMatch` traffic uses only `reliable`. It sent zero input-channel packets, so this scenario observed zero input loss and does not establish product input-loss behavior. The channel behavior itself is covered only by the synthetic network self-test. `turn40-fixedskip` is a fixed-skip control and is not evidence for work-cost improvements.

Six 10-second JSONL records, copied verbatim from the simulator's printed output, are in [simulator-baseline.jsonl](simulator-baseline.jsonl). All six report `ok=true`, equal common hashes (at least seven per scenario), reliable conservation, and zero reliable-order violations:

| Scenario (seed) | Logical rate, P1/P2 | Corrections, P1/P2 | Equal common hashes | Boundary |
| --- | ---: | ---: | ---: | --- |
| `lan` (40401) | 30.0 / 29.9 Hz | 0 / 0 | 9 | P1 frame 300 is a one-sided pending tail |
| `turn40` (40402) | 30.0 / 29.9 Hz | 0 / 0 | 9 | P1 frame 300 is a one-sided pending tail |
| `turn40-slowhost` (40403) | 30.0 / 29.9 Hz | 0 / 0 | 9 | Calibration not passed; correction/wait pattern absent |
| `turn40-fixedskip` (40404) | 25.0 / 25.0 Hz | 0 / 0 | 8 | Fixed-skip control only |
| `turn100` (40405) | 24.1 / 23.8 Hz | 21 / 0 | 7 | Corrections occur only on P1; still not the ~14 Hz field pattern |
| `lossy` (40406) | 30.0 / 29.9 Hz | 0 / 0 | 9 | Zero input-channel packets; no observed input loss |

The `lan` 10-second run was repeated with seed `40401`. Its stable projection—scenario, seed, virtual scheduler/network totals, common hashes, profile counts, and match wait/sync totals—was identical after excluding the monotonic clock origin and measured `*_us` timings. Those timings vary with host load and are not optimization evidence. The shorter 3-second LAN attempt exited 1 at the three-common-hash minimum: frames 30 and 60 matched while frame 90 was a one-sided pending tail, so it was insufficient progress rather than a divergence.

The initial all-scenario command was:

```sh
Godot --headless --path godot --log-file /private/tmp/lag04-all-10s.log \
  -s res://tests/online_lag_simulator.gd -- --all --duration-ms=10000 \
  --record=res://evidence/online/network-lag/simulator-baseline.json
```

That process **exited 1**, after printing all six successful scenario result lines, because `res://` is rooted at the `godot/` project and the requested output path was not the repository-level evidence directory. The six printed JSON records were recovered without rerunning scenarios and stored verbatim as JSONL at the linked baseline path. Record handling now resolves paths before running, creates the parent directory, and probes write/readback/cleanup. The final `--self-test` verified this helper using `/private/tmp`; the all-scenario command was not rerun, and its original process exit remains 1.

## Verification

- `Godot --headless --path godot --log-file /private/tmp/lag04-self-test-final-r2.log -s res://tests/online_lag_simulator.gd -- --self-test` — exit 0. Network semantics and record write/readback/cleanup all passed.
- The all-scenario invocation above — exit 1 due only to the record-path failure after all six result lines were printed. Each result itself has `ok=true`; this is not reported as a successful process exit.
- `Godot --headless --path godot --log-file /private/tmp/lag04-pair-smoke-final.log -s res://tests/online_match_pair_smoke.gd` — exit 0 after fixture extraction and global sequence correction. Original markers passed for startup, bootstrap correction (`frame=15`, P1 rollback count 2), ordered intro skip, fight hashes through frame 327 with a real hit, pause/resume barriers, short recovery, timeout abort, result commit, and new epoch. No `SCRIPT ERROR` was found. The log also contains existing exit-time ObjectDB/resource-use warnings.
- `git diff --check` — run after evidence finalization.
