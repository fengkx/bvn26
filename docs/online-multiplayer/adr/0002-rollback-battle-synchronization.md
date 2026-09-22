---
status: accepted
date: 2026-09-22
---

# Include full battle rollback in the first playable online release

The user selected rollback rather than initially shipping delay-only synchronized
inputs or giving one player's device authority over the battle. Both peers
simulate the match from ordered inputs; late inputs that differ from predictions
require restoring earlier complete match state and re-simulating subsequent frames.
This prioritizes responsive controls and accepts the additional state, scheduling
and performance work before the first playable online release.

The earlier preference for staged delivery still applies: prove deterministic
stepping, state save/restore and bounded re-simulation before complete networked
friend matches. Existing input recording and diagnostic snapshots do not satisfy
those gates. No complete-state or cross-browser determinism claim has been tested.

Q8 allows a small input delay agreed before the match, with actual settings to be
measured. Q9 requires mutual voluntary pause/resume. Q10 allows up to 10 seconds
of interruption recovery, without page-reload match recovery. Q12 requires all
currently enabled content in the first playable online release.
Prediction-window size and effect presentation remain open. Do not copy FPS
server-side hitbox rewind as the implementation
or modify original attacks/hitboxes/startup frames to mask network latency.

See [the research](../ROLLBACK_RESEARCH.md) and [Q5](../INTERVIEW.md).
