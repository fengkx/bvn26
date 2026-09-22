---
status: accepted
date: 2026-09-22
---

# Coordinate rooms with Durable Objects and carry gameplay over WebRTC

For mainland-China friend matches, use a Cloudflare Durable Object per room for
membership, readiness and connection signaling. Use WebRTC data channels for
gameplay input, with a separately configured TURN service when direct connections
fail. The user selected this division over relaying every input through a DO
WebSocket, to retain a direct gameplay path while using DO room coordination.

The room service does not run the Godot battle or judge hits. DO placement and
mainland connectivity must be measured; Cloudflare TURN is not implicitly selected.
Keep signaling and TURN configuration replaceable if target-network validation
fails. This decision authorizes a design direction, not deployment or expenditure.

See [the research](../RESEARCH.md) and [Q4](../INTERVIEW.md).
