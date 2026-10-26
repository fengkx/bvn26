# Native special alias fallthrough (r13)

Original Flash Debugger 32.0.0.465, macOS Rosetta, windowed capture. Only root frame 1 is instrumented; original nested definitions and non-action root tags are verified unchanged. Movement is paused; original frame scripts run. This isolates energy deduction, not full combat parity.

| Source | Start | Next | Actual deduction |
| --- | --- | --- | --- |
| yihu.swf / parent 3 / sprite 1672 | frame 537, ql 234 | frame 538, ql 234 | frame 539, ql 134 |
| rifagu.swf / parent 2 / sprite 951 | frame 566, ql 234 | frame 567, ql 234 | frame 568, ql 134 |

Both single-frame 必杀 aliases naturally enter 空中必杀. The boundary frame has no DoAction; the following original DoAction subtracts 100. Label boundaries do not stop playback. Each capture has four state observations and one completion event (8 observations / 10 events total).

The importer now traverses only contiguous frames with no source script, no action-bytecode marker, and no new clip-action metadata. It stops at the first source frame and accepts only unconditional scalar numeric assignments and literal ql subtraction. Missing timeline frames, opaque bytecode, clip scripts, calls, conditional cost and timeline controls remain errors. Source cost path/hash are retained; no default cost is introduced.

Reproduce:
```sh
python3 tools/probes/build_special_cost_probe.py --fighter yihu --parent-frame 3 --sprite 1672 --start-frame 537 --ffdec /path/to/ffdec-cli.jar --output /tmp/yihu-cost
python3 tools/probes/build_special_cost_probe.py --fighter rifagu --parent-frame 2 --sprite 951 --start-frame 566 --ffdec /path/to/ffdec-cli.jar --output /tmp/rifagu-cost
python3 tools/probes/capture_native_player.py /tmp/yihu-cost /tmp/yihu-cost/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 40
python3 tools/probes/capture_native_player.py /tmp/rifagu-cost /tmp/rifagu-cost/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 40
python3 -m unittest discover -s tools/tests -p test_special_cost_fallthrough.py
```

Regression: 11 tests pass, including original locked source donors and rejection guards. Capture metadata contains source/probe/player hashes. No production runtime changes or allowlists.
