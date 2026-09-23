# Paired Chrome checkpoint sampling

This is a same-machine browser run of two production `Main` scenes using the
local matchmaking service and WebRTC data channels. It is diagnostic evidence
for startup and checkpoint determinism through confirmed frame 60; it is not a
full-fight, cross-device, internet/NAT/TURN, or final-release acceptance run.

## Foreground run

- Chrome `153.0.8010.53`, dedicated headless profile with focus emulation enabled
  for both pages.
- Page origin `http://127.0.0.1:8016`; local matchmaking service
  `http://127.0.0.1:8787`.
- This temporary harness used the retained token-based `/join` route; it did not
  validate the new short-code lobby UI.
- The host created a room, both pages joined, prepared, completed loaded/start
  barriers, started, exchanged confirmed state hashes through frame 60, and the
  host closed the room. The harness reported
  `reportsComplete=true`, `cleanupComplete=true`, `hashesMatch=true`, and
  `success=true` in 23.3 seconds.
- Both peers' frame 0, 30, and 60 fingerprints matched. The decoded checkpoint
  records also matched exactly at each frame: 478 records per peer at frame 0,
  501 at frame 30, and 501 at frame 60. The outer timer state and battle
  terminal-frame metadata matched at all three samples.
- The pre-existing false mismatch was not reproduced. Its older artifact
  `foreground-baseline.jsonl` is preserved and remains unexplained; it recorded
  a host frame-60 digest beginning `a35c1ee6c5792956` and a guest digest beginning
  `4d159113222bfeb8`, without decoded graph data.

The full decoded samples are kept outside the repository at
`/private/tmp/online-match-start-harness/graph-samples/foreground-de189fd8-3436-4227-b491-f4425a466456.json`.
The sanitized run log is
`/private/tmp/online-match-start-harness/foreground-graph-run.log`.

## Hidden-tab probe

One probe moved the guest to `visibility=hidden` after it had become ready, while
keeping the host visible and focused. The host's `loaded` command reached the
service, but the guest did not send `loaded`; service state remained
`loadedPresent=[true,false]` until the prepare deadline. The room returned to
lobby with `start_timeout`. The host then left successfully and closed its
room; the guest tab was restored for observation and then closed by the driver.
The driver's aggregate cleanup flag stayed false because the guest did not send
its own leave after recovery, although the service room was already closed by
the host. No frame checkpoint was captured in this run. This confirms that a hidden guest
can stall the current browser startup path; it does not invalidate the
foreground frame-60 result.

The sanitized run log is
`/private/tmp/online-match-start-harness/hidden-graph-run.log`; the summary
artifact is
`/private/tmp/online-match-start-harness/graph-samples/hidden_probe-5871216e-895f-4e17-8f7e-bb2bdcd8da81.json`.

## Commands and source identity

The temporary Web export was built with Godot `4.7.2.stable.official.ed1daf0bf`
from `/private/tmp/online-match-start-harness/godot`, then driven with:

```text
node /private/tmp/online-match-start-harness/run_main_start.mjs foreground
node /private/tmp/online-match-start-harness/run_main_start.mjs hidden_probe
```

SHA-256 values below identify the temporary source copy used in that export.
The lobby source includes diagnostic-only checkpoint capture instrumentation;
the exported pack hash pins the complete build.

```text
godot/main.gd                         d69a7ac80fa0c2a84f1f200e1015d498fed0af853f9b2a7fdf3c01ba303f81d8
godot/main.tscn                        35cb8e48c210c9f2d41b598fb9683d8ef9c5e1275a9a60cc94b402006e586e38
godot/online_lobby.gd                 47e6b3203f369eb6bd75e8949c12411b3df00962423dce511bb849d3c7263fbb
godot/online_match.gd                 40e2874b09813625ca9c16d744588d008a95ebcf9ba40be3abddc6a3bc46e2a9
godot/online_room_client.gd           7d671cd0b63822e41f368d767da2019baa310d17436f8b6d141c034ddbe88dd1
godot/online_peer_transport.gd        24852d96762233b7ca8bfa85fbb64bc939f5182da5fdffcd97eedc28482268bc
godot/battle_checkpoint.gd            a0fbf2417296f0bb4aa260f7d3131d0ea3595db7aaee88ddd5c150e6d5d842ea
godot/simulation_state.gd             dfc0b2c83eaf33418b7516746ee6934df1ef8a3d89e89c566ba4417a86b6bbc4
godot/rollback_battle.gd               eddc579324b308495ca25a800d7836558fadca644b0988d121def43bbec17b93
godot/rollback_session.gd              6c5620170e6658197e261945e7235e337bfb871668e71429dd925d81d4f68164
godot/online_session_state.gd          5b0f8f4cc36c681ea4c45893ccddfac876bb5e6af90e398f5aebac7a352bb134
godot/online_timer_authority.gd        d43910c5ec8390eb8698b896e9060f3493620542088c9a2f7f6d8b189778b35a
godot/tests/online_main_start_browser.gd 8f3baf5c739a6036bfc1bd822ad475c9dc8ba952e1b0f44e6abe1bf8e7caede1
web/index.pck                          c7c7d5aaa4050702a8f03cf7302d10d9c80d257c10fe6f231c293e7a4a52c5e5
```

At evidence capture time, the working-tree copies of these files were newer
than the temporary harness copy:

```text
working tree godot/online_match.gd       8432e0d657b88d42f42813f519515ebfbd7c64d41a7d7b6678831e813e3bb3ec
working tree godot/online_lobby.gd       28090473632021f5452c8130fda17903d5d352a2cb4b05e7b1f6eab2a823245c
working tree godot/online_room_client.gd 3ba776a050c1a5acf1a5e84f237821970a37283084c7d4520c717e495fe8fc18
```

The checkpoint, state, rollback, and peer-transport source hashes matched the
working tree. Therefore this result validates the checkpoint graph code used by
the current tree, while full current-UI/coordinator browser acceptance remains
pending. No credentials, invite codes, SDP, or ICE candidates are included in
the logs or artifacts.
