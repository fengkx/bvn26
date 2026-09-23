# Offline rollback implementation progress

2026-09-22, updated 2026-09-23. The native rollback path now runs the real Main
battle: explicit inputs and callback envelopes → full local checkpoint → restore
and re-simulate after a late input. The title menu now exposes an experimental
online lobby wired to the coordinator; actual Chrome/WebRTC battle acceptance,
browser timing and the full online release gates remain separate and pending.

## Current battle API

- `godot/rollback_battle.gd` owns the real match boundary. Configure a fresh PvP
  scene at tick zero with automatic stepping disabled, explicit source time,
  recorded intro/KO/training timers and a seeded shared RNG. It adopts empty BODY
  timeout queues into recorded mode and disables direct Main input handlers.
- Submit each frame's immutable clock/intro/callback envelope with
  `set_frame_events(frame, time_ms, skip, events)` **before** advancing that frame.
  Countdown and BODY timeouts use `after_actor_advance`; nextfight uses the existing
  `before_root_observer` path. No frame-count-to-Flash-timer equivalence is assumed.
  The caller must provide the external event journal; this API does not create a
  production network timer authority or silently synthesize missing callbacks.
- `godot/rollback_session.gd` accepts immutable per-slot/per-epoch inputs, predicts
  held buttons, waits at its prediction limit, restores before a mismatch and
  recomputes through the simulated frontier. `configure(..., input_delay)` fixes
  the delay for the match; `sample_local` numbers sampled inputs at the delayed
  frame, with neutral startup frames. A repeated sample cannot change its value.
  `rollback_test_session.gd` remains a compatibility entry point for old fixtures.
- `save_state/validate_state/load_state` on the battle adapter use
  `godot/battle_checkpoint.gd`. Script objects and their named callables/weak links
  are rebuilt in phases, while native nodes needed by retained checkpoints are
  kept in a battle-local pool. Detached hit effects, stage attacks, nextfight timers
  and frozen shadows can therefore return without rerunning placement scripts.
  Nodes from the abandoned future are detached before the saved graph is installed.
- The graph preserves shared arrays/dictionaries, typed containers, generated BODY
  and projectile locals, null versus false, pending frame work, callback order,
  RNG state, clocks, timeline/sound generations, helpers, contacts, camera, HUD,
  intro, KO and round state. Read-only compiled tables remain shared. Scheduled
  display placements retain identity with those tables, including blackMu children.
- Native coordinates are restored as position/rotation/scale/skew, not only a
  transform matrix: Godot's decomposition of negative X scale otherwise changes
  later facing behavior. Restoring display lists does not execute sounds or advance
  retained child clocks. KO dispatch cycles are unbound before replacing old roots.
- `rollback_presentation.gd` deduplicates sounds by frame, owner and source event;
  logical sound bookkeeping still runs. Final scene changes stay behind the
  confirmation barrier. `commit_result()` refuses unconfirmed results, then closes
  the rollback owner and uses the existing selection transition. `close()` is a
  teardown operation, not a conversion of pending recorded timers back to live time.

The checkpoint format is **local to its owning battle and pinned Godot build**.
Its value graph contains no live Objects or Callables; immutable resources and
retained native nodes are resolved by the owner's cache. It is not an importable
savegame or a network snapshot exchange format. Malformed, foreign, expired or
modified checkpoints are rejected before any live mutation. A fast local cache
index is checked against the entire encoded graph; it is not a desync checksum.

## Current validation and limits

Run `python3 tools/test_rollback_foundations.py --godot /path/to/Godot`.
The runner checks success markers, script failures and native errors (except the
known headless macOS certificate lookup warning and shutdown-only audio playback
references, which are classified from verbose instance types and reported per test).
Other native errors still fail the runner. Evidence and reviewed hashes
are retained in [battle rollback results](../../evidence/online/battle-rollback/results.json).

The native checks cover real delayed input correction, reordered/duplicate bursts,
waiting during a temporary outage, a second independently initialized battle,
negative scale/RNG/health restoration, malformed-state atomic rejection, frozen
shadow retirement/revival, and repeated restore/replay on 11 enabled fighters,
4 helpers and 10 maps. There are eight checkpoints per roster pairing. Separate
round fixtures cover KO, nextfight, a later round, and a confirmed terminal result.
The earlier controller, queue, RNG, input and source-reference regressions remain.

These are representative input sequences across the full enabled list, **not an
exhaustive per-action/mirror/interaction matrix**. The timer envelopes in these
fixtures are explicitly synthetic external delivery schedules. No new original
Flash timer profile, Chrome/WASM comparison, p95/p99 frame budget, internet match,
shared online-control protocol or room/transport integration is certified here.
The current renderer still materializes intermediate replay frames; a render-free
fast path remains a performance task. No original migration milestone is promoted.

## Historical foundation interfaces

The sections below record the earlier component deliveries and their evidence;
statements about missing whole-Main restoration describe those earlier stages.


- `godot/manual_match_step.gd` exposes one explicit display step with both full
  ten-button samples, intro skip and an externally supplied intro callback. It
  delegates the existing `_advance_fight` order. It rejects skipped frame numbers,
  incomplete inputs, automatic stepping, live gameplay timers, input playback or
  recording, CPU matches and unsupported round-transition entry states.
  The caller must initialize the match with recorded timers, seed the shared RNG,
  provide the clock and set intro polling to recorded delivery. Hidden title-menu
  timers must be stopped in this test profile. Intro audio out-point timers are
  recognized specifically by their audio-player cleanup callback.
  This is an offline developer adapter, not a public online match driver; direct
  UI controls and external signals must not be delivered concurrently. It still
  produces presentation effects and is not a side-effect-free rollback adapter.
- `SourceRandom.use_seed/save_state/validate_state/load_state` preserves the
  actual RNG seed/state, tape cursor, consumption counters, failure and diagnostic
  records. Restoring never calls `randomize`. Existing live behavior is unchanged.
- `SourceClock.use_explicit_time/set_explicit_time/save_state/validate_state/load_state`
  makes `getTimer` observations caller-owned, while retaining recorded-tape mode.
  Normal advancement rejects backward time; restoration may restore an earlier
  time. A live clock snapshot is rejected for deterministic restoration. This API
  does **not** infer timer deliveries from frame count or replace source intervals.
- `SourceCallbackRegistry.save_state(identify)/load_state(state, resolve)` saves
  registration IDs, next ID, current tick, stable target IDs, methods and placement
  ticks. It preserves insertion and reverse dispatch order. Restore resolves all
  references before replacing entries; missing targets leave the registry intact.
  Taking/restoring a registry while dispatching is rejected. The owner still must
  recreate the target objects and restore their state before resolving references.
- `godot/simulation_state.gd` supplies a version/build/frame envelope and owned
  scalar/array/string-keyed-dictionary values, canonical hashes and first-difference
  paths. Null and false remain distinct; binary Variant encoding preserves int64
  RNG state. Objects, Callables, RIDs, non-finite values and excessive nesting are
  rejected. The adapter declares required owners; this utility cannot discover
  omitted causal state or certify that an arbitrary owner list is complete.
  The binary format is for the pinned Godot build, not a cross-version/network
  wire-format guarantee.
- `godot/rollback_test_session.gd` is an **offline test harness**, not the selected
  production rollback dependency. It accepts immutable numbered inputs, rejects
  conflicting duplicates/old epochs/out-of-range frames, predicts held buttons,
  restores before a wrong prediction and recomputes subsequent frames. It retains
  bounded frame history, exposes memory size and waits at its prediction limit.
  `confirmed` is the contiguous received-input watermark; state comparison also
  requires that frame to have been simulated. Adapter failures are terminal.
  The adapter owns validation/atomic restoration and must publish no external
  effects from `advance`. Input delay, shared controls, output reconciliation,
  transport retries, desync termination and a byte-memory budget are not supplied.

No dependency was installed; NET-006's production library decision is still open.
The small harness exercises the save/load/advance contract without choosing a
network stack or changing any gameplay rule.

## Measured checks

Baseline: clean `28e0382bf14a0058efadc4e5906e16230d5d2cb8`, Godot
`4.7.2.stable.official.ed1daf0bf`, macOS 15.7.5 / 24G624. The engine used was
`/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot`.

```sh
python3 tools/test_rollback_foundations.py --godot /path/to/Godot --report /tmp/rollback-results.json
python3 tools/test_shared_modes.py --godot /path/to/Godot
```

The runner checks timeout, exit code, success markers and script/assertion errors.
Eight native checks pass. [Retained results](../../evidence/online/foundations/results.json):

- RNG/clock restore in seeded and recorded modes; invalid-state rejection without
  changing the service; registry order/placement/ID restoration and missing targets.
- Value isolation, null/false, exact int64 binary roundtrip, build/version/owner
  mismatch rejection, object/callback rejection, stable hashes and first differences.
- A synthetic dynamic-child fixture using the real RNG/clock services: 70 starting
  boundaries × 10 re-simulated frames, alternative continuations and owned snapshots.
- 120 synthetic frames with five-frame reverse-order input bursts and duplicates:
  **73 corrections / 201 re-simulated frames**; all retained corrected states agree
  with the reference. A six-frame prediction window waits at its limit; zero-window
  operation waits until both inputs exist. Retained test state measured 222,508
  bytes after the final prediction sequence, not a game-memory estimate.
- Real Main scene: manual stepping and the previous direct call path agree over
  **330 frames in two fresh runs**, including intro, movement/attacks and selected
  fighter fields, RNG and clock state. The callback schedule is synthetic and
  explicitly supplied. This comparison is **not complete-state determinism**.
- Existing registry, AI random, hit-effect clock/random, timeout and 330-frame
  recorded-input scene checks pass.
- Shared-mode immutable original references pass before and after the change:
  PvP **602/602**, training timer **602/602** measured actor states.

The manual test first rejected the hidden title hint timer, then the intro audio
cleanup timer. The fixture now stops the unrelated menu timer; the adapter only
excludes the verified audio cleanup callback from its gameplay-timer guard.
No gameplay timer was disabled to disguise a determinism failure.

No Chrome export/performance test or complete enabled-roster rollback test has
run for this change. Existing native certificate/shutdown diagnostics are not
presented as gameplay failures or as clean-log success. No original capture,
expected output or numerical comparison threshold was changed.

## Remaining implementation, in order

1. Finish the [state-owner audit](STATE_AUDIT.md), including dynamic factories,
   inheritance, stable reference binding and every outstanding source scheduling
   phase. The inventory below is a review map, not an exhaustive field manifest.
2. Replace pending bound operations with restorable descriptors where needed,
   preserving generation and source queue order; implement complete object graph
   reconstruction for fighters, helpers, nested clips, effects and round flow.
3. Integrate all timer/control deliveries and presentation reconciliation into
   an audited full-match step. Do not let predicted KO reload/destroy the scene.
4. Connect that full adapter to restore/replay tests. Exercise all 11 fighters,
   four helpers and ten stages, then run Chrome resource/performance measurements.

NET-009 through NET-026 remain unchecked. Partial interfaces and synthetic test
success do not satisfy their full acceptance criteria. No migration milestone in
`plan/tasks.json` is promoted by this networking work. Actual effort was not timed
reliably and is left unrecorded rather than estimated from code volume.

## Continuation: reconstructible controllers and pending operations

The next implementation adds `godot/controller_checkpoint.gd` and
`godot/pending_operation_state.gd`, plus recorded-timeout save/load in
`AiSourceTimeouts`. These are object-owner restoration components; they are not
yet an atomic whole-Main checkpoint transaction.

- Controller snapshots include generated locals (including inherited predicate
  state), receiver methods, projectile model/captured initial speed, pending
  natural child frames, runtime aliases, current tick and generation counters.
  New objects are constructed without executing `_create_instance` or
  `bind_adapter`: those normal initialization paths would reset source playheads,
  replace locals and queue frame scripts again.
- `prepare` validates the source hook/type, exact set and types of generated
  locals, unique generations/registrations, source projectile model and alias
  targets. It returns a prospective graph without touching the live host.
  `commit` installs it without callbacks. The caller must also restore fighter
  state, the shared callback registry and pending work before advancing again.
- A removed projectile may still be retained by a pending operation. Such
  retired instances are reconstructed with their original generation and remain
  inactive according to the existing `instances.alive` check. Pass pending-call
  targets as `save(host, retained_targets)`; this is a required graph-root input,
  not automatic discovery of every external reference. Preserve dead alias keys,
  because source lookup checks key presence separately from target liveness.
- Pending-operation snapshots store sequence, stable target ID, named method and
  owned arguments. Preparing them rebinds to reconstructed objects without
  executing the calls. Unknown targets, anonymous closures, unsupported values
  and invalid ordering are rejected. Existing live queues remain Callables;
  conversion happens only at the checkpoint boundary.
- Recorded timeouts now preserve the next ID, pending registration order,
  requested delay and named callback descriptor. Loading validates everything
  before replacing the queue and emits no artificial registration/fire events.
  Live Timer snapshots are rejected: a caller must separately retain the actual
  external delivery schedule rather than infer deadlines from frame number.

The continuation runner has **11 passing native checks**, retaining the previous
eight and adding controller reconstruction, timeout reconstruction and the
existing source projectile driver regression. The controller test executes the
real Ichigo projectile path, releases the old object, reconstructs it, restores
the shared registry, then runs the rebound pending frame-5 rename. It also tests
nondefault generated locals, malformed local types, snapshot isolation, renamed
aliases and retired-generation no-op behavior. The timeout test rebinds to a new
BODY target and verifies nested IDs, atomic rejection and live-mode rejection.
The fighter playhead fields used by the projectile fixture are restored explicitly
by that fixture; **it is not a full fighter/battle serializer**.

Source evidence for this addition: `scripts/fighter/yihu.json`,
`DefineSprite_638/frame_327/PlaceObject2_99_28/CLIPACTIONRECORD onClipEvent(enterFrame).as`
and `DefineSprite_99/frame_5/DoAction.as` (rename to `abcd`); BODY timeout calls
originate in `DefineSprite_638/frame_1/DoAction.as`. Placement/new-generation,
next-tick dispatch, conditional hit goto, delayed rename and stale-generation
invariants remain those exercised by `ai_projectile_driver_smoke.gd`.
No source frame script, placement, goto or dispatch order was changed. This is
native restoration evidence, not a newly captured Flash or whole-match parity run.

Continuation evidence and reviewed code hashes:
[controller checkpoints](../../evidence/online/controller-checkpoints/results.json).
The shared PvP and training-timer references still match 602 actor states each.
NET-015 is now partially implemented at these owners; full state/side-effect/
round/roster/Chrome gates remain open. No production online mode is enabled.
