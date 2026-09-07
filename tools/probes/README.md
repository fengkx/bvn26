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
