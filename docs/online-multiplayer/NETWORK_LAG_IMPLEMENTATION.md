# Cross-machine online lag: implementation plan

Status: In progress, updated 2026-09-29; design revised the same day after review
(save rule, forced saves, deferred-correction ordering, unordered-channel
receive, simulator cost model, order). LAG-01–03 have implementation and
local-test evidence. LAG-01's final export and local IAB log identity check pass.
LAG-04 has a simulator implementation, but its observed slow-host result does
not reproduce the field pattern and its cost model is not calibrated.
2026-10-03: LAG-11 now has transport-drain batching and local correctness/performance
evidence; paired Web/TURN acceptance remains pending. LAG-10 has an opt-in sparse
save implementation and LAG-20 has an opt-in pacing experiment; see
[local evidence](../../evidence/online/network-lag/lag10-20-local.md). Later packages
have not started. No two-machine field or
deployed-page browser-log acceptance gate has passed. This document
turns the diagnosis in [NETWORK_LAG_PLAN.md](NETWORK_LAG_PLAN.md) into work
packages with files, designs, tests, evidence and completion checks. A local
implementation result does not close a package's paired-field or release gate.

## Goals and non-goals

Goal: on the two-machine TURN setup from the diagnosis (P1 about twice as slow
per step as P2), both peers sustain 30 logical frames per second for a full
visible match, with the existing gate from the
[30 Hz performance README](../../evidence/online/performance-30hz/README.md).

Non-goals: changing any battle rule, timer semantics visible to the simulation,
retained tapes or expected outputs; tuning around the problem with a larger
input delay as the only fix; claiming Flash parity for online timing.

## Findings that shape the order

These come from the logs and a read of the current code, and change the order
proposed in the diagnosis:

1. **Encoding, not validation, dominates a save.** `State.validate_value`
   returns immediately for the binary graph envelope, and
   `BattleCheckpoint.validate_state` is a hash plus byte comparison of the graph.
   The measured cost is `BattleCheckpoint._encode` (16.6 ms per save on P1) and
   `var_to_bytes` packing (4.0 ms). Earlier encoder micro-optimizations gave no
   stable gain. The lever is how often `save_state` runs and how many frames are
   replayed, not the validation calls.
2. **Sparse saving alone does not help the host.** P1 advanced almost every frame
   as a predicted frame. Skipping saves for already-confirmed frames helps the
   guest immediately but helps the host only after host pacing (LAG-20) keeps it
   close enough to the guest that most frames are confirmed when advanced.
3. **Save policy, batching and host pacing are locally selectable.** Their toggles do not change
   the state representation, so each peer can toggle them independently within
   one build. Sparse recovery adds a mandatory hashFloor field and compares
   periodic checkpoints; mixed builds must be rejected by the manifest. LAG-30
   will also change the transport protocol.
4. **The paired fake network cannot reproduce this.** `FakeHub` in
   `godot/tests/online_match_pair_smoke.gd` delivers or holds messages; it has no
   latency, jitter, loss or slow-peer model. A deterministic simulator (LAG-04)
   is needed before scheduling changes can be judged locally.
5. **Retained snapshots currently define three unrelated windows.** The oldest
   key of `RollbackSession._states` is the restore base, the lower bound of
   `can_receive_frame` (inputs and clock samples), and, through
   `OnlineMatch.retain_states` (`states[0].frame`), the pruning point for clock
   samples, local inputs and intro-skip frames. Any change to which frames are
   saved moves all three. LAG-10 must separate them first.
6. **Deferred correction and sparse saving share one invariant.** Both depend on
   distinguishing "inputs are complete" (`confirmed`) from "the simulated
   history matches those inputs" (no dirty frame). They are designed together in
   [Shared history invariants](#shared-history-invariants-lag-11-lag-10) and
   implemented in order LAG-11 then LAG-10.

## Package overview

| Id | Package | Depends on | Estimate | Current status |
|---|---|---|---|---|
| LAG-01 | Build identity in the deployed Web build | — | 0.5–1 d | Implemented; local tests, final export and local IAB identity log pass; deployed-page log pending |
| LAG-02 | Split performance counters and sync metrics | — | 1–1.5 d | Implemented; local smoke/analyzer tests pass; paired field measurement pending |
| LAG-03 | Replay-silent console and diagnostics | — | 0.5 d | Implemented; replay-hook smoke passes; paired field measurement pending |
| LAG-04 | Deterministic latency/loss/cost-model simulator | LAG-02 (cost constants) | 2.5–3.5 d | Implemented; slow-host validation/cost calibration pending |
| LAG-11 | One correction per message batch | LAG-02, LAG-04 | 2–3 d | Implemented for packet drains; local tests and native A/B pass; paired Web/TURN gate pending |
| LAG-10 | Sparse checkpoint saves | LAG-11 | 3–4 d | Opt-in implementation; local state/performance checks, field gate pending |
| LAG-12 | Measured hot-path trimming | LAG-02 field data | 1 d | Field-path candidate measured and rejected; no stable total gain |
| LAG-20 | Host pacing by frame advantage (experimental flag) | LAG-02, LAG-04 | 1.5–2 d | Experiment implemented; model shows no rate benefit, default off |
| LAG-30 | Redundant inputs and clock samples on the unordered channel | LAG-04, LAG-10 | 2.5–3.5 d | Not started |
| LAG-22 | Bounded catch-up (needs decision) | LAG-10, LAG-20 | 1–2 d | Not started |
| LAG-40 | Guest main-loop freeze during super pause | LAG-01 | 1–2 d | Not started |
| LAG-50 | Two-machine TURN acceptance | all above that are adopted | 0.5 d per run | Not started |

Current evidence is indexed in
[evidence/online/network-lag](../../evidence/online/network-lag/README.md).

Estimates are working days for one developer, excluding waiting for a second
tester. Record actual effort on completion.

## Milestones

- **M0 — Observable and reproducible** (LAG-01 to LAG-04). A field log names its
  build and splits step cost; the simulator, driven by measured costs,
  reproduces the diagnosed pattern on current code (host corrects, guest never
  corrects, both rates coupled).
- **M1 — Fewer corrections and saves** (LAG-11, LAG-10). Field run on the same
  two machines. Expected: corrections per message batch ≤ 1; saves per advanced
  frame well below 1 on the guest; host `input` and guest `clock` waits drop.
- **M2 — Cheaper frames and pacing experiment** (LAG-12; LAG-20 behind its flag).
  Field run with pacing off and on. Expected: slower peer's step p95 under
  25 ms; pacing is adopted only if the on-run beats the off-run.
- **M3 — Loss-tolerant transport** (LAG-30). Field run including a lossy period.
- **M4 — Acceptance** (LAG-50), plus LAG-22 if decided.

LAG-40 is not a milestone item: it starts as soon as LAG-01 is deployed and runs
in parallel, because a 9 s freeze would hide every other improvement and its
cause is unrelated to synchronization.

Expected effects are hypotheses for prioritization, not results.

**Current milestone state:** M0 remains open. LAG-01–03 local implementation
checks are recorded, but no deployed build log has non-unknown identity. The
six LAG-04 simulator scenarios pass their recorded correctness/hash checks, but
the slow-host run has not reproduced the diagnosed host-correction /
guest-zero-correction pattern and its costs remain provisional. M1–M4 remain
open; the two-machine TURN, deployed browser, and 30 Hz acceptance gates have
not passed.

Recommended serial order for one developer: LAG-01 → LAG-02 → LAG-03 → LAG-04 →
LAG-11 → LAG-10 → (M1 field run) → LAG-12 → LAG-20 → (M2 field runs) → LAG-30 →
(M3 field run) → LAG-22 decision → LAG-50, with LAG-40 inserted right after
LAG-01 whenever a second tester is available for a trace. With two developers,
the second takes LAG-40 first, then LAG-04. `rollback_session.gd` changes
(LAG-11, LAG-10, LAG-12) stay with one person and are done in that order.

## Rules for every package

- Answer [SOURCE_FIRST.md](../SOURCE_FIRST.md) where a change can reach
  simulation-visible state. For pure scheduling, storage or logging changes,
  state explicitly in the completion record that no source rule, timeline,
  timer delivery or random order changes, and prove it with the state
  comparisons listed in the package.
- Do not edit `game/`, `scripts/`, retained input/random tapes, frozen evidence
  or expected state outputs. A correction or save *count* expectation may change
  only when the package predicts that change; state equality may not.
- After changes, run `tools/verify.py` and `tools/check_handoff.py`; run
  `tools/validate_contracts.py` when a contract changes. Run the Godot checks in
  [docs/VALIDATION.md](../VALIDATION.md) proportional to the change. Regenerate
  the online manifest (`tools/build_online_manifest.py`) when runtime files
  change so mixed builds refuse to pair.
- Each change that can be toggled is added behind a constant or profile field so
  the same build can run old and new behavior for A/B comparison. Remove the old
  path only after the milestone field run.
- Evidence goes to [evidence/online/network-lag](../../evidence/online/network-lag/README.md).
  Field logs used as before/after evidence are copied there byte-for-byte with
  a dated name, listed in its README with SHA-256, and checked first for
  credentials, IP addresses and room tokens. The diagnosis logs
  (`p1-net-2026-09-29.json`, `p2-net-2026-09-29.json`) are the M0 baseline.
- Related TODO gates: LAG-04 contributes to NET-024; LAG-10/11/12 to NET-022 and
  NET-026; LAG-20/22 to NET-021 and NET-026; LAG-30 to NET-037; LAG-50 to NET-040
  and NET-026. None of these packages checks those boxes by itself.

## M0 — Observability and reproduction

### LAG-01 Build identity in the deployed Web build

At the diagnostic baseline, both field logs had `build.status = "unknown"`. The tooling exists
(`tools/build_web_diagnostics_metadata.py`, read at runtime from
`res://generated/build_metadata.json` by `diagnostic_runtime.gd` and fetched by
`godot/web/shell.html` as `build-metadata.json`), but `tools/build_web.sh`, the
Vercel build command, never calls it.

Work:

- In `tools/build_web.sh`, copy `godot/` to a temporary staging directory
  (excluding `.godot/`), run
  `build_web_diagnostics_metadata.py prepare --repo . --source-project godot --project <stage> --template <web_nothreads_release.zip> --engine-version 4.7.2`,
  export from the staged project, then run `finalize --embedded <stage>/generated/build_metadata.json --pck dist/web/index.pck --output dist/web/build-metadata.json`.
- Template path: the local export-template directory, or `$TEMPLATE_DIR` in the
  Linux/Vercel download branch.
- Commit: use `git rev-parse HEAD`; on Vercel fall back to
  `VERCEL_GIT_COMMIT_SHA` when `.git` is unavailable. Fail the build rather than
  embedding an empty commit.
- Keep the staging directory outside the repository and delete it on exit.

Tests and evidence: `tools/tests/test_web_diagnostics_metadata.py` still passes;
a local `bash tools/build_web.sh` produces `dist/web/build-metadata.json` whose
`pckSha256` matches `index.pck`; a log exported from that page shows matching
`buildID` and `sidecarBuildID` in `tools/analyze_diagnostics.py`.

Done when a deployed-page log reports a non-unknown build status with commit and
PCK hash.

Implementation update (2026-09-29): staging, commit fallback, template binding,
atomic sidecar finalization, complete export-set publication and local failure
tests are implemented. See [LAG-01 local evidence](../../evidence/online/network-lag/lag01-local.md).
The previous export predates template binding and persistent log scanning; the
final full export and a deployed-page log are still pending.

### LAG-02 Split performance counters and sync metrics

Problem: `simulation_step` mixes advance, save, validation and copies; nothing
records batch sizes, frame advantage or input arrival lead.

Work in `godot/rollback_session.gd`:

- Add `var profile := {}` with cumulative microsecond totals and counts for
  `advance`, `save`, `validate`, `copy`, `load`, `replay_advance`, and
  `saves_skipped` (used by LAG-10). Increment inside `_advance_one` and
  `_correct`. The session stays transport-independent; it only fills counters.
- Count and time presentation-node rebuilds that follow a `load_state` (the
  adapter reports them through an optional `profile_counters()` hook), so the
  cost of a correction includes what the scene does after the state restore,
  not only the restore itself.

Work in `godot/online_match.gd` and `godot/online_performance.gd`:

- Read session profile deltas per window, like the existing checkpoint deltas,
  and publish them under `rollbackWork` in each `online_performance` summary.
- Record per tick: remote messages handled since the last tick; corrections per
  tick. Record per transport drain (one `OnlinePeerTransport._process` loop):
  messages delivered and corrections, which is the unit LAG-11 batches over.
- Record **input arrival lead**: for each remote input frame at arrival,
  `frame - rollback.frontier` (negative means it arrived after the frame was
  simulated with a prediction). Publish p5/p50/p95.
- Record **observed frame advantage**: `rollback.frontier - remote_frontier`,
  where `remote_frontier = latest remote input frame - inputDelay - 1`
  (`_sample_local_once` runs before the clock gate, so a peer always sends input
  for `frontier + 1 + delay`). Publish p50/p95/max.
- Bump the summary `schemaVersion` to 2 and update
  `tools/analyze_diagnostics.py` to print the new fields.

Tests: extend `godot/tests/online_performance_diagnostics_smoke.gd` for the new
fields and schema; `tools/test_online_performance.py` still runs.

Done when a local paired run and a field log show the split costs, lead and
advantage on both peers.

Implementation update (2026-09-29): counters and summary schema are implemented;
the diagnostic, replay-service and analyzer tests pass locally. See
[LAG-02/03 local evidence](../../evidence/online/network-lag/lag02-03-local.md).
Paired field metrics are not recorded yet.

### LAG-03 Replay-silent console and diagnostics

Problem: `fighter_runtime.gd` (lines 605, 1048, 1812) and `helper_runtime.gd`
(line 103) `print("COMBAT_EVENT ", JSON.stringify(snapshot()))` on every
simulated frame, including rollback replay. Diagnostics events from
`_emit_diagnostic` are also emitted during replay without a marker.

Work:

- Add `var replaying := false` to `BattleCheckpoint` (the rollback owner found
  through `rollback_lifetime.gd::owner`). It is the encoder, not encoded state,
  so the flag cannot enter a checkpoint.
- `RollbackSession._correct` calls optional adapter hooks
  `begin_replay()`/`end_replay()` (checked with `has_method`) around the replay
  loop; `OnlineMatch` forwards to `RollbackBattle`, which sets
  `checkpoint.replaying`.
- Add a static helper next to `rollback_presentation.gd::allow_sound`, for
  example `is_replaying(node)`. Guard the four `COMBAT_EVENT` prints with it.
- In `_emit_diagnostic` for fighters and helpers, add `"replay": true` to the
  event payload while replaying instead of dropping it, so replay work remains
  auditable. The analyzer counts replay events separately.

Tests: a rollback smoke with a forced correction asserts that the console marker
count equals the confirmed-timeline count and that replay events carry the flag;
state fingerprints are unchanged.

Done when a paired run with corrections shows no duplicate `COMBAT_EVENT` lines.

Implementation update (2026-09-29): replay hooks, event tagging and console
gating are implemented; local failure-cleanup and replay-state tests pass. The
paired-match duplicate-event gate remains pending; see
[LAG-02/03 local evidence](../../evidence/online/network-lag/lag02-03-local.md).

### LAG-04 Deterministic latency, loss and work-cost simulator

Problem: no local harness reproduces the coupled host/guest behavior.

Work: new `godot/tests/online_lag_simulator.gd`, reusing `FakeHub`,
`FakeRoom` and `FakeTransport` from the pair smoke (move shared classes into a
`online_pair_fixture.gd` if needed rather than copying them).

- Virtual clock in milliseconds. Both coordinators receive
  `process_tick(virtual_now, input)` from the simulator, never wall time.
- Per-direction one-way latency, seeded jitter, loss (unordered channel only)
  and reordering. Reliable-channel messages are delayed and ordered, never lost,
  matching data-channel semantics; a lost unordered packet does not block later
  ones.
- **Work-cost model.** Each peer has virtual cost constants in microseconds:
  `step`, `save`, `load`, `replay_step` (per replayed frame, including its save
  when the save policy keeps it) and `rebuild` (presentation rebuild after a
  load). Every call the peer makes into its session adds the cost of the work it
  actually performed, read from the LAG-02 `profile` deltas, to a per-peer
  `busy_until` time. Constants come from LAG-02 field data: P1 at the diagnosed
  cost (about twice P2), P2 at its own measured cost; the scenario file records
  the log they were derived from.
- **Busy semantics.** A peer's caller tick fires at its 30 Hz schedule or at
  `busy_until`, whichever is later; ticks that fall inside a busy period are
  merged, not replayed, matching a browser frame that overran. Messages that
  arrive while a peer is busy queue and are delivered together in the next
  drain, before the tick, the same order `OnlinePeerTransport._process` gives
  today. This is what makes correction batching (LAG-11) and cheaper saves
  (LAG-10) visible as a rate change instead of a fixed cap.
- A fixed missed-tick profile (P1 processes only 25 of 30 ticks) is kept as one
  control scenario, `turn40-fixedskip`, to show the difference from the cost
  model; it is never used as evidence that an optimization helps.
- Input script: reuse `godot/tests/rollback_performance_user_log_r01.json` for
  one slot and a seeded varying script for the other, so predictions fail at a
  realistic rate.
- Output one JSON line per scenario with the LAG-02 metrics, plus the confirmed
  state fingerprint at every `HASH_INTERVAL` frame from both peers.

Scenarios (fixed seeds):

| Name | One-way latency | Jitter | Loss | Slow peer |
|---|---:|---:|---:|---|
| `lan` | 2 ms | 0 | 0 | measured costs, both fast |
| `turn40` | 20 ms | 5 ms | 0 | measured costs, both fast |
| `turn40-slowhost` | 20 ms | 5 ms | 0 | P1 at diagnosed cost |
| `turn40-fixedskip` | 20 ms | 5 ms | 0 | P1 at 25 of 30 ticks (control only) |
| `turn100` | 50 ms | 15 ms | 0 | P1 at diagnosed cost |
| `lossy` | 20 ms | 5 ms | 3% | P1 at diagnosed cost |

Evidence: `evidence/online/network-lag/simulator-baseline.jsonl` on current code.
It must reproduce the diagnosed pattern in `turn40-slowhost`: guest corrections
0, host corrections above 0, guest `clock` wait tracking host `input` wait, a
host logical rate near the field log's, and equal fingerprints on both peers.
If the rate is far from the field log, the cost constants are wrong and are
fixed before any later package uses the simulator.

Done when the baseline is recorded and every later package reports before/after
numbers from the same scenarios and seeds.

Implementation update (2026-09-29): the simulator implementation and LAN smoke
exist. All six 10-second scenarios have recorded `ok=true`, equal common hashes,
and reliable conservation/order checks. `turn40-slowhost` reached 30 Hz with
zero corrections and therefore did not reproduce the field pattern; the
work-cost model remains provisional and LAG-04 is not accepted. The retained
scenario records, pair smoke, record-path failure boundary, and model limits
are in [LAG-04 local evidence](../../evidence/online/network-lag/lag04-local.md).

## M1 — Fewer corrections and saves

### Shared history invariants (LAG-11, LAG-10)

Terms, all owned by `RollbackSession`:

- `confirmed` (unchanged): the highest frame `F` such that both slots have an
  actual input for every frame up to `F`. It can be above `frontier`.
- `_dirty_from`: the lowest frame at or below `frontier` that was simulated with
  an input different from the actual input now stored; `-1` when clean.
- `settled()` first reconciles dirty history, then returns
  `min(confirmed, frontier)` (`-1` on failure): frames whose state is final. Hashes, results, control barriers, recovery and `confirm_through` use
  `settled()`, never `confirmed`.
- `input_floor`: frames at or below it are rejected as too old; frames above it
  are accepted. It is an explicit field computed exactly like
  today's `retain_from` (`min(confirmed, frontier - capacity + 1)`, never
  lowered). It replaces `oldest_frame()` in `can_receive_frame` and in recovery
  retransmission admission. The replay journal retention floor can be older,
  because replay from a sparse checkpoint still needs its clock/input history.
  Save policy never expands input admission.

Invariants:

1. **No final read on dirty history.** Every entry point that treats a state as
   final calls `reconcile()` first: `step()`, `settled()`, the public
   `state_at()`, and in `OnlineMatch` `_maybe_hash_confirmed`,
   `_maybe_finish_result`, `_report_control_ready`, the control commit path
   (`state_at(frame)` in the commit handler), `_send_recovery_sync`,
   `_propose_recovery_comparison`, the recovery compare and commit handlers, and
   the end-of-match summary. Correctness therefore does not depend on the order
   in which messages arrive. Batching comes from where `reconcile()` is called in
   the normal flow (once per transport drain), and a read that happens earlier
   simply pays for the correction earlier.
2. **Exact-read frames are always saved.** A frame read by `state_at` for an
   exact comparison is saved when it is advanced, including during replay: every
   `HASH_INTERVAL` frame, the terminal result frame, the pending control frame,
   and recovery comparison frames (always hash frames, see LAG-10). The session
   asks the adapter through an optional `must_save(frame) -> bool` hook after
   `advance`, so it stays transport-independent.
3. **Restore base.** After advancing `F` (normally or in replay), the state is a
   restore base, and is saved, when `F + 1 > confirmed`: frame `F + 1` may still
   receive a different input. When `F + 1 <= confirmed`, `F + 1` is advanced with
   actual inputs and can never be corrected, so `F` is never a restore base. The
   rule uses `confirmed`, not `settled()`: `settled()` is capped at `frontier`,
   which equals `F` right after the advance, so it would mark every frame as a
   boundary. Invariant 1 guarantees there is no dirty frame when `F` is
   advanced, because `step()` reconciles first.
4. **Pruning keeps what the other peer can ask for.** A peer's settled frame can
   trail the other's by at most `R = predictionWindow + inputDelay + 1`: local
   `confirmed = C` implies the remote sampled frame `C`, so its frontier is at
   least `C - inputDelay - 1`, and its step gate keeps its confirmed frame at
   least `predictionWindow` below its frontier. Pruning therefore keeps every
   saved hash frame in `[settled() - R, settled()]`, the newest hash frame below
   that range, the newest saved frame at or below `settled()` (restore base), the
   pending control frame, and everything newer. The bound is verified by the
   recovery cases in `online_match_pair_smoke.gd`, not assumed.

Message handling while the session is dirty (between a mismatching input and
the next `reconcile()`):

| Event | Handling |
|---|---|
| `input_frame` | Stored; marks dirty if it contradicts a used prediction; no restore, no hash or result check per message. |
| `clock_sample` | Stored; reads no history. |
| `state_hash` from the peer | Stored; compared only when the local hash for that frame is produced after `reconcile()`. |
| `control` (request, accept, proposal, ready, commit) | A path that reads `state_at` or `settled()` reconciles first (invariant 1). A frame chosen from `frontier` is unaffected: a correction replays back to the same `frontier`. |
| `result` from the peer | Stored; the local result is computed only after `reconcile()`. |
| `recovery_*` | Handlers reconcile before reporting or comparing; inputs resent during recovery arrive in the same drain and are corrected together. |
| Invalid or conflicting peer input, `match_abort`, protocol error | Abort immediately without reconciling. The abort payload includes `_dirty_from` and the frames accepted earlier in the same drain, so diagnostics keep the valid inputs that arrived before the error. |
| Local tick while paused or recovering | `_process_tick` calls `reconcile()` before the paused/recovering early return, so pause and recovery never sit on dirty history. |
| `reconcile()` fails | Session error is set; `OnlineMatch` aborts with reason `correction_failed`, `_dirty_from`, the triggering frame and the stored actual inputs for the dirty range. |

### LAG-11 One correction per message batch

Implementation update (2026-10-03): see [local evidence](../../evidence/online/network-lag/lag11-local.md).
The implementation opts into deferred correction only inside an explicit transport
drain; standalone callers retain immediate correction. A control or recovery
message that needs final state is an early reconciliation barrier, so a drain
with interleaved controls can require more than one correction. Input-only bursts
reconcile once. The original experimental-flag/default-off proposal below is
superseded for this bounded integration; sparse saves, pacing and transport
changes remain unimplemented. Simulator calibration and field acceptance are
still open, so this local result does not close M1 or authorize subsequent gates.

Current behavior: `RollbackSession.receive()` calls `_correct(frame)` for each
mismatched frame as it arrives, from the transport `_process` callback, and
`OnlineMatch._receive_input` then checks hashes and results after every message.

Design (terms and invariants above):

- `receive()` stores the input and, if `frame <= frontier` and the used
  prediction differs, sets `_dirty_from = min(_dirty_from, frame)`. It no longer
  restores. Range checks, validation and duplicate handling are unchanged.
- Add `reconcile()`: if `_dirty_from <= frontier`, run the existing `_correct`
  from `_dirty_from`, then clear it. `_correct` itself is unchanged in this
  package (every frame is still saved).
- Add `settled()` and `input_floor`; replace every final-history read listed in
  invariant 1; `_prune` uses `settled()` and `input_floor`.
- Drain point: `OnlinePeerTransport._process` emits `peer_messages_drained`
  after its packet loop. `OnlineMatch` handles it by calling
  `rollback.reconcile()`, then `_maybe_hash_confirmed()` and
  `_maybe_finish_result()`. The same sequence runs after replaying
  `_startup_pending_messages`. `_receive_input` records receive time only and
  no longer calls the hash and result checks.
- `_process_tick` also calls `reconcile()` right after the clock and heartbeat
  checks, before the paused/recovering return, which covers transports without
  the signal (`FakeHub` in tests) and records correction time in the tick.
- Flag: `OnlineMatch.BATCH_CORRECTIONS`, default off until M1 passes.

Tests:

- New `godot/tests/rollback_batched_correction_smoke.gd`: drive one session with
  per-frame delivery and one with batched delivery of the same inputs; assert
  equal fingerprints at every frame and corrections ≤ drains; an instrumented
  adapter asserts that `state_at`, `confirm_through` and hashing never run while
  `_dirty_from <= frontier`.
- Ordering cases in `online_match_pair_smoke.gd`: in one drain, deliver a
  mismatching input followed by each of: pause request, resume commit, remote
  `result`, `recovery_sync`, remote `state_hash`, and an invalid input. Assert
  that the control and result hashes come from the corrected history, that the
  remote hash is compared against the corrected state, and that the abort
  payload for the invalid input lists the earlier valid inputs.
- `rollback_services_smoke.gd`, `rollback_battle_smoke.gd`,
  `rollback_delayed_input_profile.gd -- compare-state` keep equal state; their
  correction counts may drop and the new counts are recorded.
- Simulator: all scenarios, fingerprints equal across peers.

Done when state equality holds on all fixtures and ordering cases, and the
simulator shows corrections per drain ≤ 1.

### LAG-10 Sparse checkpoint saves

Current behavior: `_advance_one` saves and stores a snapshot for every advanced
or replayed frame, and the oldest snapshot also sets the receive window and the
coordinator's pruning point (finding 5).

Prerequisite: LAG-11 is merged, so `settled()`, `input_floor`, `reconcile()`
and the invariants in
[Shared history invariants](#shared-history-invariants-lag-11-lag-10) exist.

Rule for whether to save after advancing frame `F` (normally or in replay),
with `confirmed` read at that moment:

- **Exact-read frame:** `adapter.must_save(F)` → save (invariant 2).
- **Restore base:** `F >= confirmed` → save if `F == confirmed` or
  `(F - confirmed) % PREDICTED_STRIDE == 0` (invariant 3).
  `PREDICTED_STRIDE = 1` saves every predicted frame, as today; test 1, 2 and 3.
- **Otherwise** (`F < confirmed`) → skip and count `saves_skipped`. On the guest
  this is almost every frame. Example from review: `F = 100`, `confirmed = 102`
  → skipped, because frames 101 and 102 run on actual inputs and can never be
  corrected.

Why a correction at `m` always finds a base: `m` was predicted, so
`confirmed < m` when `m` was advanced; `confirmed` never decreases, so when
`m - 1` was advanced `m - 1 >= confirmed` held and it was saved (with stride 1),
or the newest saved predicted frame below it was (stride above 1, which costs
extra replay and is measured).

Session changes:

- `_advance_one(save: bool)`; `_used[frame]` is still recorded every frame.
- `_correct(m)` restores the newest saved state at or before `m - 1` and replays
  from there. The replay saves according to the same rule.
- `_prune` keeps the frames required by invariant 4 and drops other states.
  `_actual` and `_used` are kept from `min(input_floor, restore base)` upward so
  a replay from the restore base always has its inputs; `_anchors` are taken at
  that same point.
- `can_receive_frame` uses `input_floor` (LAG-11), so a late input just above
  the floor is accepted regardless of which states happen to be saved.
- `state_at(frame)` keeps returning `{}` for unsaved frames. Add
  `latest_saved_at_or_before(frame)`.

Coordinator changes (`godot/online_match.gd`):

- `must_save(frame)`: `frame % HASH_INTERVAL == 0`; `frame ==
  _pending_control_frame()` while a control frame is pending;
  `game.ko_terminal_pending and frame == game.physics_tick` (checked after the
  advance that set it).
- Implemented retention refinement: `input_floor` controls admission and recovery
  retransmission. `retain_states(states)` keeps replay journals through the oldest
  required restore checkpoint, computed by minimum frame rather than array order.
  Pruning those clock samples at the newer input floor would make replay from an
  older sparse checkpoint impossible. History is conservatively contiguous from
  that restore base; periodic recovery retention is enabled for both online save
  policies, while generic every-frame fixtures keep their original capacity.
- `_maybe_hash_confirmed`, `_maybe_finish_result` and the control barriers keep
  exact `state_at` reads; invariant 2 guarantees those frames exist, and a
  missing one is a bug that aborts as today (`missing_result_state`, etc.).
- Recovery: `_send_recovery_sync` reports `confirmedFrame` as the newest hash
  frame at or below `settled()` with its fingerprint, plus `hashFloor`, the
  oldest hash frame it still retains. `_propose_recovery_comparison` picks the
  largest hash frame at or below both `confirmedFrame` values and at or above
  both `hashFloor` values, and aborts `invalid_recovery_frame` if none exists.
  The compare and commit handlers accept only hash frames. This is a protocol
  change; the manifest build fingerprint prevents mixed builds from pairing.

Correctness argument to verify, not assume: `save_state` must not change
simulation. It populates encoder caches (`_constants`, `_immutable_fields`,
placement tables) and retains nodes in `_snapshots`; restores use constants
registered at their own save time. The tests below must show that saving fewer
frames produces the same states.

Tests:

- Run `rollback_delayed_input_profile.gd`, `rollback_roster_smoke.gd`,
  `rollback_round_smoke.gd` and `online_timer_round_smoke.gd` with the policy
  forced to every-frame and to sparse; compare fingerprints at every hash frame
  and after every correction (force a save at the same frames in both runs for
  comparison), and the complete graph at the final frame with the existing
  flat-graph comparator.
- `online_match_pair_smoke.gd` recovery and divergence cases pass with the new
  recovery frame selection.
- Unit cases in a new `godot/tests/rollback_sparse_save_smoke.gd`:
  - `F = 100`, `confirmed = 102` → not saved; `F = 102` → saved.
  - A KO whose terminal frame is not a multiple of `HASH_INTERVAL` still
    produces a result with the fingerprint of that exact frame.
  - A pause whose control frame is not a hash frame produces matching
    `pause_ready` hashes on both peers.
  - Recovery with local `settled() = 60`, remote `settled() = 59` and
    `HASH_INTERVAL = 30` compares frame 30 on both peers.
  - A late input just above `input_floor` is accepted, one at the floor is
    rejected with the same error as today, whichever states are saved.
- Simulator: saves per advanced frame per peer, equal fingerprints.
- Flag: `RollbackSession` save policy `"every_frame" | "sparse"`, default
  `"every_frame"` until M1 passes.

Done when state equality holds on all cases above and saves per advanced frame
are measured on both peers in the simulator and the M1 field run.

## M2 — Cheaper frames and pacing experiment

### LAG-12 Measured hot-path trimming

Only do the items whose LAG-02 cost is above 1 ms per step on the slower peer.

- `_advance_one`: skip `adapter.validate_state` for a snapshot the adapter
  produced in the same call, and store it without `duplicate(true)`; the
  session owns it and never mutates it.
- `_correct`: pass the retained snapshot to `load_state` without
  `duplicate(true)` and without the extra pre-validation; `load_state` already
  validates. `state_at` still returns a copy to external callers.
- `_prune`: if `retain_states` is significant, release only frames that left the
  window.

Tests: `battle_checkpoint_smoke.gd` tamper/rejection cases still fail closed on
the external load path; delayed-input profile state equality; before/after
LAG-02 counters.

Done when each adopted item shows a measured reduction and unchanged state.

### LAG-20 Host pacing by frame advantage (experimental)

Recommended option from the diagnosis (host throttle). It keeps the guest clock
gate and all timer semantics; only when the host steps changes. It stays behind
a flag that defaults off: it trades host throughput for fewer corrections, and
after LAG-11 and LAG-10 a correction may be cheap enough that pacing is not
worth it. It is adopted only if the M2 field run with pacing on beats the run
with it off.

Design, in `OnlineMatch._process_tick` on the clock authority only:

- Compute observed advantage `A = rollback.frontier - remote_frontier` (LAG-02
  definition). It includes the one-way delay, so it overestimates the true gap.
- If `A > profile.inputDelay + SYNC_SLACK` and the host did not skip the previous
  tick and has skipped fewer than 1 of the last 3 ticks, skip stepping this tick
  with a new wait reason `sync`. Local input sampling, heartbeats, control
  barriers and message handling still run.
- `SYNC_SLACK` starts at 2 frames; tune from the simulator and field runs. Never
  skip while a control frame, recovery or pause is pending.
- Host clock samples remain real elapsed milliseconds when a frame is stepped;
  a skipped tick simply lengthens the interval before the next sample. This is
  the same situation as today's input wait, so the delivery contract is
  unchanged. Add a "host pacing" paragraph to
  [CLIENT_TIMING.md](CLIENT_TIMING.md) and a consequence note in
  [ADR 0002](adr/0002-rollback-battle-synchronization.md) only if adopted.
- Add `sync` to `OnlinePerformance.WAIT_REASONS`.
- Flag: `OnlineMatch.HOST_PACING`, default off.

Why it may help: the host only needs to predict when it is more than
`inputDelay` frames ahead of the guest's sampling. Keeping the observed
advantage near `inputDelay + 2` leaves at most about one predicted frame at
typical TURN RTT, so most guest inputs arrive before they are needed.

Tests:

- Simulator (cost model): `turn40` and `turn40-slowhost` with pacing on versus
  off, both on top of LAG-11 and LAG-10: host corrections, host `input` wait and
  both peers' logical rate; no rate loss on `lan`; equal fingerprints.
- `online_match_pair_smoke.gd` unchanged results.
- New unit test for the skip rule: never two skips in a row, never during
  control/recovery, never on the guest.

Done when the simulator comparison and the M2 on/off field runs are recorded
and the flag's default is decided from them.

## M3 — Loss-tolerant transport

### LAG-30 Redundant inputs and clock samples on the unordered channel

Current behavior: `_send_peer` sends everything on `"reliable"`;
`receive_peer_message` drops any other channel. The `"input"` channel
(`ordered: false`, `maxRetransmits: 0`) is created in
`OnlinePeerTransport.create_peer` and never used.

Design:

- New message `input_batch` on channel `"input"`, sent once per tick after local
  sampling:
  `{"from": F0, "bits": [b0, b1, ...], "ack": A, "clock_from": C0, "clock": [ms, ...]}`.
  - `bits` holds every local input frame after the remote's last `ack`, capped
    at 32 frames. The bitmask follows the order of
    `keyboard_input_source.gd::BUTTONS`.
  - `ack` is the highest contiguous remote input frame received.
  - The guest also sends `clock_ack`, the highest contiguous clock frame it has
    stored. The clock authority includes every clock sample after the guest's
    last `clock_ack`, capped at 32 frames, so a lost packet cannot stall the
    guest's clock gate either. Before the first `clock_ack` arrives, the host
    sends from the current frontier.
- The existing receive paths are **not** idempotent for late duplicates:
  `RollbackSession.receive` checks `can_receive_frame` before the duplicate
  check, so a resend of a frame at or below `input_floor` returns
  `Input outside retained/receive range` and `_receive_input` aborts; and
  `_receive_clock_sample` aborts `clock_sample_outside_receive_window` for a
  sample that was already pruned. The batch therefore gets its own receive path,
  `_receive_input_batch`, and the reliable `input_frame` / `clock_sample` paths
  keep their current strict behavior:
  - Input frames at or below `rollback.confirmed` are dropped without calling
    the session when no stored value exists (already accepted and pruned). If a
    stored value exists and differs, abort `peer_input` with
    `Conflicting immutable input`, as today.
  - Remaining input frames go through `rollback.receive` in ascending order.
  - Clock samples at or below the guest's own `clock_ack` are dropped when no
    stored value exists, compared when one exists, and otherwise go through
    `_receive_clock_sample`.
  - Deduplication is by frame content, not by transport sequence, so the
    unordered channel does not grow `_received_sequences`; that table and its
    4096-entry limit stay reliable-only.
- Keep `state_hash`, `control`, `result`, `heartbeat`, `match_ready` and all
  `recovery_*` messages on the reliable channel. Recovery keeps resending inputs
  and clock samples over the reliable channel.
- `receive_peer_message` accepts channel `"input"` only for `input_batch`.
- Bump `OnlinePeerTransport.PROTOCOL_VERSION` and regenerate the manifest.
- Flag: `OnlineMatch.UNORDERED_INPUT` until M3 passes.

Tests:

- `online_peer_transport_smoke.gd`: unordered duplicate and reorder handling for
  `input_batch`; envelope validation.
- `online_match_pair_smoke.gd`: a batch resent after its frames were pruned is
  dropped without abort; a batch that contradicts a stored input still aborts;
  a lost batch followed by a later one fills both inputs and clock samples; a
  reliable `input_frame` below the floor still aborts as today.
- Simulator `lossy`: no stall longer than one RTT plus one tick after a single
  loss; equal fingerprints; bytes per second recorded.
- Rerun the [TURN buffer model](../../evidence/online/performance-30hz/turn-buffer-model.md)
  without the reliable-ordering assumption.

Done when the simulator and the M3 field run show no loss-induced stalls and
equal state.

## M4 — Remaining items and acceptance

### LAG-22 Bounded catch-up (needs a decision)

The delivery contract in [CLIENT_TIMING.md](CLIENT_TIMING.md) allows at most one
logical step per caller tick. After M2, if a peer still falls behind after
isolated slow ticks, allow up to 2 steps in one tick when:

- the guest already holds clock samples beyond `frontier + 1`, or the host is
  behind its own elapsed-time schedule by more than 2 frames;
- the previous tick's work was under a budget (for example 12 ms);
- the page is visible (hidden pages keep one step, so no burst on return).

This requires amending CLIENT_TIMING.md's delivery contract and the ADR before
code. Tests: simulator with injected single long ticks recovers the schedule
without exceeding 2 steps per tick; timer smokes unchanged.

### LAG-40 Guest main-loop freeze during super pause

Runs in parallel from as soon as LAG-01 is deployed (see Milestones); it is
listed here only for its content. Reproduce the diagnosed sequence (白哉 with 松本 against 小李 with 我爱罗 on
温泉) first in offline versus mode, then online, with a Chrome Performance trace
on the frozen peer. Record whether the 9 s gap is synchronous resource or shader
loading, garbage collection, or a script loop. Fix only with trace evidence and
the source-first answers if the cause is in simulation code. Done when the trace
is recorded and the sequence completes without a gap over 100 ms, or the cause
is documented as outside the project.

### LAG-50 Two-machine TURN acceptance

Procedure for M1–M4 field runs:

1. Deploy one build; confirm both pages show the same `buildID`.
2. Use the same two machines as the diagnosis where possible, same profile
   (`d2-p6` unless a profile change is being tested), visible foreground tabs,
   no other heavy load, at least 60 s of active fighting including an assist and
   a super.
3. Export both logs, copy them to `evidence/online/network-lag/` as
   `p1-net-<date>-<milestone>.json` and `p2-net-<date>-<milestone>.json`, and
   record SHA-256, machine and browser details in its README. Compare against
   the diagnosis baseline logs in the same directory.
4. Summarize with `tools/analyze_diagnostics.py` into
   `evidence/online/network-lag/<date>-<milestone>.md`: rate, split step cost,
   corrections, saves per frame, waits by reason, arrival lead, frame advantage.

Acceptance (from the diagnosis plan): both peers at 30 Hz sustained; step p95
≤ 25 ms on the slower peer; guest `clock` and host `input` waits each under 5%
of match time; no single correction over 33 ms; no stall in the super-pause
sequence. A same-machine run or native benchmark does not satisfy this.

## Risks

| Risk | Mitigation |
|---|---|
| Sparse saves expose a hidden side effect of `save_state` | Every-frame vs sparse state comparison on all rollback fixtures before enabling; flag stays off until M1 passes |
| Sparse saves drop a frame that is read exactly (result, control, recovery) | `must_save` hook (invariant 2); dedicated unit cases for off-interval KO and pause frames and for unequal recovery frames |
| Sparse saves move the receive window or coordinator pruning | Explicit `input_floor` introduced in LAG-11 with today's values, before any save is skipped |
| Deferred correction lets a wrong state be hashed, finish a round or answer a control/recovery message | Reconcile-before-read on every final-history entry point (invariant 1); ordering cases in the pair smoke; instrumented adapter asserts no read while dirty |
| Deferred correction loses diagnostics when a later message aborts | Abort payload carries `_dirty_from` and the inputs accepted earlier in the drain |
| Redundant unordered resends abort on pruned frames | Separate `_receive_input_batch` path that drops already-confirmed frames; reliable paths keep strict checks |
| Simulator overstates or hides a gain | Work-cost model calibrated from LAG-02 field data; baseline must match the field log's rate before use |
| Host pacing oscillates or costs throughput on LAN | Skip limits (no consecutive skips, ≤ 1 in 3); `lan` scenario must keep its rate |
| Recovery frame selection change breaks reconnection | Pair smoke recovery cases; protocol change pinned by manifest fingerprint |
| Unordered channel starves after a long loss burst | Unacknowledged-range resend capped at 32 frames plus the unchanged reliable recovery path |
| Improvements measured on different builds | LAG-01 first; field comparisons only between logs with verified build identity |

### 2026-10-03 prediction stride experiment

Sparse saves can now use `checkpoint_stride=2`, retaining every second predicted
frame and the existing forced hash/control/KO frames. All logical frames still
advance. This uses the existing nearest-predecessor replay path and trades at
most one extra frame per correction for fewer saves. The default remains stride
one; browser selection is `?online_sparse=1&online_stride=2`. See
[local experiment](../../evidence/online/network-lag/lag12-stride-local.md).
The field-descriptor micro-optimization was reverted after unstable timing;
no encoder format, source timing, or acceptance threshold changed.

## Replay presentation — 2026-10-03

Replay drawing now flushes once at correction completion, with current-pose
shadow capture exceptions. Online combo drawing is suppressed; logical counters
and diagnostics remain active. This is enabled by default. Native total-time
gains are not conclusive; no NET gate is closed. See
[local evidence](../../evidence/online/network-lag/replay-display-local.md).

## Online checkpoint default — 2026-10-04

Sparse saves with stride two are now the online default, superseding the earlier
opt-in status. `?online_sparse=0` restores full saving; host pacing stays off.
Native measurements and state checks are recorded in
[local evidence](../../evidence/online/network-lag/sparse-default-local.md).
Browser performance and all existing NET acceptance gates remain pending.
