# VS Human selection: local browser integration

This evidence covers the real lobby connection and two-player character-selection flow in two isolated Chrome pages. It uses the production `RenderSurface`, `OnlineLobby`, `OnlineLobbyConnection`, `OnlineRoomClient`, `OnlinePeerTransport`, and `OnlineCharacterSelectionAdapter` scripts, plus the local matchmaking Worker at `127.0.0.1:8787`.

The browser test used a temporary Web export whose main scene was replaced with `online_pair_fixture.tscn`. The fixture creates and joins a room through the production Lobby callbacks, opts both clients into the explicit LAN host-candidate mode, and waits for the actual connect controls to be visible and enabled before invoking the production connect callback. Selection input is sent to each browser canvas with a real mouse activation followed by `D`/`J` keys. The fixture does not call the selection-commit helper directly. The choices are checked in both clients' room-state projections, then both clients use the production ready action. The test leaves the guest and host rooms before closing its browser pages.

The successful run printed:

```text
ONLINE_VSHUMAN_PROGRESS both room seats admitted; waiting for visible enabled connect controls
ONLINE_VSHUMAN_PROGRESS both production handlers entered; startup=connecting,connecting
ONLINE_VSHUMAN_PROGRESS both WebRTC channels open and fighter selection active; activating each real canvas
ONLINE_VSHUMAN_PROGRESS both players committed fighter and helper choices to room state
ONLINE_VSHUMAN_PROGRESS both ready commits visible on both room projections
ONLINE_VSHUMAN_TWO_CHROME_LOBBY_OK
ONLINE_VSHUMAN_TEST_ROOMS_CLEANED=true
```

The run used Chrome 153.0.8010.53, two pages on one machine, Godot 4.7.2, and `ICE_SERVERS=[]` with the explicit LAN test option enabled on both clients. It proves local RoomClient signaling, two open WebRTC data channels, the production Lobby selection UI, room persistence of both choices, and the ready barrier. It does not test two physical devices, cross-city routes, NAT traversal, TURN, or an actual match/battle.

The temporary PCK is identified by the SHA-256 in `results.json`; it is not the production `dist/web/index.pck`. `selection-fighters.png` is the captured production selection screen. The later lobby screenshot is intentionally not retained because it displayed the temporary room identifier.

## Reproduction

Use a disposable directory and a dedicated browser profile; do not use a user's normal Chrome profile.

1. Copy the current `godot/` project to `/private/tmp/online-vshuman/godot/` and copy this directory's `online_pair_fixture.gd` and `.tscn` into the project root.
2. Set `[application] run/main_scene="res://online_pair_fixture.tscn"` in the temporary `project.godot`.
3. Export that temporary project with Godot 4.7.2 to `/private/tmp/online-vshuman/web/index.html`.
4. Serve that directory on `127.0.0.1:8017` and confirm the local matchmaking service health endpoint on `127.0.0.1:8787` returns 200.
5. Start an isolated Chrome with `--headless=new --remote-debugging-address=127.0.0.1 --remote-debugging-port=9240 --user-data-dir=/private/tmp/online-vshuman/chrome-profile --disable-background-timer-throttling --disable-renderer-backgrounding`.
6. Run `node /private/tmp/online-vshuman/run_pair.mjs` with Node 24 or later. The driver creates two tabs, keeps invitation data in memory, reports only redacted status, and closes both tabs after the test.

The fixture and driver in this directory are the versions used for the successful run. No invitation, session token, signaling payload, or ICE candidate is written to the evidence.
