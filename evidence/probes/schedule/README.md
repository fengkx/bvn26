# AVM1 scheduling probes

Captured with the native reference runtime documented in
`evidence/reference-environment.md`. Sources live under `tools/probes/as2`; the SWF
container and reproducible build command live under `tools/probes`.

```bash
python3 tools/probes/build_schedule_probes.py \
  --ffdec /absolute/path/to/ffdec-cli.jar \
  --output /tmp/bvn-schedule-probes
```

Deterministic output SHA-256 values:

| Probe | SHA-256 |
|---|---|
| `goto.swf` | `d32efa5f231e96ae4f913e97d136ae364fec1379374cca6eac989b2fbe7743a8` |
| `enter_frame.swf` | `67f2036a1dbfe03e9a07bbbdf2c47570e6d3a556d9c54f8521ecf52298fde0be` |
| `stop_play_timer.swf` | `841f76fe621b62a854f40bfa462595bc4ce20be985971bd130c62d90b3635613` |
| `clip_lifecycle.swf` | `3c8d5b96d952245dd48cc1a0205b4c7d0c5b4587f175eb217c8b25f9cbe88083` |
| `callback_order.swf` | `73515c43e5430b572e64587e30ad09010bd684e8c27baff7304395e3f136a79a` |
| `sibling_order.swf` | `23a93e51ee313b2bba9aa08ca307aae557ab78f9a62f048a62c119b03b0ee5d9` |

The U-06 pair is built separately with `build_framerate_probe.py`:

| Probe | Header FPS | SHA-256 |
|---|---:|---|
| `host.swf` | 30 | `dffdc1c33f4111f2ef85e8fe23e32d4e5c241d5127cf05f8a781eb4dc936e354` |
| `assist.swf` | 24 | `54142c86988822bebdfc90eef84bad534e794f47c4615efffac42301d04742ed` |

Observed conclusions:

- `gotoAndPlay(3)` changes the destination but the caller's remaining statements run
  before frame 3's `DoAction`.
- On an ordinary advancing tick, `_currentframe` already names the destination frame
  when `onEnterFrame` runs; the destination frame's `DoAction` runs afterward.
- A placed child's `onClipEvent(enterFrame)` runs before the root destination frame
  script in the measured case.
- The measured callback order is child `onClipEvent(enterFrame)`, dynamic root
  `onEnterFrame`, then destination root `DoAction`.
- Sibling `onClipEvent(enterFrame)` callbacks run from higher display depth to lower
  display depth in the measured two-child case.
- A removal tag takes effect before that tick's child `enterFrame` and root frame script.
- `stop()` stops timeline advancement but does not stop `onEnterFrame` or `setInterval`.
- `play()` called by an interval does not advance immediately. Advancement and the target
  frame script occur on a later display tick.
- A 24 FPS SWF loaded into a 30 FPS host advances one source frame per host display tick;
  its own header FPS does not retain a 24/30 accumulator after loading. This matches the
  production path: `scripts/main.json` loads assistance SWFs through `MovieClipLoader`,
  and manifest entry `四代` maps to the only 24 FPS assistance file, `sidai.swf`.

The original `scripts/main.json` `frame_8/DoAction.as` defines gameplay pause separately
from player/runtime focus. `pauseGame()` sets `zhanting` and calls `stopMc` for both
fighters and both assistance clips; it does not clear intervals. Fighter enter-frame code
continues to be invoked but returns early while `zhanting` is true. `resumeGame()` clears
the flag and selectively calls `playMc`. This source path, combined with the measured
`stop()` behavior above, is the pause rule to port.

OS focus behavior and the game-specific result of simultaneous two-player hits remain
pending, so `M0-03` remains pending and the profile is explicitly provisional.
