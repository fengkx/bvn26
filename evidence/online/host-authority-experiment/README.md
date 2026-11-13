# Host-authority experiment validation

Development validation only, 2026-11-12. **G0, weak-machine acceptance and real two-machine performance are not passed.** No native/Flash/FDB/debugger captures were run. Admission/proof flags remain unchanged. The same Draft PR #285 includes the preceding G0 instrumentation and this optional online mode.

Implementation and reproduction: [HOST_AUTHORITY_EXPERIMENT.md](../../../docs/HOST_AUTHORITY_EXPERIMENT.md). Machine-readable receipts: [validation.json](validation.json). Large raw logs, browser profiles and exports remain in external temporary storage, not source control.

## Passed functional checks

- Godot 4.7.2 headless foundations: strict 15% host-selection boundary, tie/stall rules, invalid reports, bounded input FIFO, reorder/conflicting duplicate/stale/reset/overflow handling, binary encoding/compression and decompression cap.
- Probe smoke: 120 measured samples after warmup; fresh match scene starts at tick zero.
- Projection smoke: 330 host ticks, 220 skipped snapshots, guest simulation tick zero; actual codec, recursive render structure, frozen shadow and malformed-state rejection.
- Coordinator pair: both authority slots, 660 combat ticks plus source KO/terminal receipt settlement, same-connection recovery, crossing resume/state handling, application RTT echo, no guest simulation. Transport and room are in-process fixtures; this is not a WebRTC result.
- Exported Chromium 145.0.7632.6 offline display: 900 host ticks, 300 applied states, 600 intentionally skipped, guest simulation tick zero, 80 super-pause ticks, zero captured browser errors. Largest encoded display payload 16,377 bytes (fixture payload, not a transport-envelope bandwidth measurement). A screenshot was inspected: world, actors and HUD rendered. Headless WebGL2, local developer machine, 900×700 viewport, DPR 1; no performance admission inference.
- Existing rollback/display/transport/lobby tests: replay display; online match pair; timer/round; lobby UI and Web HUD; auto-connect/presence; map/selection integration; room client. Tests that count UI controls now include the mode selector. Existing pair fixture uses its wall-clock settlement deadline rather than a render-frame count; timer fixture registers the battle before its timer owner and waits for audio shutdown. No gameplay acceptance threshold was relaxed.
- Local matchmaking Worker: `npm test` (typecheck + 32 tests), including mode ownership/content restrictions, P2 authority, loaded/start barriers, receipt-based result and switch back to rollback. `npm run format:check` passed. Node 24.15 ran the suite; the repository requests Node ≥24.18, so this is recorded as a toolchain limitation.
- Eight G0 Python tests, eight online-manifest tests (including font coverage), `verify.py`, `check_handoff.py`, and `validate_contracts.py`. The latter remain structural checks, not gameplay/parity evidence.

## Not passed / unrun

Two dedicated local Chromium instances did not open WebRTC channels: SDP/ICE signaling completed but connections remained checking/new and ultimately failed/timed out. This also reproduced with a minimal browser-only RTCPeerConnection pair, and with system Chrome. Runs tried normal mDNS, disabled mDNS and explicitly allowed loopback. This bounds an environmental connectivity problem; it does **not** prove the game's full browser network path works. Real browser-to-browser play, TURN/Internet behavior, two physical machines, long sessions and adverse-network performance remain unverified.

Weak-machine G0 and display/application/packet/latency budgets remain unmeasured. GPU completion is UNKNOWN; submit CPU is not GPU completion or time-to-photons. No native parity or production admission is claimed. The guest currently rebuilds visual owners for each applied state, with immutable resource templates cached; its weak-machine cost must be measured.

The menu subset was regenerated with the existing OFL font tool using the installed Sarasa UI SC Regular face (index 199); source hash and covered literals are in `godot/generated/main/title_menu/font.json`. Gameplay assets and locked `game/` / `scripts/` inputs were not changed. Exported content/build fingerprints are regenerated after Godot import by the existing Web build pipeline; the historical checked-in manifest is not claimed as this experiment's exported identity.

Follow-up: [2026-11-13 local connectivity investigation](../host-authority-connectivity/README.md) adds new scoped browser evidence and receive-queue fixes. The original failed runs and unpassed gates above are unchanged.
