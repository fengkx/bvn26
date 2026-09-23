# Online client clock and callback policy

This document records the source review for the online timer adapter. It is a
client scheduling policy, not a claim that browser/Godot callbacks reproduce a
Flash player's wall-clock phase.

## Source-first review

1. **Source callbacks and frames.** The match countdown is defined by
   `scripts/main.json::DefineSprite_1813/frame_1/DoAction.as` and retained in
   `godot/generated/main/timeout/timer.json`: `setInterval(time, 1000)` decrements
   the displayed time unless the source pause flag is set, either fighter is in
   source hit-freeze, or the match is training. The introduction poll is in
   `scripts/main.json::DefineSprite_1991/frame_1/DoAction.as` and
   `godot/generated/main/intro/intro.json`: `setInterval(kaichang, 500)` reads the
   two `kcplayed` values and advances the intro sequence. The same root clip's
   `renderSkip` checks the source attack keys from `onEnterFrame`. Round advance
   is `nextfight` in `scripts/main.json::DefineSprite_1813/frame_1/DoAction.as`,
   registered by `setInterval(nextfight, 1000)` after a non-terminal KO. BODY
   callbacks originate in source `setTimeout` registrations and are represented
   by `godot/ai_source_timeouts.gd` registration ids plus the compiled delay.
   `godot/main.gd::_advance_fight` has two existing delivery boundaries:
   `after_actor_advance` and `before_root_observer`.
2. **Placement or MOVE.** This adapter does not edit source timeline placements
   or substitute a new movie clip. Intro and countdown state stays in the
   existing `BattleIntro` and `MatchCountdown` objects. BODY timeout callback ids
   come from `AiSourceTimeouts`' monotonic registration counter and are included
   with the restored callback registrations; the online deadline map is restored
   with the rollback checkpoint and reconciled against those registrations on
   each delivery. Countdown and intro re-arming uses their audited active flags,
   not a Godot object instance id. KO interval re-arming uses
   `Main.ko_interval_sequence`.
3. **Exit and cancellation.** The online adapter does not change a source `goto`,
   `stop`, or timeline fallthrough. It observes source cancellation: the KO
   `clearint` service stops `nxtfht`, `timeset`, or `kcint`; intro timeline events
   also clear `kcint`/`nxtfht` at their compiled source frames. A due BODY event
   is checked against the current registration immediately before delivery, so a
   callback canceled or replaced by the actor step is omitted. The fixture path
   without an online event supplier remains fail-closed when a recorded callback
   cannot be delivered.
4. **Invariants and online policy.** The clock authority publishes immutable
   integer elapsed-millisecond samples indexed by simulation frame. Its origin
   is established at the first simulated frame after the room and data-channel
   barriers, not during loading. The guest waits for that sample before stepping.
   No timer is inferred from a 30 Hz or 60 Hz frame count. Rollback restores the
   timer registration/deadline owner at the same checkpoint as the battle graph
   and replays the already-recorded host clock sample for each corrected frame.
   At equal deadlines the online adapter orders countdown, intro, then BODY
   callbacks; BODY ties use P1 then P2, followed by ascending registration id.
   Countdown, intro, and BODY deliveries are derived at the existing
   `after_actor_advance` boundary; `nextfight` is derived at
   `before_root_observer`. A sampled interval delivers at most one countdown,
   intro, or nextfight callback; the next repeat deadline is anchored to that
   delivered monotonic sample. A backgrounded tab therefore does not cause an
   unbounded callback burst. These tie, re-anchor, and delivery-boundary choices
   define deterministic online behavior only; they do not establish Flash's
   relative phase among simultaneous `setInterval`, `setTimeout`, and
   `enterFrame` callbacks.

   Mutual online pause and peer recovery stop simulation. Their agreed waiting
   duration is excluded from future host time samples. Source hit/super
   `zhanting` remains part of the source simulation and does not stop the online
   host clock by itself. Intro skip is a reliable, host-ordered event at a future
   frame; it is not inferred from a locally predicted attack input during replay.
5. **Original same-input comparison.** The existing unchanged PvP and training
   timer traces in `tools/test_shared_modes.py` cover 602 actor states per mode.
   They validate the shared local battle path and do not compare wall-clock
   callbacks in the original player with this new online policy. The online
   clock/timer tests use explicit synthetic elapsed-time samples. There is no
   original Flash trace proving that this online delivery phase, repeat
   re-anchoring, or background-tab policy is equivalent to Flash; online timing
   remains an engineering determinism contract, not a parity claim.

## Delivery contract

The host sends elapsed milliseconds, never `frame * 33`. Samples are
non-decreasing and immutable. After a late input, the same clock samples and
restored scheduler values are replayed. A guest missing a sample waits without
advancing. The runtime performs at most one logical simulation step per caller
tick, so a long browser suspension does not trigger an unbounded simulation
catch-up loop.

An unseen clock sample is accepted only inside the rollback session's retained
and bounded-future receive window, matching the peer-input envelope. An exact
duplicate is idempotent; a duplicate frame with a different elapsed value is a
protocol error even if that frame has since left the current receive window.

The scheduler computes due events from its rollback-owned registration state and
the host time sample available for that frame. It never publishes a BODY
registration id as a separate journal item before its registration is confirmed
by rollback. `Main` revalidates each BODY id when it reaches delivery, because an
earlier callback can cancel a later event already selected for the same phase.
Registration changes during actor advancement are recorded at `finish_frame`;
they cannot fire before the next audited delivery phase.

The scheduler re-anchors repeating online deadlines at the current delivered
sample rather than emitting repeated callbacks to catch up after a long stall.
In the source match, the countdown interval is registered once and remains
active across a non-terminal KO/nextfight; it is cleared only through the source
`timeset` cancellation path. `nextfight` uses its own repeating interval and
source sequence. The later-round registration smoke also exercises a generic
cancel/re-register boundary for countdown and intro state, but that is not a
claim that the source creates a new countdown every round. Any test or runtime
result must report the actual elapsed samples used; a 15- or 30-step fixture is
not evidence of 500 ms or 1000 ms source equivalence.

## Evidence and limits

The online helper is `godot/online_timer_authority.gd`; its production phase hook
is `godot/main.gd::_advance_fight`, and the rollback adapter is
`godot/rollback_battle.gd`. `godot/tests/online_timer_round_smoke.gd` drives a
real Main scene through source KO and `nextfight`, confirms the existing
countdown interval stays active, and replays a checkpoint across that round
transition with an equal complete state graph. `godot/tests/online_timer_authority_smoke.gd`
separately tests irregular samples, cancellation/re-registration, bounded late
delivery and deadline restoration. These checks remain separate from the
shared-mode reference traces. The current online paired smoke and browser run
must be reported independently; neither replaces the original-player timing
comparison described above.
