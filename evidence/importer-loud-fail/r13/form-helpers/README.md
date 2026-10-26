# Original replacement helper observations (r13)

Root-only `build_form_helper_probe.py --observe-frames` invokes original wankai with HP 671, ql 234, wrapper Y 17, wudi true, undefined useAI and paused movement. Definitions and non-action placement tags remain unchanged. Native Flash Debugger 32.0.0.465 under Rosetta.

| Fighter | Next observation parent/body frame |
| --- | --- |
| Byakuya | 2 / 1046 |
| rifagu | 2 / 1204 |
| rukia | 2 / 1122 |

All three: after helper call 万解=true, transfer HP/ql=671/234, Y=17, live body HP/ql undefined. Next observation body HP/ql=671/234; key fields are 101 through 110; interval is undefined. Six events each (18 total), including done. These are bounded source observations, not complete combat or Godot parity. Earlier r09 separately covers AVM1 live-reference behavior.

Reproduce for each fighter:
```sh
python3 tools/probes/build_form_helper_probe.py --fighter rukia --observe-frames --ffdec /path/to/ffdec-cli.jar --output /tmp/helper-rukia
python3 tools/probes/capture_native_player.py /tmp/helper-rukia /tmp/helper-rukia/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 40
```

Each subdirectory preserves build metadata, native capture metadata/log and observer source; scratch SWFs are not committed.
