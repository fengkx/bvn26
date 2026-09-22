# Online multiplayer architecture

Status: Ready for final review. All 20 product decisions are accepted. Engineering
proposals below describe the planned implementation, not runtime behavior already
implemented or verified. The assembled plan has not yet received final sign-off.

## Product boundary

Two friends in mainland China use desktop Chrome and a private invitation to
play complete matches. No registration. Start with capacity for 10 concurrent
two-player rooms. Each chooses their fighter/helper; the owner chooses map/rules.
Changes clear readiness; both ready before the match starts. Results offer rematch.

Additional service spending targets US$10/month. See [cost scenarios](COSTS.md).
Other browsers remain later online validation work, not implied Chrome equivalents.

The first playable release includes rollback and all currently enabled content.
The audited set is [11 fighters, 4 helpers and 10 stages](CONTENT_SCOPE.md).
Preserve existing disabled actions/forms instead of opening unfinished mechanics.
Use a frozen build/content manifest to define this scope and reject incompatible
peers. Smaller fixtures are development steps, not a reduced release promise.

Pause/resume requires mutual consent. Brief lost inputs invoke bounded prediction
and then waiting. A sustained interruption has a 10-second recovery window, after
which the match ends without a winner. A refreshed/reopened page cannot rejoin the
old battle. Diagnostics are bounded local records explicitly downloaded by users.
Once both players have loaded, either can request a shared intro skip. The request
is applied at an agreed simulation boundary so neither peer skips independently.

## Responsibilities

| Part | Responsibility | Does not own |
|---|---|---|
| Worker entry point | Route requests, validate admission, issue short-lived connection credentials | Godot simulation |
| Room DO | Two seats, owner, setup revision, ready/start coordination, signaling | Per-frame combat decisions |
| WebRTC connection | Peer data transport, direct or through TURN | Prediction, damage or winner calculation |
| Match input adapter | Sample physical controls once and supply logical frame inputs | Reading hardware again during re-simulation |
| Online match driver | Input history, step numbering, prediction, confirmation, correction and wait policy | Character-specific combat patches |
| Restorable battle state | Source-derived gameplay, clocks, lifecycle and deterministic transitions | Sending network packets or committing external results |
| Presentation reconciler | Render current predicted state and reconcile sound/visual events | Independently changing damage or gameplay pauses |

Candidate backend: a small TypeScript Worker/DO project managed by Wrangler, with
hibernatable WebSockets for the room/signaling connection. Candidate client:
Godot's WebRTC classes, with a transport boundary separate from match simulation.
Dependency/library selection needs a Web compatibility spike before being final.

For local room development, recommend Wrangler's local SQLite-backed DO runtime.
SolidObjects + Node/SQLite is a viable alternative with a shared-Actor Cloudflare
backend, but requires explicit adapter/lifecycle/contract validation. It is not
needed merely to use SQLite locally. See [local development](LOCAL_DEVELOPMENT.md)
and NET-007 in the [implementation TODOs](TODO.md). Neither backend runs the battle.

## Match startup proposal

1. Create a non-guessable room invitation. Allocate each admitted participant a
   separate scoped session identity; the nickname is not an authorization token.
   After both seats are occupied, another invite holder cannot replace a player.
2. DO publishes one setup revision. Ready messages identify that exact revision
   and compatible build/content/protocol fingerprints. Any setup edit clears ready.
3. Exchange WebRTC offers/answers/candidates through authenticated room messages.
   Deliver short-lived TURN credentials only to admitted members. Never ship the
   long-lived credential-issuance secret in the Web export.
4. Measure the actual selected path and negotiate input delay and prediction limits
   from supported profiles. Both participants accept the same profile; freeze it
   for the match. Test direct and forced-relay paths independently during validation.
5. Preload identified resources. Both peers initialize the same match setup,
   initialization random data and explicit clock baseline; compare initial state.
6. Start a unique match epoch only after both are initialized and the start barrier
   succeeds. Late packets from previous matches/rematches cannot mutate this one.
   A participant missing the barrier cannot start an independent unbounded match.

These operations require idempotent request IDs, bounded message sizes, room-scoped
authorization and timeouts. Persistence/attachments reconstruct room state after
DO hibernation; an in-memory object remaining alive is not a correctness premise.

## Input and rollback proposal

Keep original combat simulation at 30 Hz. Sample local controls once for each new
input frame, tag them with player slot and match epoch, and record them immutably.
Re-simulation consumes history rather than `Input`, network arrival order or live
wall time. Keep simulation-frame, input-frame and render-frame counters explicit.

Send inputs promptly. A candidate low-latency channel sends a bounded rolling
input history with acknowledgments so ordinary packet loss need not wait for one
old transport packet. Application retransmission must retain every required frame
until acknowledged; exhaustion invokes waiting/recovery, never silent dropping.
Validate epoch, allowed future/past frame bounds, button bits and slot ownership.
Duplicate identical input is idempotent; conflicting input for one slot/frame is
an error rather than a last-write-wins edit of history.

Use a separate reliable control channel for setup/start, pause/resume and results,
each with an operation ID and effective agreed simulation boundary. Transport
ordering is per channel, so explicitly order controls relative to gameplay frames.
Network-message delivery callbacks may enqueue work but cannot mutate combat in
the middle of a simulation step.

Until remote input arrives, a candidate predictor repeats its last known held
buttons, deriving button edges from adjacent simulated frames. At match start use
the agreed neutral state. Do not predict menu/control operations or invent attacks
using AI. Preserve source held-input semantics and avoid a new gameplay input buffer.

On an input mismatch, restore the state immediately before the earliest affected
frame, apply actual local/remote inputs, and re-simulate to the current frontier.
Intermediate passes do not sample devices or publish external side effects.
Retain enough complete states and input history for the negotiated prediction
window. Refuse to predict further once a needed recoverable boundary would be lost.

Compute comparison hashes from canonical complete gameplay state at the same
confirmed frame, independent of object memory addresses, arrival timestamps or
dictionary serialization accidents. Include lifecycle and pending work, not only
visible fighters. Hash agreement diagnoses consistency; it is not proof that a
modified client is honest. No trusted server combat authority is introduced by DO.

## Pause and interruption proposal

Separate voluntary pause, source-defined attack/hit pauses and network waiting.
They are not interchangeable Boolean flags. A pause request does not immediately
alter the other peer's simulation; an agreed operation has a stable effective
frame and must be reflected in both input/control histories. Network processing
and the external recovery timeout continue while battle stepping waits.

During interruption, preserve the last usable history and exchange progress when
the path recovers. Resume only after agreement on epoch, complete required inputs
and the state at a common confirmed boundary. If retained history is insufficient,
fail the match explicitly rather than importing an unchecked peer snapshot. The
10-second policy is a local safety deadline, not a synchronized combat clock.
A distributed timeout cannot guarantee both screens change on the same millisecond.

Result commitment must require a confirmed terminal state and peer agreement.
Prediction alone must not destroy match state or trigger irreversible scene exit.
On confirmed-state mismatch, end without a winner and offer local diagnostics;
do not adopt the owner's state. Voluntary exit also ends without a winner. Guest
departure leaves the room available for a replacement; owner departure closes it
without ownership transfer. An inactive room expires after 30 minutes; active
gameplay is exempt. Distinguish explicit departure from a transient connection loss.
If the room/signaling connection fails while the WebRTC peer path remains healthy,
continue the current match and its peer control operations. Reconnect room service
in the background. Failure of signaling alone does not start the 10-second battle
interruption timer; actual peer-path loss does. Do not start a new match epoch
until room service, membership and setup revision have been revalidated.

On recovery, reconcile the existing epoch and any confirmed result idempotently.
If the room has expired or cannot be reclaimed, finish the healthy existing match
locally and require a new room for another match; never let a recycled room or
stale ready/start message redirect that battle. An explicit owner exit still closes
the room and ends the match under Q16. Loss of room connectivity alone is not proof
that the owner intentionally left.

## Presentation and room security

Q14 permits speculative action, health and ordinary hit feedback. Reconcile
visuals from corrected state. Short sounds may play speculatively but cannot
replay for each simulation pass. A candidate event identity includes match epoch,
source frame, stable emitter identity and deterministic ordinal; reconcile its
payload too, since a corrected hit can become a block at the same event position.
Stop/fade obsolete sustained effects; already-heard brief audio cannot be undone.
Keep gameplay-causing effect state in the simulation. Commit final results and
scene destruction only after the confirmed outcome handshake.

Treat invitation and seat credentials as distinct capabilities. A proposed
invitation uses a cryptographically random token, expires with the room, and is
revoked/replaced when an owner reinvites. Room membership binds a participant to
one slot. A reconnect in the same live page may reclaim that slot during Q10's
window using its separate session token; a new page cannot restore the old match.
Server checks reject a third seat, wrong-room messages, oversized payloads and
unbounded candidate/control floods. Display nicknames as text, not markup.

Private invitation means possession permits joining, not protection against a
modified friend client. P2P may reveal network addresses to the other participant.
No ranked results or server anti-cheat guarantee is part of this friend trial.
Invite/TURN secrets and raw SDP/candidates must be excluded from downloadable
diagnostics. Do not automatically upload input histories; minimal service events
must avoid storing gameplay inputs or unnecessary identifying payloads.

## State coverage and source semantics

See [rollback research](ROLLBACK_RESEARCH.md) for the state inventory and tests.
Audit every currently enabled mechanic and its callbacks. Preserve placement
lifetimes, nested playback state, pause exclusions, source undefined values and
callback registration order. Existing diagnostic `snapshot()` is insufficient.

Existing input recordings are a separate format with explicit limitations. Do
not silently reinterpret them as full rollback snapshots or modify retained
reference tapes. Define network protocol, restorable-state and diagnostics formats
separately and version them; contract changes require contract validation.

## Delivery sequence and gates

Use [TODO.md](TODO.md) as the actionable online work tracker: each of its 48 items
lists prerequisite task IDs, work/artifacts and a concrete completion check.
Do not treat the high-level stages below as sufficiently detailed implementation
instructions by themselves. Check tasks only after recording evidence and effort.

| Stage | Deliverable | Gate before proceeding |
|---|---|---|
| R0 | Frozen enabled-content manifest, state/scheduler audit, source-first answers and performance baseline | All causal state owners identified; unresolved source rules explicit |
| R1 | Explicit deterministic match step with controlled random/time/task scheduling | Independent identical-input runs agree; local/source regression baselines retained |
| R2 | Complete save/restore and isolated re-simulation | Restore/re-run tests across all enabled mechanics; no duplicate external effects |
| R3 | Offline network simulator with prediction/correction | Confirmed results match baseline under latency/loss/reordering; bounded CPU/history |
| R4 | DO room and real WebRTC connectivity | Authenticated two-device direct/relay tests on mainland networks; usage measurements |
| R5 | Integrated setup, rollback battle, pause, recovery, results and rematch | Full enabled-content/browser matrix and multi-room load/soak tests |
| R6 | Limited friend trial and observed acceptance | Agreed connection, latency/correction, performance and budget targets met |

Task mapping: R0 = NET-001–008; R1 = NET-009–013; R2 = NET-014–019;
R3 = NET-020–026; R4 backend = NET-027–035; R4 transport = NET-036–040;
R5 = NET-041–045; R6 = NET-046–048. Dependency IDs in TODO.md, rather than numeric
proximity, determine which tasks may start or run in parallel.

R4 transport work can proceed independently of R1-R3 once its message boundary is
agreed. Integrating it before deterministic simulation passes must not hide state
bugs as network problems. An automated delay-only mode is allowed as a reference
test, not as fulfillment of the selected rollback release.

Record measured effort and failures by stage; do not invent calendar estimates
before R0/R2 characterize the state surface and re-simulation cost. Online gates
are separate from original BVN parity and the existing migration milestones.

## Remaining design review

All product-choice questions are resolved; the assembled plan is ready for
shared-understanding confirmation. Provider, dependency revision, numerical
prediction limits, snapshot format and performance budgets are explicit research
outputs under R0-R4, not silently assumed proven capabilities. See
[acceptance work](VALIDATION_PLAN.md). No runtime work is started by this review.
