# Implementation TODOs and execution order

Status: In progress. All 48 full acceptance gates below remain unchecked. A
production `Main` rollback adapter and online coordinator cover representative
local battles, controls and result agreement through a test-only in-memory fake
network; browser/WebRTC and full release acceptance remain open. The full-state,
rollback and client task boxes remain acceptance gates: representative runs do
not by themselves satisfy every task's full-scope checks. The client transaction
is connected and has paired fake-network evidence. See
[implementation evidence](IMPLEMENTATION.md), [state audit](STATE_AUDIT.md) and
[client integration](CLIENT_IMPLEMENTATION.md).
Scope and product choices come from
[DESIGN.md](DESIGN.md) and the [20 interview answers](INTERVIEW.md).

## Server implementation update — 2026-09-22

The separately requested TypeScript Durable Object server is delivered in
[services/matchmaking](../../services/matchmaking/README.md). Room lifecycle,
admission, setup/epochs, signaling, leases, expiry and scoped TURN issuance have
local contract tests, SQLite restart evidence and a production Wrangler smoke.
See [server status and per-task boundaries](SERVER_IMPLEMENTATION.md) for
NET-007 and NET-027–035. Their full-plan checkboxes remain open where upstream
contracts, deployed lifecycle or client/network acceptance is still missing;
the independent backend implementation is no longer a proposed artifact.
The user explicitly authorized this server slice independently of unfinished
battle-state work. No full-game or migration gate is promoted by its local tests.

## How to execute and track this plan

- Select a task only when its listed dependencies have passed their acceptance
  checks. A document or source file existing does not satisfy a gate by itself.
- Each task has a concrete output and a completion check. Paths below are proposed
  implementation/artifact locations, not claims that those files already exist.
- On completion, check its box and add the commit/build, exact command, evidence
  path, measured result and actual effort. On failure, record the blocker and
  first divergent frame/event where applicable; leave the box unchecked.
- Keep this online tracker separate from `plan/tasks.json` migration milestones.
  Preserve the current 11-fighter/4-helper/10-stage boundary and existing gates.
- Do not alter `game/`, `scripts/`, retained random/input tapes or expected results
  to make a networking test pass. Source-first questions precede runtime changes.
- Run `tools/verify.py` and `tools/check_handoff.py` after tool/document changes;
  validate contracts when schemas change, and select relevant Godot/source/Web
  checks under the repository validation policy. Re-run affected checks after fixes.

## Execution order

1. **Establish the baseline and contracts:** NET-001 through NET-008. These expose
   unsupported source timing, incomplete state and incompatible dependencies early.
2. **Make simulation repeatable:** NET-009 through NET-013.
3. **Make full state restorable:** NET-014 through NET-019.
4. **Make rollback correct without the internet:** NET-020 through NET-026.
5. **Develop the local room backend in parallel:** NET-027 through NET-035 may
   start after their early contract/runtime-selection dependencies pass; they do
   not need to wait for the entire battle refactor.
6. **Connect real WebRTC paths:** NET-036 through NET-040. A transport-only smoke
   may run early; integrated match startup waits for deterministic rollback gates.
7. **Complete the player flow:** NET-041 through NET-045.
8. **Accept the full product scope:** NET-046 through NET-048. No subset becomes
   the promised first release, and no runtime/provider experiment counts as parity.

If working alone, finish one independently testable task at a time. With parallel
workers, keep battle state ownership in one workstream and backend/transport in
another, coordinating changes to NET-005 contracts before integration.

## R0 — Baseline, contracts and feasibility

- [ ] **NET-001 — Capture the unchanged baseline**
  - Depends on: none.
  - Work/output: record repository commit, dirty-tree inventory, Godot/template and
    Chrome/OS versions; select existing local input, shared-mode, pause, timer and
    source-reference fixtures in `evidence/online/baseline/README.md`.
  - Done when: baseline commands and current failures are recorded; a later change
    can be compared without rewriting expected outputs. Do not claim all parity.

- [ ] **NET-002 — Freeze the enabled-content compatibility manifest**
  - Depends on: NET-001.
  - Work/output: generator for actual menu intersections, forms, disabled actions,
    source/runtime/generated-content hashes, engine and format versions; update
    `CONTENT_SCOPE.md` with the frozen build identity.
  - Done when: output covers the agreed 11 fighters, 4 helpers and 10 maps, is
    reproducible, detects relevant changes and its comparison fixture rejects
    mismatched builds. Integration into room startup is NET-030/NET-038.

- [ ] **NET-003 — Inventory every owner of causal battle state**
  - Depends on: NET-001, NET-002.
  - Work/output: `STATE_AUDIT.md`, mapping each state field, clock, callback,
    mutable reference and external effect to its code/source owner and save policy.
  - Done when: fighters, helpers, contacts, nested timelines, RNG, timers, pause,
    intro/KO/round flow and event queues have owners; unknowns are explicit blockers.

- [ ] **NET-004 — Resolve source scheduling before changing it**
  - Depends on: NET-003.
  - Work/output: source-first five-question answers and phase/order table for each
    scheduler path to change, with original-frame/event evidence under `evidence/online/source-audit/`.
  - Done when: timer/enterFrame/goto/placement/pause ordering is supported by evidence;
    unresolved behavior is not replaced by guessed 30 Hz timer quantization.

- [ ] **NET-005 — Define versioned network and state contracts**
  - Depends on: NET-002, NET-003.
  - Work/output: `PROTOCOL.md` plus validated schemas for room setup, input batches,
    acknowledgments, ordered controls, state fingerprints and diagnostics; define
    snapshot versioning separately from existing input recording.
  - Done when: examples and rejection cases cover epochs, slots, frame bounds,
    duplicates/conflicts, build mismatch, size limits and control/input ordering.

- [ ] **NET-006 — Validate and select the rollback coordinator**
  - Depends on: NET-003, NET-005.
  - Work/output: pinned-version/license comparison from `DEPENDENCIES.md`; run an
    isolated deterministic dummy-state fixture in actual 4.7.2 single-thread Web.
  - Done when: save/load/advance and transport hooks work in Chrome, or failures
    justify a thin adapter/project coordinator. No dependency is accepted by name alone.

- [ ] **NET-007 — Select the SQLite local backend workflow**
  - Depends on: NET-005.
  - Work/output: execute the probes in `LOCAL_DEVELOPMENT.md` using Wrangler and,
    if selected for evaluation, SolidObjects; pin runtime/package revisions.
  - Done when: two-client WebSockets, restart persistence, room isolation, atomic
    admission, expiry and local Workers-adapter compatibility have measured results;
    explicitly choose the primary runner and any optional secondary runner.

- [ ] **NET-008 — Measure the pre-refactor performance baseline**
  - Depends on: NET-001, NET-003.
  - Work/output: repeatable Chrome fixtures and profiling records for representative
    heavy attacks/helpers, frame cost, memory and resource loading.
  - Done when: hardware/browser versions and p50/p95/p99 are recorded, so later
    optimization has a baseline rather than an assumed performance problem.

## Native rollback implementation update (2026-09-23)

The real Main adapter, whole local checkpoint graph, callback/object restore,
bounded prediction/correction, fixed input delay, sound deduplication and terminal
confirmation barrier are implemented. Representative fixtures cover every enabled
fighter/helper/map, plus independent initialization, KO/round flow and fault delivery.
Timer delivery uses explicit elapsed-time samples and does not claim Flash wall-clock
callback equivalence. See [current implementation](IMPLEMENTATION.md) and
[battle evidence](../../evidence/online/battle-rollback/results.json).

The checkboxes below remain release-gate checkboxes, not file-existence indicators.
Timer authority and online controls now have native regression coverage. Remaining
work includes the per-action/mirror matrix (NET-019), Chrome/WASM checkpoint and
replay measurements (NET-008/026), and the real browser/WebRTC and connectivity path
(NET-036–046). Representative native success does not close these gates or authorize
removing unverified content from the promised first release.

## Online client integration update (2026-09-23)

The title menu now exposes the experimental online lobby, and `OnlineLobby`,
`OnlineRoomClient`, `OnlinePeerTransport` and `OnlineMatchCoordinator` are wired
through the production `Main` scene. The coordinator normalizes strict integral
JSON metadata at its boundary; the focused room-projection regression passes
validation → lobby → real `Main` configuration → fake loaded/start barriers. A
paired fake-network run covers corrected inputs, ordered intro skip, mutual
pause/resume, short recovery, the tested 10-second no-winner timeout, and a source
KO through both result submissions and a fresh epoch.

Native UI smokes, the 15-case rollback foundation suite, 602 PvP/training state
comparisons and an isolated Godot Web HTTPRequest probe are recorded in
[client-match evidence](../../evidence/online/client-match/README.md) and
[client-network evidence](../../evidence/online/client-network/README.md). The HTTP
probe did not exercise the production menu. A separate Chrome 153 transport
harness forced `iceTransportPolicy=relay`, observed both selected ICE candidate
types as `relay`, and completed bidirectional data-channel ping/pong with the
production service's credentials; see
[forced-relay evidence](../../evidence/online/turn-relay/README.md). This does not
validate the production Godot Lobby/coordinator or a complete internet match.
The user reports two side-by-side browser windows can start a match, but a
confirmed 60-state hash divergence remains under investigation; background tab
throttling is also unresolved. The original-style selection adapter is now
connected to the production Lobby's room-level connection flow. Its two-Lobby
native integration smoke verifies local-seat-only input, the fighter/helper
phase barrier, ordered host/guest `select` commands, service state arriving
before HTTP replies, return to ready controls, same-choice reselection gates,
cancellation and re-entry. The smoke uses fake room connections and does not
verify real WebRTC or a complete browser match. A separate Chrome 153 two-tab
fixture export exercised the production Lobby/RoomClient/PeerTransport and
selector against the local Worker: WebRTC channels opened, fighter/helper
choices appeared in authoritative room state, both players reached ready and
left. This used same-machine LAN mode with `ICE_SERVERS=[]`; it does not verify
cross-network/TURN, reconnect, or a full battle. The temporary fixture PCK hash
and screenshot locations are recorded in [client integration](CLIENT_IMPLEMENTATION.md).
Short invitation-code
create/join/reinvite has native and backend unit coverage, and the real
RoomClient-to-Worker smoke passes create, `join-by-code`, signaling, reinvite,
rejection of the old code, new-code join and cleanup. An earlier local attempt
reported HTTP 500, but subsequent checks passed; its cause is unknown.
Cmd+V in the online text fields was confirmed working by the user in Chrome.
The room flow now continues from fighter/helper selection into the original
`MapSelection` picker: only the owner drives it, the guest mirrors its
session/revision snapshot, the service configure is acknowledged by both peers,
and host auto-prepare is gated on both ready states. The focused map and two-Lobby
integration smokes pass, including a JSON-round-tripped service projection with
integral-float rule values, configure/ack completion, refresh failure/retry,
guest cancellation/re-entry, null-profile readiness and deduplicated prepare
retry. A Chrome run confirmed host map movement and guest mirroring, but its
configure response failed the old exact numeric comparison. Production now uses
validated integral-value comparison; a post-fix browser map configure/ack and
automatic-prepare result is pending. Full-plan gates remain open.
The deployed HTTPS service separately returned `/health` 200, create 201,
authenticated `/ice` 200 with configured STUN/TURN/TURNS entries, and leave 200;
no credential values were recorded. This proves credential issuance only,
while the separate forced-relay smoke above verifies a transport-only relay path;
neither is a complete browser battle or cross-city acceptance.
Keep every full-plan checkbox open until its own acceptance test passes; do not
change `plan/tasks.json` based on these implementation slices.

## R1 — Deterministic battle stepping

- [ ] **NET-009 — Extract an explicit match-step boundary**
  - Depends on: NET-004, NET-005, NET-006.
  - Work/output: battle-step interface and driver in `godot/`, separating a new
    input sample, simulation advancement and presentation without reordering source callbacks.
  - Done when: existing local/source fixtures retain their results; one explicit
    step has a defined input/output boundary and can run without rendering.

- [ ] **NET-010 — Make gameplay clocks and scheduled work explicit**
  - Depends on: NET-009.
  - Work/output: restorable clock/scheduler adapters for source clock, countdown
    and delayed callbacks, preserving evidence-backed event phases and pause exclusions.
  - Done when: network waiting and re-simulation cannot trigger live combat timers;
    source timer/pause fixtures match. Connection timeouts still use independent wall time.

- [ ] **NET-011 — Control initialization and random consumption**
  - Depends on: NET-009.
  - Work/output: agreed initial random state and a restorable stream, including
    random-consuming hit effects/stage behavior; retain controlled reference tapes.
  - Done when: equal setup produces equal initial state and random call sequence;
    restoring then replaying does not call `randomize()` or consume a hidden stream.

- [ ] **NET-012 — Stabilize lifecycle and callback identities**
  - Depends on: NET-009, NET-010.
  - Work/output: deterministic IDs and ordering for source instances, registered
    callbacks, placements/removals and pending scripts; preserve undefined semantics.
  - Done when: nested spawn/despawn and stop/play retain original ordering across
    runs without relying on addresses, weakref identity or incidental enumeration.

- [ ] **NET-013 — Prove independent runs agree before rollback**
  - Depends on: NET-010, NET-011, NET-012.
  - Work/output: two-instance identical-input test runner, audit-defined canonical
    state dumps and first-difference reports; restoration is introduced later in R2.
  - Done when: compared complete states agree at every checked frame in representative
    full matches; remaining causal-state omissions block R2 acceptance.

## R2 — Full-state save and restore

- [ ] **NET-014 — Define and serialize complete battle state**
  - Depends on: NET-003, NET-013.
  - Work/output: snapshot schema covering all audited causal state with deep value
    ownership and explicit stable references; no raw mutable Node/Callable references.
  - Done when: schema/serializer tests include undefined values, pending work and
    nested lifetimes; existing diagnostic `snapshot()` is not mistaken for this format.

- [ ] **NET-015 — Restore the complete object and callback graph**
  - Depends on: NET-014.
  - Work/output: controlled restore phases for objects, cross-references, registries,
    timers, playheads, contacts and global match state.
  - Done when: save/load is idempotent and restoring across creation/removal boundaries
    produces the same next state under multiple alternative subsequent inputs.

- [ ] **NET-016 — Bound and version the snapshot/input history**
  - Depends on: NET-015, NET-008.
  - Work/output: history ring with explicit retained ranges, memory accounting and
    version rejection, plus atomic restoration on valid snapshots.
  - Done when: overwrite, exhaustion, malformed/version-mismatched data and repeated
    restore cannot silently corrupt the match or destroy needed recovery state.

- [ ] **NET-017 — Reconcile presentation and external effects**
  - Depends on: NET-009, NET-015.
  - Work/output: stable event identities and payload reconciliation for sounds,
    visuals, recording, network output and final result publication.
  - Done when: correction can turn hit into block without duplicate audio/network
    messages; gameplay-causing hit effects remain simulated and predicted KO cannot exit early.

- [ ] **NET-018 — Add restore-and-replay consistency tests**
  - Depends on: NET-015, NET-016, NET-017.
  - Work/output: SyncTest-style single- and multi-frame restoration harness,
    restoring before/inside/after complex events and reporting the first difference.
  - Done when: identical inputs produce identical complete state and logical events
    after repeated restoration; snapshots do not share mutable data with live state.

- [ ] **NET-019 — Audit save/restore across the entire enabled roster**
  - Depends on: NET-002, NET-018.
  - Work/output: per-action/helper/stage coverage matrix, including mirrors,
    boundaries and known cross-character interactions.
  - Done when: every enabled entry has passing evidence; unverified enabled content
    blocks release instead of being removed from the online menu.

## R3 — Rollback without transport uncertainty

- [ ] **NET-020 — Implement immutable numbered input history**
  - Depends on: NET-005, NET-009, NET-016.
  - Work/output: sample-once local input and per-slot/per-epoch receive buffers;
    derive edges consistently and isolate from live keyboard during replay.
  - Done when: hold/release, repeated packets, frame gaps and conflicting inputs
    have explicit behavior; missing input is not silently changed into a release.

- [ ] **NET-021 — Add bounded prediction and agreed input delay**
  - Depends on: NET-020.
  - Work/output: hold-last-input predictor, neutral initial state, fixed match delay
    and separate prediction-window limit.
  - Done when: zero/short/maximum windows behave correctly; exceeding the window
    waits explicitly and control/menu operations are never speculatively invented.

- [ ] **NET-022 — Restore the earliest mismatch and catch up**
  - Depends on: NET-018, NET-021.
  - Work/output: correction scheduler that restores before the first wrong input
    and replays to the current frontier without external side effects.
  - Done when: multiple late inputs, cascaded corrections and repeated corrections
    match the reference; insufficient history fails instead of skipping needed input.

- [ ] **NET-023 — Order shared controls against battle frames**
  - Depends on: NET-005, NET-022.
  - Work/output: idempotent pause/resume/skip/exit/result operations with agreed
    effective boundaries, operation ordering and start/resume barriers.
  - Done when: conflicting/simultaneous controls and pause-time resume operations
    cannot diverge; network callbacks never mutate state mid-step or require a ticking pause.

- [ ] **NET-024 — Build a deterministic network-fault simulator**
  - Depends on: NET-022, NET-023.
  - Work/output: seeded delay/jitter/loss/burst/duplicate/reorder/asymmetry scenarios
    against a no-network baseline, plus reproducible fault schedules.
  - Done when: confirmed states and outcomes agree after correction, and terminal
    failure/recovery behavior is explicit rather than hidden by retries.

- [ ] **NET-025 — Compare state and retain local diagnostics**
  - Depends on: NET-014, NET-023, NET-024.
  - Work/output: canonical complete-state hashes at equal confirmed frames and
    bounded local input/event/diff bundles with no credentials or raw SDP.
  - Done when: deliberate desync stops without a winner; reports identify missing
    history and support deterministic reproduction where retained history permits.

- [ ] **NET-026 — Pass full-content rollback and performance gates**
  - Depends on: NET-008, NET-019, NET-024, NET-025.
  - Work/output: full enabled-content rollback suite and measured Chrome profile
    candidates for save/load, catch-up, total frame budget and memory limits.
  - Done when: repeated worst-window corrections cause no growing backlog, all
    enabled content passes, and numerical limits are supported by recorded measurements.

## R4A — Local SQLite room and signaling service

- [ ] **NET-027 — Scaffold one reproducible backend project**
  - Depends on: NET-005, NET-007.
  - Work/output: proposed `services/matchmaking/` with TypeScript, pinned runtime,
    package-manager lockfile, Wrangler config and local/test scripts. Use tools to
    add dependencies; choose npm if no repository JS package-manager convention emerges.
  - Done when: clean-checkout install/start/test is repeatable; local databases,
    secrets and generated files are ignored; no cloud deployment is needed for local tests.

- [ ] **NET-028 — Persist room lifecycle in SQLite**
  - Depends on: NET-027.
  - Work/output: schema/migrations for room identity, setup revision, seats,
    lifecycle/epoch and expiry; storage boundary for the selected runtime.
  - Done when: room isolation, atomic transitions, rollback-on-error and restart
    persistence pass. No per-frame input or battle snapshot is stored here.

- [ ] **NET-029 — Implement invitations and two-seat admission**
  - Depends on: NET-028.
  - Work/output: random invitations and separate scoped seat credentials; joining,
    guest replacement and same-page reattachment with explicit authorization.
  - Done when: racing third entrants, replayed/revoked tokens, wrong-room requests,
    malicious nicknames and duplicate admissions cannot steal a seat or alter another room.

- [ ] **NET-030 — Implement setup, readiness and match epochs**
  - Depends on: NET-002, NET-005, NET-029.
  - Work/output: each player's fighter/helper choice, owner map/rules, revisioned
    readiness, build checks and idempotent creation of a new match epoch.
  - Done when: edits invalidate ready, incompatible builds cannot start, and duplicate
    ready/start operations cannot create two different matches.

- [ ] **NET-031 — Add room WebSockets and authenticated signaling**
  - Depends on: NET-029, NET-030.
  - Work/output: bounded offer/answer/ICE forwarding, room notifications, reconnect
    handling and state reconstruction after hibernation/instance eviction.
  - Done when: both clients negotiate and observe ordered room revisions; stale
    candidates cannot affect another epoch; handler memory is not required for correctness.

- [ ] **NET-032 — Limit room admission and service usage**
  - Depends on: NET-028, NET-029.
  - Work/output: at most 10 live leases, idempotent allocation/release, bounded
    request/storage/signaling rates and budget-headroom counters.
  - Done when: concurrent creates cannot overbook; crashes/retries do not leak
    capacity indefinitely; the coordinator never relays all gameplay traffic.

- [ ] **NET-033 — Implement expiry, departure and room outages**
  - Depends on: NET-030, NET-031, NET-032.
  - Work/output: 30-minute idle expiry, guest replacement, owner close and room
    recovery while an existing peer match may continue independently.
  - Done when: active matches are not treated as idle, outage is not explicit exit,
    and expired/recycled rooms cannot reassign an ongoing battle's epoch or members.

- [ ] **NET-034 — Configure STUN/TURN and scoped credentials**
  - Depends on: NET-029, NET-032.
  - Work/output: server-only issuer secret, authenticated short-lived credentials,
    provider configuration, lifetime/revocation policy and local issuer test doubles.
  - Done when: secrets never reach exports/logs, issuance is limited and invalid
    membership is rejected; local stubs are not claimed to test real TURN connectivity.

- [ ] **NET-035 — Run backend contract and failure tests**
  - Depends on: NET-028, NET-029, NET-030, NET-031, NET-032, NET-033, NET-034.
  - Work/output: real local WebSocket plus SQLite restart tests, expiry/alarm tests
    and the same externally observable room contract against each supported runner.
  - Done when: all invariants pass in Wrangler; any SolidObjects runner also passes
    its supported profile and documents hibernation/runtime differences explicitly.

## R4B — WebRTC integration

- [ ] **NET-036 — Implement the Chrome WebRTC adapter**
  - Depends on: NET-005, NET-006, NET-031.
  - Work/output: connection/channel lifecycle, frequent polling, binary messages,
    reliable control channel and bounded low-latency input channel.
  - Done when: two independent Chrome instances connect/disconnect cleanly and
    message size/backpressure/failure states are handled without blocking simulation.

- [ ] **NET-037 — Deliver numbered inputs reliably at application level**
  - Depends on: NET-020, NET-024, NET-036.
  - Work/output: recent-input redundancy, acknowledgments, bounded retransmission
    and per-channel epoch/sequence/frame validation.
  - Done when: dropped transport packets do not lose required controls; every
    retention limit invokes explicit waiting/failure instead of unbounded queues.

- [ ] **NET-038 — Integrate preloading and the shared start barrier**
  - Depends on: NET-023, NET-026, NET-030, NET-036, NET-037.
  - Work/output: agreed setup/content/profile, resource preload, initial state
    comparison and start barrier with timeout/duplicate handling.
  - Done when: both peers begin the same epoch/state; a late or mismatched peer
    cannot start an independent match; old rematch packets are ignored/rejected.

- [ ] **NET-039 — Choose measurable connection profiles**
  - Depends on: NET-026, NET-036, NET-037.
  - Work/output: preflight path measurements, fixed per-match delay/window agreement
    and clear feedback for unsupported conditions; update `VALIDATION_PLAN.md`.
  - Done when: measured performance and input-arrival distributions justify profile
    limits; no mid-match silent delay change or unsupported zero-latency promise.

- [ ] **NET-040 — Validate real direct and relayed mainland paths**
  - Depends on: NET-034, NET-035, NET-036, NET-039.
  - Work/output: connection attempts/times/failures across city/operator/home/hotspot
    pairs, forced TURN and UDP-restricted cases; select provider from evidence.
  - Done when: documented sample sizes meet the measured trial criteria and budget;
    same-machine tabs and local SQLite tests do not substitute for this gate.

## R5 — Complete player flow

- [ ] **NET-041 — Build room, selection and readiness UI**
  - Depends on: NET-030, NET-031, NET-038.
  - Work/output: create/invite/join, nickname, two seats, both selections, owner
    settings, ready cancellation, connecting/failure feedback and setup revision handling.
  - Done when: two users reach a real match through the UI without developer tools;
    all frozen content is selectable with source UI and existing action gates retained.

- [ ] **NET-042 — Integrate shared intro skip and mutual pause**
  - Depends on: NET-023, NET-038, NET-041.
  - Work/output: either player's joint skip, pause request/accept and both-ready
    resume, separated from source-defined hit/super pauses.
  - Done when: simultaneous/late/duplicate operations converge at shared boundaries;
    paused gameplay does not prevent network polling or resume negotiation.

- [ ] **NET-043 — Implement the 10-second interruption policy**
  - Depends on: NET-025, NET-033, NET-037, NET-038, NET-042.
  - Work/output: bounded prediction/wait, same-page recovery from retained history,
    timeout-to-no-result and continued gameplay during room-only outages.
  - Done when: background throttling, sleep, path loss and deadline races behave
    explicitly; page refresh does not resume; room loss alone never halts a healthy peer match.

- [ ] **NET-044 — Commit results, exit and rematch safely**
  - Depends on: NET-017, NET-023, NET-030, NET-033, NET-043.
  - Work/output: confirmed terminal-state agreement, one result per epoch, no-result
    exits/desync, owner closure and new-epoch rematch after service revalidation.
  - Done when: predicted/corrected KO never prematurely tears down the match; stale
    results cannot affect the next match; room outage blocks new matches only.

- [ ] **NET-045 — Expose player-triggered diagnostics**
  - Depends on: NET-025, NET-041, NET-043, NET-044.
  - Work/output: local download UI with bounded retention, build/profile/input/state
    evidence and explicit truncation, plus developer reproduction instructions.
  - Done when: no automatic upload or secret/SDP leak occurs; missing data cannot
    silently turn a reproduction into live-input playback.

## R6 — Release acceptance

- [ ] **NET-046 — Pass full-content online and local regression matrices**
  - Depends on: NET-019, NET-026, NET-039, NET-040, NET-041, NET-042, NET-043, NET-044, NET-045.
  - Work/output: Chrome two-computer complete matches over the agreed profiles,
    action/helper/stage coverage, interaction cases and retained offline/source checks.
  - Done when: all enabled content passes, confirmed states agree and remaining
    coverage limits are explicit. No removal of failed content to satisfy this task.

- [ ] **NET-047 — Soak 10 rooms and verify actual operating cost**
  - Depends on: NET-035, NET-040, NET-046.
  - Work/output: concurrent full-match soak, reconnect/hibernate/deploy-failure
    drills, memory/backlog graphs, account meters and revised `COSTS.md`.
  - Done when: admission and recovery hold at target scale, no persistent leaks
    appear, and usage/headroom justify the US$10 target without claiming a strict billing cap.

- [ ] **NET-048 — Prepare a reproducible release and friend trial**
  - Depends on: NET-046, NET-047.
  - Work/output: build/content fingerprint, `dist/web/` build instructions,
    backend version/config, local-development runbook, rollback procedure,
    acceptance report and remaining original-parity limits.
  - Done when: a clean checkout reproduces the tested artifacts, all checks pass
    and the trial report references evidence. Publishing/paid deployment follows
    actual user authorization; this design request does not itself perform either.

## Completion record template

For each checked item, append a record here or link a small evidence index:

```text
Task: NET-xxx
Status: completed | blocked | in_progress
Build/commit and dependency evidence:
Artifacts:
Commands and measured result:
First unresolved difference / acceptance limits:
Actual effort:
```

Retain raw local databases, exported builds, profiling traces and large run logs
outside committed source. Commit compact evidence indexes and reproducible tests
according to project conventions. Update this checklist and its dependency evidence
as implementation progresses; do not pre-check work because it is planned.
