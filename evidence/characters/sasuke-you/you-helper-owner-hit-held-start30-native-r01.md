# You helper owner-hit held start30 original capture r01

本记录采集佐助召唤鼬后，卡卡西从 fight tick 30 持续攻击至 tick 180 的原版 Flash 轨迹，并与同输入 native 结果对照。未修改 runtime、`game/` 或 `scripts/`。

## Fixture and explicit source configuration

- Fixture: `/private/tmp/sasuke-you-kakashi-owner-hit-held-start30-r01.json`
- Fixture SHA-256: `f4d23083f9c0e5855a6f506ca49bf97613b815b750d4d9990b5b97fca75e5c40`
- Setup: 佐助 p1 x=300、卡卡西 p2 x=350，双方 energy=300；frames after READY=360
- Inputs: p1 summon ticks 10..13；p2 attack ticks 30..180
- Fighters: p1 `sasuke`/佐助，p2 `kakashi`/卡卡西
- Explicit helpers: p1 `you`/鼬，p2 `kon`/魂（build CLI 显式传入）
- Fresh build/run: `/private/tmp/sasuke-you-kakashi-owner-hit-held-start30-original-r01`，run ID `sasuke-you-kakashi-owner-hit-held-start30-original-r01`
- Build metadata: `/Users/fengkx/me/code/bvn2_6/evidence/characters/sasuke-you/you-helper-owner-hit-held-start30-native-r01.build.json`
- Raw capture: `/Users/fengkx/me/code/bvn2_6/evidence/characters/sasuke-you/you-helper-owner-hit-held-start30-native-r01.original.log.gz`；raw SHA-256 `28c3a39625b0d50dd64e0ca47ca50bf9d9a9778a4dec55dbeebc86ff44ce7dd4`
- Collected events: `/Users/fengkx/me/code/bvn2_6/evidence/characters/sasuke-you/you-helper-owner-hit-held-start30-native-r01.events.jsonl.gz`；events SHA-256 `5e5b6c1c9beabb01d78b73b9125694b984bd1a836a6fe539695022c17f332fc6`
- Native input: `/private/tmp/sasuke-you-kakashi-owner-hit-held-start30-r01-native-r01/native.json`；native SHA-256 `d51b0f80fc5387aadf14f5928ddcc2f0e2d6c4dcb6829441718d340b0cb88902`

本次采集 10,804 条 raw AIREF 事件，含唯一 `ready`/`done`、360 fight ticks、0 条 post-done event、1,270 fighter states + 1,270 helper states；连续 run_id/sequence 校验通过。

## Original trace: owner hurt overlaps helper hit

- 佐助首次受击在 tick35：root frame862，HP 1000→970，随后短暂 paused；后续 owner 轨迹最终回到 frame1 at tick107，HP 保持970。
- 鼬 tick15 spawn。helper state 在 local frame48 at tick62 检测到卡卡西 `bdmn` 后，tick63 跳到 local frame92；随后 local frames 92..176 执行攻击段。攻击窗口标记出现在 frame128/129（tick99/100）、144/145（tick115/116）、160/161（tick131/132）、176/177（tick147/148）。对应卡卡西 HP 由项目 decoder 解码为 1000→960 (tick100)→920 (tick116)→880 (tick132)→780 (tick148)，共 4 hits；卡卡西保持在 x=322，未被 owner 伤害。
- 对应源脚本路径为 `scripts/fighter/fz/you.json`：`frame_48/PlaceObject2_24_3/CLIPACTIONRECORD onClipEvent(enterFrame).as` 用 `this.hitTest(_root.game["p" + _parent.pn].mc.bdmn)` 命中后 `gotoAndPlay("攻击2")`；`frame_76/DoAction.as` 是未命中时的 `gotoAndStop(1)` fallthrough。本 case 原版 raw 明确走命中分支，helper 由 48→92，攻击段的 marker 与 p2 HP 变化成对出现。

HP、hits 使用项目 decoder `tools/probes/collect_ai_reference.py:16` 的 `decode_number` 解释。

## Native comparison

比较命令：

```text
python3 tools/probes/compare_mode_reference.py /private/tmp/sasuke-you-kakashi-owner-hit-held-start30-original-r01/collected.json/events.jsonl /private/tmp/sasuke-you-kakashi-owner-hit-held-start30-r01-native-r01/native.json --output /private/tmp/sasuke-you-kakashi-owner-hit-held-start30-original-r01/compare-native.json
```

结果：`matched`，source states 722，native states 722，`differences=[]`。该结果显示当前 native 已覆盖 start30 的 owner hurt 与 You helper 攻击重叠路径；此项是固定输入证据，不能外推为广泛 parity。
