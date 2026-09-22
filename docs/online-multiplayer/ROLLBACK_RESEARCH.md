# Rollback and hit-registration research

Checked: 2026-09-22. Design analysis only; no networking or rollback implementation.

## User-provided reading

[The art of Hit Registration](https://danieljimenezmorales.github.io/2023-10-29-the-art-of-hit-registration/)
by Daniel Jimenez Morales (2023-10-29) examines FPS hit registration with server
authority and snapshot interpolation. It separates immediate feedback from confirmed
results, explains historical collision queries and discusses limiting compensation
to avoid excessive corrections. It also notes that latency/jitter and interpolation
make reconstructing the shooter's observed instant difficult.

Use this article to identify questions, not as proof of the internal behavior of
every cited game. Its examples were cross-checked against primary material below.
We do not adopt its particular game thresholds or treat half of RTT as an exact
measurement of one-way delay.

## Primary-source cross-check

[Riot's VALORANT technical lead](https://www.unrealengine.com/tech-blog/valorant-s-foundation-is-unreal-engine?lang=en-US)
describes historical animation/bone reconstruction for hit tests. This supports
the FPS historical-query example; it does not establish that this project can
recover complete battle state using collider history alone.

[GGPO's developer guide](https://github.com/pond3r/ggpo/blob/master/doc/DeveloperGuide.md)
requires deterministic frame execution, complete save/load state and advancing
without rendering. Its SyncTest approach exercises restored simulation to expose
hidden state. [GGPO's synchronization code](https://github.com/pond3r/ggpo/blob/master/src/lib/ggpo/sync.cpp)
restores a past frame, repeatedly advances to the present and bounds prediction.
These are requirements to reproduce, not evidence that GGPO itself is a ready-made
Godot Web integration.

[SnapNet's rollback explanation](https://www.snapnet.dev/blog/netcode-architectures-part-2-rollback/)
distinguishes prediction, state restoration and re-simulation. It describes combining
input delay with rollback and warns about repeated-simulation CPU cost. For
presentation-only effects, it discusses tracking events and handling incorrect
predictions rather than assuming audio can be restored like simulation memory.
Its example timings are not this project's performance or latency targets.

## Application to BVN: engineering conclusions

These are deductions from the project behavior and the sources above.

| Historical FPS hit query | Selected BVN battle rollback |
|---|---|
| Reconstruct a target at the shot's historical instant | Restore the entire causally relevant match at a frame boundary |
| Perform a collision query using that history | Reapply both players' inputs through the unchanged combat rules |
| Return queried entities to their current state | Recompute every affected subsequent frame up to the prediction frontier |

A late guard can replace a hit with a block, change hitstun/energy and alter the
rest of a combo. A late attack can change helper lifetime or super/hit pauses.
Restoring only HP, position and collision boxes cannot repair that chain.

Do not introduce a separate client message that declares a successful hit or lets
the victim accept/reject damage. Peers exchange validated frame-tagged inputs;
the same source-derived simulation computes consequences. Peer equality does not
make either device trustworthy against deliberate client modification.

Predicted health and hitstun may change speculatively and must be restorable.
Irreversible session actions, such as final result publication and scene teardown,
must wait for the corresponding agreed inputs/state. A single local prediction
cannot finalize the match. Exact result agreement and failure policy are still
to be specified; matching hashes are an accidental-divergence check, not anti-cheat.

Retain original 30 Hz semantics and attack timing. Do not add startup animation
frames, enlarge hitboxes or alter damage to compensate for network conditions.
Frame numbers drive battle history; local wall clocks may measure connection
timeouts without becoming combat inputs implicitly.

## Proposed state and scheduler work

Audit fighter and helper state, source variables (including undefined semantics),
nested playheads/stops, display-list instance lifetimes, transforms, attack-contact
state, pending source scripts, RNG state, logical clocks and scheduled callbacks.
Preserve global callback registration and placement order. Include intro, round,
countdown, KO and match-control state wherever they can affect future execution.
This is an audit starting list, not a proven exhaustive snapshot schema.

Current independent Godot timers cannot simply continue during network waits or
fire again during re-simulation. Design their explicit scheduling from source
evidence, including which timers advance during each kind of pause. Keep local
mode behavior as a regression baseline; network waiting is not a source pause flag.

Separate state transition from external output. A headless re-simulation must
not re-send network messages, duplicate recording writes, replay sounds each pass,
or leave predicted visual objects behind. Stable event identities and reconciliation
are a candidate design. Q14 now selects predictive short sounds with deduplication
and confirmed final outcomes; already-heard sounds cannot be undone.
Hit effects that consume shared RNG or pause actors remain part of battle state,
even if their rendering/audio output is presented separately.

## Proposed acceptance gates

1. Complete identical-input matches in independent instances; compare canonical
   state at each confirmed frame and locate the first mismatch. Repeat across
   supported browser combinations. Never compare speculative states at unrelated
   frame frontiers or claim partial diagnostic hashes prove complete determinism.
2. Save before a frame, advance, restore, and re-run: require identical state and
   logical output events. Extend to nested spawns/removals and multi-frame restore.
   Test both continuations of different subsequent inputs, not just one happy path.
3. Inject late, lost, reordered and duplicate inputs. After correction, confirmed
   state must match a non-network baseline; old-session/conflicting inputs must be
   rejected and missing input must never silently become a release.
4. Bound prediction and retained history; at the boundary, explicitly wait or
   invoke the selected interruption policy. Do not invent a late-input hit or
   discard input that is required to reconstruct the match.
5. Exercise hit/block corrections, simultaneous attacks, helpers, nested timelines,
   supers and their pauses, countdown, KO, input holds/releases and match controls.
   Confirm no duplicate sound/event publication and no premature match teardown.
6. Measure snapshot size, save/load cost and worst-window re-simulation p95/p99 on
   target browsers/hardware. A 30 Hz step is about 33.3 ms; the whole application
   needs rendering and other work within its budget, not just battle computation.
   Numerical performance and experience limits remain to be agreed from measurements.

Suggested experiment matrix: input delay 0/1/2 logical frames and prediction
distance 2/4/6 frames, with controlled latency/jitter/loss and real network paths.
These are test points, not accepted shipping settings. Verify burst-loss recovery,
background throttling and sustained re-simulation load, not only average RTT.

## Decision outcome and evidence still needed

Q8-Q18 have settled delay tolerance, pause/recovery, complete enabled-content
coverage, predictive presentation, local diagnostics, failure policy, Chrome-only
initial acceptance and the US$10 trial budget. Q19 permits either participant to
request a shared intro skip; Q20 preserves healthy peer matches during room-service
outages while blocking the next match. Technical limits and dependency/provider choices require
measured validation rather than more speculative numerical promises.
