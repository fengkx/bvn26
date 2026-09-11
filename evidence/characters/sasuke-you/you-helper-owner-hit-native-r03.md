# Sasuke + You helper owner-hit original-player capture r03

本记录验证召唤鼬后佐助本体受击时，鼬是否继续执行攻击并命中对手。未修改 runtime、`game/` 或 `scripts/`。

## Fixture and explicit source configuration

- Fixture: `/private/tmp/sasuke-you-kakashi-owner-hit-r02.json`
- Setup: 佐助 p1 x=300、卡卡西 p2 x=350，双方 energy=300；p1 summon ticks 10..13；p2 attack ticks 20..23
- Frames after READY: 360
- Fresh build/run: `/private/tmp/bvn-sasuke-you-kakashi-owner-hit-r03`, run ID `sasuke-you-kakashi-owner-hit-r03`
- Explicit helper config: `p1_helper=you` / `p1sf=鼬`; `p2_helper=kon` / `p2sf=魂`
- Source and generated output hashes: `you-helper-owner-hit-native-r03.build.json`
- Raw capture: `you-helper-owner-hit-native-r03.original.log.gz`
- Collected events: `you-helper-owner-hit-native-r03.events.jsonl.gz`
- Collector summary: `you-helper-owner-hit-native-r03.summary.json`

The capture has 10,918 events, one `ready`, one `done`, 360 fight ticks, zero post-done events, one helper spawn, and 1,294 fighter plus 1,294 helper state events. The Flash window was released after the first `done`.

## Observed owner-hit and helper continuation

The p2 attack reaches p1 at fight tick 25. The p1 source state changes to frame 862 with `hits=1`; the project decoder `tools/probes/collect_ai_reference.py:16` decodes p1 HP as 1000.0 before the hit and 970.0 after it. P1 remains in the hurt sequence through frames 862..870 and returns to the normal frame loop at tick 39.

The owner hit does not stop or reset the helper. The helper is already at frame 11 at tick 25, reaches `atm1` at frame 48/tick 62 and follows the hit branch to frame 92 at tick 63. It produces the three `atm2` windows at frames 128..129, 144..145, and 160..161, followed by `atm3` at frames 176..177. The synchronized p2 target receives four hits: HP 1000.0→960.0 at tick 100, →920.0 at tick 116, →880.0 at tick 132, and →780.0 at tick 148; p2 `hits` reaches 4.

This confirms the requested original-player behavior for this exact input: the owner is hurt while the helper animation continues, and the helper still interrupts/damages the opponent through its source attack windows. The source helper attack code is `scripts/fighter/fz/you.json`, with owner-hit handling isolated in `scripts/fighter/Sasuke.json`, `DefineSprite_1019/frame_1/DoAction.as` (`onBeHit0`, `onBeHit`, `hitlosehp`, and `beidax`).

## Evidence boundary

The instrumentation logs synchronized fighter/helper states and input delivery, but no direct `hitTest` callback event. Contact is established from source attack windows together with target frame, hit count, and HP transitions. This is an explicit source capture case, not a broad parity claim.
