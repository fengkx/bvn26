# Online multiplayer design

Status: All 20 product decisions recorded; assembled design ready for review.
Implementation and networking validation have not started.
Started: 2026-09-22.

This folder contains the design for online BVN 2.6 matches. It is separate from
the completed input-boundary work and from original-gameplay parity acceptance.

- [Domain language](CONTEXT.md): established project concepts.
- [Research and current implementation](RESEARCH.md): verified facts, technical
  explanations and remaining evidence gaps.
- [Decision tree and interview](INTERVIEW.md): all 20 answers and their rationale.
- [Rollback research](ROLLBACK_RESEARCH.md): the user-provided hit-registration
  article, primary references and their application to this project's state model.
- [Room/transport decision](adr/0001-room-coordination-and-webrtc.md).
- [Rollback decision](adr/0002-rollback-battle-synchronization.md).
- [Architecture and delivery gates](DESIGN.md).
- [Detailed implementation TODOs](TODO.md): 48 tasks with dependencies, outputs
  and completion checks, including serial and parallel execution order.
- [Local SQLite development](LOCAL_DEVELOPMENT.md): Wrangler recommendation and
  SolidObjects compatibility assessment.
- [Current content scope](CONTENT_SCOPE.md): 11 fighters, 4 helpers and 10 stages.
- [Dependency candidates and validation](DEPENDENCIES.md).
- [Trial cost scenarios and controls](COSTS.md).
- [Acceptance and measurement plan](VALIDATION_PLAN.md).

Accepted direction: DO room coordination and signaling, WebRTC gameplay transport,
full rollback in the first playable online version, anonymous private invitations,
and up to 10 simultaneous two-player rooms. Initial browser acceptance is desktop
Chrome only. Additional service spending targets US$10/month; the TURN supplier
still depends on measured mainland paths. Staging now means proving rollback foundations
before complete online matches, not shipping delay-only play as the selected goal.
The first playable online release covers all currently enabled content; smaller
internal test slices do not satisfy that release boundary.

After both players load, either can request a shared intro skip. Voluntary pause
and resume require mutual consent. Peer interruptions allow 10 seconds to recover;
failure or confirmed-state divergence ends the match without a winner. A temporary
room-service outage does not interrupt a healthy peer match, but blocks the next
match until room service recovers. Room-owner departure closes the room; idle
rooms expire after 30 minutes. Reports are downloaded locally, not auto-uploaded.

Carry forward the previously confirmed friend-room direction from
[the input design](../input-decoupling/ADR.md). The existing product target is
desktop browsers; native apps and mobile support are not silently added here.
Public casual play remains a possible later extension.

The user requested design documents in a dedicated directory under `docs/`.
Consequently this folder owns its glossary and any future `adr/` entries, rather
than creating a root glossary or unrelated repository-wide architecture records.
The ADRs record consequential accepted choices. The assembled design includes
the implementation sequence and validation gates; specific libraries, providers
and tuning values require the documented experiments before being selected.

No runtime changes or migration milestone completion are part of this interview.
Any subsequent scheduler or combat work must preserve the source-first evidence
requirements in [SOURCE_FIRST.md](../SOURCE_FIRST.md) and
[HIT_RECEIVE_SOP.md](../HIT_RECEIVE_SOP.md).

Documentation validation on 2026-09-22: `tools/verify.py` and
`tools/check_handoff.py` passed. Local links in this directory were checked
separately because the handoff checker only scans top-level documentation.
These checks do not validate network behavior or gameplay synchronization.
