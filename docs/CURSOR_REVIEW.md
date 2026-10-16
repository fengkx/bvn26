# Cursor whole-repo review (2026-10-16)

Branch: `cursor/review-fixes` @ `ea6fb79c` (pre-fix). Scope: correctness,
Flash 1:1 parity gaps, determinism/rollback hazards, online robustness, dead
code, and test gaps. Style-only notes omitted. Process rules from
[SOURCE_FIRST.md](SOURCE_FIRST.md). Intentional Flash deviation
`_clear_interrupted_super_preparation` is out of scope (bytes must stay).

Known Godot smoke failures (`ai_colors`, `ai_context`, `ai_host`,
`title_menu_source`, `ai_hit_gate`) remain waived only under the signatures in
`evidence/characters/itachi/baseline-godot-failures.json`.

## High

### H1 — Host exits recovery before guest applies `recovery_commit`

- **Evidence:** `godot/online_match.gd:1481-1483` (P1 `_complete_recovery` immediately
  after a successful `recovery_commit` send); `godot/online_match.gd:1486-1498`
  (P2 completes only on receive); `godot/online_match.gd:467-471` (only
  `recovering`/`paused` stop simulation).
- **Risk:** After hash agreement the host can leave recovery and call
  `rollback.step()` while the guest has not yet received/applied the commit.
  Host advances `frontier`, emits inputs/hashes, then hits `state_mismatch` or
  leaves the guest wedged until `peer_disconnect_timeout`.
- **Fix plan:** Keep P1 in `recovering` after sending `recovery_commit`. P2
  validates commit, completes, and replies with `recovery_commit_ack`. P1
  completes only on that ack. Add a regression that holds the commit/ack so P1
  cannot simulate early.
- **Status:** Fixed in this branch.

### H2 — WebRTC data-channel loss has no match-time renegotiation

- **Evidence:** `godot/online_match.gd:2345-2352` (disconnect/failed → recovery
  only); `godot/online_match.gd:1520-1537` (signaling reconnect reopens the
  WebSocket, not `WebRTCPeerConnection`); `godot/online_peer_transport.gd:327-331`
  (`reliable_sequence_gap` → permanent `transport_error`); sequences reset only in
  `configure`/`close_peer` (`godot/online_peer_transport.gd:403-408`).
- **Risk:** NAT rebinding, background tabs, or one lost reliable SCTP message
  poison the channel. Recovery traffic uses the dead peer; matches stall ~30s
  then abort. Real paired-browser acceptance is still open
  (`docs/STATUS.md`).
- **Fix plan:** Bounded match-time renegotiation (`resumeNegotiationId` on the
  worker, `close_peer` + new offer/answer, reset sequences, replay inputs from
  the rollback floor, then recovery compare). Needs protocol/service design
  choices (epoch vs negotiation reuse, guest/host offer roles).
- **Status:** Left. Requires an explicit product/protocol decision; not safe
  as a silent local patch.

## Medium

### M1 — Cancel hit stash never reaches the production receiver path

- **Evidence:** `godot/fighter_runtime.gd:1164-1183` (`_stash_current_attack` before
  `start_action`); `godot/fighter_runtime.gd:727-731` (stash returned only when
  `source_receiver` is false); `godot/combat_resolver.gd:11-14` (production
  `resolve_incoming` always uses `source_receiver=true`); `main.gd` never calls
  `CombatResolver.resolve_pair` (tests only).
- **Risk:** Same-tick cancel clears the display list / `_hit_instances` via
  `start_action` (`fighter_runtime.gd:1045-1046`) before the defender `bdmn`
  `checkHit` callback. Flash still resolves contact that was active on that
  display tick; production drops it. Comment at `fighter_runtime.gd:164-165`
  documents the intent against the obsolete `resolve_pair` path.
- **Flash evidence:** Shared defender `checkHit` / getHitObj on BODY
  (`DefineSprite_2`); cancel windows are compiled into `command_catalog`. Stash
  was added to preserve pre-`start_action` contact for that same tick — wiring
  was incomplete for the compiled receiver hooks.
- **Fix plan:** Return `_stashed_attack` for both polling modes; clear unused
  stash after `source_callbacks.dispatch` so it cannot leak into the next tick.
  No per-character branches.
- **Status:** Fixed in this branch.

### M2 — `SourceRandom` / `SourceClock` failures do not stop `main._advance_fight`

- **Evidence:** `godot/source_random.gd:118-124` (tape mismatch → `failure` + NAN);
  `godot/hit_effect_runtime.gd:122-126` (silent skip); `godot/main.gd` never
  reads `source_random.failure` / `source_clock.failure`. Probes and
  `manual_match_step.gd:96-97` already treat failure as fatal.
- **Risk:** Online/seeded and recorded paths can fork silently after a consumer
  mismatch while the match keeps advancing.
- **Fix plan:** After combat callbacks (and before completing the tick), if either
  stream has `failure`, set `match_input.error` and stop via `_check_match_input`.
- **Status:** Fixed in this branch.

### M3 — Per-client sparse checkpoint URL/CLI flags are not negotiated

- **Evidence:** `godot/online_match.gd:132-163` (local URL/CLI overrides);
  `godot/online_match.gd:268-270` (applied only locally); pair smoke
  `--mixed-saves` (`godot/tests/online_match_pair_smoke.gd:59-61`) shows divergent
  save density.
- **Risk:** One peer with `?online_sparse=0` and another on defaults produces a
  deterministic `state_mismatch` under identical inputs.
- **Fix plan:** Include `sparseSaves` / `checkpointStride` on `match_ready`; abort
  with `checkpoint_policy_mismatch` when they differ. Keep overrides for paired
  measurement, but fail closed at the start barrier.
- **Status:** Fixed in this branch.

### M4 — Input-channel send failures are silent

- **Evidence:** `godot/online_match.gd:1271-1272` and `:1370-1371` ignore
  `send_peer_message` false; reliable sends already queue/recover
  (`godot/online_match.gd:2063-2072`).
- **Risk:** While the input channel is closing, batches drop with no recovery
  trigger until ACK timeout (10s+) or 60s abort.
- **Fix plan:** On input send failure, `_begin_recovery("input_send_failed")`
  when not already recovering.
- **Status:** Fixed in this branch.

### M5 — `OnlineRoomClient._accept_state` silently drops invalid payloads

- **Evidence:** `godot/online_room_client.gd:680-682` returns without emitting
  `error` when validation fails. The WebSocket path validates first
  (`:649-651`), but HTTP/command and lobby refresh paths call `_accept_state`
  directly.
- **Risk:** Schema drift or a bad projection leaves `_room_state` stale while the
  socket stays up; lobby UI / auto-prepare disagree with the server.
- **Fix plan:** Emit `error("invalid_room_state")` on validation failure (keep
  silent skip only for regressing revision).
- **Status:** Fixed in this branch.

### M6 — Hash confirmation backlog aborts without attempting recovery

- **Evidence:** `godot/online_match.gd:1711-1712` / `:1724-1725`
  (`MAX_HASH_HISTORY := 256` → `hash_confirmation_stalled`).
- **Risk:** Partial reliable loss or a stuck peer grows pending hashes until
  hard abort (~7680 frames of skew).
- **Fix plan:** At a lower watermark, force recovery / re-ICE instead of immediate
  abort; depends on H2 renegotiation for lasting repair.
- **Status:** Left pending H2.

## Low

### L1 — Dual body-pressure paths (compiled BODY vs `resolve_body_collision`)

Production uses compiled BODY `on_enterframe`; `CombatResolver.resolve_body_pair`
is test/smoke-only. Drift risk if tests pass the alternate path. Prefer asserting
via `run_body` / `_advance_fight`.

### L2 — Global callback newest-first order is intentional Flash parity

`godot/source_callback_registry.gd:20-37` and
`evidence/probes/schedule/README.md` (new instances before older across subtrees;
sibling depth high→low). Not a P1/P2 bug. The `resolve_body_pair` “p1 then p2”
comment applies only to the unused test helper.

### L3 — Live random `consumed` truncated at 4096

`godot/source_random.gd:7` / `:138-142`. Online uses `use_seed`; checkpoints also
store RNG `seed`/`state`, so simulation restore stays correct. Truncation mainly
hurts long live tape audits.

### L4 — Fingerprints allow raw floats

`godot/simulation_state.gd:17-18`, `:88-94`. Wire integers are validated
(`online_match_values.gd`); cross-engine float drift remains a residual online
hash risk. Quantize only with a dedicated golden test.

## Intentional deviation (do not change)

`_clear_interrupted_super_preparation` — documented anti-deadlock when a real hit
interrupts `bs` before `bsd` init. Protected bytes:
`evidence/characters/itachi/review-mediums/preservation.json`.

## Test gaps addressed here

- Recovery commit/ack barrier (lockstep review regression must still pass; pair
  short-recovery covers the happy path).
- `match_ready` checkpoint policy mismatch (pair smoke `--mixed-saves` expects
  start failure).
- Cancel stash: protected by existing cancel + hit regressions; no per-character
  test added beyond stream-failure and online policy checks.

## Out of scope / not upgraded

Full Flash golden traces (R-01), full AI acceptance, browser WebRTC/TURN, and the
five inherited Godot smoke failures remain as documented in `STATUS.md` /
`REGRESSION_INDEX.md`.
