# Online performance diagnostics

The coordinator emits a bounded `online_performance` diagnostic event at most
once per elapsed second while an online match is active. The version 1 payload
keeps window values separate from match totals. It reports frontier progress
and confirmed progress separately; neither is presented as render FPS. Tick
intervals and synchronous work durations are separate from the mutually
exclusive wall-time counters for clock, input, control, confirmation, pause,
and recovery waits.

Coordinator ticks, frontier-advancing simulation steps, tick intervals, input
receive calls, and receive calls that trigger correction have count, total or
maximum duration, and p95/p99 values where applicable. Each window retains at
most 120 duration samples per metric and reports retained sample count,
dropped-sample count, and a truncation flag. Correction duration measures the
complete `RollbackSession.receive()` call when its rollback counter increases;
it includes receive overhead and is not labeled as replay-only CPU time. The
payload also carries visibility, recovery/pause state, and existing checkpoint
profile counters. RTT is explicitly unavailable because the peer transport
does not expose reliable RTT statistics.

Instrumentation is held in a separate `OnlinePerformance` object and is not
added to rollback snapshots, input or clock envelopes, or peer messages.
Periodic events use the existing local `DiagnosticRuntime.push_event` bridge.
Abort summaries are attached to the locally downloadable diagnostic report;
the room abort operation continues to send only its existing type and epoch.
There are no shell heap fields or serialized retained-state measurements in
the timed path.

## Verification

Executed with Godot 4.7.2 on macOS:

- `godot --headless --path godot -s res://tests/online_performance_diagnostics_smoke.gd`
  — passed sample bounds and truncation, percentile values, window reset versus
  match totals, exclusive wait accounting, unavailable RTT, optional
  diagnostics fallback, `online_performance` event identity, teardown safety,
  and snapshot isolation. The final focused run completed with
  `ONLINE_PERFORMANCE_DIAGNOSTICS_OK`.
- `godot --headless --path godot -s res://tests/online_match_pending_command_smoke.gd`
  — passed; startup barrier and visibility lifecycle markers were emitted.
- `godot --headless --path godot -s res://tests/online_match_pair_smoke.gd`
  — an initial current-tree attempt hit `clock_regression` at recovery after
  parity, correction, fight hash, pause, and resume checks. It did not print
  the two clock values, so no numeric delta is inferred. The test had advanced
  synthetic `time_origin + 330 * 33` ticks before switching to wall time. The
  test-only fix now supplies `max(control_now, Time.get_ticks_msec())`, records
  previous/wall/supplied timestamps, and leaves the 9,999/10,000 ms timeout
  assertions unchanged. With that same script, both frozen baseline and current
  tree passed all markers through short recovery, timeout abort, result commit,
  and new epoch. Baseline recovery timestamps were
  `previous_ms=13913`, `wall_now_ms=84130`, `supplied_now_ms=84130`
  (`raw_delta_ms=70217`); current-tree timestamps were `previous_ms=21135`,
  `wall_now_ms=52270`, `supplied_now_ms=52270` (`raw_delta_ms=31135`).

Godot printed headless log-directory and macOS certificate lookup warnings in
these runs; the focused diagnostics smoke and both corrected pair runs still
exited successfully.
No browser A/B performance result is included here.

## Hidden presentation and diagnostics fast paths

`main.gd` now avoids formatting hidden tick/state labels and constructs the
per-input diagnostics event only while diagnostics are enabled. The health HUD
refresh and energy display-tick advancement remain unconditional. These paths
are outside rollback state and do not change input values or event contents when
diagnostics are enabled. The focused diagnostics smoke passed after these
changes; their Web performance gain has not been isolated or quantified by an
A/B run.
