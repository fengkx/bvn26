# LAG-02 and LAG-03 local implementation evidence

Date: 2026-09-29

## Scope

LAG-02 adds cumulative rollback work counters and online sync samples. The
session exposes counts and microseconds for adapter advances, saves, explicit
validation calls, dictionary copies, state loads, and presentation rebuilds.
Replay adapter advances are counted separately from normal advances;
`replay_save_count` is a subset of `save_count`. `save_count` includes the
initial configure snapshot, while the online window baseline is captured after
configure, so its first `windowDelta` excludes that initial save. Load time is
exclusive of measured presentation rebuild time. Local input packet copies and
retained input-anchor copies are included in `copy` counters; profiler snapshot
copies are excluded to avoid measuring the observer itself.

Online summaries report remote messages and corrections per caller tick and
per transport drain. Drain message counts include validated packets emitted to
the coordinator. Input arrival lead is `input frame - frontier at arrival` and
is recorded only after an accepted input. Frame advantage is sampled before
the tick as `frontier - (latest remote input frame - inputDelay - 1)`. The
summary schema is version 2. Counters remain cumulative; consumers calculate
window deltas from a post-configure baseline.

LAG-03 brackets correction replay with paired adapter hooks. The replay flag
lives on `BattleCheckpoint`, outside the encoded battle graph. Replay
diagnostics remain in the event stream with `payload.replay = true`; only
replayed `COMBAT_EVENT` console lines are suppressed. Earlier predicted events
remain present in diagnostics, so suppression does not turn the console into a
confirmed timeline.

No source rule, timeline, timer delivery, input sequence, random order, or
simulation-visible state was changed. The five source-first questions do not
apply to this presentation/telemetry-only package: no per-frame source action,
PlaceObject/MOVE interpretation, tag-leaving behavior, or original-game
invariant was changed. The replay regression compares the same actual inputs
through a synthetic adapter; it is a state-restoration check, not Flash parity
evidence. Retained inputs, expected outputs, `game/`, and `scripts/` were not
modified.

## Verification

- Godot 4.7.2 `online_performance_diagnostics_smoke.gd`:
  `ONLINE_PERFORMANCE_DIAGNOSTICS_OK`; also checks the configure-time initial
  save baseline and counts for local packet and retained-anchor copies.
- Godot 4.7.2 `rollback_replay_hooks_smoke.gd`: `ROLLBACK_REPLAY_HOOKS_SMOKE_OK`;
  covers correction state equality, replay diagnostics tagging, retention of
  the original predicted event, console gating, and cleanup after validation,
  load, advance, and save failures.
- Godot 4.7.2 `rollback_services_smoke.gd`:
  `ROLLBACK_SERVICES_SMOKE_OK scope=services_and_synthetic_fixture_not_battle`.
- Final Godot logs are in `/private/tmp/lag02-03-final-online-performance.log`,
  `/private/tmp/lag02-03-final-replay-hooks.log`, and
  `/private/tmp/lag02-03-final-rollback-services.log`.
- `python3 -m unittest tools.tests.test_analyze_diagnostics`: 11 tests total;
  8 passed and 3 skipped because optional historical captures were unavailable.
- Python compilation, `python3 tools/check_handoff.py`, `git diff --check`, and
  final `python3 tools/verify.py` passed. The integration check updated the
  tracked hashes for the two runtime files and the online build manifest.

Godot also prints a macOS system-CA `noErr` warning in this environment; the
project smoke logs contain no `SCRIPT ERROR`.

## Acceptance boundary

No two-peer field run or performance conclusion is claimed here. The local
smokes establish telemetry shape, hook cleanup, and synthetic state equality
only. LAG-02 field metrics and LAG-03 no-duplicate console behavior in a paired
match remain to be measured with the coordinated simulator/run evidence.
