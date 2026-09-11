# Sasuke + You helper far guard original-player capture r02

本记录用于验证远距离持续防御时辅助鼬是否会误触发攻击或破防。未修改 runtime、`game/` 或 `scripts/`。

## Fixture and explicit source configuration

- Fixture: `/Users/fengkx/me/code/bvn2_6/evidence/characters/sasuke-you/sasuke-you-kakashi-guard-far-fixture-r01.json`
- Fixture SHA-256: `f4698649ebc7f469e2898512dfc036e01f7e7affc406b938456b78935c264c8b`
- Setup: 佐助 p1 x=300、卡卡西 p2 x=800，双方 energy=300；p1 summon ticks 10..13；p2 down ticks 1..240
- Frames after READY: 240
- Fresh build/run: `/private/tmp/bvn-sasuke-you-kakashi-guard-far-r02`, run ID `sasuke-you-kakashi-guard-far-r02`
- Explicit helper config: `p1_helper=you` / `p1sf=鼬`; `p2_helper=kon` / `p2sf=魂`
- Source and generated output hashes: `you-helper-guard-far-native-r02.build.json`
- Raw capture: `you-helper-guard-far-native-r02.original.log.gz`
- Collected events: `you-helper-guard-far-native-r02.events.jsonl.gz`
- Collector summary: `you-helper-guard-far-native-r02.summary.json`

The capture has 7,008 events, one `ready`, one `done`, 240 fight ticks, zero post-done events, one helper spawn, and 1,020 fighter plus 1,020 helper state events. The Flash window was released after the first `done`.

## Observed no-contact path

The source helper `scripts/fighter/fz/you.json` reaches helper frame 48 with `atm1` at fight tick 62. At x=800, the target is outside the `atm1` hitbox, so the source callback does not jump to root frame 92 (`攻击2`). The helper continues through source frame 59, reaches frame 60, sets `动作=0` at frame 61, continues through frame 75, and resets to frame 1 at fight tick 90. It is inactive from tick 91 onward. No `atm2` or `atm3` window is observed.

The synchronized target remains in source defense frame 1093 for the capture. Project decoder `tools/probes/collect_ai_reference.py:16` decodes the recorded HP fields: p2 HP is 1000.0 at the first fight state and 1000.0 at the final state; `hits` remains 0. This confirms no contact and no guard-break event in the far case.

This result matches the source no-hit branch at `scripts/fighter/fz/you.json`, `frame_48/PlaceObject2_24_3/CLIPACTIONRECORD onClipEvent(enterFrame).as`, followed by `frame_76/DoAction.as` (`_root.fzccXg(this); gotoAndStop(1)`). It is original-player source evidence for the far guard no-contact case, not a broad parity claim.
