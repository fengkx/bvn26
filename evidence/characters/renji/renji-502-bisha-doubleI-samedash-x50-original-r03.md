# Renji continuous double I same direction dash x50 original capture r03

本记录将 Renji 两次 `必杀` 与一护两次同世界方向右冲刺的原版 Flash 轨迹，与现有同输入 native 结果对照。未修改 runtime、`game/` 或 `scripts/`。

## Fixture and source configuration

- Fixture: `/private/tmp/renji-i-magnet-r02/renji-502-bisha-continuous-doubleI-samedash-right-from-x50.json`
- Fixture SHA-256: `89b77f9aac151e090b4a7ab9f055d0406ed756362f27b5524bb6551c7217462f`
- Setup: 恋次 p1 x=300、一护 p2 x=50，双方 energy=300
- Inputs: p1 special ticks 10..13 and 74..77; p2 dash ticks 10..13 and 74..77
- Frames after READY: 240
- Explicit helper config: p1 `woailuo/我爱罗`、p2 `kon/魂`
- Fresh build/run: `/private/tmp/renji-502-bisha-original-r03`, run ID `renji-502-bisha-original-r03`
- Source/output/instrumentation hashes: `renji-502-bisha-doubleI-samedash-x50-original-r03.build.json`
- Raw capture: `renji-502-bisha-doubleI-samedash-x50-original-r03.original.log.gz`
- Collected events: `renji-502-bisha-doubleI-samedash-x50-original-r03.events.jsonl.gz`

The capture has 7,863 events, one `ready`, one `done`, 240 fight ticks, zero post-done events, 1,054 fighter states and 1,054 helper states. The Flash window was released after `done`.

## Original result and comparison

In the original capture, Renji enters root frame 502 at fight tick 11 and frame 503 at tick 12 for the first I; the attack placement frame 522 is tick 31 and active frames 544..549 are ticks 53..58. The second dispatch enters frame 502 at tick 75, frame 503 at tick 76, placement frame 522 at tick 95, and active frames 544..549 are ticks 117..122.

P2 dashes right in both windows: x=50→200 during the first dash and x=200→350 during the second. P2 HP remains 1000.0 and hits remains 0 throughout; values were interpreted with the project decoder in `tools/probes/collect_ai_reference.py:16`. The source state trace matches the existing 482-row native output at `/private/tmp/renji-i-magnet-r02/native/right-from-x50.json`; `renji-502-bisha-doubleI-samedash-x50-original-r03.compare.json` reports `matched` with 482 source and 482 native states.

This is a fixed-input original/native comparison for the x50 case. It does not establish the separate x0 boundary case or broad Renji parity.
