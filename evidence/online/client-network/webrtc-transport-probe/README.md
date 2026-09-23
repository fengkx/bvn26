# Two-page WebRTC transport probe

This isolated Godot Web export drives the production `OnlineRoomClient` and
`OnlinePeerTransport` against the local matchmaking service. It is a transport
smoke only; it does not load the production menu, `Main` or match coordinator.

The two pages use `BroadcastChannel` only to exchange the local test invitation
and coordinate socket readiness. Offer/answer/candidate signaling passes
through the service, and test payloads pass through real WebRTC data channels.
The test uses `ICE_SERVERS = []`; it does not test two machines, NAT traversal,
TURN or cross-city connectivity. The source deliberately does not print tokens,
SDP or ICE candidate contents.

## Run locally

Prerequisites: Godot 4.7.2 with Web export templates, the local matchmaking
Worker at `http://127.0.0.1:8787`, and a static server rooted at `dist/web` on
`http://127.0.0.1:8000`.

Export the fixture to a temporary subdirectory under the static root:

```sh
mkdir -p dist/web/_webrtc_transport
Godot --headless --path evidence/online/client-network/webrtc-transport-probe \
  --export-release Web "$PWD/dist/web/_webrtc_transport/index.html"
```

Start a dedicated Chrome profile on loopback CDP port 9234 with background
throttling disabled and keep it running while the driver executes. The driver
creates two isolated pages, enables Network/Runtime/Focus before navigation,
and holds both CDP sessions until cleanup. Then run:

```sh
node evidence/online/client-network/webrtc-transport-probe/run_pair.mjs
```

On success both clients leave and the driver closes both pages. On failure it
keeps the pages open for inspection. Do not print or persist CDP request bodies,
authorization headers, invitation/session tokens, SDP or ICE candidates.

## Recorded run

The 2026-09-23 run passed in headless Chrome 153.0.8010.53 in 2,974 ms:
both rooms completed local admission, both reliable/input channels opened, each
peer received one packet on each channel, and both leave requests returned 200.
The owner sent one offer and one candidate; the guest returned one answer and
one candidate. Both pages were closed after successful cleanup. A noncritical
static resource returned 404. See the parent [results](../results.json) for
the compact marker, response statuses, bounds and source hashes.

The run used RoomClient snapshot
`931228c401b5566a62952e48b1e97277496dae0343fd692d6bf7e4a500aa9762` and
PeerTransport `24852d96762233b7ca8bfa85fbb64bc939f5182da5fdffcd97eedc28482268bc`.
The copied RoomClient fixture was refreshed afterward to include the
read-only `is_command_in_flight()` accessor; that is the only source difference
from the tested snapshot. These hashes identify the probe source, not a release
build fingerprint.
