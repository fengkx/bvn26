# Online 30 Hz performance acceptance

This evidence tracks whether the rollback battle can keep up with its 30 Hz
logical clock while preserving the complete simulation graph. A burst benchmark
measures operation cost; it does not establish real-time cadence or browser
frame rate.

## Acceptance gate

The browser gate is a normal, visible paired Chromium match on one
machine, held in the foreground for at least 60 measured seconds. Record both
peers and include their browser and engine versions, source/PCK hashes, display
configuration, and relevant machine load. Do not run another CPU-heavy test
during the capture.

For each peer, record logical frames advanced per wall-clock second, one-second
frontier and confirmation samples, prediction backlog, time spent waiting,
correction count, frames replayed, and correction cost. Report p50/p95/p99 and
the longest observed tick/correction stall. The normal logical step p95 target
is 25 ms. A passing run must sustain 30 logical ticks per second without a
frontier backlog that continues to grow. Keep renderer/audio and transport
measurements visible alongside simulation cost; report maximum rollback-window
replay cost separately. Track live retained state using O(1) container sizes
(`RollbackSession._states`, checkpoint `_snapshots`, `_snapshot_graphs`,
`_constants`, `_constant_values`, `_constant_keys`, and `_retired`). Keep these
separate from cumulative checkpoint save counters. Do not serialize retained
history during the timed run to estimate its size.

Run each source against the same fixture, input tape, random seed, intro event
schedule, engine, export settings, and browser procedure. Compare full graph
traces before interpreting any speedup. Current graph parity evidence is
recorded with each run; a matching checkpoint hash alone is insufficient.

Two fixtures are required: the default Naruto/Ichigo pairing and the observed
Hitsugaya/Sasuke pairing with the configured `you` and Gaara helpers on 现世.
The latter uses a sanitized, partial 222-tick input sample from the supplied
browser log. It retains both player slots exactly for the captured range and is
representative input, not a complete fight replay. The configured helper name
`鼬` maps to the `you` asset; see the roster table and the captured runtime
resource path rather than inferring this from the English label. The supplied
sample contains movement, down, and three attack ticks; it has no assist or
super activation. Assist/super acceptance must use their separate recorded
action fixtures and documented energy preconditions.

Passing these two pairings is a focused performance result. It does not close
the all-content NET-026 gate, prove every move/character, or establish public
internet, NAT, or TURN behavior.

## Frozen sources and fixtures

| Label | Source | File count | SHA-256 tree | Purpose |
|---|---|---:|---|---|
| Baseline | commit `a17e361bec5081495b3a5c7a34923b44f6efc90a`, frozen at `/private/tmp/bvn26-performance-baseline-a17e361b/godot` | 20,834 | `5983354e90f1669d877a92bbdfc57cbe8c978794bc6d8210d4971124578602d1` | Pre-optimization reference |
| First-round candidate | same base commit plus uncommitted first-round checkpoint changes, frozen at `/private/tmp/bvn26-performance-candidate-round1/godot` | 20,836 | `814e66b5a9b982264efd6e39453b6cb5f30a13568cb3fac29e08cfa2d2c2e887` | Immutable first-round comparison source |
| Combined candidate | round-2 final snapshot plus current `battle_checkpoint.gd` and `main.gd`, frozen at `/private/tmp/bvn26-performance-candidate-round3-userfixture/godot` | 20,839 | `c5505dae3bd053b8d05dfc4c08ca99f990d0277e6e07c0cfcaed2dad9c6d7094` | Current native and Web user-log comparison source |

The repository retains compact summaries for the baseline
([frozen-baseline.json](frozen-baseline.json)), first-round candidate
([first-round-candidate.json](first-round-candidate.json)), and round-2
candidate ([round2-candidate.json](round2-candidate.json)). Each summary keeps
the source revision, freeze time, file count, tree identity, key runtime file
hashes, absolute frozen-source and full-inventory paths, and inventory checksum.
The full per-file inventories are preserved byte-for-byte beside their frozen
source trees under `/private/tmp`; the original inventory-generation commands
were not recorded. Each summary includes the exact command to validate its
preserved JSON and checksum. The sanitized recorded input is
[hitsugaya-sasuke-you-gaara-input-r01.json](hitsugaya-sasuke-you-gaara-input-r01.json).
The first-round graph comparison captured 331 checkpoints from each source;
both traces were 158,996,470 bytes and had SHA-256
`b0227f7af37d10b220bcddcbdc0a73429f31b76c0d1d125c5b81f154897db17b`.

## Measured results

The following earlier browser numbers came from the valid full-shell Web
profile at `/tmp/bvn-lag-web-profile`, using Godot 4.7.2 and the representative
330-frame Naruto/Ichigo fixture. The initial profile with missing JavaScript
shell bridges is excluded. These measurements are synchronous burst costs, not
wall-clock 30 Hz acceptance:

| Operation | Observed value | Scope |
|---|---:|---|
| Battle advance | 21.0 ms mean | 330 measured frames |
| Rollback session step, no late inputs | 62.6 ms mean; 82.2 ms p95 | Zero corrections; session step includes checkpoint work |
| Complete checkpoint | about 42 ms | Isolated checkpoint observation; percentile not retained |

The frozen-baseline native `rollback_battle_smoke` completed with
`frames=330`, `rollbacks=10`, `replayed=65`, `waits=15`,
`elapsed_ms=10925`, `retained_bytes=5798152`, and
`sounds_suppressed=8`. It ended with
`ROLLBACK_INDEPENDENT_RUN_OK frames=330 full_state=true`. Godot emitted the
known macOS certificate lookup warning and headless audio shutdown leak records;
there were no script, parse, or assertion failures.

The first native A/B run is retained in `native-initial-r01.json` as a
diagnostic only. It had no warm-up and ran baseline before candidate. Its
battle-only p95 moved from 148.28 ms to 15.24 ms even though the first-round
changes target checkpoint work. The baseline maximum was 991 ms. This large
unexplained shift shows machine/cache non-stationarity; do not infer a gain
from it. A warmed ABBA screen is in `native-warmed-abba-r02.json`.

The final round-2 candidate restores the generic immutable-constant identity
scan after the typed prototype is registered. It was frozen as a one-file
overlay on the round-2 snapshot in `round2-final-candidate-overlay.json`; the
replacement `battle_checkpoint.gd` SHA-256 is
`c95630c37680922618d985ad980717fd882b587ad6180de644c3647601500c23`. Its
331-frame checkpoint graph matches the frozen baseline byte-for-byte.

The sequential 330-frame Web burst build metadata is recorded in
`web-build-user-log-r01-final.json`; its timing values were transcribed from
the root-read browser `#report` DOM. Two 60-second local WebRTC captures were
also run for the representative user-log fixture.

The original user run log recorded the Hitsugaya/Sasuke pairing on 现世 from
fight tick 51 through 208 in 29.503 seconds: 5.32 logical ticks per second,
183 ms median tick cost, and 248 ms p95. It later recorded a six-second hidden
period. The window was closed before the timeout. This is the reported failure
signal, not a controlled benchmark; it does not isolate the cause or pass the
60-second browser gate.

## Paired real-time browser result

The visible Codex IAB (Chrome 153, DPR 2) ran two same-machine peers on
different local origins with loopback Worker signaling and connected WebRTC
data channels. Renderer-process separation was not verified; ICE servers were
empty, so this is not public-internet/NAT/TURN coverage.

With d0/p2, the peers advanced 1,634/1,632 frames in about 60 s (27.23/27.18
Hz): one-second p50 was 28.18/28.21, p5 was 22.37/21.36, and five-/ten-second
rolling p5 stayed near 24 Hz. There were no zero-progress windows, but sampled
step maxima reached 69.4/62.6 ms; host input wait was 4.045 s and guest clock
wait 4.947 s. The one d2/p6 comparison was near 30 Hz for 18 s, then fell to
16.62/16.71 Hz over 61.8/61.3 s; late step maxima reached 1.124/0.988 s. Both
pages stayed visible and connected, with no reported errors, corrections, or
replay; host input wait was 4.508 s and guest clock wait 3.877 s.

Immediately after d2/p6, system load was 31.03/29.29/16.08 on 8 CPUs with
14,540.31/15,360 MiB swap used. This was a post-run snapshot, not a continuous
trace; a Python-only 17 s report calculation may also have overlapped capture.
These are possible confounders, while runtime/state growth is not ruled out, so
the run does not identify the cause. Keep production at d0/p2: d2 adds about
66.7 ms of input latency and changed prediction window at the same time. Raw d0 and d2
reports are preserved at `/private/tmp/bvn-online-performance-60s/web-paired-60s-d0p2-raw.json`
(SHA-256 `a1c856fe83c2c1b5acbc12ceb4ee0851928263f6b86e9f6d9def440b57c3d018`)
and `/private/tmp/bvn-online-performance-60s/web-paired-60s-d2p6-raw.json`
(SHA-256 `69accbe798dbbd7c21b6c69d0885c1823a0c4d7fd97bfb89e013da2c4499e10a`).
The 330-frame burst comparison separately reduced mean receive-plus-step by
11.47% and checkpoint encoding by 26.64%; the paired 30 Hz gate remains
**not passed** and these runs do not close NET-026 or exercise assists/supers.

The 2026-09-24 user-log diagnosis and rejected checkpoint experiments are
recorded in [round 3 checkpoint profiling](round3-checkpoint-profiling.md).

The focused 2026-09-24 native checkpoint profile is documented in [checkpoint micro-profile](checkpoint-microprofile-2026-09-24.md), with raw counters and run hashes in the [structured record](checkpoint-microprofile-2026-09-24.json). No checkpoint optimization was accepted, and the browser 30 Hz gate remains **not passed**.

The deterministic [TURN buffer scheduling model](turn-buffer-model.md), with all nine cases in the [structured result](turn-buffer-model.json), tests injected 50/100/150 ms RTT plus fixed jitter while preserving the guest authoritative-clock gate and reliable ordering. Its rates are a scheduling upper bound, not measured FPS or evidence of TURN relay use. New lobbies now initialize at d2/p6 (about 67 ms of input delay at 30 Hz) to reduce waiting in higher-latency sessions; users can adjust the setting, and both peers must agree on a profile.
