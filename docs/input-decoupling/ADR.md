# Input decoupling for future friend-room PvP

Status: Input-boundary implementation authorized and implemented 2026-09-22;
see [implementation and verification](IMPLEMENTATION.md).
Date: 2026-09-11.

## Confirmed decisions

- Q1: implement input decoupling only. Extracting an externally driven battle
  step is deferred.
- Q2: the first future online experience targets friends joining a room.
  Preserve room to support public casual matches later.
- Q3: cover fighter controls, intro skipping, pause and resume. Selection,
  map navigation and settings UI stay outside this change.
- Q4: include developer input recording and playback alongside automated tests;
  no player-facing replay browser is requested.
- Q5: record one match from its initial setup, including the intro, until exit.
  Playback recreates that setup and runs from the beginning; arbitrary mid-match
  capture and restoration are excluded.
- Q6: guarantee faithful input playback. Validate matching battle outcomes only
  in explicitly controlled regression conditions; arbitrary live-match outcome
  reproduction is excluded.

## Pre-refactor implementation evidence (2026-09-11)

- `godot/game_session.gd`: `fighter_input` maps configured keys to ten logical
  held buttons; `is_slot_down` reads the global Godot input device.
- `godot/player_body_driver.gd`: `begin_tick` copies logical input, and
  `Context.source_key` exposes it to the existing source controller.
- `godot/main.gd`: `_input_for` still samples the local device, while
  `_advance_fight` reads intro-skip keys independently. `_input` delivers pause
  UI events separately from the physics callback.
- `godot/pause_menu.gd`: opening, navigation and confirmation depend on key
  release; the detail page also handles key press and mouse press/release.
- `godot/tests/intro_continuous_reference.gd`: the existing replay adapter
  injects synthetic Godot keyboard events rather than logical input directly.
- `spec/schemas/replay.schema.json`: a retained format contract exists, but its
  button vocabulary differs from the live dictionaries. Do not silently change
  this contract or describe it as the implemented recorder format.

## Proposed implementation boundaries

These are engineering proposals, not additional confirmed user decisions.

1. Separate local device sampling from device-independent input delivery.
   Keyboard and developer playback feed the same logical input boundary.
2. Keep both player slots explicit. Preserve all ten held buttons, simultaneous
   keys, absolute left/right directions and existing source control semantics.
   AI remains on its existing source branch; do not force it into a synthetic
   keyboard implementation.
3. Tag recorded samples with their existing display tick. Missing recorded data
   must not silently mean that the player released every button. Frame tags do
   not introduce network waiting, prediction or a new simulation clock.
4. Represent match-affecting system operations separately from fighter held
   buttons. Retain the existing event phase/order and eligibility checks;
   do not defer immediate pause behavior by one physics tick merely to simplify
   the recording format. UI navigation can remain local, but any resulting
   operation that changes the match must cross the boundary.
5. Keep the source callback order, gameplay rules, timers and random consumers
   unchanged. Resolve any required input-timing evidence under
   [SOURCE_FIRST.md](../SOURCE_FIRST.md) before changing runtime behavior.
6. Playback must not modify the global keyboard state. Keep dedicated device
   adapter tests; reuse existing source-reference fixtures through a logical
   adapter where appropriate, preserving their inputs and expected outputs.

## Confirmed recording boundary

The first recorder starts from a fresh, identified match setup and
records logical inputs and match-control operations. It is not an arbitrary
mid-match save, a rewind system or a guarantee of deterministic full-match
playback. Exact state comparisons require controlled initialization, clocks,
random values and asynchronous callback phases. Existing reference facilities
can supply those conditions for bounded regression cases.

## Agreed implementation sequence

1. Retain baseline fixtures and complete the source-first input timing audit.
2. Extract the local keyboard adapter and logical input delivery for both slots,
   retaining the current battle loop and source controller behavior.
3. Route intro and pause-menu match operations through device-independent
   delivery, preserving held-input and ordered press/release semantics. Include
   the exit-to-title operation so a recording has an explicit terminal event.
4. Add developer recording and playback from fresh match initialization, with
   version/setup metadata and explicit rejection of unsupported or incomplete
   records. Do not fall back to live gameplay keys during playback.
5. Verify input equivalence and controlled battle outcomes, then run relevant
   existing source/native/Web checks. Report each acceptance boundary separately.

Window-focus policy and future online pause permissions are not changed here.
The user explicitly requested implementation on 2026-09-22. The earlier interview
confirmation requirement is satisfied by that request. Implementation does not
mark any migration milestone or original gameplay parity gate complete.

## Proposed acceptance

- Local keyboard and logical playback deliver identical input samples and
  ordered match-control operations for the same fixture.
- Playback controls either player slot independently of live gameplay keys.
- Remapping, simultaneous keys, holds/releases, intro skipping and pause/resume
  retain their source-derived behavior, including boundary cases.
- Controlled regression cases retain fighter/action/frame/position and combat
  outcomes; do not claim that input equality alone proves full-match parity.
- Existing relevant player-controller, visual-input, pause, intro and shared-mode
  checks pass; retain original-player comparisons required by the source gate.
- Run package checks for documentation changes. Run contract validation if a
  replay contract is added or changed during implementation.

## Deferred work

Room UI, transport, matchmaking, public matches, anti-cheat, network delay
policy, external battle stepping, deterministic clock scheduling, full-state
save/restore, rollback and a general simulation/presentation split are deferred.
Do not mark existing migration milestones or character parity complete based on
this refactor.

See [the glossary](GLOSSARY.md) for the terms used here.
