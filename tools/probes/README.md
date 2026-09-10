# Scheduling probe tools

`build_minimal_swf.py` creates a small three-frame AVM1 container. JPEXS replaces
its empty actions with the checked-in AS2 fixtures. No locked input is rewritten.

Build all probes with:

```bash
python3 tools/probes/build_schedule_probes.py \
  --ffdec /absolute/path/to/ffdec-cli.jar \
  --output /tmp/bvn-schedule-probes
```

Enable native Debug Player trace output by installing `mm.cfg` as `~/mm.cfg`, then
open one generated SWF at a time. The debugger writes `flashlog.txt` beneath its
Macromedia preferences directory. Compare only lines prefixed with the probe ID.

Build the external frame-rate pair with:

```bash
python3 tools/probes/build_framerate_probe.py \
  --ffdec /absolute/path/to/ffdec-cli.jar \
  --output /tmp/bvn-framerate-probe
```

Open `host.swf` from that output directory so its relative `assist.swf` load resolves.


Native Flash captures share an account-wide log. All launchers must use
`capture_native_player.py` and `/tmp/bvn-native-flash-capture.lock`; unique run
IDs do not isolate file truncation. Lock scope includes launch, log collection,
local snapshot and termination of the owned player. Wait for the lock outside
the playback deadline. A batch collector must not impose a shorter timeout on
that wait. Previously started Python batch processes retain their loaded timeout
policy until restarted. Do not clear the global log to recover a failed case;
retain incomplete captures and rerun with a fresh run ID.
