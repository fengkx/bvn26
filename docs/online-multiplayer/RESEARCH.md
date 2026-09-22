# Online multiplayer research

Checked: 2026-09-22. This is design evidence, not an implementation or network test.

## Current project

- [SPEC.md](../../SPEC.md) selects Godot 4.7.2, desktop browsers, Compatibility
  rendering and a 30 Hz source timeline. [Environment evidence](../../evidence/environment.md)
  records the engine/toolchain; browser parity remains a separate acceptance gate.
- [Input delivery](../input-decoupling/IMPLEMENTATION.md) was implemented on
  2026-09-22. It accepts logical input for both player slots and preserves separate
  ordered match-control events. A future network input source has an existing seam.
- That change deliberately retained clocks, random consumers, callbacks and the
  battle scheduler. Recordings omit random/clock tapes and asynchronous callbacks.
  Faithful input delivery does not prove identical outcomes on two machines.
- An externally driven battle step, arbitrary mid-match state restoration and
  rollback remain deferred. Their readiness must not be inferred from the recorder.
- The earlier exclusion of character/map selection applied to the input refactor.
  Online agreement on match setup is a new design question, not a permanently
  excluded feature.

## What WebRTC supplies

Godot exposes `WebRTCPeerConnection`, `WebRTCDataChannel` and an integration with
the multiplayer API. The browser implementation is built in; native platforms
need an additional extension. Establishing a connection requires exchanging
offers, answers and connectivity candidates, usually through a signaling service.
The tutorial's in-process example is not an internet room service.
Source: [Godot WebRTC tutorial](https://docs.godotengine.org/en/stable/tutorials/networking/webrtc.html).

`WebRTCMultiplayerPeer` manages peer connections and channels. It does not create
offers or set session descriptions for the application. Choosing it still leaves
room lifecycle, signaling and game synchronization to the project.
Source: [Godot 4.7 WebRTCMultiplayerPeer](https://docs.godotengine.org/en/4.7/classes/class_webrtcmultiplayerpeer.html).

The `stable` tutorial currently carries a notice that its content has not yet
been updated for Godot 4.7. Class references are pinned to 4.7; API fit and real
connectivity must still be tested with the project's exact 4.7.2 build.

Direct connections are not always possible. TURN relays traffic when peers
cannot connect directly; it can be self-hosted or purchased as a service.
Source: [WebRTC TURN guide](https://webrtc.org/getting-started/turn-server).

## Plain-language technical distinctions

| Term | Meaning | What it does not establish |
|---|---|---|
| Signaling | Introduces two devices and exchanges connection information | Agreement on hits, HP or winners |
| Direct connection | Game data travels between the two devices | Guaranteed connectivity or low latency |
| TURN relay | A server forwards the devices' network traffic | An authoritative battle judge |
| Battle synchronization | Defines how both screens follow one match | Supplied automatically by a transport API |
| Determinism | The same full starting state and ordered inputs produce the same future state | Proven merely by using fixed ticks or one random seed |
| Delay-based input synchronization | Both sides wait for the inputs needed to advance | Immunity to divergent clocks, random calls or callback order |
| Rollback | Predict missing input, then restore and recompute when the actual input differs | Elimination of network latency or unlimited correction capacity |
| Authoritative simulation | One designated simulator decides the official state | Necessarily a dedicated server; a player's device can also be authoritative |

The synchronization descriptions are engineering alternatives under evaluation,
not a recommendation already accepted by the user. A transport test and a
cross-device battle-consistency test must have separate acceptance criteria.

## Evidence still needed before choosing a synchronization design

Code inspection identifies concrete blockers: live clock reads in
`godot/source_clock.gd:44`, independently running countdown timers in
`godot/match_countdown.gd:30`, and hit effects that consume shared randomness and
emit gameplay pause/resume events in `godot/hit_effect_runtime.gd:122`.
`godot/source_callback_registry.gd:4` retains placement and registration order;
`godot/fighter_runtime.gd:2286` provides a diagnostic snapshot, not complete
restorable state. These were inspected, not exercised as a networking test.

1. Inventory all match-affecting state, random consumers, wall-clock reads,
   timers, callback phases and ordering constraints, including helpers and nested
   timelines. Identify what can be controlled without changing original semantics.
2. Determine how to advance the complete match by an explicit step and how network
   waiting interacts with source timers, pause, intro and KO. Stopping only the
   fighter update is insufficient unless the remaining clocks are accounted for.
3. Run identical inputs and setup in separate instances, compare meaningful state
   throughout the match and find the first divergence. Extend to target browsers.
4. If rollback is selected, prove complete save/restore and repeatable re-simulation,
   including lifecycle/registry state and audio/visual event duplication handling.
5. Measure connection success, input latency, jitter, packet loss, background-tab
   behavior and performance on the chosen player networks. Numerical acceptance
   thresholds will be agreed after the target experience is selected.

## Cloudflare Durable Objects candidate

The user proposed Durable Objects after accepting small-scale service costs.
Cloudflare recommends one object per coordination unit, including a game session.
This supports a candidate mapping of one friend room to one object; it is an
engineering fit, not yet an accepted deployment decision.
Source: [Rules of Durable Objects](https://developers.cloudflare.com/durable-objects/best-practices/rules-of-durable-objects/).

A room object can accept both browsers' WebSocket connections and coordinate
membership and connection information. Hibernation preserves incoming WebSockets
while an idle object is evicted, but in-memory state is reset. Room membership
must be reconstructible from attachments/storage; continuous gameplay messages
must not be costed as an idle room.
Source: [DO WebSockets](https://developers.cloudflare.com/durable-objects/best-practices/websockets/).

Two distinct candidates need comparison:

- DO for rooms/signaling, WebRTC for gameplay, and a separate TURN service when
  a direct connection cannot be established.
- DO for rooms and all gameplay messages over WebSockets. This avoids a separate
  WebRTC setup but places the object and its TCP connections on every input path.

Neither arrangement automatically synchronizes Godot battle state or supplies
anti-cheat. Forwarding inputs does not make the room object a battle authority.
Cloudflare Realtime TURN is a separate managed service with its own credentials
and usage charges, not a capability obtained merely by creating a DO.
Source: [Cloudflare TURN](https://developers.cloudflare.com/realtime/turn/).

An object's location is not every edge location simultaneously. Placement hints
are best effort, and existing objects currently do not relocate. A generic
Asia-Pacific hint is not a guarantee of a mainland-China location or latency.
Mainland connectivity and latency remain measurement requirements.
Source: [DO data location](https://developers.cloudflare.com/durable-objects/reference/data-location/).

Cloudflare explicitly states that its Realtime TURN does not run in the China
Network; users in China connect to locations outside it. This does not mean
connections necessarily fail, but it makes real target-network measurement
essential before selecting it for mainland intercity gameplay.
Source: [TURN China Network FAQ](https://developers.cloudflare.com/realtime/turn/faq/#does-cloudflare-realtime-turn-run-in-the-cloudflare-china-network).

The TURN supplier can relay WebRTC data channels. If selected, keep the long-lived
TURN key/API token on the backend and issue short-lived credentials to admitted
room members. Rate limits and lifetime/renewal policy are application design work.
Sources: [TURN data FAQ](https://developers.cloudflare.com/realtime/turn/faq/#what-data-can-cloudflare-access-when-turn-is-used-with-webrtc),
[TURN credentials](https://developers.cloudflare.com/realtime/turn/generate-credentials/).

Pricing remains an estimate task after usage and a budget ceiling are known.
Count room-hours, incoming WebSocket messages, active object duration, storage and
relayed network bytes, including protocol overhead. Do not price every connected
room as hibernating or every session as directly connected.
Sources: [DO pricing](https://developers.cloudflare.com/durable-objects/platform/pricing/),
[TURN pricing FAQ](https://developers.cloudflare.com/realtime/turn/faq/#what-is-cloudflare-realtime-turn-pricing-how-exactly-is-it-calculated).

## Workflow sources

The locally installed [grilling skill](../../.agents/skills/grilling/SKILL.md)
drives the interview. Its missing local companion was read from the upstream
[domain-modeling skill](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md),
with its glossary and ADR formats. No skill installation was performed.
