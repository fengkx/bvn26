# Online multiplayer decision tree

Status: All 20 interview questions answered. Accepted product decisions are
recorded below; the assembled engineering plan is ready for final review.

## Established context

- Request: design online multiplayer, explain choices in beginner-friendly language,
  and write the documents inside a dedicated `docs/` folder.
- Previously confirmed: begin with friends joining a room and preserve a path
  toward public casual play. Source: [input ADR](../input-decoupling/ADR.md).
- Existing product platform: desktop browsers. This interview has not expanded it.
- This is a design session; no battle or networking implementation is authorized
  by completion of an individual interview answer.

## Round 1: independent product constraints

### Q1: Target player networks

- A: Same Wi-Fi/LAN first. Narrow validation scope; no ordinary remote play promise.
- B: Different cities in mainland China, home networks and hotspots. Recommended
  for the existing friend-room direction; requires internet connectivity testing.
- C: International/intercontinental from the first release. Larger latency and
  deployment scope; cannot promise equivalent local-play responsiveness.

Answer: B, confirmed 2026-09-22. Target mainland-China intercity play over home
networks and hotspots.

### Q2: Operational budget

- A: Accept a small signaling/relay deployment within a stated budget. Recommended;
  ask for an approximate monthly ceiling or details of available servers.
- B: No additional spending; accept connectivity failures and manual setup limits.
- C: Prioritize connection success; request a cost estimate before fixing the cap.

Answer: A, confirmed 2026-09-22. The user specifically proposed Cloudflare Durable
Objects as a likely fit. Evaluate that candidate first. The later Q18 fixes the
budget target; actual room-hours still require measurement. No purchase or
deployment is authorized.

### Q3: First delivery priority

- A: Complete experimental matches first, then improve measured latency. Accept
  input delay or network waits during the experimental phase. Recommended.
- B: Low input latency is a requirement of the first playable release; accept
  substantial determinism/rollback groundwork before it is available.
- C: Technical proof first: connection and matching battle state, with full room
  and match UX outside the first deliverable.

Answer: A, confirmed 2026-09-22. Aim first for complete experimental friend
matches, accepting input delay or network waits during that phase, then improve
latency using measurements. This does not yet select a synchronization
architecture or declare delayed synchronization inexpensive.

## Dependent branches for later rounds

| Decision | Prerequisite | Why it matters |
|---|---|---|
| Synchronization and authority | Q1, Q3, current scheduler/state evidence | Input delay, corrections, implementation scope and fairness |
| Signaling/TURN deployment | Q1, Q2, expected concurrent matches | Connectivity, region, operating cost and maintenance |
| Room admission and identity | First-delivery scope and trust model | Invite links/codes, accidental entry, reconnect identity |
| Selection and ready/start agreement | Room flow and synchronization | Both sides must start the same match with compatible content |
| Online pause, intro skip, exit | Synchronization and authority | Avoid one player's local UI unilaterally changing the other match |
| Disconnect, focus loss and recovery | Synchronization and lifecycle | End, wait or reconnect; prevent silent background divergence |
| Rematches, round/result lifecycle | Match and room ownership | Define what persists between matches |
| Compatibility and integrity checks | Deployment and authority | Reject mismatched builds and invalid or excessive messages |
| Diagnostics and replay scope | Synchronization and privacy choices | Reproduce failures without confusing input capture with snapshots |
| Acceptance targets and rollout gates | Above decisions and measurements | Define playable, verified and unsupported conditions explicitly |

Recompute the open questions after every answer. Do not ask a dependent choice
as though its prerequisites were already settled. Close the design only after
the user confirms a shared understanding of the resulting plan.

## Round 2: architecture direction and room scale

### Q4: Role of Durable Objects

- A: A room object coordinates membership/readiness and WebRTC signaling; game
  inputs travel over WebRTC, with independently selected TURN fallback.
  Recommended, subject to mainland connectivity measurements. It avoids routing
  every input through the DO when a direct connection works.
- B: A room object relays all game inputs over WebSockets. Fewer transport pieces,
  but the DO location and TCP recovery affect every gameplay message. This does
  not automatically make the object a battle authority.

Answer: A, confirmed 2026-09-22. DO manages rooms and signaling; WebRTC carries
gameplay input. TURN supplier remains a separate downstream decision, subject to
target-network tests. See [ADR-0001](adr/0001-room-coordination-and-webrtc.md).

### Q5: Initial battle synchronization

- A: Delay-based synchronized inputs. Both devices advance only with the required
  inputs for that step. First prove controlled clocks/randomness and repeated
  state agreement; then connect the transport. Network jitter may cause waits.
  Recommended for the accepted experimental delivery priority.
- B: Rollback from the outset. Respond before remote input arrives, then restore
  and recompute on prediction errors. Requires full state capture/restoration and
  re-simulation budgets in addition to the consistency work needed by A.
- C: One player's device is the battle authority. It decides hits/results and
  sends state to the other. Avoids independent authoritative outcomes, but creates
  host advantage and requires complete state replication and guest presentation.

Answer: B, confirmed 2026-09-22, overriding the earlier recommendation of A.
Rollback is part of the first playable online release. Q3 still means staged
delivery, now through deterministic stepping, complete state restoration,
rollback tests and then full online matches. A delay-only build may be a test
harness, but does not fulfill the selected first playable release.
See [ADR-0002](adr/0002-rollback-battle-synchronization.md).

### Q6: Joining a friend room

- A: Temporary nickname and a private invite link, without accounts. Recommended
  for friend matches; the link is a bearer invitation, so avoid public listing.
- B: Accounts and login in the first version. More identity/account work, but a
  foundation for persistent profiles and invitations tied to known accounts.

Answer: A, confirmed 2026-09-22. Temporary nicknames and private invite links,
without accounts. Token lifetime, reconnect identity, room ownership and abuse
limits follow once the lifecycle is selected.

### Q7: Initial operating scale

- A: Up to 10 simultaneous two-player rooms (20 players). Recommended initial
  sizing target for a friend experiment, not an infrastructure performance claim.
- B: Up to 100 simultaneous rooms (200 players).
- C: Another stated target, or ask for 10-room and 100-room cost scenarios first.

Answer: A, confirmed 2026-09-22. Size the initial experiment for up to 10
simultaneous two-player rooms (20 players). Monthly room-hours are still needed
for cost; peak concurrency alone cannot determine the bill. See Q18 for the budget.

## Round 3: rollback experience and first playable scope

### Q8: Input delay within rollback

- A: Allow a small input delay, agreed before the match using network measurements;
  do not silently change it during a match. Tune the actual frame count in tests.
- B: No deliberately added input delay; accept more corrections and network waits.

Answer: A, confirmed 2026-09-22. At 30 Hz, one frame is about 33.3 ms.
Input delay and maximum prediction distance are separate parameters.

### Q9: Player-requested pause

- A: Both players approve pausing and both are ready before resuming.
- B: Either player may pause the shared match immediately.
- C: No player-requested pause during an online match; exit remains possible.

Answer: A, confirmed 2026-09-22. Source-defined super/hit pauses are gameplay
state and are distinct from voluntary pause requests.

### Q10: Connection interruption and background suspension

- A: Stop advancing when continuation is impossible; allow up to 10 seconds to
  recover. On failure, terminate without a winner and return to the room when
  reachable. A page reload cannot restore the old match in the first release.
- B: Support page reload/relaunch recovery into the old match, including identity
  recovery, snapshot transfer, validation and input catch-up.

Answer: A, confirmed 2026-09-22. Brief packet delay is handled by bounded
prediction/waiting before treating it as an interruption. Exact joint suspension
and restart protocol remains an engineering design item.

### Q11: Room-to-match flow

- A: Each player chooses fighter/helper; room owner selects stage/rules; both
  ready; play; offer rematch after results. Configuration changes clear readiness.
- B: Fixed fighters/helpers/stage for the first experiment; ready/play/rematch only.

Answer: A, confirmed 2026-09-22.

### Q12: Content coverage for first rollback release

- A: A small verified roster of fighters/helpers/stages, expanded in tested batches.
  Select the initial roster from actual code and test evidence.
- B: Every currently enabled piece of content, accepting longer state audits/tests.

Answer: B, confirmed 2026-09-22, overriding recommendation A. The first playable
online release must cover all currently enabled content. Freeze the launch roster
and its existing gates in a versioned manifest. Internal milestones may validate
subsets, but cannot pass the release gate by silently shrinking the roster.
Local availability still does not establish rollback correctness.

### Q13: Sharing diagnostic recordings

- A: Bounded local records; the player explicitly downloads and shares a report.
  Do not automatically upload match recordings.
- B: Automatically upload compact failure diagnostics, with separate decisions
  on disclosure, retention and operational cost.

Answer: A, confirmed 2026-09-22. Service operational logs are a distinct topic;
invite secrets and TURN credentials must not appear in downloadable reports.

## Round 4: presentation, failures and operating boundary

### Q14: Predicted feedback

- A: Predict actions, health and ordinary hit feedback; reconcile them after
  rollback. Short sounds may play speculatively but must not duplicate during
  re-simulation. Final results and scene exit wait for confirmation.
- B: Delay all hit sounds and hit effects until their inputs are confirmed.

Answer: A, confirmed 2026-09-22. Heard sounds cannot be undone.

### Q15: Confirmed-state mismatch

- A: Stop the match without a winner, offer local diagnostics, and return to room.
- B: Adopt the room owner's state and continue, adding state transfer and making
  the owner a conflict-resolution authority.

Answer: A, confirmed 2026-09-22. This differs from correcting a wrong prediction.

### Q16: Leaving and room lifetime

- A: Voluntary exit ends the match without a winner. A departed guest can be
  replaced in the room; owner departure closes the room. No ownership transfer.
  Close after 30 minutes idle, but never apply that idle timeout to active play.
- B: Change ownership transfer, forfeits or another part of the proposed policy.

Answer: A, confirmed 2026-09-22.

### Q17: First online browser acceptance

- A: Desktop Chrome/Edge first, followed by Firefox and Safari. This only stages
  online experimental acceptance; the original project's final targets remain.
- B: Chromium, Firefox and Safari all pass before the first online release.

Answer: Chrome only, confirmed 2026-09-22. This is narrower than the proposed A:
Edge, Firefox and Safari are not part of the first online trial's acceptance.
The original project's eventual browser targets remain unchanged.

### Q18: Monthly additional service budget

- A: Target US$10/month, limiting new room creation if spending risk grows.
- B: Target US$25/month, allowing more relay/testing headroom.
- C: Estimate free allowances and actual usage before fixing a numerical target.

Answer: A, confirmed 2026-09-22: US$10/month additional service budget target.
Existing Workers subscription is unknown, so estimates include its base cost
rather than assuming it is already paid. This is not a guaranteed billing cap.

## Final flow questions

### Q19: Intro skip

- A: Once both players have loaded, either may request a shared intro skip.
- B: Require both players to request it.

Answer: A, confirmed 2026-09-22. Once both peers have loaded, either participant
may request a shared intro skip. It is an ordered shared control operation, not
a local jump ahead of the other peer.

### Q20: Room-service outage during healthy peer gameplay

- A: Continue the current match while the peer path stays healthy; reconnect the
  room service in the background and block another match until recovered.
- B: Treat room-service loss as a battle interruption under the 10-second policy.

Answer: A, confirmed 2026-09-22. Continue the current match while the peer path
is healthy, reconnect the room service in the background, and block a new match
until room service and membership are restored. Actual peer-path loss invokes Q10.

## Interview outcome

No product-choice questions remain open. The assembled [design](DESIGN.md) and
[validation plan](VALIDATION_PLAN.md) distinguish accepted scope from engineering
parameters that require evidence. Dependency/provider selection and measured
prediction/performance limits are implementation research gates, not unasked
product decisions. Final plan review does not itself deploy services or change
runtime behavior.
