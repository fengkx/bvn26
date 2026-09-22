# Online acceptance and measurement plan

Status: Proposed engineering gates for final design review. No test result is
claimed here. Use desktop Chrome for the first online trial, with recorded exact
browser/OS versions and independent computers/networks.

Execution is tracked by [48 implementation tasks](TODO.md). Local backend probes
are specified separately in [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md); SQLite
persistence tests do not substitute for browser rollback or real network tests.

## Correctness gates

- Every [enabled entry](CONTENT_SCOPE.md) remains available and has an explicit
  action/lifecycle coverage record. Frozen build/content/state versions match.
- Independent simulation runs receive the same setup, controls and controlled
  external events. Every compared confirmed frame has identical canonical complete
  state. A mismatch is a failure, not a tolerance to average away.
- Save/restore/re-simulate tests cover frames before/during/after spawn, removal,
  helper attacks, hit/block, simultaneous contact, supers, gameplay freezes,
  timer callbacks, KO and round transitions. Preserve all hidden causal state.
- Corrected confirmed state equals a no-network baseline under delayed/lost/
  duplicated/reordered inputs, including burst loss and late releases. Reject
  conflicting same-frame input and packets from prior match epochs.
- Source fixtures and input tapes remain unchanged; local-mode and relevant
  original-reference regressions pass. This does not promote partial parity claims.
- Source-first five-question audits precede scheduler/runtime changes. If a source
  clock or callback rule is unresolved, record the blocker instead of inventing
  timer quantization to obtain matching hashes.

## Experience and performance experiments

Measure input delay 0/1/2 frames and prediction windows 2/4/6 frames as experiment
points. One source frame is about 33.3 ms. Do not import another game's 60 Hz frame
counts or confuse round-trip delay with exact one-way latency.

Record p50/p95/p99 of complete-state save/load, one simulation step, worst-window
catch-up, total application CPU frame cost and memory footprint. Include rendering,
audio and transport work when judging a 33.3 ms application budget. Repeated
maximum-window corrections must not create a growing backlog. Bound snapshot and
input history from the accepted window plus recovery requirements.

Before trial release, publish a measured profile table stating allowed delay,
maximum prediction, expected stall/correction behavior and compatible hardware.
Start with latency tests at 0/50/100/150/250 ms RTT, jitter at 0/20/50 ms, and loss
at 0/1/3%, including asymmetric paths and bursts. These are test axes, not a
promise that every combination is playable. Reject unsupported preflight
conditions clearly rather than promising unlimited-latency rollback.

Agree the selected profile before start and keep it fixed during the match.
Exceeding prediction limits produces bounded waiting and eventually the agreed
10-second interruption outcome; never unlimited prediction or silent input changes.

## Connectivity and room workflow

Test multiple mainland city/operator pairs, home networks and hotspots; record
actual direct/relay selection. Test forced relay even if direct tests pass, plus
UDP-restricted paths using supported TURN transports. Same-computer tabs alone
do not validate internet connectivity.

For each provider/path record attempts, failures, connection time and latency
distribution with sample size. Establish support from results; do not extrapolate
a small successful sample to all mainland networks. Failure to find an acceptable
path inside the budget blocks release.

Exercise edits after ready, duplicate operations, third-entrant races, owner/guest
departure, exit during rollback, invite replay, rematch isolation, DO hibernation,
rolling deployment/version mismatch and quota rejection. Run 10-room concurrent
full-match soak tests to validate the selected sizing target.

Test mutual pause, resume while one peer is late, intro skip, predicted/corrected
KO, background-tab throttling, machine sleep, interruption timeout, and recovery
just before/after the deadline. Refresh must not resume an old battle silently.
Test that room-service loss leaves a healthy peer match running and prevents
starting the next match. Exercise DO recovery, expiry and duplicate result/start
messages: reattachment must preserve epoch/identity, and an expired room must not
be silently replaced beneath an ongoing battle. Confirm that intro skip from
either participant is applied jointly after both have loaded.

## Diagnostics and operating evidence

Bound local retention in bytes/time and include epoch/build/profile, inputs,
confirmed frontier and state-comparison details. Provide a developer reproduction
bundle where retention permits; identify missing history explicitly and never
fall back to live controls during reproduction.

Use stable source object/event identities to locate the first difference. Keep
existing input recordings distinct from complete-state evidence. Reports exclude
credentials, invitation tokens and raw network addressing data; no automatic match
upload occurs. Verify sound deduplication, sustained-effect cancellation and
exactly-once final-result publication per match epoch.

Measure Workers/DO/TURN usage and reconcile [cost assumptions](COSTS.md). Admission
restrictions need headroom for active sessions and meter latency. Alerts do not
constitute a strict billing cap.

## Evidence and status

R0-R6 maintain artifacts, actual effort, tested versions and unresolved failures.
Fill numeric launch targets from measured R0-R4 results before R6. Changing scope,
budget or a confirmed decision requires reopening it. No migration milestone is
completed merely because online checks or document checks pass.
