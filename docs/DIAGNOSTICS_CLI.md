# Diagnostics CLI

Use `tools/analyze_diagnostics.py` to inspect local Web diagnostic exports without treating a comparison as proof of source parity.

```sh
python3 tools/analyze_diagnostics.py analyze /path/to/bvn26-log.json
python3 tools/analyze_diagnostics.py analyze /path/to/bvn26-log.json --json
python3 tools/analyze_diagnostics.py compare /path/to/baseline.json /path/to/candidate.json
python3 tools/analyze_diagnostics.py compare /path/to/baseline.json /path/to/candidate.json --json
python3 tools/analyze_diagnostics.py replay /path/to/eligible-v2-log.json \
  --godot /path/to/Godot --project /path/to/matching-godot-project \
  --output /private/tmp/replay-result.json
```

`analyze` reads legacy schema v1 console entries and v2 structured runtime exports. It reports build/PCK identity, event coverage and drops, input counts, match/player/pause snapshots, critical incidents, and replay limitations. For v1 files, it extracts JSON `COMBAT_EVENT` console lines but does not invent global fight ticks. A field such as `fighter.zhanting` is fighter-local; it does not establish global pause state.

Browser log exports also include a top-level `webrtc` object with bounded summaries for each observed `RTCPeerConnection`. This is separate from `runtime.events[].payload.network.rttAvailable`: the latter describes Godot's online-performance telemetry, while `webrtc` is sampled by the browser shell. `webrtc.available` means only that the constructor hook was installed; inspect each sample's status and `rttMs` before treating a measurement as available.

Each sample follows `transport.selectedCandidatePairId` to the selected candidate pair and reports local/remote candidate types. A `relay` type on either selected endpoint indicates that the selected pair uses a TURN relay; ICE-server configuration or an unselected relay candidate does not prove that TURN was selected. `currentRoundTripTime` is the ICE connectivity-check RTT, not application or input end-to-end latency. Sampling is at most 1 Hz, retains at most 8 connections and 60 samples per connection, and omits IPs, ports, candidate identifiers, URLs, SDP, and credentials.

`compare` ignores run IDs, build IDs, and observation timestamps when finding the first ordered event difference. It also reports the first snapshot path that differs. The result is a diagnostic comparison only; it is not a native-versus-source parity verdict.

`replay` invokes only the repository's fixed Godot fresh-Main executor; logs cannot select a script, scene, or `res://` path. `--project` points to the source Godot project copy used for the matching Web build and must contain unchanged embedded metadata and resources. The current executor accepts mode 3 (`versus`) with two human-controlled players only. It refuses schema v1, incomplete fresh-start input/random/clock capture, build/PCK/resource-version mismatch, and fighters/helpers/maps outside the current catalogs. Output paths must be new files. The executor's result JSON is authoritative for replay status; a preflight-ready report is not itself proof of exact replay.

A latest snapshot marked `completeCheckpoint: false` can still be eligible when a `match_started` event contains a canonical fresh-match recipe and the full input/random/clock stream is retained. The CLI reports those prerequisites separately from the executor's final verdict. Unsupported modes, AI configurations, and timer tape are rejected before invoking the executor.
