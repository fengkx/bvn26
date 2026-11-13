# Local host-authority connectivity investigation

2026-11-13 follow-up to the merged experiment, base `db7a9ac44286bc68b9c2c63b05f26cf258a7dfc4`. This record does not rewrite the [2026-11-12 failure](../host-authority-experiment/README.md). **G0, weak-machine, two-physical-machine, TURN/Internet and production admission remain unpassed.**

## Diagnosis

The minimal browser-only data-channel pair still failed with default settings. Chromium logged mDNS resolution failure; stats had local candidates but no remote candidates/selected pair. Disabling mDNS and allowing loopback alone still failed. Advertised candidates included the local `utun9` address in the 198.18.0.0/15 benchmark range. A separate UDP self-echo succeeded on loopback and the physical interface, but timed out on that virtual interface. This is evidence about this machine's routing/candidate environment, not proof that all VPNs or all ICE implementations fail.

Explicit IP handling policy alone did not fix it. Holding a CDP `audioCapture` permission override for the **local test origin only** exposed additional interface candidates and allowed an ordinary browser-only pair to exchange ping/pong. The successful game runs used two independent temporary Chromium profiles and the same scoped override. The runner does not call `getUserMedia`, capture media, rewrite SDP/candidates, substitute WebRTC, or alter system routes. Closing the CDP session removes the override. This is a controlled testing workaround, not a product microphone requirement or LAN/Internet acceptance.

The game then opened reliable/input/state channels, exposing a separate product bug: `Buffer full! Dropping data.` in Godot's WebRTC receive buffer. Pacing only the initial snapshot was insufficient: the error also occurred after active play began. Sender `bufferedAmount` does not bound a busy receiver's queue.

## Fix

- Guest sends reliable presenter-ready before the host sends its initial display. Initial retries are at most once per second, with loaded still waiting for actual application/hash acknowledgement.
- Guest acknowledges the latest applied state after each drain. Host permits two unacknowledged states and keeps simulating at 30 Hz while replacing obsolete unsent display states. A third maximum-size packet is reserved for a paced recovery probe; neither the 16 KiB wire limit nor Godot's 64 KiB receive limit was increased.
- If an unreliable window is lost, one fresh state can probe each second only while recent reliable heartbeats prove the guest is processing. A stalled guest does not get a catch-up burst. Existing freeze/resume/abort behavior remains.
- Browser runner records selected candidate pair and all three open channels, strips addresses/ICE credentials from stats, separates prior-page console history, and explicitly records the permission override and pass/failure outcome. It additionally checks guest keyboard input reaches host simulation and returns as changed guest display position.

Final browser run: both peers selected a succeeded UDP host-candidate pair and opened reliable/input/state channels. Host advanced 239 ticks; guest applied 233 states with zero simulation ticks. Guest D key reached host input; its displayed X moved from 637.10 to 775.10 on both peers. Both browser error arrays were empty. This run uses the real local Worker, WebRTC and exported game, with the existing test fixture skipping the intro; it is not an entire manual lobby/rematch acceptance run.

Raw logs/exports stay outside the repository. [validation.json](validation.json) records hashes and observed outcomes. This is functional developer-machine validation, not a performance report; no GPU completion or time-to-photons measurement.

## Review residuals

The probe's `battle.advance()` includes synchronous materialization: `Main._advance_fight` invokes timeline rendering, `TimelinePreview._render_frame` calls `materialize_display` when there is no rollback owner, and the probe configures `Battle.configure(game, false)`. It excludes deferred engine rendering, GPU completion and pure-guest decode/application. Adding a second explicit materialize would double work. Documentation now states that boundary.

Authority lobby readiness intentionally skips the rollback-only selection/map peer connection. Its fixed content does not need that connection; ready submits the authoritative room profile and the Worker checks both profiles at prepare. This was not replaced with a second required connection. No presentation-only lifecycle rewrite or font/manifest asset churn was introduced.

Local Node remains 24.15 (repository requests >=24.18); this requirement was not loosened. Wrangler request-stream-after-response warnings appeared during ticket requests, but signaling, barriers and data channels completed; no evidence tied those warnings to the ICE failure, so unrelated Worker code was not changed.

References: [WebRTC stats](https://www.w3.org/TR/webrtc-stats/), [Chromium loopback/IP-policy switches](https://chromium.googlesource.com/chromium/src/+/lkgr/content/public/common/content_switches.cc), [Godot WebRTC receive-buffer limit](https://docs.godotengine.org/en/4.5/classes/class_projectsettings.html#class-projectsettings-property-network-limits-webrtc-max-channel-in-buffer-kb).
